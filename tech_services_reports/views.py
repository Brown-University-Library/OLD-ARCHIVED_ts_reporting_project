# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint

# from tech_services_reports.lib.accessions_view_helper import AccessionReportMaker
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from tech_services_reports import settings_app
from tech_services_reports.lib.index_view_helper import DateMaker
from tech_services_reports.lib.accession_report_view_helper import AccessionReport, AccessionReportViewHelper


log = logging.getLogger("webapp")
dt_mkr = DateMaker()
accssn_rprt_hlpr = AccessionReportViewHelper()


def hi( request ):
    """ Returns simplest response. """
    now = datetime.datetime.now()
    log.debug( 'now, `{}`'.format(now) )
    return HttpResponse( '<p>hi</p> <p>( %s )</p>' % now )


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


def accessions_report( request, year, month ):
    log.debug( 'starting accessions_report()' )
    context = accssn_rprt_hlpr.make_context( year, month, request.scheme, request.get_host() )
    if request.GET.get( 'format', None ) == 'json':
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/accessions.html', context )
    return resp


def accessions_report_v2( request, year2, month2 ):
    log.debug( 'starting accessions_report_v2()' )
    context = accssn_rprt_hlpr.make_context_2( year2, month2, request.scheme, request.get_host() )
    if request.GET.get( 'format', None ) == 'json':
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/accessions_2.html', context )
    return resp


# def OLD_accessions_report(request, year, month=None, start=None, end=None):
#     log.debug( 'starting old accessions_report' )
#     log.debug( 'year, `{yr}`; month, `{mo}`; start, `{st}`; end, `{en}`'.format( yr=year, mo=month, st=start, en=end ) )
#     from django.template import loader, Context, RequestContext
#     from tech_services_reports.utility_code import AccessionReport, last_day_of_month, last_harvest
#     from datetime import date
#     # context = RequestContext(request)
#     context = {}
#     context['STATIC_URL'] = project_settings.STATIC_URL
#     context['HOME_URL'] = '{sch}://{hst}{url}'.format( sch=request.scheme, hst=request.get_host(), url=reverse('index_url') )
#     report_format = request.GET.get('format', None)
#     year = int(year)
#     if start and end:
#         #This becomes report label
#         context['report_date_header'] = "From %s to %s" % (start, end)
#     else:
#         if not month:
#             month = 1
#             start = date(year, month, 1)
#             #last day of the year
#             end = date(year, 12, 31)
#             context['report_date_header'] = "%s yearly total" % (year)
#         else:
#             month = int(month)
#             start = date(year, month, 1)
#             #Get the end of the month dynamically.
#             end = last_day_of_month(start)
#             context['report_date_header'] = "%s %s" % (start.strftime('%B'), year)
#     context['start'] = start
#     context['end'] = end
#     ar = AccessionReport(start, end)
#     report = {}

#     context['year'] = start.year
#     report['by_building'] = ar.building_summary()

#     context['all_formats_acq_type'] = ar.all_formats_acq_type()
#     context['acq_types'] = ar.acq_types()
#     context['building_count'] = ar.building_summary()
#     context['total_titles'] = ar.total_titles
#     context['total_volumes'] = ar.total_volumes
#     context['formats'] = ar.formats()
#     context['locations'] = ar.locations()
#     context['serial_added_volumes'] = ar.serial_added_volumes()

#     format_reports = []
#     for format in ar.formats():
#         format_reports.append(ar.by_format(format=format))
#     context['format_reports'] = format_reports

#     #Gcharts
#     chart_label = context['report_date_header']

#     context['by_format_chart_url'] = ar.gchart(ar.by_format_chart(),
#                                      chart_label,
#                                      'Accessions by format')

#     context['by_building_chart_url'] = ar.gchart(report['by_building'],
#                                      chart_label,
#                                      'Accessions by location',
#                                      color='3366CC')

#     #return HttpResponse(simplejson.dumps(report, indent=2))
#     context['report_header'] = settings_app.ACC_REPORT_HEADER
#     #context['format_reports'] = format_reports
#     context['settings_app'] = settings_app
#     context['last_updated'] = ar.last_updated
#     log.debug( 'type(context), `{}`'.format( type(context) ) )
#     log.debug( 'context, ```````{}```````'.format(pprint.pformat(context)) )

#     if report_format == 'csv':
#         return accesssions_report_csv(request, context)
#     else:
#         # return render_to_response('accessions.html', context)
#         return render(request, 'tech_services_reports_templates/accessions.html', context)


def cataloging( request, year, month ):
    msg = '<p>will return cataloging info for `{yr}` and `{mo}`</p>'.format( yr=year, mo=month )
    return HttpResponse( msg )

