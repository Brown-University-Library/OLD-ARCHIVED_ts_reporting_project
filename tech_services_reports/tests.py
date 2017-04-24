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

    def test_prepare_loop_vars(self):
        """ Checks loop initialization. """
        p = Parser()
        label_dct = {}
        labels = [ 'start', 'file_size', 'counter', 'count_processed', 'count_good', 'count_bad', 'last_position', 'current_position', 'segment_to_review', 'reader', 'process_flag' ]
        for i, label in enumerate( labels ):
            label_dct[ label ] = i
        with open( self.loop_filepath, 'rb' ) as fh:
            returned_tpl = p.prepare_loop_vars( fh )
            self.assertEqual( datetime.datetime, type( returned_tpl[label_dct['start']] ) )
            self.assertEqual( 154390421, returned_tpl[label_dct['file_size']] )
            self.assertEqual( pymarc.reader.MARCReader, type( returned_tpl[label_dct['reader']] ) )
            self.assertEqual( True, returned_tpl[label_dct['process_flag']] )


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

