# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from .models import Accession, CatEdit, Harvest, SummaryAccession, SummaryCatEdit
from django.contrib import admin


class AccessionAdmin(admin.ModelAdmin):
    list_display = [ 'created', 'number', 'format', 'acquisition_method', 'volumes', 'titles', 'location', 'serial_added_volume' ]
    search_fields = ('created', 'format', 'location', 'acquisition_method')
    list_filter = [ 'format', 'acquisition_method', 'location', 'serial_added_volume' ]
    ordering = [ '-created' ]


class SummaryAccessionAdmin(admin.ModelAdmin):
    list_display = [ 'date', 'format', 'acquisition_method', 'volumes', 'titles', 'location' ]
    search_fields = [ 'date', 'format', 'acquisition_method',    'location', 'format' ]
    list_filter = [ 'date', 'format', 'acquisition_method', 'location', 'format' ]
    ordering = [ '-date' ]


class CatEditAdmin(admin.ModelAdmin):
    list_display = ('edit_date', 'editor', 'type', 'mat_type', 'source', 'bib')
    list_filter = ('type', 'editor', 'mat_type', 'source')
    search_fields = ('editor', 'bib', 'type', 'source')
    #list_filter = ('cat_type', 'level', 'mat_type')


admin.site.register( Harvest )
admin.site.register( Accession, AccessionAdmin )
admin.site.register( SummaryAccession, SummaryAccessionAdmin )
admin.site.register( CatEdit, CatEditAdmin )
admin.site.register( SummaryCatEdit )
