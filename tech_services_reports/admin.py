# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from .models import Accession, CatEdit, Harvest, SummaryAccession, SummaryCatEdit
from django.contrib import admin


class AccessionAdmin(admin.ModelAdmin):
    list_display = ('created', 'format', 'acquisition_method', 'volumes', 'titles')
    search_fields = ('created', 'format', 'location', 'acquisition_method')
    list_filter = ('acquisition_method', 'format', 'location')


class CatEditAdmin(admin.ModelAdmin):
    list_display = ('edit_date', 'editor', 'type', 'mat_type', 'source', 'bib')
    list_filter = ('type', 'editor', 'mat_type', 'source')
    search_fields = ('editor', 'bib', 'type', 'source')
    #list_filter = ('cat_type', 'level', 'mat_type')


admin.site.register(Harvest)
admin.site.register(Accession, AccessionAdmin)
admin.site.register(SummaryAccession)
admin.site.register(CatEdit, CatEditAdmin)
admin.site.register(SummaryCatEdit)
