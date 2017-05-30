# -*- coding: utf-8 -*-

import csv, datetime, json, logging, pprint

from django.http import HttpResponse



class CatalogingCSVwriter( object ):

    def __init__( self ):
        pass

    def get_csv_response( self, context ):

        response = HttpResponse( content_type='text/csv; charset=utf-8' )

        return response

        ## end def get_csv_response()


    ## end class CatalogingCSVwriter()
