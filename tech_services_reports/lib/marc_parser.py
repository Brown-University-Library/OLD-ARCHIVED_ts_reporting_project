# -*- coding: utf-8 -*-


def parse_marc_file( marc_file ):

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
