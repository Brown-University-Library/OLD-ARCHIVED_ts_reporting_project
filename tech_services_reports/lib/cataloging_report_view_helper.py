# -*- coding: utf-8 -*-

import datetime, json, logging, pprint
from collections import defaultdict
from operator import itemgetter

from django.conf import settings as project_settings
from tech_services_reports import settings_app


log = logging.getLogger("webapp")


class CatalogingReportViewHelper(object):
    """ Prepares context for cataloging report view. """

    # def make_context( self, year_str, month_num_str, scheme, host ):
    #     """ Manages context creation.
    #         Called by views.cataloging_report_v2() """
    #     ( start, end, report_date_header ) = self.set_dates( year_str, month_num_str )
    #     context = self.update_context_dates( start, end, report_date_header )
    #     cr = CatalogingReport(start, end)
    #     context = self.update_context_data( context, cr )
    #     context = self.update_context_charg_data( context, cr )
    #     log.debug( 'type(context), `{typ}`;\n context, ```````{val}```````'.format( typ=type(context), val=pprint.pformat(context) ) )
    #     return context

    def make_context( self, start, end, report_date_header, scheme, host ):
        """ Manages context creation.
            Called by views.cataloging_report_v2() """
        # ( start, end, report_date_header ) = self.set_dates( year_str, month_num_str )
        context = self.update_context_dates( start, end, report_date_header )
        cr = CatalogingReport(start, end)
        context = self.update_context_data( context, cr )
        context = self.update_context_charg_data( context, cr )
        log.debug( 'type(context), `{typ}`;\n context, ```````{val}```````'.format( typ=type(context), val=pprint.pformat(context) ) )
        return context

    def make_context_v2( self, year_str, month_num_str, scheme, host ):
        """ TODO: prepare a json-serializable context.
            Manages context creation.
            Called by views.cataloging_report_v2() """
        context = {}
        log.debug( 'type(context), `{typ}`;\n context, ```````{val}```````'.format( typ=type(context), val=pprint.pformat(context) ) )
        return context

    def set_dates( self, year_str, month_num_str=None ):
        """ Sets start and end dates from url vars.
            Called by make_context() """
        report_date_header = None
        if not month_num_str:
            ( year_num, month_num ) = ( int(year_str), 1 )
            start = datetime.date( year_num, month_num, 1 )  # first day of year
            end = datetime.date( year_num, 12, 31 )  # last day of year
        else:
            ( year_num, month_num ) = ( int(year_str), int(month_num_str) )
            start = datetime.date( year_num, month_num, 1 )
            end = self.last_day_of_month( start )
            report_date_header = start.strftime('%B')
        return ( start, end, report_date_header )

    def last_day_of_month( self, date_obj ):
        """ Returns the last day of the month for any given Python date object.
            Code from: http://stackoverflow.com/questions/42950/get-last-day-of-the-month-in-python
            Called by set_dates() """
        if date_obj.month == 12:
            new_dt = date_obj.replace( day=31 )
        else:
            new_dt = date_obj.replace( month=date_obj.month+1, day=1 ) - datetime.timedelta( days=1 )
        return new_dt

    def update_context_dates( self, start, end, report_date_header ):
        """ Initializes and stores main date info.
            Called by make_context() """
        context = {}
        context['STATIC_URL'] = project_settings.STATIC_URL
        year = start.year
        context['year'] = year
        context['report_date_header'] = report_date_header
        context['report_header'] = settings_app.CAT_STATS_REPORT_HEADER
        context['start'] = start.strftime("%Y-%m-%d")
        context['end'] = end.strftime("%Y-%m-%d")
        return context

    def update_context_data( self, context, cr ):
        """ Updates context with CatalogingReport data.
            Called by make_context() """
        context['by_format'] = cr.by_format()
        context['by_format_and_type'] = cr.by_format_and_type()
        context['by_cataloger'] = cr.by_cataloger()
        context['by_edit_type'] = cr.by_edit_type()
        context['by_cataloger_and_format'] = cr.by_cataloger_and_format()
        context['by_cataloger_and_edit_type'] = cr.by_cataloger_and_edit_type()
        context['total_cataloged'] = cr.total_cataloged
        context['report'] = cr
        context['last_updated'] = cr.last_updated
        return context

    def update_context_charg_data( self, context, cr ):
        """ Updates chart data.
            Called by make_context() """
        chart_label = ''
        if context['report_date_header']:
            chart_label += context['report_date_header']
        # chart_label += ' ' + str(year)
        chart_label += ' ' + str(context['year'])
        context['by_format_chart_url'] = cr.gchart(
            context['by_format'], chart_label, 'Cataloging by format')
        context['by_edit_type_chart_url'] = cr.gchart(
            context['by_edit_type'], chart_label, 'Cataloging by type', color='3366CC')
        return context

    ## end class CatalogingReportViewHelper()


class CatalogingReport(object):
    """ Prepares cataloging data. """

    def __init__(self, start, end, cataloger=None):
        from tech_services_reports.models import CatEdit, SummaryCatEdit
        from itertools import chain
        from django.db import connection
        self.connection = connection
        #self.catalogs = Cataloging.objects.filter(cat_date__gte=start,
        #                                           cat_date__lte=end)
        self.edits = CatEdit.objects.filter(edit_date__gte=start,
                                            edit_date__lte=end)
        self.summary_edits = SummaryCatEdit.objects.filter(edit_date__gte=start,
                                            edit_date__lte=end)
        #Combine edits and summary edits
        self.edits = list(chain(self.edits, self.summary_edits))
        self.total_edited = len(self.edits)
        self.total_cataloged = self.total_edited
        self.last_updated = CatEdit.objects.latest('edit_date').edit_date


    def _material_string(self, mat_type):
        """Returns full mat type string."""
        try:
            return settings_app.MAT_TYPE_MAP[mat_type]
        except KeyError:
            return 'Unknown'

    def _cataloger(self, initials):
        """Returns full name of cataloger from initials."""
        try:
            return settings_app.CATALOGERS[initials]
        except KeyError:
            return 'Unknown'

    def _distinct(self, field):
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT %s from tech_services_reports_catedit;" % field)
        distinct = cursor.fetchall()
        try:
            return [r[0] for r in distinct]
        except TypeError:
            return []

    def _value(self, dbobj):
        """Check if this is a summary object or an individual object
        and set a value to increment."""
        v = 1
        if dbobj._meta.model_name == 'summarycatedit':
            v = dbobj.number
        return v

    def distinct_cat_types(self):
        return settings_app.DISTINCT_CAT_TYPES

    def _summary_csv(self, report):
        """Create list of rows that will be handled by a csv writer."""
        out = []
        out.append(report['header'])
        for label, cell in report['data']:
            out.append([label, cell])
        totals = []
        totals.append('Total')
        for total in report['totals']:
            totals.append(total)
        out.append(totals)
        return out

    def _multi_summary_csv(self, report):
        """Create list of rows that will be handled by a csv writer."""
        out = []
        #write header row
        out.append([' '] + report['header'])
        #write data rows
        for row_label, cell_data in report['data'].items():
            this_row = []
            this_row.append(row_label)
            for header in report['header']:
                for cell_type, data_point in cell_data.items():
                    if cell_type.title() == header:
                        this_row.append(data_point)
            out.append(this_row)
        total_row = ['Total']
        for head in report['header']:
            try:
                total_row.append(report['cross'][head.lower()])
            except KeyError:
                total_row.append(0)
        out.append(total_row)
        return out

    def distinct_formats(self):
        formats = []
        for bib in self.edits:
            mt = bib.mat_type
            if mt not in formats:
                formats.append(mt)
        return formats

    def by_cataloger(self, report_format='html'):
        summary = defaultdict(int)
        total = 0
        for ed in self.edits:
            cataloger = self._cataloger(ed.editor.upper())
            v = self._value(ed)
            summary[cataloger] += v
            total += v
        # summary = sorted(summary.iteritems(), key=itemgetter(1), reverse=True)
        summary = sorted(summary.items(), key=itemgetter(1), reverse=True)
        header = ['Cataloger', 'Count']
        report = {'header': header,
                'data': summary,
                'totals': [total]}
        if report_format == 'html':
            return report
        else:
            return self._summary_csv(report)

    def by_edit_type(self, report_format='html'):
        summary = defaultdict(int)
        total = 0
        for ed in self.edits:
            v = self._value(ed)
            ctype = ed.type.lower()
            if ctype == 'catalog':
                ctype = ed.source
            summary[ctype.title()] += v
            total += v
        # summary = sorted(summary.iteritems(), key=itemgetter(1), reverse=True)
        summary = sorted(summary.items(), key=itemgetter(1), reverse=True)
        header = ['Edit type', 'Count']
        report = {'header': header,
                'data': summary,
                'totals': [total]}
        if report_format == 'csv':
            return self._summary_csv(report)
        else:
            return report

    def by_format(self, report_format='html'):
        """Reporting on CatEdits only."""
        summary = defaultdict(int)
        total = 0
        for bib in self.edits:
            v = self._value(bib)
            mat_string = self._material_string(bib.mat_type)
            summary[mat_string] += v
            total += v
        # summary = sorted(summary.iteritems(), key=itemgetter(1), reverse=True)
        summary = sorted(summary.items(), key=itemgetter(1), reverse=True)
        header = ['Format', 'Count']
        report = {'header': header,
                'data': summary,
                'totals': [total]}
        if report_format == 'csv':
            return self._summary_csv(report)
        else:
            return report

    def by_format_and_type(self, report_format='html'):
        #Format    Original    Enriched    Copy    Total
        summary = {}
        cross = defaultdict(int)
        bibs = self.edits
        #Add distinct types from setting
        cat_types = self.distinct_cat_types()
        header = []
        for bib in bibs:
            mat_string = self._material_string(bib.mat_type)
            format = mat_string
            cat = bib.type.lower()
            if cat == 'catalog':
                cat = bib.source
            summary[format] = summary.get(format, {})
            for dc in cat_types:
                dc = dc.lower()
                ov = self._value(bib)
                if dc == cat.lower():
                    v = ov
                else:
                    v = 0
                summary[format][dc] = summary[format].get(dc, 0) + v
                summary[format]['total'] = summary[format].get('total', 0) + v
                cross[dc] += v
                cross['total'] += v

        #header = [h.title() for h in cross.keys()]
        #hspot = header.index('Total')
        #header.pop(hspot)
        header = [d.title() for d in cat_types]
        header.append('Total')
        #header.append('Total')
        #Sort by totals
        report = {'header': header,
                'rows': summary.keys(),
                'data': summary,
                'cross': dict(cross)}
        if report_format == 'csv':
            return self._multi_summary_csv(report)
        else:
            return report

    def by_cataloger_and_format(self, report_format='html'):
        summary = {}
        edits = self.edits
        distinct_formats = self.distinct_formats()
        cross = defaultdict(int)
        for edit in edits:
            try:
                cataloger = settings_app.CATALOGERS[edit.editor.upper()]
            except KeyError:
                cataloger = edit.editor.upper()
            summary[cataloger] = summary.get(cataloger, {})
            for df in distinct_formats:
                format = self._material_string(df)
                ov = self._value(edit)
                if df == edit.mat_type:
                    v = ov
                else:
                    v = 0
                summary[cataloger][format] = summary[cataloger].get(format, 0) + v
                summary[cataloger]['total'] = summary[cataloger].get('total', 0) + v
                cross[format.lower()] += v
                cross['total'] += v

        header = [self._material_string(d) for d in distinct_formats]
        header.append('Total')
        report = {'header': header,
                'rows': summary.keys(),
                'data': summary,
                'cross': dict(cross)}
        if report_format == 'csv':
            return self._multi_summary_csv(report)
        else:
            return report

    def by_cataloger_and_edit_type(self, report_format='html'):
        summary = {}
        edits = self.edits
        distinct = self.distinct_cat_types()
        cross = defaultdict(int)
        for dt in distinct:
            for edit in edits:
                try:
                    cataloger = settings_app.CATALOGERS[edit.editor.upper()]
                except KeyError:
                    cataloger = edit.editor.upper()
                summary[cataloger] = summary.get(cataloger, {})
                edit_type = edit.type.lower()
                if edit_type == 'catalog':
                    edit_type = edit.source
                ov = self._value(edit)
                if edit_type == dt:
                    v = ov
                else:
                    v = 0
                summary[cataloger][dt] = summary[cataloger].get(dt, 0) + v
                summary[cataloger]['total'] = summary[cataloger].get('total', 0) + v
                cross[dt] += v
                cross['total'] += v

        header = [d.title() for d in distinct]
        header.append('Total')
        report = {'header': header,
                'rows': summary.keys(),
                'data': summary,
                'cross': dict(cross)}
        if report_format == 'csv':
            return self._multi_summary_csv(report)
        else:
            return report

    def gchart(self, vals, period, name, color='438043'):
        return self.gchart_url(vals, period, name, color=color)

    def gchart_url(self, vals, period, name, color='438043'):
        """ TODO: refactor this with identical accession_report_view_helper.py function. """
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

    ## end class CatalogingReport()
