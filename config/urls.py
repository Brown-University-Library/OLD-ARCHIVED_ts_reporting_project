# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from tech_services_reports import views as ts_views


admin.autodiscover()

urlpatterns = [

    url( r'^info/$',  ts_views.hi, name='info_url' ),

    url( r'^admin/', include(admin.site.urls) ),

    url( r'^stats/$',  ts_views.index, name='index_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='index_url') ),

    # url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    ]
