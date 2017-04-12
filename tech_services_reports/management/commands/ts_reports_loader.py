# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
  Loading accessions statistics.
"""

import datetime, json, logging, pprint, re, sys, time, urllib
from datetime import date, timedelta
from optparse import make_option

import pymarc, requests
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from tech_services_reports import settings_app


log = logging.getLogger( "processing" )
log.debug( 'loaded ts_reports_loader.py' )


#For format mappings
url = settings_app.LOCATION_FORMAT_URL
r = requests.get( url )
location_format_map = json.loads( r.content )
# log.debug( 'location_format_map, ```{}```'.format(pprint.pformat(location_format_map)) )
location_format_map = location_format_map['result']['items']

#For cat edits
#101111,sf,Catalog
CAT_RE = re.compile('([0-9]{6})\,(\w+)\,(\w+)$')

TODAY = datetime.date.today()
#Number of days to go back for reports.
CUTOFF_DAY_DELTA = datetime.timedelta(days=2)


class Command(BaseCommand):
    help = "For loading Josiah exports for reports."

    def add_arguments(self, parser):
        parser.add_argument(
            '--summary', dest='summary', help='Loads from MARC exports.  Expecting items in MARC exports.'
            )
        parser.add_argument(
            '--cleaner',
            dest='cleaner',
            help='Cleans up database by finding common data entry problems.'
            )

    def __init__(self):
        self.last_harvest = self.last_harvest()

    def handle(self, **options):
        log.debug( 'options, ```{}```'.format(pprint.pformat(options)) )
        if options['summary']:
            self.summary(options['summary'])
        elif options['cleaner']:
            self.cleaner()
        else:
          print>>sys.stderr, 'no file specified'

    def first_item(self, items):
        """Get the first attached item and use that as the accessions
        count date.  E.g.  Items will be counted as an accessioned title
        on the date of the first attached item."""
        from tech_services_reports.utility_code import convert_date
        from datetime import date
        first = date(1900, 1, 1)
        for count, item in enumerate(items):
            item_created = convert_date(item['z'])
            if not item_created:
                continue
            #Initialize first attached item date.
            if count == 0:
                first = item_created
            if item_created < first:
                first = item_created
        return first

    def counted_items(self):
        """ Grabs stored accession items from db.
            Called by Command.summary() """
        log.debug( 'starting counted_items()' )
        timestamp = datetime.datetime.now()
        numbers = cache.get('counted_items__numbers')
        if numbers is None:
            from tech_services_reports.models import Accession
            numbers = set([i.number for i in Accession.objects.all()])
            cache.set( 'counted_items__numbers', numbers, 60*60*24 )  # db grab cached for a day
        log.info( 'that took, `{}`'.format( str(datetime.datetime.now()-timestamp) ) )
        log.debug( 'first three numbers, ```{three}```; number-count, `{count}`'.format(three=list(numbers)[0:2], count=len(numbers)) )
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

    def get_bib_created(self, this_record):
        from tech_services_reports.utility_code import convert_date
        d = this_record['907']['c']
        return convert_date(d)

    def summary(self, marc_file):
        """Harvests data points from exported MARC fields.
        Date counts will include the date of a given harvest."""
        log.debug( 'starting summary()' )
        from tech_services_reports.utility_code import convert_date
        from tech_services_reports.utility_code import CatStat
        from tech_services_reports.models import Accession, CatEdit, Harvest
        from datetime import date
        log.info( 'reading MARC file, ```{}```'.format(marc_file) )
        #Dicts to store counts
        cataloging_edit_count = {}
        cataloging_count = {}
        title_count = {}
        volume_count = {}
        #Find items already counted.
        #Add logic to skip counted items.
        log.info( 'retrieving existing items stored in Accessions database' )
        existing_items = self.counted_items()
        #Loop through marc records.
        counter = 0
        for record in pymarc.MARCReader( open(marc_file), force_utf8=True, utf8_handling='ignore' ):
            # log.debug( 'record, ```{}```'.format(record) )
            if counter > 0 and counter % 10000 == 0:
                # print>>sys.stderr, '`{}` records processed'.format(counter)
                log.info( '`{}` records processed'.format(counter) )
            counter += 1
            try:
                bib_number = record['907']['a'][1:]
                log.debug( 'bib_number, `{}`'.format(bib_number) )
            except TypeError:
                log.debug( 'no bib_number' )
                continue
            bib_level = record['998']['c']
            bib_created = self.get_bib_created(record)
            #==================================================================
            # Count cat edits
            #==================================================================
            cat_date = convert_date(record['998']['b'])
            cat_stat = CatStat(record)
            #Count cataloging edits
            #Store needed fields.
            marc_995 = record.get_fields('995')
            mat_type = cat_stat.mat_type()
            source = cat_stat.cat_type()
            #Batch edit notes stored here.
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

            #Count individual edits added by staff.
            this_cat_edit = self.count_cataloging_edits(bib_number,
                                                        mat_type,
                                                        marc_995,
                                                        cataloging_edit_count,
                                                        source)
            cataloging_edit_count.update(this_cat_edit)
            #==================================================================
            # Count accessions based off item fields.
            #==================================================================
            items = record.get_fields('945')
            #Count the volumes
            #This will be dict with a named tuple as a key.
            this_count = self.count_volumes(items,
                                            cat_date,
                                            mat_type,
                                            existing_items)
            #We won't be counting everything - skipping some old items.
            if this_count is None:
                continue
            #Pull the volume and title count from the accessions key.
            this_vol = this_count['volumes']
            this_title = this_count['titles']

            #Add the title count
            for k, title in this_title.items():
                title_count[k] = title_count.get(k, 0) + title

            #Add the volume count
            #Iterate through item counts and update
            for k, vol in this_vol.items():
                volume_count[k] = volume_count.get(k, 0) + vol
        log.debug( 'volume_count dct, ```{}```'.format( pprint.pformat(volume_count) ) )

        #Finish looping through MARC records

        #======================================================================
        # Put the individual counts together into a db fixture.
        #======================================================================
        db_fixture = []
        # print>>sys.stderr, "Creating accessions stats fixture."
        log.info( 'creating accessions stats fixture' )
        for meta, count in volume_count.items():
            #Prep fixture.
            fixd = {}
            fixd['model'] = "tech_services_reports.accession"
            fixd['pk'] = meta.number
            f = {}
            #f['number'] = meta.number
            f['created'] = meta.created.isoformat()
            f['acquisition_method'] = meta.acquisition_method
            f['format'] = meta.format
            f['location'] = meta.location
            f['volumes'] = count
            try:
                title_val = title_count[meta]
            except KeyError:
                title_val = 0
            f['titles'] = title_val

            f['serial_added_volume'] = meta.serial_added_volume

            fixd['fields'] = f

            db_fixture.append(fixd)

        # print>>sys.stderr, "Creating cataloging stats fixtures."
        log.info( 'creating cataloging stats fixture' )
        for meta, count in cataloging_edit_count.items():
            fixd = {}
            fixd['model'] = "tech_services_reports.catedit"
            #Create a unique stamp to serve as the primary key.
            #Important not to change this as the database moves
            #forward.
            cataloger, edate, ctype, bib, mat_type, source = meta
            meta_str = ''.join([bib,
                                cataloger,
                                ctype,
                                mat_type,
                                source,
                                edate.isoformat(),])
            if len(meta_str) > 50:
                meta_str = meta_str.replace('Backstage Library Works', 'BL')
            if len(meta_str) > 50:
                # print>>sys.stderr, "Can't record edit for {0}.  Edit string too long.".format(bib)
                log.warning( "can't record edit for bib `{}`; edit string too long".format(bib) )
                continue
            fixd['pk'] = meta_str
            f = {}
            f['editor'] = cataloger
            f['edit_date'] = edate.isoformat()
            f['type'] = ctype
            f['bib'] = bib
            f['mat_type'] = mat_type
            f['source'] = source
            fixd['fields'] = f
            db_fixture.append(fixd)

        #Done.  Print the fixture.
        # print simplejson.dumps(db_fixture)
        print( json.dumps(db_fixture) )

        ## end def summary()


    def count_volumes(self, marc_items, cat_date, material_type, counted_items):
        """Create summary accession info for items created within given range."""
        log.debug( 'starting count_volumes()' )
        from tech_services_reports.utility_code import convert_date, AcquisitionMethod
        from tech_services_reports.helpers import defaultdict as DD
        from tech_services_reports.helpers import namedtuple
        from datetime import date
        # log.debug( 'marc_items[0:2], ```{}```'.format( pprint.pformat(marc_items[0:2]) ) )
        # log.debug( 'cat_date, `{}`'.format(cat_date) )
        # log.debug( 'material_type, `{}`'.format(material_type) )
        # log.debug( 'list(counted_items)[0:2], ```{}```'.format( pprint.pformat(list(counted_items)[0:2]) ) )  # this stays the same??

        summary = DD(int)
        summary_titles = DD(int)

        #Marker to hold whether this title has been counted as an accession.
        title_counted = False

        #Named tuple used as key for storing totals.
        #Method names need to match models.
        Acc = namedtuple('acc_summary', ['number',
                                         'created',
                                         'acquisition_method',
                                         'format',
                                         'location',
                                         'serial_added_volume'],
                                        verbose=False)

        #For determine if a title is accessioned.
        #Only need to find first attached items for those with more than
        #one item.
        #if len(marc_items) > 1:
        #Get the first items for serials.
        if material_type != 's':
            first_item = self.first_item(marc_items)
        else:
            first_item = cat_date

        #else:
        #first_item = date.today()
            #print>>sys.stderr, first_item
        for item in marc_items:
            try:
                item_number = item['y']
                if not item_number:
                    #print>>sys.stderr, 'no item number? ', item
                    continue
                if item_number:
                    item_number = item_number.lstrip('.')
            except KeyError:
                #print>>sys.stderr, 'no item number? ', item
                continue
            #Get acc note, skip anything without one.
            item_acc_note = item[settings_app.ITEM_ACC_NOTE]
            if not item_acc_note:
                #print>>sys.stderr, 'no accession note ', item_number
                continue

            item_created = convert_date(item['z'])
            #Yes, some item records don't have a created date.
            if not item_created:
                #print>>sys.stderr, 'no item create date? ', item
                continue
            #Skip items from before system was implemented.
            if item_created.year < settings_app.BEGIN_YEAR:
                #print>>sys.stderr, 'too old ', item_number, item_created
                continue
            if item_created.year == settings_app.BEGIN_YEAR:
                if item_created.month < settings_app.BEGIN_MONTH:
                    #print>>sys.stderr, 'too old ', item_number, item_created
                    continue
            #Don't count old stuff.
            #if TODAY - item_created < CUTOFF_DAY_DELTA:
            #    #print>>sys.stderr, "Old accession skipping. %s" % first_item
        #   continue
            #Skip known items
            if item_number in counted_items:
                #print>>sys.stderr, item_number, ' already counted.  skipping.'
                #print>>sys.stderr, '-',
                continue

            #Determine bib's accession date by
            try:
                if not item['l']:
                    print>>sys.stderr, 'no location code ', item_number
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
            except NameError as e:
                print>>sys.stderr, item, e
                continue
            try:
                item_format = location_format_map[raw_location]['format']
            except KeyError:
                #print>>sys.stderr, "%s is an unknown location code." % item_location
                item_format = 'unknown'

            #Serial added volumes: item record create date > bib record cat date AND bib record bib level equals = serial
            serial_added_volume = False
            if cat_date:
                if item_created > cat_date:
                    if material_type == 's':
                        serial_added_volume = True

            _key = Acc(number=item_number,
                       created=item_created,
                       acquisition_method=acquisition_method,
                       format=item_format,
                       location=item_location,
                       serial_added_volume=serial_added_volume)
            summary[_key] += 1

            #Add to the title count.
            if not title_counted:
                try:
                    if item_created <= first_item:
                        summary_titles[_key] += 1
                        title_counted = True
                except TypeError:
                    pass

        return_val = {'volumes': dict(summary), 'titles': dict(summary_titles)}
        if return_val['volumes'] or return_val['titles']:
            log.debug( 'return_val, ```{}```'.format( pprint.pformat(return_val) ) )
        return return_val


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
                if ctype == 'Batch Load':
                    ctype = 'Batch'
                year = 2000 + int(edate[:2])
                month = int(edate[2:4])
                day = int(edate[4:6])
                if month > 12:
                    print>>sys.stderr, "Month value not valid.", bib_number, marc_995
                    continue
                try:
                    edate = date(year, month, day)
                except Exception as e:
                    log.warning( 'date problem for bib, `{b}`: year, `{y}`; month, `{m}`; day, `{d}`'.format( b=bib_number, y=year, m=month, d=day ) )
                    log.error( 'exception processing date, ```{}```'.format( repr(e) ) )
                    log.warning( 'marc_995 field, ```{}```'.format( str(edit).decode('utf-8') ) )
                    continue
                if edate.year < settings_app.BEGIN_YEAR:
                    continue
                if edate.year == settings_app.BEGIN_YEAR:
                    if edate.month < settings_app.BEGIN_MONTH:
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
            edate = create_date
            if edate.year < settings_app.BEGIN_YEAR:
                    continue
            if edate.year == settings_app.BEGIN_YEAR:
                if edate.month < settings_app.BEGIN_MONTH:
                    continue
            if field['a'] == 'ybp':
                shelf_ready = True
                editor = 'YBP'
            elif field['a'] == 'Aux Amateurs shelf-ready':
                shelf_ready = True
                editor = 'Aux Amateurs'
            elif field['g'] == 'Casalini Libri':
                shelf_ready = True
                editor = 'Casalini'
            elif field['a'] == 'Coutts':
                shelf_ready = True
                editor = 'Coutts'
            elif field['a'] == 'BSLW shelfready':
                shelf_ready = True
                editor = 'Backstage Library Works'

            #Logic for 910 to determine if it's Shelf ready.
            if shelf_ready:
                #print field
                _key = (editor, create_date, 'batch load', bib_number, mat_type, source)
                cat_edit_count[_key] = cat_edit_count.get(_key, 0) + 1
                #Counted it, break out of this record.
                break
        return cat_edit_count

    def cleaner(self):
        """
        Utility to clean up common data entry problems.
        """
        #from tech_services_reports.utility_code import convert_date, CatStat
        from tech_services_reports.models import Accession, CatEdit, Harvest
        from datetime import date

        # location_format_map = simplejson.load(urllib.urlopen(settings_app.LOCATION_FORMAT_URL))
        location_format_map = json.loads(urllib.urlopen(settings_app.LOCATION_FORMAT_URL))
        location_format_map = location_format_map['result']['items']

        edits = CatEdit.objects.filter(type="Batch Load")
        print>>sys.stderr, "Will merge %s Batch Loads to Batch." % len(edits)
        for e in edits:
            print>>sys.stderr, e
            e.type = 'Batch'
            e.save()

        #Try to re-map unknown formats in accessions.
        unknowns = Accession.objects.filter(format="unknown")
        print>>sys.stderr, "Removing known unknowns -- approximately %s." % len(unknowns)
        for acc in unknowns:
            loc_code = str(acc.location)
            try:
                format = location_format_map[loc_code]['format']
                #print loc_code, format
                acc.format = format
                acc.save()
            except KeyError as e:
                print>>sys.stderr, "Bad code: ", loc_code




#        edits = CatEdit.objects.filter(type="Batch Load")
#        print>>sys.stderr, "Will merge %s Batch Loads to Batch." % len(edits)
#        for e in edits:
#            print>>sys.stderr, e
#            e.type = 'Batch'
#            e.save()





