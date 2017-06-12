# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from .models import Accession, CatEdit, Harvest, SummaryAccession, SummaryCatEdit
from django.contrib import admin


class AccessionAdmin(admin.ModelAdmin):
    list_display = [ 'created', 'number', 'format', 'acquisition_method', 'volumes', 'titles', 'location', 'serial_added_volume' ]
    search_fields = ('created', 'format', 'location', 'acquisition_method')
    list_filter = [ 'created', 'format', 'acquisition_method', 'location', 'serial_added_volume' ]
    ordering = [ '-created' ]


class SummaryAccessionAdmin(admin.ModelAdmin):
    list_display = [ 'date', 'format', 'acquisition_method', 'volumes', 'titles', 'location' ]
    search_fields = [ 'date', 'format', 'acquisition_method', 'location', 'format' ]
    list_filter = [ 'date', 'format', 'acquisition_method', 'location', 'format' ]
    ordering = [ '-date' ]


class CatEditAdmin(admin.ModelAdmin):
    list_display = [ 'edit_date', 'editor', 'type', 'mat_type', 'source', 'bib' ]
    search_fields = [ 'edit_date', 'editor', 'type', 'bib', 'source', 'bib' ]
    list_filter = [ 'edit_date', 'editor', 'type', 'mat_type', 'source' ]
    ordering = [ '-edit_date' ]


class SummaryCatEditAdmin(admin.ModelAdmin):
    list_display = [ 'edit_date', 'editor', 'type', 'mat_type', 'source', 'number' ]
    search_fields = [ 'edit_date', 'editor', 'type', 'mat_type', 'source' ]
    list_filter = [ 'edit_date', 'editor', 'type', 'mat_type', 'source' ]
    ordering = [ '-edit_date' ]


admin.site.register( Harvest )
admin.site.register( Accession, AccessionAdmin )
admin.site.register( SummaryAccession, SummaryAccessionAdmin )
admin.site.register( CatEdit, CatEditAdmin )
admin.site.register( SummaryCatEdit, SummaryCatEditAdmin )
