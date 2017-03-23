# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint
from .models import Accession, CatEdit
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

log = logging.getLogger(__name__)


def hi( request ):
    """ Returns simplest response. """
    now = datetime.datetime.now()
    return HttpResponse( '<p>hi</p> <p>( %s )</p>' % now )


def index( request ):
    """ Returns simplest response. """
    now = datetime.datetime.now()
    return HttpResponse( '<p>index</p> <p>( %s )</p>' % now )


# @bul_login
def index( request, response_format=None ):
    # import time
    # from datetime import date
    # from django.db import connection, transaction
    # from django.template import loader, RequestContext
    # context = RequestContext( request )
    context = {}
    params = request.GET
    if params.has_key( 'format' ):
        requested_format = params['format']
    else:
        requested_format = None
    #Accessions
    #Months to reports
    acc_months = Accession.objects.dates('created', 'month', order='DESC')
    #Years to report
    acc_years = Accession.objects.dates('created', 'year', order='DESC')
    context['acc_months'] = acc_months
    context['acc_years'] = acc_years

    #Cataloging
    cat_months = CatEdit.objects.dates('edit_date', 'month', order='DESC')
    #Years to report
    cat_years = CatEdit.objects.dates('edit_date', 'year', order='DESC')
    context['cat_months'] = cat_months
    context['cat_years'] = cat_years

    # context['settings_app'] = settings_app
    resp = render( request, u'tech_services_reports_templates/index.html', context )
    return render_to_response('index.html', context)
