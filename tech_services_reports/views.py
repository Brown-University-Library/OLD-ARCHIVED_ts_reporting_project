# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from tech_services_reports.lib.index_view_helper import DateMaker


log = logging.getLogger("webapp")
dt_mkr = DateMaker()


def hi( request ):
    """ Returns simplest response. """
    now = datetime.datetime.now()
    log.debug( 'now, `{}`'.format(now) )
    return HttpResponse( '<p>hi</p> <p>( %s )</p>' % now )


# def index( request ):
#     log.debug( 'starting index()' )
#     context = {
#         'STATIC_URL': project_settings.STATIC_URL, 'acc_months': dt_mkr.get_acc_months(), 'acc_years': dt_mkr.get_acc_years(), 'cat_months': dt_mkr.get_cat_months(), 'cat_years': dt_mkr.get_cat_years() }
#     if request.GET.get( 'format', None ) == 'json':
#         jsn = json.dumps( context, sort_keys=True, indent=2 )
#         resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
#     else:
#         resp = render( request, u'tech_services_reports_templates/index.html', context )
#     return resp


def index( request ):
    log.debug( 'starting index()' )
    context = dt_mkr.make_context( request.scheme, request.get_host() )
    if request.GET.get( 'format', None ) == 'json':
        jsn = json.dumps( context, sort_keys=True, indent=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/index_v2.html', context )
    return resp


def accessions( request, year, month ):
    msg = '<p>will return accession info for `{yr}` and `{mo}`</p>'.format( yr=year, mo=month )
    return HttpResponse( msg )


def cataloging( request, year, month ):
    msg = '<p>will return cataloging info for `{yr}` and `{mo}`</p>'.format( yr=year, mo=month )
    return HttpResponse( msg )

