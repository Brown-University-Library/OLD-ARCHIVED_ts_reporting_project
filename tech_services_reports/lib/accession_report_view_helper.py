# -*- coding: utf-8 -*-

import datetime, json, logging
import urllib.request
from collections import defaultdict
from itertools import chain

# from helpers import defaultdict
# from models import Accession, SummaryAccession
# from tech_services_reports.helpers import defaultdict
from django.db import connection
from tech_services_reports import settings_app
from tech_services_reports.models import Accession, SummaryAccession


log = logging.getLogger("webapp")


class AccessionReportViewHelper(object):

    def make_context( self, year_str, month_num_str, scheme, host ):
        """ Manages context creation.
            Called by views.accessions_report_v2() """
        context = self.initialize_context( scheme, host )
         ( start, end, report_date_header ) = self.set_dates( year_str, month_num_str )
         context = self.update_context_dates( start, end, report_date_header )
         context['year'] = start.year

        log.debug( 'context, ```{}```'.format( pprint.pformat(context) ) )
        return context

    def initialize_context( self, scheme, host ):
        """ Sets initial vars.
            Called by make_context() """
        context = {
            'STATIC_URL': project_settings.STATIC_URL,
            'HOME_URL': '{sch}://{hst}{url}'.format( sch=scheme, hst=host, url=reverse('index_url') ),

            'report_date_header': 'init',

            'start': 'init',
            'end': 'init',
            'year': 'init',

            'all_formats_acq_type': 'init',
            'acq_types': 'init',
            'building_count': 'init',
            'total_titles': 'init',
            'total_volumes': 'init',
            'formats': 'init',
            'locations': 'init',
            'serial_added_volumes': 'init',
            'format_reports': 'init',

            'by_format_chart_url': 'init',
            'by_building_chart_url': 'init',

            'report_header': 'init',
            'last_updated': 'init',
            }
        return context

    def set_dates( self, year_str, month_num_str=None ):
        """ Called by views.accessions_report_v2() """
        if not month_num_str:
            ( year_num, month_num ) = ( int(year_str), 1 )
            start = datetime.date( year_num, month_num, 1 )  # first day of year
            end = datetime.date( year_num, 12, 31 )  # last day of year
            report_date_header = '{} yearly total'.format( year_str )
        else:
            ( year_num, month_num ) = ( int(year_str), int(month_num_str) )
            start = datetime.date( year_num, month_num, 1 )
            end = self.last_day_of_month( start )
            report_date_header = "{mo} {yr}".format( mo=start.strftime('%B'), yr=year_str )
        return ( start, end, report_date_header )

    def last_day_of_month( self, date_obj ):
        """ Returns the last day of the month for any given Python date object.
            Code from: http://stackoverflow.com/questions/42950/get-last-day-of-the-month-in-python
            Called by set_dates() """
        if date_obj.month == 12:
            date_obj.replace( day=31 )
        else:
            date_obj.replace( month=date_obj.month+1, day=1 ) - datetime.timedelta( days=1 )
        return date_obj

    def update_context_dates( self, start, end, report_date_header ):
        context['start'] = start
        context['end'] = end
        context['report_date_header'=report_date_header
        return context


    ## end class AccessionReportViewHelper()


class AccessionReport(object):

    def __init__(self, start, end, period=None):

        self.connection = connection  # from django.db import connection
        self.start = start
        self.end = end
        self.items = Accession.objects.filter(created__gte=start, created__lte=end)
        self.summary_items = SummaryAccession.objects.filter(date__gte=start, date__lte=end)
        #Combine edits and summary edits
        self.all_items = list(chain(self.items, self.summary_items))
        #self.items = Accession.objects.all()
        self.total_items = len(self.items)
        location_format_map = json.loads( urllib.request.urlopen(settings_app.LOCATION_FORMAT_URL).read() )
        self.location_format_map = location_format_map['result']['items']
        self.total_volumes = self.total_volumes(self.items)
        self.total_titles = self.total_titles(self.items)
        self.last_updated = Accession.objects.latest('created').created

    def _loc(self, item):
        try:
            loc = self.location_format_map[item.location]['building']
        except KeyError:
            loc = item.location
        return loc

    def total_volumes(self, qset):
        total = 0
        for it in qset:
            total += it.volumes
        return total

    def total_titles(self, qset):
        total = 0
        for it in qset:
            total += it.titles
        return total

    def _distinct(self, field):
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT %s from tech_services_reports_accession;" % field)
        distinct = cursor.fetchall()
        cursor.execute("SELECT DISTINCT %s from tech_services_reports_summaryaccession;" % field)
        distinct_summary = cursor.fetchall()
        distinct += distinct_summary
        if field == 'location':
            locs = []
            for val, in distinct:
                try:
                    build = self.location_format_map[val]['building']
                except KeyError:
                    build = val
                if build not in locs:
                    locs.append(build)
            return locs
        else:
            try:
                return [r[0] for r in distinct]
            except TypeError:
                return []

    def formats(self):
        formats = self._distinct('format')
        out = []
        for f in formats:
            if f not in out:
                out.append(f)
        return out

    def locations(self):
        return self._distinct('location')

    def acq_types(self):
        atypes = self._distinct('acquisition_method')
        out = []
        #Deduplicate
        for a in atypes:
            if a not in out:
                out.append(a)
        return out

    def building_summary(self):
        cross = defaultdict(int)
        total = 0
        for item in self.all_items:
            loc = self._loc(item)
            cross[loc] += item.volumes
            total += item.volumes
        # sort = sorted(cross.iteritems(), key=itemgetter(1), reverse=True)
        sort = sorted(cross.items(), key=itemgetter(1), reverse=True)
        return {'header': ['Building', 'Volumes'],
                'data': sort,
                'totals': [total]}

    def all_formats_acq_type(self, location=None, serial_added_only=False):
        #Get project wide named tuples.
        # from settings_app import Acc, AccTotal
        cross = defaultdict(int)
        if not location and not serial_added_only:
            header = 'All formats by building.'
            items = self.all_items
        elif serial_added_only:
            header = 'Serial added volumes'
            items = self.items.filter(serial_added_volume=True)
        else:
            header = location.title()
            items = self.items.filter(location=location)
            sum_items = self.summary_items.filter(location=location)
            items = chain(items, sum_items)

        for item in items:
            loc = self._loc(item)
            # _k = Acc(location=unicode(loc),
            #          acquisition_method=unicode(item.acquisition_method),
            #          count_type=u'volumes')
            _k = Acc(location=smart_text( loc ),
                     acquisition_method=smart_text( item.acquisition_method ),
                     count_type='volumes')
            cross[_k] += item.volumes
            _k = _k._replace(count_type='titles')
            cross[_k] += item.titles
            #Do totals by purchase type
            _tk = AccTotal(param=item.acquisition_method, param2='titles')
            cross[_tk] += item.titles
            _tk = _tk._replace(param2='volumes')
            cross[_tk] += item.volumes
        #sort = sorted(cross.iteritems(), key=itemgetter(0), reverse=True)
        #print sort
        return {'header': header,
                'data': cross}

    def by_format(self, format=None):
        # from settings_app import Acc, AccTotal
        cross = defaultdict(int)
        if not format:
            header = 'All formats'
            items = self.all_items
        else:
            header = '%s' % format
            items = self.items.filter(format=format,
                                      serial_added_volume=False)
            sum_items = self.summary_items.filter(format=format)
            items = chain(items, sum_items)

        for item in items:
            loc = self._loc(item)
            # _k = Acc(location=unicode(loc),
            #          acquisition_method=unicode(item.acquisition_method),
            #          count_type=u'volumes')
            _k = Acc(location=smart_text( loc ),
                     acquisition_method=smart_text( item.acquisition_method ),
                     count_type='volumes')
            cross[_k] += item.volumes
            _k = _k._replace(count_type='titles')
            cross[_k] += item.titles
            _tk = AccTotal(param=item.acquisition_method, param2='titles')
            cross[_tk] += item.titles
            _tk = _tk._replace(param2='volumes')
            cross[_tk] += item.volumes
        return {'header': header,
                'data': cross}

    def by_format_chart(self, format=None):
        # from settings_app import Acc, AccTotal
        cross = defaultdict(int)
        if not format:
            header = 'All formats'
            items = self.all_items
        else:
            header = '%s' % format
            items = self.items.filter(format=format)
            sum_items = self.summary_items.filter(format=format)
            items = chain(items, sum_items)
        for item in items:
            cross[item.format] += 1
        # sort = sorted(cross.iteritems(), key=itemgetter(1), reverse=True)
        sort = sorted(cross.items(), key=itemgetter(1), reverse=True)
        return {'header': header,
                'data': sort}

    def serial_added_volumes(self):
        """Limit search to only serial added volumes."""
        return self.all_formats_acq_type(self, serial_added_only=True)

    def gchart(self, vals, period, name, color='438043'):
        return gchart_url(vals, period, name, color=color)

    ## end class AccessionReport()
