"""
WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
from sys import path


PROJECT_DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_MODULE = 'config.settings'


## update path
path.append(PROJECT_DIR_PATH)



## activate venv -- works under python2, not python3
# activate_this_path = os.path.join( os.path.dirname(PROJECT_DIR_PATH),'env_ts_rprt/bin/activate_this.py' )
# execfile(activate_this_path, dict(__file__=activate_this))



## activate venv  -- works; source: <http://devmartin.com/blog/2015/02/how-to-deploy-a-python3-wsgi-application-with-apache2-and-debian/>
activate_this_path = os.path.join( os.path.dirname(PROJECT_DIR_PATH),'env_ts_rprt/bin/activate_this.py' )
exec( open(activate_this_path).read() )


## activate venv  -- works; source: <http://stackoverflow.com/questions/30642894/getting-flask-to-use-python3-apache-mod-wsgi>
# def execfile(filename):
#     globals = dict( __file__ = filename )
#     exec( open(filename).read(), globals )

# activate_this_path = os.path.join( os.path.dirname(PROJECT_DIR_PATH),'env_ts_rprt/bin/activate_this.py' )
# execfile( activate_this_path )



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




