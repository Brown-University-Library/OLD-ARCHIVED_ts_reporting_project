# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
  Loading Josiah updates to the new titles app.
"""

import sys

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.utils import simplejson
from optparse import make_option

from datetime import timedelta
from datetime import date

import time

from tech_services_reports import settings_app


class Command(BaseCommand):
    help = "For generating accession reports."
    option_list = BaseCommand.option_list + (
        make_option('--monthly', '-m', dest='monthly',
                    help='Creates monthly reports.'),
    )
    def handle(self, **options):
        #if options['monthly']:
        #  self.monthly_reports()
        #else:
        #  print 'no file specified'
        self.monthly_reports()
        self.yearly_reports()

    def sort_orders(self):
        from tech_services_reports.utility_code import location_sort_order, format_sort_order
        #Dump a sort key for locations.
        sorted_locations = location_sort_order()
        simplejson.dump(sorted_locations,
                        open("%s/location_sort_order.json" % settings_app.REPORT_DIR, 'w'), indent=2)
        sorted_formats = format_sort_order()
        simplejson.dump(sorted_formats,
                        open("%s/format_sort_order.json" % settings_app.REPORT_DIR, 'w'), indent=2)

    def monthly_reports(self):
        from tech_services_reports.utility_code import monthly_reports as m
        self.sort_orders()
        monthly_totals = m()
        simplejson.dump(monthly_totals,
                        open("%s/monthly.json" % settings_app.REPORT_DIR, 'w'), indent=2)
        print>>sys.stderr, "Building sort and monthly totals dumped to to %s." % settings_app.REPORT_DIR

    def yearly_reports(self):
        from tech_services_reports.utility_code import yearly_reports as y
        self.sort_orders()
        yearly_totals = y()
        simplejson.dump(yearly_totals,
                        open("%s/yearly.json" % settings_app.REPORT_DIR, 'w'), indent=2)
        print>>sys.stderr, "Building sort and yearly totals dumped to to %s." % settings_app.REPORT_DIR

#  {
#    "pk": "i157511923",
#    "model": "tech_services_reports.item",
#    "fields": {
#      "acquisition_method": "Gift",
#      "format": "Book",
#      "location": "qs",
#      "created": "2010-10-01"
#    }
#  },

#  {
#    "pk": "b40709796",
#    "model": "tech_services_reports.bib",
#    "fields": {
#      "items": [
#        "i124313553",
#        "i126742492",
#        "i145935723",
#        "i157736283"
#      ],
#      "level": "s",
#      "cat_date": "1994-05-20"
#    }
#  },





