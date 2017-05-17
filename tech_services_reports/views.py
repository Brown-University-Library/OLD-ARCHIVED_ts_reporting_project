# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint

from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from tech_services_reports import settings_app
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
