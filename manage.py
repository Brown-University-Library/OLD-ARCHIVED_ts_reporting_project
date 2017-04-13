#!/usr/bin/env python
import os, pprint, sys
import dotenv

if __name__ == "__main__":

    PROJECT_DIR = os.path.dirname( os.path.abspath(__file__) )
    ENV_PATH = os.path.abspath( '{}/../ts_reporting_env_settings.env'.format(PROJECT_DIR) )
    # print( 'ENV_PATH, ```{}```'.format(ENV_PATH) )

    # print( 'environ initially, ```{}```'.format( pprint.pformat(dict(os.environ)) ) )
    dotenv.read_dotenv( ENV_PATH )
    # print( 'environ now, ```{}```'.format( pprint.pformat(dict(os.environ)) ) )

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
