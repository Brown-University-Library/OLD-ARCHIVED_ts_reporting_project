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
from tech_services_reports.lib import marc_parser
from tech_services_reports.models import Accession, CatEdit, Harvest
from tech_services_reports.utility_code import CatStat
from tech_services_reports.utility_code import convert_date


log = logging.getLogger( "processing" )
log.debug( 'loaded ts_reports_loader.py' )


#For format mappings
url = settings_app.LOCATION_FORMAT_URL
requests.packages.urllib3.disable_warnings()
r = requests.get( url, verify=False )
location_format_map = json.loads( r.content.decode('utf-8') )
# log.debug( 'location_format_map, ```{}```'.format(pprint.pformat(location_format_map)) )
location_format_map = location_format_map['result']['items']

#For cat edits
#101111,sf,Catalog
# CAT_RE = re.compile('([0-9]{6})\,(\w+)\,(\w+)$')

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
        first_item = marc_parser.get_first_item( items )
        return first_item


    def counted_items(self):
        """ Grabs stored accession items from db.
            Called by Command.summary() """
        log.debug( 'starting counted_items()' )
        timestamp = datetime.datetime.now()
        numbers = cache.get('counted_items__numbers')
        if numbers is None:
            from tech_services_reports.models import Accession
            numbers = set([i.number for i in Accession.objects.all()])
            cache.set( 'counted_items__numbers', numbers, settings_app.CACHED_ACCESSION_QUERY_SECONDS_TIMEOUT )  # cache for development convenience
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

    # def get_bib_created(self, this_record):
    #     from tech_services_reports.utility_code import convert_date
    #     d = this_record['907']['c']
    #     return convert_date(d)


    def get_bib_created( self, this_record ):
        dt = marc_parser.get_bib_created( this_record )
        return dt


    def check_file( self, marc_filepath ):
        """ Handles known api file-creation issues.
            Called by summary()
            Notes...
            - brace-check handles api-contents like, eg, `{"code":123,"specificCode":0,"httpStatus":401,"name":"Unauthorized","description":"invalid_grant"}`
            - brace-check also handles temporary hack for an `Invalid parameter` response.
            - error-code check handles the common `Record not found` response.
            """
        with open( marc_filepath, 'r' ) as fh:  # normally marc files are opened with 'rb'
            segment = fh.read( 20 )
            validity = True
            if segment[0] == '{':
                validity = False
            elif segment[0:10] == 'ErrorCode(':
                validity = False
            log.debug( 'validity, `%s`' % validity )
            return validity


    def summary(self, marc_filepath):
        """ Harvests data points from exported MARC fields.
            Date counts will include the date of a given harvest. """
        log.debug( 'starting summary()' )
        log.info( 'reading MARC file, ```{}```'.format(marc_filepath) )

        validity = self.check_file( marc_filepath )
        if validity is False:
            log.WARNING( 'file invalid; halting processing of ```%s```' % marc_filepath )
            return

        #Dicts to store counts
        cataloging_edit_count = {}
        # cataloging_count = {}
        title_count = {}
        volume_count = {}

        #Find items already counted.
        #Add logic to skip counted items.
        log.info( 'retrieving existing items stored in Accessions database' )
        existing_items = self.counted_items()

        #======================================================================
        # parse marc file
        #======================================================================

        #Loop through marc records.
        # ( cataloging_edit_count, title_count, volume_count ) = marc_parser.parse_marc_file( marc_file, existing_items )
        from tech_services_reports.lib.marc_parser import FileParser
        file_parser = FileParser()
        ( cataloging_edit_count, title_count, volume_count ) = file_parser.process_marc_file( marc_filepath, existing_items, location_format_map )

        log.debug( 'cataloging_edit_count, ```{}```'.format( pprint.pformat(cataloging_edit_count) ) )
        log.debug( 'title_count, ```{}```'.format( pprint.pformat(title_count) ) )
        log.debug( 'volume_count dct, ```{}```'.format( pprint.pformat(volume_count) ) )

        #Finish looping through MARC records

        #======================================================================
        # put individual counts together into  db fixture
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


    def count_volumes( self, marc_items, cat_date, material_type, counted_items ):
        """Create summary accession info for items created within given range."""
        volumes_and_titles_dct = marc_parser.count_volumes( marc_items, cat_date, material_type, counted_items )
        return volumes_and_titles_dct


    def count_cataloging_edits(self,
                               bib_number,
                               mat_type,
                               marc_995,
                               cat_edit_count,
                               source):
        cat_edit_count = marc_parser.count_cataloging_edits(
            bib_number, mat_type, marc_995, at_edit_count, source )
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
        cat_edit_count = marc_parser.count_batch_edits(
            bib_number, create_date, mat_type, marc_910, cat_edit_count, source )
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
