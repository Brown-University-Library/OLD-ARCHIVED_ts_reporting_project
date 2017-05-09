# -*- coding: utf-8 -*-

import logging, pprint
from django.core.cache import cache
from django.core.urlresolvers import reverse
from tech_services_reports.models import Accession, CatEdit


log = logging.getLogger("webapp")


class DateMaker(object):
    """ Prepares accession and catalog dates. """

    def get_acc_months( self ):
        """ Returns accession monthly dates.
            Called by views.index() """
        acc_months = cache.get( 'acc_months_cached' )
        if acc_months is None:
            acc_months = Accession.objects.dates('created', 'month', order='DESC')
            cache.set( 'acc_months_cached', acc_months, 60*60*24 )  # 1 day
        # log.debug( 'type(acc_months), `{typ}`; acc_months, ```{val}```'.format( typ=type(acc_months), val=acc_months) )
        return acc_months

    def get_acc_years( self ):
        """ Returns accession year dates.
            Called by views.index() """
        acc_years = cache.get( 'acc_years_cached' )
        if acc_years is None:
            acc_years = Accession.objects.dates('created', 'year', order='DESC')
            cache.set( 'acc_years_cached', acc_years, 60*60*24 )
        log.debug( 'type(acc_years), `{typ}`; acc_years, ```{val}```'.format( typ=type(acc_years), val=pprint.pformat(acc_years)) )
        return acc_years

    def get_acc_years_v2( self, scheme, host ):
        """ Returns accession year dates.
            Called by views.index() """
        acc_years = cache.get( 'acc_years_cached' )
        acc_years_lst = []
        if acc_years is None:
            acc_years = Accession.objects.dates('created', 'year', order='DESC')
            cache.set( 'acc_years_cached', acc_years, 60*60*24 )
        for year in acc_years:
            acc_years_lst.append( { year.year: '{sch}://{hst}{url}{yr}/'.format(
                sch=scheme, hst=host, url=reverse('accessions'), yr=year.year) } )
        log.debug( 'type(acc_years), `{typ}`; acc_years, ```{val}```'.format( typ=type(acc_years), val=pprint.pformat(acc_years)) )
        log.debug( 'acc_years_lst, ```{}```'.format(pprint.pformat(acc_years_lst)) )
        return acc_years_lst

    def get_cat_months( self ):
        """ Returns cataloging monthly dates.
            Called by views.index() """
        cat_months = cache.get( 'cat_months_cached' )
        if cat_months is None:
            cat_months = CatEdit.objects.dates('edit_date', 'month', order='DESC')
            cache.set( 'cat_months_cached', cat_months, 60*60*24 )
        return cat_months

    def get_cat_years( self ):
        """ Returns cataloging year dates.
            Called by views.index() """
        cat_years = cache.get( 'cat_years_cached' )
        if cat_years is None:
            cat_years = CatEdit.objects.dates('edit_date', 'year', order='DESC')
            cache.set( 'cat_years_cached', cat_years, 60*60*24 )
        return cat_years
