# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime, io, logging, os, pprint
import pymarc
from django.test import TestCase
from tech_services_reports.lib.marc_parser import FileParser, RecordParser
from tech_services_reports.lib.accession_report_view_helper import AccessionReportViewHelper


log = logging.getLogger(__name__)
TestCase.maxDiff = None


class RecordParserTest( TestCase ):
    """ Checks lib.marc_parser.RecordParser() """

    def setUp(self):
        self.rp = RecordParser()
        self.bad_marc_no_bib = b'02671cas a2200541 a 4500001001200000003000700012005001700019006001900036007001500055008004100070010001500111022002500126035001500151040005000166041001800216042000800234043001200242050001500254245012700269246003800396260014800434299005700582310001500639336002200654337002400676338003300700362004100733500002200774506004600796538003600842546007200878650003200950651005300982710005501035710008101090856016901171880013401340880021401474880004201688880007501730880011301805907003501918998004501953910002901998910002802027990000802055945006602063\x1eocm60778015\x1eWaSeSS\x1e20130213090332.0\x1em        d        \x1ecr  n         \x1e050630c20039999ru qr pss     0    0ruso \x1e  \x1fa2005200327\x1e  \x1fa1727-0634\x1fl1727-0634\x1e  \x1fassj0056376\x1e  \x1faDLC\x1fbeng\x1fcDLC\x1fdDLC\x1fdOCoLC\x1fdUKMGB\x1fdInU\x1fdWaSeSS\x1e0 \x1farus\x1fbeng\x1ffeng\x1e  \x1fapcc\x1e  \x1fae-ru---\x1e00\x1faHN1\x1fb.Z485\x1e00\x1f6880-01\x1faZhurnal issledovani\xc4\xad so\xef\xb8\xa0t\xef\xb8\xa1sial\xca\xb9no\xc4\xad politiki\x1fh[electronic resource] =\x1fbThe journal of social policy studies.\x1e31\x1faJournal of social policy studies.\x1e  \x1f6880-02\x1faSaratov :\x1fbRossi\xc4\xadskoe obshchestvo so\xef\xb8\xa0t\xef\xb8\xa1siologov [i] \xef\xb8\xa0T\xef\xb8\xa1Sentr so\xef\xb8\xa0t\xef\xb8\xa1sial\xca\xb9no\xc4\xad politiki i gendernykh issledovani\xc4\xad,\x1fc[2003]-\x1e00\x1faZhurnal issledovani\xc4\xad so\xef\xb8\xa0t\xef\xb8\xa1sial\xca\xb9no\xc4\xad politiki =\x1e  \x1faQuarterly.\x1e  \x1fatext\x1f2rdacontent.\x1e  \x1facomputer\x1f2rdamedia.\x1e  \x1faonline resource\x1f2rdacarrier.\x1e0 \x1f6880-03\x1faT.1, N 1 (\xef\xb8\xa0i\xef\xb8\xa1anv. 2003)-\x1e  \x1faTitle from cover.\x1e  \x1faMay be limited to Brown University users.\x1e  \x1faMode of access: World Wide Web.\x1e  \x1faIn Russian, with summaries and added tables of contents in English.\x1e 0\x1faSocial policy\x1fvPeriodicals.\x1e 0\x1faRussia (Federation)\x1fxSocial policy\x1fvPeriodicals.\x1e2 \x1f6880-04\x1faRossi\xc4\xadskoe obshchestvo so\xef\xb8\xa0t\xef\xb8\xa1siologov.\x1e2 \x1f6880-05\x1fa\xef\xb8\xa0T\xef\xb8\xa1Sentr so\xef\xb8\xa0t\xef\xb8\xa1sial\xca\xb9no\xc4\xad politiki i gendernykh issledovani\xc4\xad\x1e40\x1fzClick here to view online version; access limited to Brown University users.\x1fuhttp://RL3TP7ZF5X.search.serialssolutions.com/?V=1.0&L=RL3TP7ZF5X&S=JCs&C=ZHISP&T=marc\x1e00\x1f6245-01/(N\x1fa\xd0\x96\xd1\x83\xd1\x80\xd0\xbd\xd0\xb0\xd0\xbb \xd0\xb8\xd1\x81\xd1\x81\xd0\xbb\xd0\xb5\xd0\xb4\xd0\xbe\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xe6\xd0\xb8 \xd1\x81\xd0\xbe\xd1\x86\xd0\xb8\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xe6\xd0\xb8 \xd0\xbf\xd0\xbe\xd0\xbb\xd0\xb8\xd1\x82\xd0\xb8\xd0\xba\xd0\xb8 =\x1fbThe journal of social policy studies.\x1e  \x1f6260-02/(N\x1fa\xd0\xa1\xd0\xb0\xd1\x80\xd0\xb0\xd1\x82\xd0\xbe\xd0\xb2 :\x1fb\xd0\xa0\xd0\xbe\xd1\x81\xd1\x81\xd0\xb8\xe6\xd0\xb8\xd1\x81\xd0\xba\xd0\xbe\xd0\xb5 \xd0\xbe\xd0\xb1\xd1\x89\xd0\xb5\xd1\x81\xd1\x82\xd0\xb2\xd0\xbe \xd1\x81\xd0\xbe\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbb\xd0\xbe\xd0\xb3\xd0\xbe\xd0\xb2 [\xd0\xb8\xd7\x99Q\xce\xb2 \xd0\xa6\xd0\xb5\xd0\xbd\xd1\x82\xd1\x80 \xd1\x81\xd0\xbe\xd1\x86\xd0\xb8\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd7\x994\xe2\x80\xa0I \xd0\xbf\xd0\xbe\xd0\xbb\xd0\xb8\xd1\x82\xd0\xb8\xd0\xba\xd0\xb8 \xd0\xb8 \xd0\xb3\xd0\xb5\xd0\xbd\xd0\xb4\xd0\xb5\xd1\x80\xd0\xbd\xd1\x8b\xd1\x85 \xd0\xb8\xd1\x81\xd1\x81\xd0\xbb\xd0\xb5\xd0\xb4\xd0\xbe\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xfd\xd0\xb8,\x1fc[2003]-\x1e0 \x1f6362-03/(N\x1fa\xd0\xa2.1, \xd0\x9d 1 (\xd1\x8f\xd0\xbd\xd0\xb2. 2003)-\x1e2 \x1f6710-04/(N\x1fa\xd0\xa0\xd0\xbe\xd1\x81\xd1\x81\xd0\xb8\xe6\xd0\xb8\xd1\x81\xd0\xba\xd0\xbe\xd0\xb5 \xd0\xbe\xd0\xb1\xd1\x89\xd0\xb5\xd1\x81\xd1\x82\xd0\xb2\xd0\xbe \xd1\x81\xd0\xbe\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbb\xd0\xbe\xd0\xb3\xd0\xbe\xd0\xb2\x1e2 \x1f6710-05/(N\x1fa\xd0\xa6\xd0\xb5\xd0\xbd\xd1\x82\xd1\x80 \xd1\x81\xd0\xbe\xd1\x86\xd0\xb8\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xe6\xd0\xb8 \xd0\xbf\xd0\xbe\xd0\xbb\xd0\xb8\xd1\x82\xd0\xb8\xd0\xba\xd0\xb8 \xd0\xb8 \xd0\xb3\xd0\xb5\xd0\xbd\xd0\xb4\xd0\xb5\xd1\x80\xd0\xbd\xd1\x8b\xd1\x85 \xd0\xb8\xd1\x81\xd1\x81\xd0\xbb\xd0\xb5\xd0\xb4\xd0\xbe\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xe6\xd0\xb8\x1e  \x1fa.b41506819\x1fb06-12-15\x1fc07-10-07\x1e  \x1faes001\x1fb02-14-13\x1fcs\x1fda\x1fe-\x1ffrus\x1fgru \x1fh0\x1fi1\x1e  \x1faSerials Solutions Change\x1e  \x1faHathi Trust report None\x1e0 \x1faHN1\x1e  \x1fg1\x1fj0\x1fless  \x1fp$0.00\x1fs-\x1ft255\x1fu0\x1fv0\x1fw0\x1fx0\x1fy.i143357967\x1fz07-10-07\x1e\x1d'
        self.good_marc_with_bib = b'''01743nam a2200361Ia 45e0001001200000003000400012005001700016008004100033010001500074020004300089020004000132020003800172020003500210040005400245050002600299090002700325100002800352245012900380260003400509300003700543505026300580500004800843504006400891600005800955907003501013998004501048910000801093910001401101910002701115993001401142945012201156996010301278ocm74987998RPB20080522192622.0061031s2007    nyuh     bk   001 0deng    a2006036501  a9780826418760 (hardcover : alk. paper)  a0826418767 (hardcover : alk. paper)  a9780826418777 (pbk. : alk. paper)  a0826418775 (pbk. : alk. paper)  aDLCcDLCdBAKERdBTCTAdC#PdYDXCPdIXAdGK8dJED00aML420.W5525bL36 2007  aML420.W5525bL36 2007 1 aLambert, Philip,d1958-10aInside the music of Brian Wilson :bthe songs, sounds, and influences of the Beach Boys' founding genius  /cPhilip Lambert.  aNew York :bContinuum,c2007.  axii, 404 p. :bfacsim. ;c23 cm.0 aAwakenings -- Surf harmony -- First album -- Surfin' U.S.A -- Produced by Brian Wilson -- Catching waves -- Fun, fun, fun -- Beach-Boys-mania -- Please let me wonder -- Beach Boys '65 -- Pet sounds -- American gospel -- A cork on the ocean -- Love and mercy.  a"Brian Wilson song chronology": p. 334-378.  aIncludes bibliographical references (p. 389-394) and index.10aWilson, Brian,d1942- xCriticism and interpretation.  a.b41368526b06-18-15c06-27-07  ag0001b06-27-07cmdae-fenggnyuh0i1  aybp  aBackstage  aHathi Trust report SPM  aftp062907  fbookplate 054177_purchased_2007g1i31236091278161j0lorwigo-p$0.00q r s-t0u5v2w2x1y.i143051210z06-27-07  uhttp://library.brown.edu/bookplates/fund.php?account=054177zPurchased with the Emmett Family Fund'''

    def make_record( self, raw_bytes ):
        """ Not a test; preps record object. """
        s = raw_bytes.decode( 'utf-8', errors='ignore' )  # 'replace' and 'backslashreplace' generate errors on ```record = next( reader )```
        handled_b = s.encode( 'utf-8' )
        fh = io.BytesIO( handled_b )
        reader = pymarc.MARCReader( fh )
        record = next( reader )
        return record

    def test_parse_problem_bib(self):
        """ Checks bib handling. """
        record = self.make_record( self.bad_marc_no_bib )
        self.assertEqual( None, self.rp.get_bib( record ), record.as_dict() )

    def test_parse_good_bib(self):
        """ Checks bib handling. """
        record = self.make_record( self.good_marc_with_bib )
        self.assertEqual( 'b41368526', self.rp.get_bib( record ), record.as_dict() )

    def test_parse_bib_date_bad_record_problem_date(self):
        """ Checks bib date.
            The initial extract yields ```07-10-07  ``` """
        record = self.make_record( self.bad_marc_no_bib )
        self.assertEqual( datetime.date(2007, 7, 10), self.rp.get_bib_created( record ), record.as_dict() )

    def test_parse_cat_date_bad_record(self):
        """ Checks bib date. """
        record = self.make_record( self.bad_marc_no_bib )
        self.assertEqual( datetime.date(2013, 2, 14), self.rp.get_cat_date( record ), record.as_dict() )

    def test_get_field_bad_record_no995(self):
        """ Checks marc995 handling. """
        record = self.make_record( self.bad_marc_no_bib )
        self.assertEqual( [], self.rp.get_field( record, '995' ), '{}'.format( pprint.pformat(record.as_dict()) ) )

    def test_get_field_bad_record_910(self):
        """ Checks marc910 handling. """
        record = self.make_record( self.bad_marc_no_bib )
        self.assertEqual( 2, len( self.rp.get_field(record, '910') ), '{}'.format( pprint.pformat(record.as_dict()) ) )

    def test_get_field_good_record_910(self):
        """ Checks marc910 handling. """
        record = self.make_record( self.good_marc_with_bib )
        self.assertEqual( 3, len( self.rp.get_field(record, '910') ), '{}'.format( pprint.pformat(record.as_dict()) ) )

    def test_get_field_bad_record_945(self):
        """ Checks marc945 handling in bad record. """
        record = self.make_record( self.bad_marc_no_bib )
        self.assertEqual( 1, len( self.rp.get_field(record, '945') ), '{}'.format( pprint.pformat(record.as_dict()) ) )

    def test_get_field_good_record_945(self):
        """ Checks marc945 handling in good record. """
        record = self.make_record( self.good_marc_with_bib )
        self.assertEqual( 1, len( self.rp.get_field(record, '945') ), '{}'.format( pprint.pformat(record.as_dict()) ) )

    # end class RecordParserTest()


class FileParserTest( TestCase ):
    """ Checks lib.marc_parser.FileParser() """

    def setUp(self):
        self.loop_filepath = os.environ['TS_RPRT__PREP_LOOP_FILEPATH']
        self.fl_prsr = FileParser()
        self.location_format_map = {
            'arc': {'building': 'Hay', 'display': 'HAY ARCHIVES', 'format': 'Book'},
            'arccd': {'building': 'Hay', 'display': 'HAY ARCHIVES CD', 'format': 'CD (Sound Recording)'},
            'arccs': {'building': 'Hay', 'display': 'HAY ARCHIVES CASSETTE', 'format': 'Cassette'}
            }

    def test_OLD_process_marc_file(self):
        """ Temp. """
        from tech_services_reports.lib import marc_parser
        from tech_services_reports.models import Accession
        acc1 = Accession( number='i186011167', created=datetime.datetime.strptime('2017-04-07', '%Y-%m-%d'), acquisition_method='Gift', format='Book', location='japan', volumes=1, titles=1, serial_added_volume=False )
        acc2 = Accession( number='i186010953', created=datetime.datetime.strptime('2017-04-07', '%Y-%m-%d'), acquisition_method='Purchase', format='dvd', location='rdv', volumes=1, titles=1, serial_added_volume=False )
        acc3 = Accession( number='i186010394', created=datetime.datetime.strptime('2017-04-07', '%Y-%m-%d'), acquisition_method='Gift', format='CD (Sound Recording)', location='ocd', volumes=1, titles=1, serial_added_volume=False )
        acc1.save(); acc2.save(); acc3.save()
        existing_items = set( [i.number for i in Accession.objects.all()] )
        data_tple = marc_parser.process_marc_file( self.loop_filepath, existing_items, self.location_format_map )
        self.assertEqual( tuple, type(data_tple) )
        self.assertEqual( 211, len(data_tple[0]) )
        self.assertEqual( 9, len(data_tple[1]) )
        self.assertEqual( 98, len(data_tple[2]) )

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
        data_tple = self.fl_prsr.process_marc_file( self.loop_filepath, existing_items, self.location_format_map )
        self.assertEqual( tuple, type(data_tple) )
        self.assertEqual( 211, len(data_tple[0]) )
        self.assertEqual( 9, len(data_tple[1]) )
        self.assertEqual( 98, len(data_tple[2]) )

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


class AccessionReportViewHelperTest( TestCase ):
    """ Checks helpers for accession-report. """

    def test_set_dates__good_month_and_year(self):
        """ Checks returned start and end dates. """
        hlpr = AccessionReportViewHelper()
        self.assertEqual(
            ( datetime.date(2014, 2, 1), datetime.date(2014, 2, 1), 'February 2014' ),
            hlpr.set_dates( 2014, 2 )
            )

    def test_set_dates__year_only(self):
        """ Checks returned start and end dates. """
        hlpr = AccessionReportViewHelper()
        self.assertEqual(
            ( datetime.date(2014, 1, 1), datetime.date(2014, 12, 31), '2014 yearly total' ),
            hlpr.set_dates( 2014 )
            )
