# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from tech_services_reports import views as ts_views


admin.autodiscover()

urlpatterns = [

    url( r'^admin/', include(admin.site.urls) ),

    url( r'^info/$',  ts_views.hi, name='info_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    # url( r'^', include('tech_services_reports.urls_app', namespace='foo') ),

    ]
