# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os


#####################################################
### for tech_services_reports/management/commands ###
#####################################################

## ts_reports_loader.py
LOCATION_FORMAT_URL = 'https://library.brown.edu/services/location_format/v1/?data=dump'

BEGIN_YEAR = 2016  # for start of report processing
BEGIN_MONTH = 1

OCLC_CODE = 'RBN'  # for determining cataloging type

ITEM_ACC_NOTE = 'e'  # mappings for MARC record to database; these are subfields; value changed of 2011-March-30
# ITEM_ACC_NOTE = 'n'  # original value
