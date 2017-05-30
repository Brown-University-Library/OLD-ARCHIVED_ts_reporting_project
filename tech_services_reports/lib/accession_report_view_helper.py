# -*- coding: utf-8 -*-

import datetime, json, logging, pprint
import urllib.request
from collections import defaultdict
from itertools import chain
from operator import itemgetter, attrgetter

import requests
from django.conf import settings as project_settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import connection
from django.utils.encoding import smart_text
from tech_services_reports import settings_app
from tech_services_reports.models import Accession, SummaryAccession


log = logging.getLogger("webapp")


class AccessionReportViewHelper(object):

    def set_dates( self, year_str, month_num_str=None ):
        """ Sets start and end dates from url vars.
            Called by views.accessions_report() """
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

    def make_context( self, start, end, report_date_header, scheme, host ):
        """ Manages context creation.
            Called by views.accessions_report() """
        context = self.update_context_dates( self.initialize_context(scheme, host), start, end, report_date_header )
        context['year'] = start.year
        accssn_rprt = self.make_accession_report( start, end )
        context = self.update_context_with_report_data( context, accssn_rprt, start, end )
        context = self.update_context_with_chart_data( context, accssn_rprt )
        context['report_header'] = settings_app.ACC_REPORT_HEADER
        context['settings_app'] = settings_app
        context['last_updated'] = accssn_rprt.last_updated
        context['csv_url'] = self.get_csv_url( context )
        log.debug( 'type(context), `{typ}`;\n context, ```````{val}```````'.format( typ=type(context), val=pprint.pformat(context) ) )
        return context

    def make_context_2( self, year_str, month_num_str, scheme, host ):
        """ TODO: prepare a json-serializable context.
            Manages context creation.
            Called by views.accessions_report_v2() """
        # ( start, end, report_date_header ) = self.set_dates( year_str, month_num_str )
        # context = self.update_context_dates( self.initialize_context(scheme, host), start, end, report_date_header )
        # context['year'] = start.year
        # accssn_rprt = AccessionReport( start, end )
        # context = self.update_context_with_report_data( context, accssn_rprt, start, end )
        # context = self.update_context_with_chart_data( context, accssn_rprt )
        # context['report_header'] = settings_app.ACC_REPORT_HEADER
        # context['settings_app'] = settings_app
        # context['last_updated'] = accssn_rprt.last_updated
        # log.debug( 'type(context), `{typ}`;\n context, ```````{val}```````'.format( typ=type(context), val=pprint.pformat(context) ) )
        # return context
        return HttpResponse( 'under construction' )

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

    def last_day_of_month( self, date_obj ):
        """ Returns the last day of the month for any given Python date object.
            Code from: http://stackoverflow.com/questions/42950/get-last-day-of-the-month-in-python
            Called by set_dates() """
        if date_obj.month == 12:
            new_dt = date_obj.replace( day=31 )
        else:
            new_dt = date_obj.replace( month=date_obj.month+1, day=1 ) - datetime.timedelta( days=1 )
        return new_dt

    def update_context_dates( self, context, start, end, report_date_header ):
        """ Adds start & end dates to intialized context.
            Called by: make_context() """
        context['start'] = start
        context['end'] = end
        context['report_date_header'] = report_date_header
        return context

    def make_accession_report( self, start, end ):
        accssn_rprt = cache.get( 'accssn_rprt_cached' )
        if accssn_rprt is None:
            accssn_rprt = AccessionReport( start, end )
            cache.set( 'accssn_rprt_cached', accssn_rprt, 60*60*24 )  # 1 day
        return accssn_rprt

    def update_context_with_report_data( self, context, accssn_rprt, start_date, end_date ):
        """ Updates context from AccessionReport().
            Called by make_context() """
        context['all_formats_acq_type'] = accssn_rprt.all_formats_acq_type()
        context['acq_types'] = accssn_rprt.acq_types()
        context['building_count'] = accssn_rprt.building_summary()
        context['total_titles'] = accssn_rprt.total_titles
        context['total_volumes'] = accssn_rprt.total_volumes
        context['formats'] = accssn_rprt.formats()
        context['locations'] = accssn_rprt.locations()
        context['serial_added_volumes'] = accssn_rprt.serial_added_volumes()
        context['format_reports'] = self.make_format_reports( accssn_rprt )
        return context

    def make_format_reports( self, accssn_rprt ):
        """ Creates format_report list.
            Called by update_context_with_report_data() """
        format_reports = []
        for format in accssn_rprt.formats():
            format_reports.append( accssn_rprt.by_format(format=format) )
        return format_reports

    def update_context_with_chart_data( self, context, accssn_rprt ):
        """ Updates context with AccessionReport data for charting.
            Called by make_context() """
        # chart_label = context['report_date_header']
        chart_label = ''
        context['by_format_chart_url'] = accssn_rprt.gchart(
            accssn_rprt.by_format_chart(), chart_label, 'Accessions by format' )
        context['by_building_chart_url'] = accssn_rprt.gchart(
            accssn_rprt.building_summary(), chart_label, 'Accessions by location', color='3366CC' )
        return context

    def update_context_for_jsn( self, context ):
        """ Temporarily deletes non-jsonable elements.
            Eventually context-data should directly feed the templates.
            Called by views.accessions_report() """
        del context[ 'serial_added_volumes' ]
        del context[ 'all_formats_acq_type' ]
        del context[ 'start' ]
        del context[ 'end' ]
        del context[ 'format_reports' ]
        del context[ 'last_updated' ]
        del context[ 'settings_app' ]
        log.debug( 'context after temp deletions, ```{}```'.format(pprint.pformat(context)) )
        return context

    def get_csv_url( self, context ):
        """ Prepares csv download url.
            Called by make_context() """
        start_str = context['start'].strftime( '%Y-%m-%d' )
        end_str = context['end'].strftime( '%Y-%m-%d' )
        csv_url_root = reverse( 'accessions_csv' )
        url = '{rt}?start={st}&end={en}'.format( rt=csv_url_root, st=start_str, en=end_str )
        log.debug( 'csv_url, ```{}```'.format(url) )
        return url

    ## end class AccessionReportViewHelper()


class AccessionReport(object):

    def __init__(self, start, end, period=None):
        log.debug( 'start, `{st}`; end, `{en}`'.format( st=start, en=end ) )
        self.connection = connection  # from django.db import connection
        self.start = start
        self.end = end
        self.items = Accession.objects.filter(created__gte=start, created__lte=end)
        log.debug( 'len(self.items), `{}`'.format( len(self.items) ) )
        self.summary_items = SummaryAccession.objects.filter(date__gte=start, date__lte=end)
        #Combine edits and summary edits
        self.all_items = list(chain(self.items, self.summary_items))
        self.total_items = len(self.items)
        # location_format_map = json.loads( urllib.request.urlopen(settings_app.LOCATION_FORMAT_URL).read() )
        r = requests.get( settings_app.LOCATION_FORMAT_URL )
        location_format_map = r.json()
        self.location_format_map = location_format_map['result']['items']
        self.total_volumes = self.total_volumes(self.items)
        self.total_titles = self.total_titles(self.items)
        self.last_updated = Accession.objects.latest('created').created
        log.debug( '__init__() done' )

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
        log.debug( 'starting; location, ```{loc}```; serial_added_only, `{ser}`'.format( loc=location, ser=serial_added_only ) )
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
        # log.debug( 'items, ```{}```'.format( pprint.pformat(items) ) )
        for item in items:
            loc = self._loc(item)
            _k = settings_app.Acc(
                location=smart_text( loc ),
                acquisition_method=smart_text( item.acquisition_method ),
                count_type='volumes' )
            # log.debug( '_k, ```{}```'.format(_k) )
            # log.debug( '_k._asdict(), ```{}```'.format(_k._asdict()) )
            cross[_k] += item.volumes
            _k = _k._replace(count_type='titles')
            cross[_k] += item.titles
            #Do totals by purchase type
            _tk = settings_app.AccTotal(param=item.acquisition_method, param2='titles')
            cross[_tk] += item.titles
            _tk = _tk._replace(param2='volumes')
            cross[_tk] += item.volumes
        #sort = sorted(cross.iteritems(), key=itemgetter(0), reverse=True)
        #print sort
        return_data = {'header': header, 'data': cross}
        log.debug( 'return_data, ```{}```'.format( pprint.pformat(return_data) ) )
        return return_data

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
            _k = settings_app.Acc(location=smart_text( loc ),
                     acquisition_method=smart_text( item.acquisition_method ),
                     count_type='volumes')
            cross[_k] += item.volumes
            _k = _k._replace(count_type='titles')
            cross[_k] += item.titles
            _tk = settings_app.AccTotal(param=item.acquisition_method, param2='titles')
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
        return self.gchart_url(vals, period, name, color=color)

    def gchart_url(self, vals, period, name, color='438043'):
            data_labels = []
            data_values = []
            for label,val in vals['data']:
                data_labels.append(label)
                data_values.append(val)
            low = 0
            try:
                high = data_values[0]
            except IndexError:
                return
            data_values = "%s" % (','.join([str(d) for d in data_values]))
            data_labels = '|'.join([l.replace(' ', '+') for l in data_labels])
            range = "%s, %s" % (low, high)
            chart_url = """http://chart.apis.google.com/chart?chs=450x300
                   &cht=p
                   &chco=%(color)s
                   &chds=%(range)s
                   &chd=t:%(data_values)s
                   &chl=%(data_labels)s
                   &chtt=%(period)s+%(chart_name)s
                   &chma=40,40,40,40
                   &chts=000000,18
                   """ % {'range':range,
                          'data_labels':data_labels,
                          'data_values':data_values,
                          'period': period.replace(' ', '+'),
                          'color':color,
                          'chart_name':name.replace(' ', '+')
                          }
            #Remove line breaks and spaces from url.
            return chart_url.replace('\n', '').replace(' ', '')

    ## end class AccessionReport()
