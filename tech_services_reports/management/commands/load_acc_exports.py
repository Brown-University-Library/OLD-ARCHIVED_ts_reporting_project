# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
  Loading accessions statistics.
"""

import sys

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import simplejson
from optparse import make_option
import urllib

from datetime import timedelta
from datetime import date
import time
import re

from tech_services_reports import settings_app


def marc_field(field, indicator):
    try:
        data = field[indicator]
        if data:
            return data.strip()
    except TypeError, e:
        print>>sys.stderr, e
        return

#For format mappings
location_format_map = simplejson.load(urllib.urlopen(settings_app.LOCATION_FORMAT_URL))
location_format_map = location_format_map['result']['items']

#For cat edits
#101111,sf,Catalog
CAT_RE = re.compile('([0-9]{6})\,([a-z]+)\,([A-Z][a-z]+)$')


class Command(BaseCommand):
    help = "For loading Josiah exports for reports."
    option_list = BaseCommand.option_list + (
        make_option('--bib', '-b', dest='bib',
                    help='Loads Bib exports.  Need specific format.'),
        make_option('--item', '-i', dest='item',
                    help='Loads Item exports.  Need specific format.'),
        make_option('--marc', '-m', dest='marc',
                    help='Loads from MARC exports.  Expecting items in MARC exports.'),
        make_option('--item_fixture', '-y', dest='item_fixture',
                    help='Creates a fixture for the Item model based on CSV.'),
        make_option('--bib_fixture', '-z', dest='bib_fixture',
                    help='Creates a fixture for the Bib model based on CSV.'),
    )
    def handle(self, **options):
        if options['bib']:
          self.new_bibs(options['bib'])
        elif options['item']:
          self.new_items(options['item'])
        elif options['marc']:
          self.new_marc(options['marc'])
        elif options['item_fixture']:
          self.new_item_fixture(options['item_fixture'])
        elif options['bib_fixture']:
          self.new_bib_fixture(options['bib_fixture'])
        else:
          print 'no file specified'

    def new_bibs(self, bib_file):
      import csv
      from tech_services_reports.utility_code import convert_date
      from tech_services_reports.models import Bib, Item
      bibs = csv.reader(open(bib_file))
      bibs.next()
      bib_count = 0
      for row in bibs:
        if len(row) > 1:
            bib_count += 1
            number = row[0]
            cat_date = convert_date(row[1])
            level = row[2]
            items = row[3:]
            bib, o_created = Bib.objects.get_or_create(number=number)
            bib.level = level
            bib.cat_date = cat_date
            print>>sys.stderr, bib, o_created, cat_date
            for item in items:
                iobj, icreated = Item.objects.get_or_create(number=item)
                bib.items.add(iobj)
            bib.save()

    def new_items(self, item_file):
      import csv
      from tech_services_reports.utility_code import convert_date, AcquisitionMethod
      from tech_services_reports.models import Item
      items = csv.reader(open(item_file))
      items.next()
      #Get mappings from service
      location_format_map = simplejson.load(urllib.urlopen(settings_app.LOCATION_FORMAT_URL))
      location_format_map = location_format_map['result']['items']
      #RECORD #(ITEM)    CREATED(ITEM)    LOCATION    999    RECORD #(BIBLIO)
      item_count = 0
      for row in items:
        if len(row) > 1:
            item_count += 1
            number = row[0]
            create_date = convert_date(row[1])
            location = row[2].strip()
            acq_note = row[3]
            bibs = row[4:]
            item, obj_created = Item.objects.get_or_create(number=number)
            item.created = create_date
            print>>sys.stderr, item, obj_created
            #Normalize to lower case
            item.location = location.lower()
            item.format = location_format_map[location]['format']
            item.acquisition_method = AcquisitionMethod(acq_note).note
            item.save()


    def new_marc(self, marc_file):
        from tech_services_reports.utility_code import convert_date, CatStat
        from tech_services_reports.models import Bib, Item
        from datetime import date
        from pymarc import MARCReader
        fixture = []
        cedit_count = 0
        for record in MARCReader(file(marc_file)):
            bib_number = record['907']['a'][1:]
            bib_level = record['998']['c']
            cat_date = convert_date(record['998']['b'])
            cat_stat = CatStat(record)
            no_items = False
            #Create Bib fixture
            bdict = {}
            bdict['pk'] = bib_number
            bdict['model'] = 'tech_services_reports.bib'
            _fields = {}
            _fields['level'] = bib_level
            _fields['cat_type'] = cat_stat.cattype
            _fields['mat_type'] = cat_stat.mattype
            if cat_date:
                _fields['cat_date'] = cat_date.strftime("%Y-%m-%d")
            else:
                cat_date = None
            items = record.get_fields('945')
            #Need to do a check to see if any attached items
            #were created after the check d
            #Prep item fixture and append to main fixture
            _i = self.item_fixture(items)
            item_fixture = _i['fixture']
            valid_items = _i['valid_items']
            if len(_i['valid_items']) == 0:
                no_items = True
            #Checks to see if this bib, items pair is within reporting range.
            #The item_fixture function will skip items that aren't created
            #within the reporting range.
            #Skip pairs without a cat date and no items.
            if not cat_date:
                if no_items:
                    continue
            #Allow pairs with no cat date but with items to be added to the fixture.
            #Skip pairs with an old cat date and no items.
            if cat_date:
                if cat_date < date(2010, 10, 01):
                    if no_items:
                        continue
            #Item fixture is a list so we need to add it to main list.
            fixture += item_fixture
            _fields['items'] = valid_items
            bdict['fields'] = _fields
            #This is just a dict so append.
            fixture.append(bdict)

            #Get cat edits
            marc_995 = record.get_fields('995')
            cedit = self.cat_edit_fixture(marc_995, bib_number)
            fixture += cedit['fixture']
            cedit_count += len(cedit['fixture'])
            #print>>sys.stderr, cedit_count



        #print>>sys.stderr, "Total items: %d." % item_count
        print simplejson.dumps(fixture + item_fixture, indent=2)

    def item_fixture(self, marc_items):
        import urllib
        from tech_services_reports.utility_code import convert_date, AcquisitionMethod
        item_fixture = []
        item_count = 0
        valid_items = []
        for item in marc_items:
            try:
                item_number = item['y'].strip()[1:]
            #No item number?
            except AttributeError:
                continue
            item_created = convert_date(item['z'])
            try:
                item_location = item['l'].strip()
            except AttributeError:
                item_location = 'unknown'
            item_acc_note = item[settings_app.ITEM_ACC_NOTE]
            #Prep DB fixture
            #Skip items without create dates.
            if not item_created:
                continue
            #Skip items not created after the reporting start date.
            if item_created < date(settings_app.BEGIN_YEAR,
                                   settings_app.BEGIN_MONTH,
                                   1):
                continue
            try:
                acquisition_method = AcquisitionMethod(item_acc_note).note
            except NameError:
                #print>>sys.stderr, "Can't find acq method for %s." % item_acc_note
                acquisition_method = None
            except AttributeError:
                #print>>sys.stderr, "Skipping, no acq note for %s." % item_number
                #continue
                acquisition_method = None
            try:
                item_format = location_format_map[item_location]['format']
            except KeyError:
                #print>>sys.stderr, "%s is an unknown location code." % item_location
                item_format = None
            idict = {}
            idict['pk'] = item_number
            idict['model'] = 'tech_services_reports.item'
            _fields = {}
            _fields['acquisition_method'] = acquisition_method
            _fields['format'] = item_format
            _fields['location'] = item_location
            _fields['created'] = item_created.strftime("%Y-%m-%d")
            idict['fields'] = _fields
            item_fixture.append(idict)
            valid_items.append(item_number)
            item_count += 1
        return {'fixture': item_fixture,
                'valid_items': valid_items}

    def cat_edit_fixture(self, marc_995, bib_number):
        import re
        cat_edit_fixture = []
        for edit in marc_995:
            note = edit['a']
            match = CAT_RE.search(note)
            if match:
                _fields = {}
                ce_dict = {}
                ce_dict['pk'] = "%s%s" % (bib_number, note.replace(',', '').lower())
                ce_dict['model'] = 'tech_services_reports.catedit'
                _fields = {}
                edate, editor, ctype = match.groups()
                year = 2000 + int(edate[:2])
                month = int(edate[2:4])
                day = int(edate[4:6])
                edate = date(year, month, day).strftime("%Y-%m-%d")
                _fields['editor'] = editor
                _fields['edit_date'] = edate
                _fields['type'] = ctype
                _fields['bib'] = bib_number
                ce_dict['fields'] = _fields
                cat_edit_fixture.append(ce_dict)
            else:
                #print>>sys.stderr, "Cat edit note in other format " + note
                continue
        return {'fixture': cat_edit_fixture}


    def new_item_fixture(self, item_file):
        import csv
        import urllib
        from tech_services_reports.utility_code import convert_date, AcquisitionMethod
        from tech_services_reports.models import Item
        items = csv.reader(open(item_file))
        items.next()
        #Get mappings from service
        location_format_map = simplejson.load(urllib.urlopen(settings_app.LOCATION_FORMAT_URL))
        location_format_map = location_format_map['result']['items']
        #RECORD #(ITEM)    CREATED(ITEM)    LOCATION    999    RECORD #(BIBLIO)
        item_count = 0
        item_fixture = []
        for row in items:
            if len(row) > 1:
                item_count += 1
                number = row[0]
                create_date = convert_date(row[1])
                location = row[2].strip()
                acq_note = row[3]
                try:
                    acquisition_method = AcquisitionMethod(acq_note).note
                except NameError:
                    acquisition_method = None
                try:
                    format = location_format_map[location]['format']
                except KeyError:
                    print>>sys.stderr, "%s is an unkown location code." % location
                    format = None
                bibs = row[4:]
                idict = {}
                idict['pk'] = number
                idict['model'] = 'tech_services_reports.item'
                _fields = {}
                _fields['acquisition_method'] = acquisition_method
                _fields['format'] = format
                _fields['location'] = location
                _fields['created'] = create_date.strftime("%Y-%m-%d")
                idict['fields'] = _fields
                item_fixture.append(idict)

        print>>sys.stderr, "Total items: %d." % item_count
        print simplejson.dumps(item_fixture, indent=2)

    def new_bib_fixture(self, bib_file):
      import csv
      from tech_services_reports.utility_code import convert_date
      from tech_services_reports.models import Bib, Item
      bibs = csv.reader(open(bib_file))
      bibs.next()
      bib_count = 0
      bib_fixture = []
      for row in bibs:
        if len(row) > 1:
            bib_count += 1
            number = row[0]
            cat_date = convert_date(row[1])
            level = row[2]
            items = row[3:]
            if len(items) > 1000:
                print>>sys.stderr, number, len(items)
                continue
            bdict = {}
            bdict['pk'] = number
            bdict['model'] = 'tech_services_reports.bib'
            _fields = {}
            _fields['level'] = level
            if cat_date:
                _fields['cat_date'] = cat_date.strftime("%Y-%m-%d")
            else:
                cat_date = None
            _fields['items'] = items
            bdict['fields'] = _fields
            bib_fixture.append(bdict)

      print>>sys.stderr, "Total items: %d." % bib_count
      print simplejson.dumps(bib_fixture, indent=2)
#  {
#    "pk": "i157511923",
#    "model": "tech_services_reports.item",
#    "fields": {
#      "acquisition_method": "Gift",
#      "format": "Book",
#      "location": "qs",
#      "created": "2010-10-01"
#    }
#  },

#  {
#    "pk": "b40709796",
#    "model": "tech_services_reports.bib",
#    "fields": {
#      "items": [
#        "i124313553",
#        "i126742492",
#        "i145935723",
#        "i157736283"
#      ],
#      "level": "s",
#      "cat_date": "1994-05-20"
#    }
#  },



