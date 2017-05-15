# -*- coding: utf-8 -*-

import datetime, json, logging, pprint

from django.conf import settings as project_settings
from tech_services_reports import settings_app


log = logging.getLogger("webapp")


class CatalogingReportViewHelper(object):

    def make_context( self, year_str, month_num_str, scheme, host ):
        """ Manages context creation.
            Called by views.cataloging_report_v2() """
        ( start, end, month_for_context ) = self.set_dates( year_str, month_num_str )
        context = {}
        context['STATIC_URL'] = project_settings.STATIC_URL
        context['year'] = start.year
        context['month'] = month_for_context
        context['report_header'] = settings_app.CAT_STATS_REPORT_HEADER
        context['start'] = start.strftime("%Y-%m-%d")
        context['end'] = end.strftime("%Y-%m-%d")


        log.debug( 'type(context), `{typ}`;\n context, ```````{val}```````'.format( typ=type(context), val=pprint.pformat(context) ) )
        return context

    def set_dates( self, year_str, month_num_str=None ):
        """ Sets start and end dates from url vars.
            Called by make_context() """
        month_for_context = None
        if not month_num_str:
            ( year_num, month_num ) = ( int(year_str), 1 )
            start = datetime.date( year_num, month_num, 1 )  # first day of year
            end = datetime.date( year_num, 12, 31 )  # last day of year
        else:
            ( year_num, month_num ) = ( int(year_str), int(month_num_str) )
            start = datetime.date( year_num, month_num, 1 )
            end = self.last_day_of_month( start )
            month_for_context = start.strftime('%B')
        return ( start, end, month_for_context )

    def last_day_of_month( self, date_obj ):
        """ Returns the last day of the month for any given Python date object.
            Code from: http://stackoverflow.com/questions/42950/get-last-day-of-the-month-in-python
            Called by set_dates() """
        if date_obj.month == 12:
            new_dt = date_obj.replace( day=31 )
        else:
            new_dt = date_obj.replace( month=date_obj.month+1, day=1 ) - datetime.timedelta( days=1 )
        return new_dt
