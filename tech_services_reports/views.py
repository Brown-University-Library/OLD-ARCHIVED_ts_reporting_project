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
from tech_services_reports.lib.accession_csv_helper import AccessionCSVwriter
from tech_services_reports.lib.cataloging_csv_helper import CatalogingCSVwriter


log = logging.getLogger("webapp")
dt_mkr = DateMaker()
accssn_rprt_hlpr = AccessionReportViewHelper()
accssn_csv_wrtr = AccessionCSVwriter()
ctlgng_rprt_hlpr = CatalogingReportViewHelper()
ctlgng_csv_wrtr = CatalogingCSVwriter()


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


@bul_login
def accessions_report_csv( request ):
    log.debug( 'starting accessions_report_csv' )
    ( start, end ) = common.make_dates_from_params( request.GET )
    report_date_header = 'From {st} to {en}.'.format( st=start, en=end )
    context = accssn_rprt_hlpr.make_context( start, end, report_date_header, request.scheme, request.get_host() )
    resp = accssn_csv_wrtr.get_csv_response( context )
    return resp


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
def cataloging_report_csv( request ):
    log.debug( 'starting cataloging_report_csv' )
    ( start, end ) = common.make_dates_from_params( request.GET )
    report_date_header = 'From {st} to {en}.'.format( st=start, en=end )
    context = ctlgng_rprt_hlpr.make_context( start, end, report_date_header, request.scheme, request.get_host() )
    resp = ctlgng_csv_wrtr.get_csv_response( context )
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
