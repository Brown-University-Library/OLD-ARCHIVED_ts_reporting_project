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
ENV_PATH = os.path.abspath( '{}/../local_settings.env'.format(PROJECT_DIR) )
# print( 'ENV_PATH, ```{}```'.format(ENV_PATH) )


## update path
sys.path.append( PROJECT_DIR )

## load up env vars
dotenv.read_dotenv( ENV_PATH )

## reference django settings
os.environ['DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULE  # so django can access its settings

## gogogo
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
