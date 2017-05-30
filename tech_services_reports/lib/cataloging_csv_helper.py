# -*- coding: utf-8 -*-

import csv, datetime, json, logging, pprint

from django.http import HttpResponse
from tech_services_reports.lib.cataloging_report_view_helper import CatalogingReport


class CatalogingCSVwriter( object ):

    def __init__( self ):
        pass

    def get_csv_response( self, context ):

        report = context['report']
        header = context['report_header']
        header_details = "%s to %s" % (context['start'], context['end'])
    #    location_sort_order, format_sort_order = utility_code.load_sort_orders()
        #Prep CSV response with HTTP mimetype.
        response = HttpResponse( content_type='text/csv; charset=utf-8' )
        response['Content-Disposition'] = 'attachment; filename=cataloging_%s.csv'\
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
        cr = CatalogingReport(context['start'], context['end'])

        #By type
        #by_type_data = cr.by_type(report_format='csv')
        #for row in by_type_data:
        #    rw.writerow(row)

        #By format
        rw.writerow([])
        rw.writerow(['By format'])
        #report object
        data = cr.by_format(report_format='csv')
        for row in data:
            rw.writerow(row)


        #By format and type
        rw.writerow([])
        rw.writerow(['By format and type'])
        #report object
        data = cr.by_format_and_type(report_format='csv')
        for row in data:
            rw.writerow(row)

        #By cataloger
        rw.writerow([])
        rw.writerow(['By cataloger'])
        by_cataloger = cr.by_cataloger(report_format='csv')
        for row in by_cataloger:
            rw.writerow(row)

        #By cataloging edit type
        rw.writerow([])
        rw.writerow(['By cataloging edit type'])
        by_cataloger = cr.by_edit_type(report_format='csv')
        for row in by_cataloger:
            rw.writerow(row)

        #By cataloger and edit type
        #By cataloger and format
        rw.writerow([])
        rw.writerow(['By cataloger and format'])
        #report object
        data = cr.by_cataloger_and_edit_type(report_format='csv')
        for row in data:
            rw.writerow(row)

        #By cataloger and format
        rw.writerow([])
        rw.writerow(['By cataloger and format'])
        #report object
        data = cr.by_cataloger_and_format(report_format='csv')
        for row in data:
            rw.writerow(row)

        return response

        ## end def get_csv_response()

    ## end class CatalogingCSVwriter()
