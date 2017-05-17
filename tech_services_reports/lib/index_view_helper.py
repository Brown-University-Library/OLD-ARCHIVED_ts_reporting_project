# -*- coding: utf-8 -*-

import calendar, logging, pprint
from django.conf import settings as project_settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from tech_services_reports.models import Accession, CatEdit


log = logging.getLogger("webapp")


class DateMaker(object):
    """ Prepares accession and catalog dates. """

    def make_context( self, scheme, host ):
        """ Builds context for index view.
            Called by views.index() """
        context = {
            'STATIC_URL': project_settings.STATIC_URL,
            'acc_months': self.get_acc_months( scheme, host ),
            'acc_years': self.get_acc_years( scheme, host ),
            'cat_months': self.get_cat_months( scheme, host ),
            'cat_years': self.get_cat_years( scheme, host ),
            'admin_edit_harvested_accession_data_url': reverse('admin:tech_services_reports_accession_changelist'),
            'admin_edit_harvested_cat_data_url': reverse('admin:tech_services_reports_catedit_changelist')
            }
        log.debug( 'context,```{}```'.format( pprint.pformat(context) ) )
        return context

    def get_acc_months( self, scheme, host ):
        """ Returns accession monthly date info.
            Called by make_context() """
        acc_months = cache.get( 'acc_months_cached' )
        acc_month_lst = []
        if acc_months is None:
            acc_months = Accession.objects.dates('created', 'month', order='DESC')  # grabs list of accession date-objects, one-per-month
            cache.set( 'acc_months_cached', acc_months, 60*60*24 )  # 1 day
        for date_obj in acc_months:
            link = '{sch}://{hst}{url}{yr}/{mo}/'.format( sch=scheme, hst=host, url=reverse('accessions'), yr=date_obj.year, mo=date_obj.month )
            acc_month_lst.append( { 'month': date_obj.month, 'month_name': calendar.month_name[date_obj.month], 'year': date_obj.year, 'link': link } )
        # log.debug( 'type(acc_months), `{typ}`; acc_months, ```{val}```'.format( typ=type(acc_months), val=acc_months) )
        log.debug( 'acc_month_lst, ```{}```'.format(pprint.pformat(acc_month_lst)) )
        return acc_month_lst

    def get_cat_months( self, scheme, host ):
        """ Returns catalog monthly date info.
            Called by make_context() """
        cat_months = cache.get( 'cat_months_cached' )
        cat_month_lst = []
        if cat_months is None:
            cat_months = CatEdit.objects.dates('edit_date', 'month', order='DESC')  # grabs list of cataloging date-objects, one-per-month
            cache.set( 'cat_months_cached', cat_months, 60*60*24 )  # 1 day
        for date_obj in cat_months:
            link = '{sch}://{hst}{url}{yr}/{mo}/'.format( sch=scheme, hst=host, url=reverse('cataloging'), yr=date_obj.year, mo=date_obj.month )
            cat_month_lst.append( { 'month': date_obj.month, 'month_name': calendar.month_name[date_obj.month], 'year': date_obj.year, 'link': link } )
        log.debug( 'cat_month_lst, ```{}```'.format(pprint.pformat(cat_month_lst)) )
        return cat_month_lst

    def get_acc_years( self, scheme, host ):
        """ Returns accession year date info.
            Called by make_context() """
        acc_years = cache.get( 'acc_years_cached' )
        acc_years_lst = []
        if acc_years is None:
            acc_years = Accession.objects.dates('created', 'year', order='DESC')  # grabs list of accession date-objects, one-per-year
            cache.set( 'acc_years_cached', acc_years, 60*60*24 )
        for date_obj in acc_years:
            link = '{sch}://{hst}{url}{yr}/'.format( sch=scheme, hst=host, url=reverse('accessions'), yr=date_obj.year )
            acc_years_lst.append( {'year': date_obj.year, 'link': link} )
        log.debug( 'acc_years_lst, ```{}```'.format(pprint.pformat(acc_years_lst)) )
        return acc_years_lst

    def get_cat_years( self, scheme, host ):
        """ Returns catalog year dates.
            Called by views.index() """
        cat_years = cache.get( 'cat_years_cached' )
        cat_years_lst = []
        if cat_years is None:
            cat_years = CatEdit.objects.dates('edit_date', 'year', order='DESC')  # grabs list of cataloging date-objects, one-per-year
            cache.set( 'cat_years_cached', cat_years, 60*60*24 )
        for date_obj in cat_years:
            link = '{sch}://{hst}{url}{yr}/'.format( sch=scheme, hst=host, url=reverse('cataloging'), yr=date_obj.year )
            cat_years_lst.append( {'year': date_obj.year, 'link': link} )
        log.debug( 'cat_years_lst, ```{}```'.format(pprint.pformat(cat_years_lst)) )
        return cat_years_lst

    ## end class DateMaker()
