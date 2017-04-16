"""
WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
from sys import path


SITE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_MODULE = 'config.settings'


## update path
path.append(SITE_ROOT)



## activate venv -- works under python2
# activate_this = os.path.join(os.path.dirname(SITE_ROOT),'env_ts_rprt/bin/activate_this.py')
# execfile(activate_this, dict(__file__=activate_this))



## activate venv  -- not quite; source: <http://devmartin.com/blog/2015/02/how-to-deploy-a-python3-wsgi-application-with-apache2-and-debian/>
# activate_this = os.path.join(os.path.dirname(SITE_ROOT),'env_ts_rprt/bin/activate_this.py')
# exec( open(activate_this).read() )



def execfile(filename):
    globals = dict( __file__ = filename )
    exec( open(filename).read(), globals )

activate_this = os.path.join(os.path.dirname(SITE_ROOT),'env_ts_rprt/bin/activate_this.py')
execfile( activate_this )



## reference django settings
os.environ[u'DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULE  # so django can access its settings

## load up env vars
SETTINGS_FILE = os.environ['RPRTNG__SETTINGS_PATH']  # set in activate_this.py, and activated above
import shellvars
var_dct = shellvars.get_vars( SETTINGS_FILE )
for ( key, val ) in var_dct.items():
    os.environ[key.decode('utf-8')] = val.decode('utf-8')

## gogogo
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()




