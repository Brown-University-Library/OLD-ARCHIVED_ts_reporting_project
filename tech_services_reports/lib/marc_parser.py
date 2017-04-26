# -*- coding: utf-8 -*-

import datetime, logging, pprint, re
import pymarc
from tech_services_reports import settings_app
from tech_services_reports import utility_code
from tech_services_reports.utility_code import CatStat


log = logging.getLogger( "processing" )


class RecordParser(object):
    """ Contains functions for extracting data from a pymarc record object. """

    def __init__( self ):
        self.bib_number = None
        self.bib_created = None
        self.cat_date = None
        self.marc995 = None
        self.marc910 = None

    def parse_record( self, record ):
        """ Manages parsing.
            Called by Called by FileParser.parse_record()
            Note: not executing ```bib_level = record['998']['c']``` because it's not used anywhere. """
        self.get_bib( record )
        if not self.bib_number:
            return
        self.get_bib_created( record )
        self.get_cat_date( record )
        self.marc995 = self.get_field( record, '995' )
        self.marc910 = self.get_field( record, '910' )
        return

    def get_bib( self, record ):
        """ Extracts bib; includes check-digit.
            Called by parse_record() """
        try:
            self.bib_number = record['907']['a'][1:]  # lops off initial '.'
            if len( self.bib_number ) is not 9:
                self.bib_number = None
                log.info( 'invalid bib-length' )
        except TypeError:
            pass
        log.debug( 'bib_number, `{}`'.format(self.bib_number) )
        return self.bib_number

    def get_bib_created( self, record ):
        """ Extracts bib date string and attempts to return a date-object.
            Called by parse_record() """
        datestr = record['907']['c'].strip()
        self.bib_created = utility_code.convert_date(datestr)
        return self.bib_created

    def get_cat_date( self, record ):
        """ Extracts cat date string and attempts to return a date-object.
            Called by parse_record() """
        datestr = record['998']['b'].strip()
        self.cat_date = utility_code.convert_date(datestr)
        return self.cat_date

    def get_field( self, record, num_str ):
        """ Extracts 995 field if available.
            Returns a list of field-objects, or an empty list.
            Called by parse_record() """
        field_list = record.get_fields( num_str )
        return field_list

    # end class RecordParser()


class FileParser(object):
    """ Contains functions for iterating through a marc file.
        Notes:
        - The `return-data` init values are in the form of:
            self.count = { named_tuple_a: 1, named_tuple_b: 1 }
        - Example:
            self.cataloging_edit_count, ```{
                ('SAM', datetime.date(2016, 2, 2), 'ENRICH', 'b41376304', 'a', 'copy'): 1,
                ('SAM', datetime.date(2016, 2, 2), 'ENRICH', 'b41875436', 'a', 'copy'): 1
                }```
        - This is to prepare the fixtures that will be loaded into the db.  """

    def __init__( self ):
        ## time-tracker
        self.start_time = datetime.datetime.now()
        ## return data
        self.cataloging_edit_count = {}
        self.title_count = {}
        self.volume_count = {}
        ## loop-tracking data
        self.counter = 0
        self.count_processed = 0
        self.count_good = 0
        self.count_bad = 0
        self.last_position = 0
        self.current_position = 0
        self.process_flag = True
        self.segment_to_review = 'init'
        self.file_size = 0  # bytes

    def process_marc_file( self, marc_filepath, existing_items, location_format_map ):
        """ Manages processing.
            Called by management.commands.ts_reports_loader.summary() """
        with open( marc_filepath, 'rb' ) as fh:
            self.set_file_size( fh )
            reader = pymarc.MARCReader( fh )
            while self.process_flag is True:
                record = self.get_record( reader, fh, marc_filepath )
                data = self.parse_record( record, existing_items, location_format_map )
            self.log_summary( marc_filepath )
        return_tpl = ( self.cataloging_edit_count, self.title_count, self.volume_count )
        return return_tpl

    def set_file_size( self, fh ):
        """ Sets file size.
            Called by process_marc_file() """
        fh.seek( 0, 2 )
        self.file_size = fh.tell()
        fh.seek( 0 )
        return self.file_size

    def get_record( self, reader, fh, marc_filepath ):
        """ Tries to iterate to the next record.
            Called by process_marc_file() """
        record = None
        try:
            record = next( reader )
            self.count_good += 1
            self.current_position = fh.tell()
            self.last_position = self.current_position
        except Exception as e:
            self._handle_bad_record( e, fh, marc_filepath )
        self._update_counts( fh )
        return record

    def _handle_bad_record( self, e, fh, marc_filepath ):
        """ Updates necessary loop vars on unsuccessful record-instantiation.
            Called by get_record() """
        log.info( 'exception accessing record, ```{count}```; tell-count, ```{tell}```'.format( count=self.count_processed, tell=fh.tell() ) )
        log.info( 'exception in file, ```{fl}```\n; info-a, ```{err_a}```\ninfo-b, ```{err_b}```'.format( fl=marc_filepath, err_a=e, err_b=repr(e) ) )
        self.count_bad += 1
        self.current_position = fh.tell()
        segment_to_review_byte_count = self.current_position - self.last_position
        fh.seek( self.last_position )
        self.segment_to_review = fh.read( segment_to_review_byte_count )
        log.info( 'segment_to_review, ```{}```'.format( self.segment_to_review ) )  ## TODO: write these to a separate file
        fh.seek( self.current_position )
        self.last_position = self.current_position
        return

    def _update_counts( self, fh ):
        """ Updates `count_processed` after record record-instantiation.
            Called by get_record() """
        if fh.tell() == self.file_size:
            self.process_flag = False
        self.count_processed += 1
        if self.count_processed % 10000 == 0:
            log.info( '`{}` records processed'.format( self.count_processed ) )
        return



    def parse_record( self, record, existing_items, location_format_map ):
        """ Parses record to update counts.
            Called by process_marc_file()
            TODO: refactor; create a RecordParser() class """

        rp = RecordParser()
        rp.parse_record
        if not rp.bib_number:
            return

        # try:
        #     bib_number = record['907']['a'][1:]
        #     log.debug( 'bib_number, `{}`'.format(bib_number) )
        # except TypeError:
        #     log.debug( 'no bib_number' )
        #     return
        # bib_level = record['998']['c']
        # bib_created = get_bib_created( record )

        #==================================================================
        # Count cat edits
        #==================================================================
        # cat_date = utility_code.convert_date(record['998']['b'])
        cat_stat = CatStat(record)
        #Count cataloging edits
        #Store needed fields.
        # marc_995 = record.get_fields('995')
        mat_type = cat_stat.mat_type()
        source = cat_stat.cat_type()
        #Batch edit notes stored here.
        # marc_910 = record.get_fields('910')
        #Count the batch load info
        this_batch_edit = count_batch_edits(
            bib_number, bib_created, mat_type, marc_910, self.cataloging_edit_count, source )
        self.cataloging_edit_count.update(this_batch_edit)

        #Count individual edits added by staff.
        this_cat_edit = count_cataloging_edits(bib_number,
                                                    mat_type,
                                                    marc_995,
                                                    self.cataloging_edit_count,
                                                    source)
        self.cataloging_edit_count.update(this_cat_edit)

        #==================================================================
        # Count accessions based off item fields.
        #==================================================================
        items = record.get_fields('945')
        #Count the volumes
        #This will be dict with a named tuple as a key.
        this_count = count_volumes(items,
                                        cat_date,
                                        mat_type,
                                        existing_items, location_format_map)
        #We won't be counting everything - skipping some old items.
        if this_count is None:
            return
        #Pull the volume and title count from the accessions key.
        this_vol = this_count['volumes']
        this_title = this_count['titles']

        #Add the title count
        for k, title in this_title.items():
            self.title_count[k] = self.title_count.get(k, 0) + title

        #Add the volume count
        #Iterate through item counts and update
        for k, vol in this_vol.items():
            self.volume_count[k] = self.volume_count.get(k, 0) + vol

        return



    # def parse_record( self, record, existing_items, location_format_map ):
    #     """ Parses record to update counts.
    #         Called by process_marc_file()
    #         TODO: refactor; create a RecordParser() class """
    #     try:
    #         bib_number = record['907']['a'][1:]
    #         log.debug( 'bib_number, `{}`'.format(bib_number) )
    #     except TypeError:
    #         log.debug( 'no bib_number' )
    #         return
    #     bib_level = record['998']['c']
    #     bib_created = get_bib_created( record )

    #     #==================================================================
    #     # Count cat edits
    #     #==================================================================
    #     cat_date = utility_code.convert_date(record['998']['b'])
    #     cat_stat = CatStat(record)
    #     #Count cataloging edits
    #     #Store needed fields.
    #     marc_995 = record.get_fields('995')
    #     mat_type = cat_stat.mat_type()
    #     source = cat_stat.cat_type()
    #     #Batch edit notes stored here.
    #     marc_910 = record.get_fields('910')
    #     #Count the batch load info
    #     this_batch_edit = count_batch_edits(
    #         bib_number, bib_created, mat_type, marc_910, self.cataloging_edit_count, source )
    #     self.cataloging_edit_count.update(this_batch_edit)

    #     #Count individual edits added by staff.
    #     this_cat_edit = count_cataloging_edits(bib_number,
    #                                                 mat_type,
    #                                                 marc_995,
    #                                                 self.cataloging_edit_count,
    #                                                 source)
    #     self.cataloging_edit_count.update(this_cat_edit)

    #     #==================================================================
    #     # Count accessions based off item fields.
    #     #==================================================================
    #     items = record.get_fields('945')
    #     #Count the volumes
    #     #This will be dict with a named tuple as a key.
    #     this_count = count_volumes(items,
    #                                     cat_date,
    #                                     mat_type,
    #                                     existing_items, location_format_map)
    #     #We won't be counting everything - skipping some old items.
    #     if this_count is None:
    #         return
    #     #Pull the volume and title count from the accessions key.
    #     this_vol = this_count['volumes']
    #     this_title = this_count['titles']

    #     #Add the title count
    #     for k, title in this_title.items():
    #         self.title_count[k] = self.title_count.get(k, 0) + title

    #     #Add the volume count
    #     #Iterate through item counts and update
    #     for k, vol in this_vol.items():
    #         self.volume_count[k] = self.volume_count.get(k, 0) + vol

    #     return



    def log_summary( self, marc_filepath ):
        """ Logs summary of processing.
            Called by process_marc_file()
            (warning level really just for console output)
            """
        end_time = datetime.datetime.now()
        log.warning( 'summary for marc file, ```{}```'.format(marc_filepath) )
        log.warning( 'count_processed, `{}`'.format(self.count_processed) )
        log.warning( 'count_good_encoding, `{}`'.format(self.count_good) )
        if self.count_bad > 0:
            bad_msg = 'count_bad_encoding, `{}`; problem-segments are in log'.format( self.count_bad )
        else:
            bad_msg = 'count_bad_encoding, `{}`'.format( self.count_bad )
        log.warning( bad_msg )
        log.warning( 'time_taken, `{}`'.format( end_time-self.start_time ) )

    # end class FileParser()


def process_marc_file( marc_file, existing_items, location_format_map ):

    counter = 0
    cataloging_edit_count = {}
    title_count = {}
    volume_count = {}

    with open( marc_file, 'rb' ) as fh:

        start = datetime.datetime.now()
        fh.seek( 0, 2 ); file_size = fh.tell(); fh.seek( 0 )
        log.debug( 'file_size(K), `{}`'.format( file_size/1024 ) )
        count_processed = 0; count_good = 0; count_bad = 0
        last_position = 0; current_position = 0
        segment_to_review = 'init'
        # reader = pymarc.MARCReader( fh, to_unicode=True, force_utf8=True, utf8_handling='ignore' )
        # reader = pymarc.MARCReader( fh, force_utf8=True, utf8_handling='ignore' )
        # reader = pymarc.MARCReader( fh, utf8_handling='ignore' )
        reader = pymarc.MARCReader( fh )
        process_flag = True

        while process_flag is True:
            try:

                record = next( reader )
                count_good += 1
                current_position = fh.tell()
                last_position = current_position

                try:
                    bib_number = record['907']['a'][1:]
                    log.debug( 'bib_number, `{}`'.format(bib_number) )
                except TypeError:
                    log.debug( 'no bib_number' )
                    continue
                bib_level = record['998']['c']
                bib_created = get_bib_created( record )

                #==================================================================
                # Count cat edits
                #==================================================================
                cat_date = utility_code.convert_date(record['998']['b'])
                cat_stat = CatStat(record)
                #Count cataloging edits
                #Store needed fields.
                marc_995 = record.get_fields('995')
                mat_type = cat_stat.mat_type()
                source = cat_stat.cat_type()
                #Batch edit notes stored here.
                marc_910 = record.get_fields('910')
                #Count the batch load info
                this_batch_edit = count_batch_edits(
                    bib_number, bib_created, mat_type, marc_910, cataloging_edit_count, source )
                cataloging_edit_count.update(this_batch_edit)

                #Count individual edits added by staff.
                this_cat_edit = count_cataloging_edits(bib_number,
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
                this_count = count_volumes(items,
                                                cat_date,
                                                mat_type,
                                                existing_items, location_format_map)
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

            except Exception as e:
                ## info level to handle console output
                log.info( 'exception accessing record, ```{count}```; tell-count, ```{tell}```'.format(count=count_processed, tell=fh.tell() ) )
                log.info( 'exception in file, ```{fl}```\n; info-a, ```{err_a}```\ninfo-b, ```{err_b}```'.format( fl=marc_file, err_a=e, err_b=repr(e) ) )
                count_bad += 1

                current_position = fh.tell()
                segment_to_review_byte_count = current_position - last_position
                fh.seek( last_position )
                segment_to_review = fh.read( segment_to_review_byte_count )
                log.info( 'segment_to_review, ```{}```'.format(segment_to_review) )  ## TODO: write these to a separate file
                fh.seek( current_position )
                last_position = current_position

            if fh.tell() == file_size:
                process_flag = False
            count_processed += 1
            if count_processed % 10000 == 0:
                log.info( '`{}` records processed'.format(count_processed) )
            # if count_processed > 10000:
            #     break

        end = datetime.datetime.now()
        ## warning level really just for console output
        log.warning( 'summary for marc file, ```{}```'.format(marc_file) )
        log.warning( 'count_processed, `{}`'.format(count_processed) )
        log.warning( 'count_good_encoding, `{}`'.format(count_good) )
        if count_bad > 0:
            bad_msg = 'count_bad_encoding, `{}`; problem-segments are in log'.format( count_bad )
        else:
            bad_msg = 'count_bad_encoding, `{}`'.format( count_bad )
        log.warning( bad_msg )
        log.warning( 'time_taken, `{}`'.format(end-start) )

    log.info( 'cataloging_edit_count, ```{}```'.format( pprint.pformat(cataloging_edit_count) ) )
    log.info( 'title_count, ```{}```'.format( pprint.pformat(title_count) ) )
    log.info( 'volume_count dct, ```{}```'.format( pprint.pformat(volume_count) ) )
    return_tpl = ( cataloging_edit_count, title_count, volume_count )
    return return_tpl

    ## end def process_marc_file()


def get_bib_created( this_record ):
    d = this_record['907']['c']
    return utility_code.convert_date(d)


def count_batch_edits(
    bib_number, create_date, mat_type, marc_910, cat_edit_count, source ):
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


def count_cataloging_edits(
    bib_number, mat_type, marc_995, cat_edit_count, source ):
    #101111,sf,Catalog
    CAT_RE = re.compile('([0-9]{6})\,(\w+)\,(\w+)$')
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
                # print>>sys.stderr, "Month value not valid.", bib_number, marc_995
                log.warning( 'month value not valid; bib_number, `{bib}`; marc_995, `{mrc}`'.format( bib=bib_number, mrc=marc_995 ) )
                continue
            try:
                edate = datetime.date(year, month, day)
            except Exception as e:
                log.warning( 'date problem for bib, `{b}`: year, `{y}`; month, `{m}`; day, `{d}`'.format( b=bib_number, y=year, m=month, d=day ) )
                log.error( 'exception processing date, ```{}```'.format( repr(e) ) )
                log.warning( 'marc_995 field, ```{}```'.format(edit) )
                continue
            if edate.year < settings_app.BEGIN_YEAR:
                continue
            if edate.year == settings_app.BEGIN_YEAR:
                if edate.month < settings_app.BEGIN_MONTH:
                    continue
            _key = (editor, edate, ctype, bib_number, mat_type, source)
            cat_edit_count[_key] = cat_edit_count.get(_key, 0) + 1
    return cat_edit_count


def count_volumes( marc_items, cat_date, material_type, counted_items, location_format_map ):
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
        first_item = get_first_item( marc_items )
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
                # print>>sys.stderr, 'no location code ', item_number
                log.warning( 'no location code; item_number, `{}`'.format(item_number) )
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
            # print>>sys.stderr, item, e
            log.warning( 'error instantiating AcquisitionMethod(); error logged' )
            log.info( 'error instantiating AcquisitionMethod();\nitem, ```{itm}```;\ninfo, ```{err}```'.format( itm=item, err=repr(e) ) )
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

    ## end def count_volumes()


def get_first_item( items ):
    """Get the first attached item and use that as the accessions
    count date.  E.g.  Items will be counted as an accessioned title
    on the date of the first attached item."""
    first = datetime.date(1900, 1, 1)
    for count, item in enumerate(items):
        item_created = utility_code.convert_date(item['z'])
        if not item_created:
            continue
        #Initialize first attached item date.
        if count == 0:
            first = item_created
        if item_created < first:
            first = item_created
    return first
