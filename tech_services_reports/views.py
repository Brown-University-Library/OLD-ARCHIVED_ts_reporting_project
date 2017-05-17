# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint

# from tech_services_reports.lib.accessions_view_helper import AccessionReportMaker
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from tech_services_reports import settings_app
from tech_services_reports.lib.index_view_helper import DateMaker
from tech_services_reports.lib.accession_report_view_helper import AccessionReport, AccessionReportViewHelper
from tech_services_reports.lib.cataloging_report_view_helper import CatalogingReportViewHelper

from tech_services_reports.lib.auth import bul_login


log = logging.getLogger("webapp")
dt_mkr = DateMaker()
accssn_rprt_hlpr = AccessionReportViewHelper()
ctlgng_rprt_hlpr = CatalogingReportViewHelper()


def hi( request ):
    """ Returns simplest response. """
    now = datetime.datetime.now()
    log.debug( 'now, `{}`'.format(now) )
    return HttpResponse( '<p>hi</p> <p>( %s )</p>' % now )



# def bul_login(func):
#     """ Decorator to create a user object for the Shib user and/or log the user in to Django.
#         Utility code function knows how to assign proper Django User object status. """
#     log.debug( 'starting bul_login() decorator' )
#     def decorator(request, *args, **kwargs):
#         import copy
#         from tech_services_reports.utility_code import pull_shib_info
#         from django.contrib.auth import authenticate, login
#         #Call Birkin's auth function
#         shib_dict = auth(request, data_only=True)
#         #data = simplejson.dumps( new_dict, sort_keys=True, indent=2 )
#         # user_obj = utility_code.pull_shib_info(request, shib_dict)
#         user_obj = pull_shib_info(request, shib_dict)
#         if not user_obj:
#             return HttpResponseForbidden('403 / Forbidden')
#         #else:
#             #user = authenticate(username=user_obj.username)
#         #login(request, user)
#         return func(request, *args, **kwargs)
#     return decorator

# def auth(request, data_only=None, SSL=None):
#   log.debug( 'starting auth()' )
#   # from django.utils import simplejson
#   import copy
#   # get rid of mod_wsgi dictionary items not serializable
#   new_dict = copy.copy(request.META)
#   log.debug( 'new_dict, ```{}```'.format(pprint.pformat(new_dict)) )
#   for (key, val) in request.META.items():
#     if 'passenger' in key:
#         new_dict.pop( key )
#     elif 'wsgi.' in key:
#         new_dict.pop( key )
#   # new_dict.pop('wsgi.errors')
#   # new_dict.pop('wsgi.file_wrapper')
#   # new_dict.pop('wsgi.input')
#   if data_only:
#       return new_dict
#   # data = simplejson.dumps( new_dict, sort_keys=True, indent=2 )
#   data = json.dumps( new_dict, sort_keys=True, indent=2 )
#   return HttpResponse(data, mimetype='text/javascript' )



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
    """ TODO: return a json serializable context. """
    log.debug( 'starting accessions_report_v2()' )
    context = accssn_rprt_hlpr.make_context_2( year2, month2, request.scheme, request.get_host() )
    if request.GET.get( 'format', None ) == 'json':
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/accessions_2.html', context )
    return resp


def cataloging_report( request, year, month ):
    log.debug( 'starting cataloging_report_v2' )
    context = ctlgng_rprt_hlpr.make_context( year, month, request.scheme, request.get_host() )
    if request.GET.get( 'format', None ) == 'json':
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/cataloging.html', context )
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



# def OLD_cataloging( request, year, month, start=None, end=None ):
#     from datetime import date, timedelta, datetime
#     from tech_services_reports.utility_code import CatalogingReport, last_day_of_month, last_harvest
#     from datetime import date
#     context = {}
#     context['STATIC_URL'] = project_settings.STATIC_URL
#     year = int(year)
#     context['year'] = year
#     #Handle custom dates
#     if start and end:
#         context['month'] = None
#     #Do monthly/yearly reports
#     else:
#         if not month:
#             month = 1
#             start = date(year, month, 1)
#             #last day of the year
#             end = date(year, 12, 31)
#             context['month'] = None
#         else:
#             month = int(month)
#             start = date(year, month, 1)
#             #Get the end of the month dynamically.
#             end = last_day_of_month(start)
#             context['month'] = start.strftime('%B')

#     context['report_header'] = settings_app.CAT_STATS_REPORT_HEADER
#     context['settings_app'] = settings_app
#     format = request.GET.get('format', None)
#     params = request.GET
#     context['start'] = start.strftime("%Y-%m-%d")
#     context['end'] = end.strftime("%Y-%m-%d")

#     cr = CatalogingReport(start, end)
#     #context['by_type'] = cr.by_type()
#     context['by_format'] = cr.by_format()
#     context['by_format_and_type'] = cr.by_format_and_type()
#     context['by_cataloger'] = cr.by_cataloger()
#     context['by_edit_type'] = cr.by_edit_type()
#     context['by_cataloger_and_format'] = cr.by_cataloger_and_format()
#     context['by_cataloger_and_edit_type'] = cr.by_cataloger_and_edit_type()
#     context['total_cataloged'] = cr.total_cataloged
#     context['report'] = cr
#     context['last_updated'] = cr.last_updated

#     chart_label = ''
#     if context['month']:
#         chart_label += context['month']
#     chart_label += ' ' + str(year)

#     context['by_format_chart_url'] = cr.gchart(context['by_format'],
#                                      chart_label,
#                                      'Cataloging by format')
#     context['by_edit_type_chart_url'] = cr.gchart(context['by_edit_type'],
#                                      chart_label,
#                                      'Cataloging by type',
#                                      color='3366CC')
# #    context['by_cataloger_chart_url'] = cr.gchart(context['by_edit_type'],
# #                                     chart_label,
# #                                     'By edit type',
# #                                     color='3366CC')
#     log.debug( 'context type, `{typ}`; context, ```````{val}```````'.format( typ=type(context), val=pprint.pformat(context) ) )
#     if format == 'csv':
#         return cataloging_report_csv(request, context)
#     else:
#         # template = loader.get_template('cataloging.html')
#         # response = HttpResponse(template.render(context))
#         # return response
#         return render(request, 'tech_services_reports_templates/cataloging.html', context)



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
