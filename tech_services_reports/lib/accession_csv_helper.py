# -*- coding: utf-8 -*-

import datetime, json, logging, pprint


class AccessionCSVwriter( object ):

    def __init__( self ):
        pass

    def write_data( self, context ):

        from utility_code import AccessionReport
        from tech_services_reports.helpers import namedtuple
        from tech_services_reports.settings_app import Acc
        from tech_services_reports.helpers import namedtuple
        from tech_services_reports.settings_app import AccTotal
        import csv
        #report = context['report']
        header = context['report_header']
        header_details = "%s to %s" % (context['start'], context['end'])
    #    location_sort_order, format_sort_order = utility_code.load_sort_orders()
        #Prep CSV response with HTTP mimetype.
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=accessions_%s.csv'\
                                         % header_details.replace(' to ', '_')
        rw = csv.writer(response, dialect='excel')
        #Begin csv creation
        rw.writerow([header])
        #Add last updated to header_details and convert to list
        header_details = [header_details]
        header_details += ['', '', 'Last updated: %s' % context['last_updated']]
        rw.writerow(header_details)
        #By type
        #rw.writerow([])
        #rw.writerow(['By cataloging type'])
        #report object
        ar = AccessionReport(context['start'], context['end'])

        #By building
        rw.writerow([])
        report = ar.building_summary()
        rw.writerow(['By building (volumes)'])
        rw.writerow(report['header'])
        for row in report['data']:
            rw.writerow(row)

        acq_type_header = []
        for acq_type in context['acq_types']:
            acq_type_header += [acq_type, '']

        #All formats by building
        rw.writerow([])
        report = ar.all_formats_acq_type()
        rw.writerow([report['header']])
        rw.writerow([''] + acq_type_header)
        #Multiply by length of acq_types to get the proper spacing.
        rw.writerow([' '] + settings_app.ACC_COUNT_TYPES * len(context['acq_types']))
        for location in context['locations']:
            this_row = []
            this_row.append(location)
            for acq_type in context['acq_types']:
                for count_type in settings_app.ACC_COUNT_TYPES:
                    _k = Acc(location=location.title(),
                             acquisition_method=acq_type.title(),
                             count_type=count_type)
                    try:
                        v = report['data'][_k]
                    except KeyError:
                        v = 0
                    this_row.append(v)
            rw.writerow(this_row)
        #Write the total row
        #{% accession_tuple_total report.data head "volumes" %}
        total_row = ['Total']
        for acq_type in context['acq_types']:
            for count_type in settings_app.ACC_COUNT_TYPES:
                _k = AccTotal(param=acq_type,
                          param2=count_type)
                try:
                    v = report['data'][_k]
                except KeyError:
                    v = 0
                total_row.append(v)
        rw.writerow(total_row)

        rw.writerow([])

        #Reports - all formats plus Serial Added Volumes
        report_set = context['format_reports']
        report_set.append(context['serial_added_volumes'])
        #Format reports
        for report in report_set:
            rw.writerow([report['header']])
            rw.writerow([''] + acq_type_header)
            #Multiply by length of acq_types to get the proper spacing.
            rw.writerow([''] + settings_app.ACC_COUNT_TYPES * len(context['acq_types']))
            for count, location in enumerate(context['locations']):
                this_row = []
                this_row.append(location)
                for acq_type in context['acq_types']:
                    for count_type in settings_app.ACC_COUNT_TYPES:
                        _k = Acc(location=location.title(),
                         acquisition_method=acq_type.title(),
                         count_type=count_type)
                        try:
                            v = report['data'][_k]
                        except KeyError:
                            v = 0
                        this_row.append(v)
                rw.writerow(this_row)
            #Write the total row
            #{% accession_tuple_total report.data head "volumes" %}
            total_row = ['Total']
            for acq_type in context['acq_types']:
                for count_type in settings_app.ACC_COUNT_TYPES:
                    _k = AccTotal(param=acq_type,
                              param2=count_type)
                    try:
                        v = report['data'][_k]
                    except KeyError:
                        v = 0
                    total_row.append(v)
            rw.writerow(total_row)
            #For spacing between reports
            rw.writerow([])

        return response

        ## end def write_data()

    ## end class AccessionCSVwriter()
