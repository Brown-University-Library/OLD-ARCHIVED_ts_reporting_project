# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint
from .models import Accession, CatEdit
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render



log = logging.getLogger("webapp")


def hi( request ):
    """ Returns simplest response. """
    now = datetime.datetime.now()
    log.debug( 'now, `{}`'.format(now) )
    return HttpResponse( '<p>hi</p> <p>( %s )</p>' % now )


def index( request ):
    log.debug( 'starting index()' )
    context = {
        'STATIC_URL': project_settings.STATIC_URL, 'acc_months': indx_hlpr.get_acc_months(), 'acc_years': indx_hlpr.get_acc_years(), 'cat_months': indx_hlpr.get_cat_months(), 'cat_years': indx_hlpr.get_cat_years() }
    if request.GET.get( 'format', None ) == 'json'
        jsn = json.dumps( context, sort_keys=True, index=2 )
        resp = HttpResponse( jsn, content_type=u'application/javascript; charset=utf-8' )
    else:
        resp = render( request, u'tech_services_reports_templates/index.html', context )
    return resp

    #Accessions
    #Months to reports
    acc_months = cache.get( 'acc_months_cached' )
    if acc_months is None:
        acc_months = Accession.objects.dates('created', 'month', order='DESC')
        cache.set( 'acc_months_cached', acc_months, 60*60*24 )  # 1 day
    #Years to report
    acc_years = cache.get( 'acc_years_cached' )
    if acc_years is None:
        acc_years = Accession.objects.dates('created', 'year', order='DESC')
        cache.set( 'acc_years_cached', acc_years, 60*60*24 )
    context['acc_months'] = acc_months
    context['acc_years'] = acc_years

    #Cataloging
    cat_months = cache.get( 'cat_months_cached' )
    if cat_months is None:
        cat_months = CatEdit.objects.dates('edit_date', 'month', order='DESC')
        cache.set( 'cat_months_cached', cat_months, 60*60*24 )
    #Years to report
    cat_years = cache.get( 'cat_years_cached' )
    if cat_years is None:
        cat_years = CatEdit.objects.dates('edit_date', 'year', order='DESC')
        cache.set( 'cat_years_cached', cat_years, 60*60*24 )
    context['cat_months'] = cat_months
    context['cat_years'] = cat_years

    # context['settings_app'] = settings_app
    log.debug( 'context, ```{}```'.format(pprint.pformat(context)) )
    index_resp = render( request, u'tech_services_reports_templates/index.html', context )
    return index_resp


# def index( request, response_format=None ):
#     log.debug( 'starting index()' )

#     context = { 'STATIC_URL': project_settings.STATIC_URL }
#     params = request.GET
#     if 'format' in params.keys():
#         requested_format = params['format']
#     else:
#         requested_format = None

#     #Accessions
#     #Months to reports
#     acc_months = cache.get( 'acc_months_cached' )
#     if acc_months is None:
#         acc_months = Accession.objects.dates('created', 'month', order='DESC')
#         cache.set( 'acc_months_cached', acc_months, 60*60*24 )  # 1 day
#     #Years to report
#     acc_years = cache.get( 'acc_years_cached' )
#     if acc_years is None:
#         acc_years = Accession.objects.dates('created', 'year', order='DESC')
#         cache.set( 'acc_years_cached', acc_years, 60*60*24 )
#     context['acc_months'] = acc_months
#     context['acc_years'] = acc_years

#     #Cataloging
#     cat_months = cache.get( 'cat_months_cached' )
#     if cat_months is None:
#         cat_months = CatEdit.objects.dates('edit_date', 'month', order='DESC')
#         cache.set( 'cat_months_cached', cat_months, 60*60*24 )
#     #Years to report
#     cat_years = cache.get( 'cat_years_cached' )
#     if cat_years is None:
#         cat_years = CatEdit.objects.dates('edit_date', 'year', order='DESC')
#         cache.set( 'cat_years_cached', cat_years, 60*60*24 )
#     context['cat_months'] = cat_months
#     context['cat_years'] = cat_years

#     # context['settings_app'] = settings_app
#     log.debug( 'context, ```{}```'.format(pprint.pformat(context)) )
#     index_resp = render( request, u'tech_services_reports_templates/index.html', context )
#     return index_resp


def accessions( request, year, month ):
    msg = '<p>will return accession info for `{yr}` and `{mo}`</p>'.format( yr=year, mo=month )
    return HttpResponse( msg )


def cataloging( request, year, month ):
    msg = '<p>will return cataloging info for `{yr}` and `{mo}`</p>'.format( yr=year, mo=month )
    return HttpResponse( msg )

