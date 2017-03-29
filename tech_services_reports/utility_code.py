# -*- coding: utf-8 -*-

from __future__ import unicode_literals


# from django.utils import simplejson as json
import datetime, json, logging, time, re
from datetime import date
import settings_app
# from django.utils import simplejson
import urllib
#from models import Bib, CatEdit, Item
from operator import itemgetter, attrgetter
from helpers import defaultdict
from itertools import chain


log = logging.getLogger( "processing" )
log.debug( 'loaded utility_code.py' )


#Brown specific
format_codes = {
      'a': 'book',
      'k': '2-D graphic',
      's': 'serial/journal',
      'g': 'audio visual',
      'm': 'computer file',
      't': 'manuscript',
      'f': 'map, mss',
      'j': 'music record',
      'd': 'score, mss',
      'i': 'spoken record',
      'r': '3-D object',
      'o': 'kit',
      'e': 'map',
      'p': 'mixed',
      'c': 'score',
      's': 'serial or journal'
}

bib_level_codes = {
      'c': 'collection',
      'i': 'integrating_resource',
      'a': 'monograph component part',
      'b': 'serial component part',
      's': 'serial',
      'd': 'sub unit',
      'm': 'monograph',
}

def pull_shib_info(request, data):
    """Pull information for the Shib request and get/create and login
    Django User object."""
    from django.contrib.auth.models import User
    from django.contrib.auth import login, get_backends
    import settings_app
    try:
        from settings_app import ENV
        if ENV == 'testing':
            testing = True
            u = User.objects.get(username=settings_app.TEST_USER)
            backend = get_backends()[0]
            u.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
            login(request, u)
            return u
        else:
            pass
    except ImportError:
        pass
    username = data.get('Shibboleth-eppn', None)
    netid = data.get('Shibboleth-brownNetId', None)
    #Quite now because user is not authenticated for some reason.
    if not username or not netid:
        return
    else:
	#strip @brown.edu from username.
	username = username.replace('@brown.edu', '').strip()
    u, created = User.objects.get_or_create(username=username)
    #Fill in user details after first login.
    #if created:
    u.first_name = data.get('Shibboleth-givenName', '')
    u.last_name = data.get('Shibboleth-sn', '')
    u.email = data.get('Shibboleth-mail', None)
    #Each login check super or staff status to allow for changes
    #to the setting fail.
    if netid in settings_app.SUPER_USERS:
        u.is_superuser = True
    if netid in settings_app.STAFF_USERS:
        u.is_staff = True
    #Brute force login, see - http://djangosnippets.org/snippets/1552/
    backend = get_backends()[0]
    u.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
    login(request, u)
    #Put garbage in the passward
    u.set_unusable_password()
    u.save()
    return u


def convert_date(datestr):
   """III Only reports two digit year numbers in MARC records.
   Delimited text exports will report 2000 and on as four digits.
   This function tries to handle both and convert to calculable date
   objects."""
   from datetime import datetime, timedelta, date
   if not datestr:
       return
   if datestr[2] == '/':
       dgroups = datestr.split('/')
   else:
       dgroups = datestr.split('-')
   #CSV
   #10/1/2010

   try:
       month = int(dgroups[0])
       day = int(dgroups[1])
       year = int(dgroups[2])
   except ValueError, e:
       #print>>sys.stderr, e, ' in date function.'
       return
   except IndexError, e:
       return
   this_year = (date.today().year) - 2000
   #If the year integer is greater than the current year then,
   #pad with 1900.
   if len(str(year)) < 3:
       if year > this_year:
           year = 1900 + year
       else:
           year = 2000 + year
   try:
       return date(year, month, day) #.isoformat() + 'Z'
   except ValueError:
       return

def last_day_of_month(date):
    """Function to return the last day of the month for any given
    Python date object.  Code from:
    http://stackoverflow.com/questions/42950/get-last-day-of-the-month-in-python"""
    if date.month == 12:
        return date.replace(day=31)
    return date.replace(month=date.month+1, day=1) - datetime.timedelta(days=1)

def gchart_url(vals, period, name, color='438043'):
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

#class Accession:
#    def __init__(self, building, format, acq_type, volumes, titles):
#        self.building = building
#        self.format = format
#        self.volumes = volumes
#        self.titles = titles
#        self.acq_type = acq_type
#    def __repr__(self):
#        return repr((self.building, self.format, self.acq_type, self.volumes, self.titles))

#class Accession:
#    def __init__(self, location, format, acq_type, volumes, titles):
#        self.location = location
#        self.format = format
#        self.volumes = volumes
#        self.titles = titles
#        self.acq_type = acq_type
#    def __repr__(self):
#        return repr((self.location, self.format))


class AcquisitionMethod(object):

    def __init__(self, note):
        log.debug( 'starting AcquisitionMethod.__init__()' )
		#Clean up bad data in templates.
        self.note = note.strip('.')
        self.chunked = note.split(' ')
        self.possible_notes = [
            "Purchase Serial AV",
            "Gift Serial AV",
            "Exchange Serial AV",
            "Purchase AC/AV",
            "Gift AC/AV",
            "Exchange AC/AV",
            "Purchase",
            "Gift",
            "Exchange",
            "Serials Solutions",
            "Purchase AV",
            "Serial Analytic"
        ]
        self.possible_acq_types = [
            "Purchase",
            "Gift",
            "Exchange",
            "Serials Solutions",
            #"Serial Solutions",
        ]
        self.process_notes( note )

    def process_notes( self, note ):
        if note not in self.possible_notes:
            note_found = False
            for split in note.split(';'):
                #Clean up dirty template data
                split = split.lstrip('00')
                split = split.strip('.')
                split = split.replace('exch', 'Exchange')
                split = split.replace('"', '').title()
                #Remove 'd' for purchased, exchanged, etc.
                split = split.rstrip('d').title().strip()
                log.debug( 'split, `{}`'.format(split) )
                #Brute force cleaning
                if split == 'Gifts':
                    split = 'Gift'
                elif split == 'exchange':
                    split == 'Exchange'
                elif split == 'Puchase':
                    split == 'Purchase'
                if split in self.possible_notes:
                    self.note = split
                    note_found = True
                    break
            log.debug( 'note_found, `{}`'.format(note_found) )
            if not note_found:
                # raise NameError( '```{note}``` not in the possible notes: ```{poss}```'.format( note=note, poss=", ".join(self.possible_notes)) )
                message = '```{note}``` not in the possible notes: ```{poss}```'.format( note=note, poss=", ".join(self.possible_notes) )
                log.debug( message )
                raise NameError( message )

    def acq_type(self):
        if self.chunked[0] in self.possible_acq_types:
            return self.chunked[0]
        elif self.note in self.possible_acq_types:
            return self.note
        else:
            raise NameError('%s, %s not in the possible acq types: %s' \
                % (self.chunked[0], self.note, ", ".join(self.possible_acq_types)))

#    def added_copies(self):
#        if len(self.chunked) > 1:
#            return {'titles': 0, 'volumes': 1}
#        else:
#            return {'titles': 1, 'volumes': 1}

class CatStat(object):
    """Used during import to translate from MARC fields to database fields.
    """
    def __init__(self, rec):
        # log.debug( 'starting CatStat.__init__()' )
        self.rec = rec
        self.oclc_code = settings_app.OCLC_CODE
        self.number = rec['907']['a'][1:]
        self.original = self.is_original()
        self.enriched = self.is_enriched()
        self.copy = self.is_copy()
        self.material_type = self.mat_type()
        self.cattype = self.cat_type()
        self.mattype = self.mat_type()


    def _sf_iter(self, field, indicator):
        """Iterate through subfields.
        Takes a field as input and a subfield indicator."""
        matches = []
        if not field:
            return []
        for sf in field:
            if sf[0] == indicator:
                matches.append(sf[1])
        return matches

    def source(self):
        source = {}
        o40 = self.rec['040']
        source['original'] = self._sf_iter(o40, 'a')
        source['language'] = self._sf_iter(o40, 'b')
        source['transcribing'] = self._sf_iter(o40, 'c')
        source['transcribing'] = self._sf_iter(o40, 'c')
        source['modifying'] = self._sf_iter(o40, 'd')
        return source

    def is_original(self):
        if self.oclc_code in self.source()['original']:
            return True
        else:
            return False

    def is_enriched(self):
        if self.oclc_code in self.source()['modifying']:
            return True
        else:
            return False

    def is_copy(self):
        source = self.source()
        if self.oclc_code not in source['original']:
            #if self.oclc_code not in source['modifying']:
            return True
            #else:
            #    return False
        else:
            return False

    def mat_type(self):
        try:
            return self.rec['998']['d']
        except KeyError:
            return

    def cat_type(self):
        """Return cataloging type.  Per Sam, if an item isn't
        original then it is copy."""
        if self.original:
            return 'original'
        else:
            return 'copy'

    # end class CatStat()


def location_format_mappings():
    import urllib
    # from django.utils import simplejson
    url = settings_app.LOCATION_FORMAT_URL
    map = urllib.urlopen(url)
    # map = simplejson.load(map)
    map = json.loads( map )
    location_format_dict = map['result']['items']
    #print>>sys.stderr, location_format_dict
    return location_format_dict


def jqueryUIDates(datestr):
    """Preps dates for jqueryUI widgets"""
    from datetime import date
    #03/02/2011
    datestr = datestr.rstrip('?format=csv')
    chunks = datestr.split('/')
    month = int(chunks[0])
    day = int(chunks[1])
    year = int(chunks[2])
    return date(year, month, day)


class CatalogingReport(object):
    def __init__(self, start, end, cataloger=None):
        from models import CatEdit, SummaryCatEdit
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
        if dbobj._meta.module_name == 'summarycatedit':
            v = dbobj.number
        return v

    def distinct_cat_types(self):
        return settings_app.DISTINCT_CAT_TYPES
#        raw = [t.lower() for t in self._distinct('type')]
#        spot = raw.index('catalog')
#        raw.pop(spot)
#        #Add from source field
#        source = self._distinct('source')
#        all = raw + source
#        return all

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
        summary = sorted(summary.iteritems(), key=itemgetter(1), reverse=True)
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
        summary = sorted(summary.iteritems(), key=itemgetter(1), reverse=True)
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
        summary = sorted(summary.iteritems(), key=itemgetter(1), reverse=True)
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
        return gchart_url(vals, period, name, color=color)



def last_harvest():
    return

def count_bib(item):
    """Get the first attached item and use that as the accessions
    count date.  E.g.  Items will be counted as an accessioned title
    on the date of the first attached item.

    Searches on the link table that connects the bibs and items."""
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute("SELECT bib_id FROM tech_services_reports_bib_items WHERE item_id = %s", [item.pk])
    bibs = cursor.fetchall()
    for b in bibs:
        acc_count_date = Bib.objects.get(number=b[0]).accession_count_date()
        #If the acc count date is less than the this item's create date
        #don't count as a title
        if acc_count_date < item.created:
            return False
    return True

class AccessionReport(object):
    def __init__(self, start, end, period=None):
        from models import Accession, SummaryAccession
        from django.db import connection
        from helpers import defaultdict
        from itertools import chain

        self.connection = connection

        self.start = start
        self.end = end
        self.items = Accession.objects.filter(created__gte=start, created__lte=end)
        self.summary_items = SummaryAccession.objects.filter(date__gte=start, date__lte=end)
        #Combine edits and summary edits
        self.all_items = list(chain(self.items, self.summary_items))
        #self.items = Accession.objects.all()
        self.total_items = len(self.items)
        # location_format_map = simplejson.load(urllib.urlopen(settings_app.LOCATION_FORMAT_URL))
        location_format_map = json.loads(urllib.urlopen(settings_app.LOCATION_FORMAT_URL))
        self.location_format_map = location_format_map['result']['items']
        self.total_volumes = self.total_volumes(self.items)
        self.total_titles = self.total_titles(self.items)
        self.last_updated = Accession.objects.latest('created').created

#        summary = defaultdict( int )
#        for item in self.items:
#            summary[item.location, item.acquisition_method] += 1
#        acc = list( q for q,_ in summary.keys())
#        table = []
#        for q in sorted( acc ):
#            table.append(q.location, q.acquisition_method, summary.count(q,'volumes'), summary.count(q,'titles'))
#
#        print table

        #self.formats = self.formats()
        #self.locations = self.locations()
        #formats = []
        #for item in self.items:
        #    if item.format not in formats:
        #        formats.append(item.format)
        #self.unique_formats = formats

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
        sort = sorted(cross.iteritems(), key=itemgetter(1), reverse=True)
        return {'header': ['Building', 'Volumes'],
                'data': sort,
                'totals': [total]}

    def all_formats_acq_type(self, location=None, serial_added_only=False):
        #Get project wide named tuples.
        from settings_app import Acc, AccTotal
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

        for item in items:
            loc = self._loc(item)
            _k = Acc(location=unicode(loc),
                     acquisition_method=unicode(item.acquisition_method),
                     count_type=u'volumes')
            cross[_k] += item.volumes
            _k = _k._replace(count_type='titles')
            cross[_k] += item.titles
            #Do totals by purchase type
            _tk = AccTotal(param=item.acquisition_method, param2='titles')
            cross[_tk] += item.titles
            _tk = _tk._replace(param2='volumes')
            cross[_tk] += item.volumes
        #sort = sorted(cross.iteritems(), key=itemgetter(0), reverse=True)
        #print sort
        return {'header': header,
                'data': cross}

    def by_format(self, format=None):
        from settings_app import Acc, AccTotal
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
            _k = Acc(location=unicode(loc),
                     acquisition_method=unicode(item.acquisition_method),
                     count_type=u'volumes')
            cross[_k] += item.volumes
            _k = _k._replace(count_type='titles')
            cross[_k] += item.titles
            _tk = AccTotal(param=item.acquisition_method, param2='titles')
            cross[_tk] += item.titles
            _tk = _tk._replace(param2='volumes')
            cross[_tk] += item.volumes
        return {'header': header,
                'data': cross}

    def by_format_chart(self, format=None):
        from settings_app import Acc, AccTotal
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
        sort = sorted(cross.iteritems(), key=itemgetter(1), reverse=True)
        return {'header': header,
                'data': sort}

    def serial_added_volumes(self):
        """Limit search to only serial added volumes."""
        return self.all_formats_acq_type(self, serial_added_only=True)

    def gchart(self, vals, period, name, color='438043'):
        return gchart_url(vals, period, name, color=color)





