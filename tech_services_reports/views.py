# -*- coding: utf-8 -*-

import csv, datetime, json, logging, os, pprint

from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from tech_services_reports import settings_app
from tech_services_reports.lib import common
from tech_services_reports.lib.accession_report_view_helper import AccessionReport, AccessionReportViewHelper
from tech_services_reports.lib.auth import bul_login  # decorator
from tech_services_reports.lib.cataloging_report_view_helper import CatalogingReportViewHelper
from tech_services_reports.lib.index_view_helper import DateMaker


log = logging.getLogger("webapp")
dt_mkr = DateMaker()
accssn_rprt_hlpr = AccessionReportViewHelper()
ctlgng_rprt_hlpr = CatalogingReportViewHelper()


def hi( request ):
    """ Returns simplest response. """
    now = datetime.datetime.now()
    log.debug( 'now, `{}`'.format(now) )
    return HttpResponse( '<p>hi</p> <p>( %s )</p>' % now )


@bul_login
def index( request ):
    log.debug( 'starting index()' )
    context = dt_mkr.make_context( request.scheme, request.get_host() )
    log.debug( 'type(context), `{}`'.format( type(context) ) )
    if request.GET.get( 'format', None ) == 'json':
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/index.html', context )
    return resp


@bul_login
def accessions_report( request, year, month ):
    log.debug( 'starting accessions_report()' )
    ( start, end, report_date_header ) = accssn_rprt_hlpr.set_dates( year, month )
    context = accssn_rprt_hlpr.make_context( start, end, report_date_header, request.scheme, request.get_host() )
    if request.GET.get( 'format', None ) == 'json':
        context = accssn_rprt_hlpr.update_context_for_jsn( context )
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/accessions.html', context )
    return resp




def accessions_report_csv( request ):
    log.debug( 'starting accessions_report_csv' )
    ( start, end ) = common.make_dates_from_params( request.GET )
    log.debug( 'start, `{st}`; end, `{en}`'.format( st=start, en=end ) )
    log.debug( 'type(start), `{}`'.format( type(start) ) )
    report_date_header = 'From {st} to {en}.'.format( st=start, en=end )
    context = accssn_rprt_hlpr.make_context( start, end, report_date_header, request.scheme, request.get_host() )


    header = context['report_header']
    header_details = "%s to %s" % (context['start'], context['end'])
#    location_sort_order, format_sort_order = utility_code.load_sort_orders()

    #Prep CSV response with HTTP mimetype.
    # response = HttpResponse(mimetype='text/csv')
    response = HttpResponse( content_type='text/csv; charset=utf-8' )

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
                _k = settings_app.Acc(location=location.title(),
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
            _k = settings_app.AccTotal(param=acq_type,
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
                    _k = settings_app.Acc(location=location.title(),
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
                _k = settings_app.AccTotal(param=acq_type,
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


    return HttpResponse( 'in_progress' )




@bul_login
def cataloging_report( request, year, month ):
    log.debug( 'starting cataloging_report' )
    ( start, end, report_date_header ) = ctlgng_rprt_hlpr.set_dates( year, month )
    context = ctlgng_rprt_hlpr.make_context( start, end, report_date_header, request.scheme, request.get_host() )
    if request.GET.get( 'format', None ) == 'json':
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/cataloging.html', context )
    return resp


@bul_login
def custom_report( request ):
    log.debug( 'starting custom-report' )
    report_type = request.GET.get( 'report-type', None )
    ( start, end ) = common.make_dates_from_params( request.GET )
    report_date_header = 'From {st} to {en}.'.format( st=start, en=end )
    if report_type == 'accessions':
        context = accssn_rprt_hlpr.make_context( start, end, report_date_header, request.scheme, request.get_host() )
        resp = render( request, u'tech_services_reports_templates/accessions.html', context )
    elif report_type == 'cataloging':
        context = ctlgng_rprt_hlpr.make_context( start, end, report_date_header, request.scheme, request.get_host() )
        resp = render( request, u'tech_services_reports_templates/cataloging.html', context )
    return resp


###########################
## future TODO refactors ##
###########################


def accessions_report_v2( request, year2, month2 ):
    """ TODO: return a json serializable context. """
    log.debug( 'starting accessions_report_v2()' )
    context = accssn_rprt_hlpr.make_context_2( year2, month2, request.scheme, request.get_host() )
    if request.GET.get( 'format', None ) == 'json':
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/accessions_2.html', context )
    return resp


def cataloging_report_v2( request, year, month ):
    """ TODO: return a json serializable context. """
    log.debug( 'starting cataloging_report_v2' )
    context = ctlgng_rprt_hlpr.make_context_v2( year, month, request.scheme, request.get_host() )
    if request.GET.get( 'format', None ) == 'json':
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/cataloging.html', context )
    return resp
