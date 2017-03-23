# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.template import Library
from tech_services_reports import settings_app


register = Library()

from tech_services_reports.utility_code import AccessionReport

def crosstab_value(context, format, _key):
    #return report[dict_key]
    return {'total': context[format][_key]}
register.inclusion_tag('snippets/crosstab_value.html')(crosstab_value)

def dict_value(d, k):
    try:
        v = d[k]
    except KeyError:
        v = None
    return {'total': v}
register.inclusion_tag('snippets/crosstab_value.html')(dict_value)

def accession_tuple(acc, location, acq_type, count_type):
    from tech_services_reports.helpers import namedtuple
    from tech_services_reports.settings_app import Acc
    _k = Acc(location=location,
             acquisition_method=acq_type,
             count_type=count_type)
    try:
        v = acc[_k]
    except KeyError:
        v = 0
    return {'total': v}
register.inclusion_tag('snippets/crosstab_value.html')(accession_tuple)

def accession_tuple_total(acc, param, param2):
    from tech_services_reports.helpers import namedtuple
    from tech_services_reports.settings_app import AccTotal
    _k = AccTotal(param=param,
                  param2=param2)
    try:
        v = acc[_k]
    except KeyError:
        v = 0
    return {'total': v}

register.inclusion_tag('snippets/crosstab_value.html')(accession_tuple_total)

def accession_cross_value(d, k1, k2, k3):
    try:
        _k = "%s-%s-%s" % (k1, k2, k3)
        v = d[_k]
    except KeyError:
        v = 0
    return {'total': v}
register.inclusion_tag('snippets/crosstab_value.html')(accession_cross_value)


def summary_table(report):
    """Returns an HTML table."""
    return {'report': report}
register.inclusion_tag('snippets/summary_table.html')(summary_table)

def accession_table(report, headers, rows):
    """Returns an HTML table."""
    return {'report': report,
            'headers': headers,
            'rows': rows}
register.inclusion_tag('snippets/accession_table.html')(accession_table)

def multi_summary_table(report):
    """Returns an HTML table."""
    return {'report': report}
register.inclusion_tag('snippets/multi_summary_table.html')(multi_summary_table)

def accessions_summary_table(report):
    """Returns an HTML table."""
    return {'report': report}
register.inclusion_tag('snippets/accessions_summary_table.html')(accessions_summary_table)

def month_report_link(date_obj, url_prefix):
    label = date_obj.strftime('%B %Y')
    link = '%s/%s/%s' % (url_prefix, date_obj.year, date_obj.month)
    return {'label': label,
            'href': link}
register.inclusion_tag('snippets/report_link.html')(month_report_link)

def year_report_link(date_obj, url_prefix):
    label = date_obj.strftime('%Y')
    link = '%s/%s' % (url_prefix, date_obj.year)
    return {'label': label,
            'href': link}
register.inclusion_tag('snippets/report_link.html')(year_report_link)

