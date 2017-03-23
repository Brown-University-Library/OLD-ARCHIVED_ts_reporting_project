# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib import admin



from .models import SummaryAccession, CatEdit, Accession, Harvest, SummaryCatEdit
# from django.contrib import admin


class AccessionAdmin(admin.ModelAdmin):
    list_display = ('created', 'format', 'acquisition_method', 'volumes', 'titles')
    search_fields = ('created', 'format', 'location', 'acquisition_method')
    list_filter = ('acquisition_method', 'format', 'location')

#class CatalogingAdmin(admin.ModelAdmin):
#    list_display = ('cat_date', 'cat_type', 'level')
#    search_fields = ('cat_date', 'cat_type', 'level')
#    list_filter = ('cat_type', 'level', 'mat_type')

class CatEditAdmin(admin.ModelAdmin):
    list_display = ('edit_date', 'editor', 'type', 'mat_type', 'source', 'bib')
    list_filter = ('type', 'editor', 'mat_type', 'source')
    search_fields = ('editor', 'bib', 'type', 'source')
    #list_filter = ('cat_type', 'level', 'mat_type')

admin.site.register(Harvest)
admin.site.register(Accession, AccessionAdmin)
#admin.site.register(Cataloging, CatalogingAdmin)
admin.site.register(SummaryAccession)
admin.site.register(CatEdit, CatEditAdmin)
admin.site.register(SummaryCatEdit)
#admin.site.register(BibItem, BibItemAdmin)
