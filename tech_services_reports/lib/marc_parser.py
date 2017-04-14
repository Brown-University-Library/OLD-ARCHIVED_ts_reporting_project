# -*- coding: utf-8 -*-

import datetime, logging
import pymarc
from tech_services_reports import utility_code
from tech_services_reports.utility_code import CatStat


log = logging.getLogger( "processing" )


def parse_marc_file( marc_file ):

    counter = 0

    with open( marc_file, 'rb' ) as fh:
        reader = pymarc.MARCReader( fh, to_unicode=True, force_utf8=True, utf8_handling='ignore' )
        start = datetime.datetime.now()
        count = 0
        for record in reader:
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

    ## end def parse_marc_file()


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
