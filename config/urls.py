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

    url( r'^stats/accessions/$',  RedirectView.as_view(pattern_name='index_url'), name='accessions' ),  # exists only for a reverse() lookup
    url( r'^stats/accessions/(?P<year>.*)/(?P<month>.*)/$',  ts_views.accessions_report, name='accessions_w_params' ),
    # url( r'^stats/accessions_v2/(?P<year2>[0-9]{4})/(?P<month2>\d+)/$',  ts_views.accessions_report_v2, name='accessions_v2_w_params' ),
    url( r'^stats/accessions_v2/(?P<year2>.*)/(?P<month2>.*)/$',  ts_views.accessions_report_v2, name='accessions_v2_w_params' ),

    url( r'^stats/cataloging/$',  RedirectView.as_view(pattern_name='index_url'), name='cataloging' ),  # exists only for a reverse() lookup
    url( r'^stats/cataloging/(?P<year>.*)/(?P<month>.*)/$',  ts_views.cataloging, name='cataloging_w_params' ),

    url( r'^stats/$',  ts_views.index, name='index_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='index_url') ),

    ]
