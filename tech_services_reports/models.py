# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime, json, logging, os, pprint
from django.conf import settings as project_settings
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect


log = logging.getLogger(__name__)


class Harvest(models.Model):
    date = models.DateField()
    notes = models.TextField(null=True, blank=True)
    def __unicode__(self):
        return u'%s' % self.date


class Accession(models.Model):
    """Create indexes for the fields used for reporting."""
    number = models.CharField(max_length=15, primary_key=True)
    created = models.DateField(db_index=True)
    acquisition_method = models.CharField(max_length=50, db_index=True)
    format = models.CharField(max_length=50, db_index=True)
    location = models.CharField(max_length=50, db_index=True)
    volumes = models.IntegerField()
    titles = models.IntegerField()
    serial_added_volume = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s %s %s %s' % (self.created, self.acquisition_method, self.location, self.format)


class SummaryAccession(models.Model):
    date = models.DateField()
    format = models.CharField(max_length=50)
    location = models.CharField(max_length=50)
    volumes = models.IntegerField()
    titles = models.IntegerField()
    location = models.CharField(max_length=50)
    format = models.CharField(max_length=50)
    acquisition_method = models.CharField(max_length=50)

    def __unicode__(self):
        return u'%s %s' % (self.date, self.format)


class CatEdit(models.Model):
    #Make a hash of edit_date, bib, mat_type, editor, type, source
    id = models.CharField(max_length=50, primary_key=True)
    edit_date = models.DateField(db_index=True)
    bib = models.CharField(max_length=15)
    mat_type = models.CharField(max_length=15, db_index=True)
    editor = models.CharField(max_length=50, db_index=True)
    type = models.CharField(max_length=50, db_index=True)
    source = models.CharField(max_length=15, blank=True, null=True, db_index=True)

    def __unicode__(self):
        return u'%s %s' % (self.edit_date, self.editor)


class SummaryCatEdit(models.Model):
    edit_date = models.DateField()
    mat_type = models.CharField(max_length=15)
    editor = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    source = models.CharField(max_length=15, blank=True, null=True)
    number = models.IntegerField()

    def __unicode__(self):
        return u'%s %s' % (self.edit_date, self.mat_type)
