# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
from collections import namedtuple


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


#####################################################
### for compiling total tables                    ###
#####################################################

# from helpers import namedtuple
Acc = namedtuple('acc_summary', ['location',
                                 'acquisition_method',
                                 'count_type'
                                 ],
                                 verbose=False)
AccTotal = namedtuple('acc_total',['param',
                                 'param2',
                                 ],
                                 verbose=False)

ACC_REPORT_HEADER = 'Accession Statistics -- Brown University Library'

CAT_STATS_REPORT_HEADER = 'Cataloging Statistics -- Brown University Library'
