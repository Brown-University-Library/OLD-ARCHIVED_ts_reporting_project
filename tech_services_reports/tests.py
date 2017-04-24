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
                ['count_bad', 'count_good', 'count_processed', 'counter', 'current_position', 'file_size_MB', 'last_position', 'process_flag', 'reader', 'segment_to_review', 'start_time'],
                sorted( loop_dct.keys() )
                )
            self.assertEqual( datetime.datetime, type( loop_dct['start_time'] ) )
            self.assertEqual( 147.23817920684814, loop_dct['file_size_MB'] )
            self.assertEqual( pymarc.reader.MARCReader, type( loop_dct['reader'] ) )
            self.assertEqual( True, loop_dct['process_flag'] )


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

