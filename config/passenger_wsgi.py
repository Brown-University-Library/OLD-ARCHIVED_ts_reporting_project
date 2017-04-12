"""
WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os, sys
import dotenv


PROJECT_DIR = os.path.dirname( os.path.dirname(os.path.abspath(__file__)) )
SETTINGS_MODULE = 'config.settings'
ENV_PATH = os.path.join( PROJECT_DIR, '..env' )
print( 'ENV_PATH, ```{}```'.format(ENV_PATH) )


## update path
sys.path.append( PROJECT_DIR )

# ## activate venv
# activate_this = os.path.join(os.path.dirname( PROJECT_DIR ),'env_ts_reports/bin/activate_this.py')
# execfile(activate_this, dict(__file__=activate_this))

## load up env vars
dotenv.read_dotenv(  )

## reference django settings
os.environ['DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULE  # so django can access its settings

# ## load up env vars
# SETTINGS_FILE = os.environ['IIP__SETTINGS_PATH']  # set in activate_this.py, and activated above
# import shellvars
# var_dct = shellvars.get_vars( SETTINGS_FILE )
# for ( key, val ) in var_dct.items():
#     os.environ[key] = val

## gogogo
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
