# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf.urls import include, url
from django.contrib import admin


admin.autodiscover()

urlpatterns = [

    url( r'^admin/', include(admin.site.urls) ),  # eg host/project_x/admin/

    url( r'^', include('tech_services_reports.urls_app', namespace='foo') ),  # eg host/project_x/anything/

    ]
