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


#For format mappings
location_format_map = simplejson.load(urllib.urlopen(settings_app.LOCATION_FORMAT_URL))
location_format_map = location_format_map['result']['items']

#For cat edits
#101111,sf,Catalog
CAT_RE = re.compile('([0-9]{6})\,(\w+)\,(\w+)$')


class Command(BaseCommand):
    help = "For loading Josiah exports for reports."
    option_list = BaseCommand.option_list + (
        make_option('--summary', '-s', dest='summary',
                    help='Loads from MARC exports.  Expecting items in MARC exports.'),
    )

    def __init__(self):
        self.last_harvest = self.last_harvest()

    def handle(self, **options):
        if options['summary']:
            self.summary(options['summary'])
        else:
          print 'no file specified'

    def first_item(self, items):
        """Get the first attached item and use that as the accessions
        count date.  E.g.  Items will be counted as an accessioned title
        on the date of the first attached item."""
        from tech_services_reports.utility_code import convert_date
        from datetime import date
        first = date(1900, 1, 1)
        for count, item in enumerate(items):
            item_created = convert_date(item['z'])
            #Initialize first attached item date.
            if count == 0:
                first = item_created
            if item_created < first:
                first = item_created
        return first

    def counted_items(self):
        from tech_services_reports.models import Accession
        numbers = [i.number for i in Accession.objects.all()]
        return numbers

    def last_harvest(self):
        from tech_services_reports.models import Harvest
        from tech_services_reports import settings_app
        from datetime import date, timedelta
        try:
            last = Harvest.objects.order_by('date')[0:1].get()
            return last
        except:
            hdate = date(settings_app.BEGIN_YEAR, settings_app.BEGIN_MONTH, 1)
            #Set last harvest to one day before starting harvest info.
            hdate = hdate - timedelta(days=1)
            obj, created = Harvest.objects.get_or_create(date=hdate)
            obj.note = 'Initial harvest'
            obj.save()
            return obj

    def summary(self, marc_file):
        """Harvests data points from exported MARC fields.
        Date counts will include the date of a given harvest."""
        from tech_services_reports.utility_code import convert_date, CatStat
        from tech_services_reports.models import Accession, Cataloging, CatEdit,Harvest
        from datetime import date
        from pymarc import MARCReader
        #Dicts to store counts
        cataloging_edit_count = {}
        cataloging_count = {}
        title_count = {}
        volume_count = {}
        #Find items already counted.
        #Add logic to skip counted items.
        existing_items = self.counted_items()
        #Find last harvest.
        #Last harvest is only used as a date for scanning MARC records.
        #This should speed up loading but data is stored and aggregated
        #in the database by item create date and cat date without reference
        #to harvested date.
        last_harvest =self.last_harvest
        last_harvest_date = last_harvest.date
        this_harvest, created = Harvest.objects.get_or_create(date=date.today())
        this_harvest_date = this_harvest.date
        #Loop through marc records.
        for record in MARCReader(file(marc_file)):
            try:
                bib_number = record['907']['a'][1:]
            except TypeError:
                print>>sys.stderr, "No bib number"
                print>>sys.stderr, record
                continue
            bib_level = record['998']['c']
            bib_created = convert_date(record['998']['b'])
            cat_date = convert_date(record['998']['b'])
            cat_stat = CatStat(record)
#            if cat_date:
                #No longer using cataloging table.  All cataloging info
                #will be stored in CatEdits.
                #Count cataloging
#                if cat_date > last_harvest_date:
#                    if cat_date <= this_harvest_date:
#                        this_cat = self.count_cataloging(cat_date,
#                                                         bib_level,
#                                                         cat_stat,
#                                                         cataloging_count)
#                        cataloging_count.update(this_cat)
#
            #Count cataloging edits
            marc_995 = record.get_fields('995')
            mat_type = cat_stat.mat_type()
            source = cat_stat.cat_type()
            marc_910 = record.get_fields('910')

            #Count the batch load info
            this_batch_edit = self.count_batch_edits(
                           bib_number,
                           bib_created,
                           mat_type,
                           marc_910,
                           cataloging_edit_count,
                           source)
            cataloging_edit_count.update(this_batch_edit)

            this_cat_edit = self.count_cataloging_edits(bib_number,
                                                        mat_type,
                                                        marc_995,
                                                        cataloging_edit_count,
                                                        source)
            cataloging_edit_count.update(this_cat_edit)

            items = record.get_fields('945')
            #Count the volumes
            #This will be dict with a named tuple as a key.
            this_vol = self.count_volumes(items,
                                         this_harvest,
                                         existing_items)
            #Skip bibs without attached items.
            if this_vol == {}:
                continue
            #Use the details from the first attached volume for the title count.
            #Determine if this bib should count as a title.
            first_item = self.first_item(items)
            if first_item > last_harvest_date:
                if first_item <= this_harvest_date:
                    k = this_vol.keys()[0]
                    title_count[k] = title_count.get(k, 0) + 1
            #Iterate through item counts and update
            for k, vol in this_vol.items():
                volume_count[k] = volume_count.get(k, 0) + vol

        #Finish looping through MARC records
        #Write accession summary to DB
        #This might have to become a fixture.
        print>>sys.stderr, "Writing accessions stats to DB."
        for meta, count in volume_count.items():
            obj, created = Accession.objects.get_or_create(
                                                           number=meta.number,
                                                           created=meta.created,
                                                           acquisition_method=meta.acquisition_method,
                                                           location=meta.location,
                                                           format=meta.format,
                                                           defaults={'volumes': 0,
                                                                     'titles': 0},
                                                           )
            #Add volume count.  Need to add to what is there.  One harvest date
            #will have multiple files, each of which might have accessions or
            #cataloging on the same day.
            obj.volumes = obj.volumes + count
            try:
                title_val = title_count[meta]
            except KeyError:
                title_val = 1
            obj.titles = obj.titles + title_val
            #print>>sys.stderr, obj.volumes, obj.titles
            obj.save()

        print>>sys.stderr, "Writing cataloging edits to DB."
        for meta, count in cataloging_edit_count.items():
            cataloger, edate, ctype, bib, mat_type, source = meta
            obj, created = CatEdit.objects.get_or_create(edit_date=edate,
                                                        editor=cataloger,
                                                        type=ctype,
                                                        bib=bib,
                                                        mat_type=mat_type,
                                                        source=source)


    def count_volumes(self, marc_items, this_harvest, counted_items):
        """Create summary accession info for items created within given range."""
        from tech_services_reports.utility_code import convert_date, AcquisitionMethod
        from tech_services_reports.helpers import defaultdict as DD
        from tech_services_reports.helpers import namedtuple
        summary = DD(int)

        #Named tuple used as key for storing totals.
        #Method names need to match models.
        Acc = namedtuple('acc_summary', ['number',
                                         'created',
                                         'acquisition_method',
                                         'format',
                                         'location'],
                                        verbose=False)

        for item in marc_items:
            #Get acc note, skip anything without one.
            item_acc_note = item[settings_app.ITEM_ACC_NOTE]
            if not item_acc_note:
                continue

            try:
                item_number = item['y'].lstrip('.')
            except KeyError:
                print>>sys.stderr, 'no item number? ', item
                continue

            #Skip known items
            if item_number in counted_items:
                print>>sys.stderr, item_number, ' already counted.  skipping.'
                continue

            item_created = convert_date(item['z'])
            item_number = item['y']
            #Yes, some item records don't have a created date.
            if not item_created:
                print>>sys.stderr, 'no item create date? ', item
                continue
            #Skip items from before system was implemented.
            if item_created.year < settings_app.BEGIN_YEAR:
                continue
            if item_created.year == settings_app.BEGIN_YEAR:
                if item_created.month < settings_app.BEGIN_MONTH:
                    continue
#            if item_created <= self.last_harvest.date:
#                continue
#            #Shouldn't really be possible but you never know.
#            if item_created > this_harvest.date:
#                continue
            #Determine bib's accession date by
            try:
                if not item['l']:
                    continue
                raw_location = item['l'].strip()
                #Store raw location codes in case building names change in the future.
                #This will make display tricky.
                item_location = raw_location
                #item_location = location_format_map[raw_location]['building']
            except KeyError:
                #item_location = 'unknown'
                item_location = 'unknown'

            try:
                acquisition_method = AcquisitionMethod(item_acc_note).note
            except NameError, e:
                print>>sys.stderr, item_created, item_number, item_acc_note
                continue
            try:
                item_format = location_format_map[raw_location]['format']
            except KeyError:
                #print>>sys.stderr, "%s is an unknown location code." % item_location
                item_format = 'unknown'

            #Create a tuple for the summary key.
            if acquisition_method == 'Gift':
                print item

            _key = Acc(number=item_number,
                       created=item_created,
                       acquisition_method=acquisition_method,
                       format=item_format,
                       location=item_location)
            summary[_key] += 1

        return dict(summary)

    def count_cataloging(self, cat_date, bib_level, cat_stat, cataloging_count):
        """Store cataloging totals in dict with tuple key."""
        _key = (cat_date, bib_level, cat_stat.mattype, cat_stat.cattype)
        cataloging_count[_key] = cataloging_count.get(_key, 0) + 1
        return cataloging_count

    def count_cataloging_edits(self,
                               bib_number,
                               mat_type,
                               marc_995,
                               cat_edit_count,
                               source):
        for edit in marc_995:
            note = edit['a']
            if not note:
                continue
            match = CAT_RE.search(note)
            #print>>sys.stderr, note, match
            if match:
                _fields = {}
                edate, editor, ctype = match.groups()
                year = 2000 + int(edate[:2])
                month = int(edate[2:4])
                day = int(edate[4:6])
                edate = date(year, month, day)
                #Skip edits already captured with previous harvest.
                if edate <= self.last_harvest.date:
                    continue
                _key = (editor, edate, ctype, bib_number, mat_type, source)
                cat_edit_count[_key] = cat_edit_count.get(_key, 0) + 1
        return cat_edit_count

    def count_batch_edits(self,
                           bib_number,
                           create_date,
                           mat_type,
                           marc_910,
                           cat_edit_count,
                           source):
        """Count Shelf Ready bibs.  Email from Sam.
        YBP (b56908994) and Aux Amateurs (b57122490) use constant data in 910 $a.
        For Casalini (b57128510), the constant data we're interested in is
        placed in 910 $g.
        Also note that records created even a few weeks ago have overlays from our authority control vendor, Backstage Library Works; the YBP record also has an overlay from OCLC BibNote.  In these cases, the original cat date -- now lost -- equals the create date."""

        shelf_ready = False
        for field in marc_910:
            if field['a'] == 'ypb':
                shelf_ready = True
                editor = 'YBP'
            elif field['a'] == 'Aux Amateurs shelf-ready':
                shelf_ready = True
                editor = 'Aux Amateurs'
            elif field['g'].find('Casalini') > -1:
                shelf_ready = True
                editor = 'Casalini'

            #Logic for 910 to determine if it's Shelf ready.
            if shelf_ready:
                #print field
                _key = (editor, create_date, 'BATCH', bib_number, mat_type, source)
                cat_edit_count[_key] = cat_edit_count.get(_key, 0) + 1
                #Counted it, break out of this record.
                break


        return cat_edit_count
