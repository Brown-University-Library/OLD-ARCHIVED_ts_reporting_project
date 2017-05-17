# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json, os
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

CACHED_ACCESSION_QUERY_SECONDS_TIMEOUT = int( os.environ['TS_RPRT__CACHED_ACCESSION_QUERY_SECONDS_TIMEOUT'] )  # short for production; long for development


#####################################################
### for Accession Report                          ###
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


#####################################################
### for Cataloging Report                         ###
#####################################################

CAT_STATS_REPORT_HEADER = 'Cataloging Statistics -- Brown University Library'

MAT_TYPE_MAP = {
    'a': 'Book',
    'c': 'Score',
    'k': '2D-Graphic',
    'r': '3D-Object',
    'g': 'Audovisual',
    'm': 'Computer File',
    'o': 'Kit',
    't': 'Manuscript',
    'e': 'Map',
    'f': 'Map, MSS.',
    'p': 'Mixed Material',
    'j': 'Music Record',
    'c': 'Score',
    'd': 'Score, MSS.',
    's': 'Serial/Journal',
    'i': 'Spoken Record'
    }

DISTINCT_CAT_TYPES = ['copy', 'original', 'enrich', 'batch']

CATALOGERS = {
    'TB':'Tatyana Badalyan',
    'JJB':'Jennifer Betts',
    'CGB':'Catherine Busselen',
    'RJB':'Ray Butti',
    'EASTUDENT':'East Asian Student',
    'TE':'Timothy Engels',
    'SF':'Barbara Filipac',
    'CCG':'Christopher Geissler',
    'PH':'Peter Harrington',
    'JPH':'Patrick Hutchinson',
    'JK':'Joanna Katsune',
    'GDL':'Gayle Lynch',
    'TM':'Toshiyuki Minami',
    'SAM':'Sam Mizer',
    'EM':'Ellen Moreau',
    'RCN':'Richard Noble',
    'DP':'Deb Peterson',
    'NQ':'Ned Quist',
    'RR':'Robert Rosa',
    'HPS':'Howard Stone',
    'JCT':'Joanne Tandy',
    'GSY':'Gretchen Yealy',
    'CASALINI': 'Casalini Libre',
    'YBP': 'YBP',
    'AUX AMATEURS': 'Aux Amateurs',
    'KAE': 'Karen Eberhart',
    'BC': 'Bill Corrente',
    'WK': 'Wendy Korwin',
    'TDN': 'Teresa Negrucci',
    'YW': 'Yiwei Want',
    'Coutts': 'Coutts',
    'BSLW shelfready': 'Backstage Library Works',
    }


#####################################################
### for Admin edits                               ###
#####################################################

TEST_USERNAME = os.environ['TS_RPRT__TEST_USERNAME']
TEST_NETID = os.environ['TS_RPRT__TEST_NETID']

SUPER_USERS = json.loads( os.environ['TS_RPRT__SUPER_USERS_JSON'] )
STAFF_USERS = json.loads( os.environ['TS_RPRT__STAFF_USERS_JSON'] )
