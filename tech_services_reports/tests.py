# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime, logging, os
import pymarc
from django.test import TestCase
from tech_services_reports.lib.marc_parser import Parser


log = logging.getLogger(__name__)
TestCase.maxDiff = None


class ParserTest( TestCase ):
    """ Checks lib.mar_parser.Parser() """

    def setUp(self):
        self.loop_filepath = os.environ['TS_RPRT__PREP_LOOP_FILEPATH']
        self.prsr = Parser()

    def test_prepare_loop_vars(self):
        """ Checks loop initialization. """
        with open( self.loop_filepath, 'rb' ) as fh:
            loop_dct = self.prsr.prepare_loop_vars( fh )
            self.assertEqual(
                ['count_bad', 'count_good', 'count_processed', 'counter', 'current_position', 'file_size', 'last_position', 'process_flag', 'reader', 'segment_to_review'],
                sorted( loop_dct.keys() )
                )
            self.assertEqual( 154390421, loop_dct['file_size'] )
            self.assertEqual( pymarc.reader.MARCReader, type( loop_dct['reader'] ) )
            self.assertEqual( True, loop_dct['process_flag'] )

    def test_process_marc_file(self):
        """ Checks file processing. """
        ## get `existing items`
        from tech_services_reports.models import Accession
        acc1 = Accession( number='i186011167', created=datetime.datetime.strptime('2017-04-07', '%Y-%m-%d'), acquisition_method='Gift', format='Book', location='japan', volumes=1, titles=1, serial_added_volume=False )
        acc2 = Accession( number='i186010953', created=datetime.datetime.strptime('2017-04-07', '%Y-%m-%d'), acquisition_method='Purchase', format='dvd', location='rdv', volumes=1, titles=1, serial_added_volume=False )
        acc3 = Accession( number='i186010394', created=datetime.datetime.strptime('2017-04-07', '%Y-%m-%d'), acquisition_method='Gift', format='CD (Sound Recording)', location='ocd', volumes=1, titles=1, serial_added_volume=False )
        acc1.save(); acc2.save(); acc3.save()
        existing_items = set( [i.number for i in Accession.objects.all()] )
        ## the test
        data_tple = self.prsr.process_marc_file( self.loop_filepath, existing_items )
        self.assertEqual( 2, type(data_tple) )

    # end class ParserTest()


class RootUrlTest( TestCase ):
    """ Checks root urls. """

    def test_root_url_no_slash(self):
        """ Checks '/root_url'. """
        response = self.client.get( '' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )  # permanent redirect
        redirect_url = response._headers['location'][1]
        self.assertEqual(  '/stats/', redirect_url )

    def test_root_url_slash(self):
        """ Checks '/root_url/'. """
        response = self.client.get( '/' )  # project root part of url is assumed
        self.assertEqual( 302, response.status_code )  # permanent redirect
        redirect_url = response._headers['location'][1]
        self.assertEqual(  '/stats/', redirect_url )

    # end class RootUrlTest()

