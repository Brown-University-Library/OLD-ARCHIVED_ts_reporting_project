# -*- coding: utf-8 -*-

import datetime


def make_dates_from_params( rqst_dct ):
    """ Sets start and end dates from url params.
        Called by views.custom_report() """
    start = datetime.datetime.strptime( rqst_dct['start'], "%m/%d/%Y" ).date()
    end = datetime.datetime.strptime( rqst_dct['end'], "%m/%d/%Y" ).date()
    return ( start, end )
