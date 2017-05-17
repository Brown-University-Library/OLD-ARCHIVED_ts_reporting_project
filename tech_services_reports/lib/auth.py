# -*- coding: utf-8 -*-

import copy, json, logging, pprint

from django.contrib.auth import authenticate, get_backends, login
from django.contrib.auth.models import User
from tech_services_reports import settings_app


log = logging.getLogger("webapp")


def bul_login(func):
    """ Decorator to create a user object for the Shib user, if necessary, and log the user into Django.
        Called by views.py decorators. """
    log.debug( 'starting bul_login() decorator' )
    def decorator(request, *args, **kwargs):
        hlpr = LoginDecoratorHelper()
        cleaned_meta_dct = hlpr.prep_shib_dct( request.META )
        user_obj = hlpr.manage_usr_obj( request, cleaned_meta_dct )
        if not user_obj:
            return HttpResponseForbidden( '403 / Forbidden' )
        return func(request, *args, **kwargs)
    return decorator


class LoginDecoratorHelper(object):
    """ Handles login decorator code. """

    def prep_shib_dct( self, request_meta_dct ):
        """ Returns dct from shib-info.
            Called by bul_login() """
        log.debug( 'starting prep_shib_dct()' )
        new_dct = copy.copy( request_meta_dct )
        log.debug( 'new_dct, ```{}```'.format(pprint.pformat(new_dct)) )
        for (key, val) in request_meta_dct.items():  # get rid of some dictionary items not serializable
            if 'passenger' in key:
                new_dct.pop( key )
            elif 'wsgi.' in key:
                new_dct.pop( key )
        return new_dct

    def manage_usr_obj( self, request, meta_dct ):
        """ Pull information for the Shib request and get/create and login Django User object.
            Called by bul_login() """
        ( username, netid ) = self.set_basics( request.get_host(), meta_dct )
        if not username or not netid:
            return
        usr = self.update_userobj( username, netid, meta_dct )
        backend = get_backends()[0]
        usr.backend = '{module}.{classname}'.format( module=backend.__module__, classname=backend.__class__.__name__ )
        login( request, usr )  #Brute force login, see - http://djangosnippets.org/snippets/1552/
        log.debug( 'login complete' )
        return usr

    def set_basics( self, host, meta_dct ):
        """ Grabs username and netid.
            Called by manage_usr_obj() """
        if host == '127.0.0.1':
            username = settings_app.TEST_USERNAME
            netid = settings_app.TEST_NETID
        else:
            username = meta_dct.get('Shibboleth-eppn', None)
            netid = meta_dct.get('Shibboleth-brownNetId', None)
        log.debug( 'username, `{usr}`; netid, `{net}`'.format( usr=username, net=netid ) )
        return ( username, netid )

    def update_userobj( self, username, netid, meta_dct ):
        """ Grabs user object, updates and saves it.
            Called by manage_usr_obj() """
        usr, created = User.objects.get_or_create( username=username.replace('@brown.edu', '').strip() )
        if netid in settings_app.SUPER_USERS: usr.is_superuser = True
        if netid in settings_app.STAFF_USERS: usr.is_staff = True
        if created:
            usr.first_name = meta_dct.get( 'Shibboleth-givenName', '' )
            usr.last_name = meta_dct.get( 'Shibboleth-sn', '' )
            usr.email = meta_dct.get( 'Shibboleth-mail', None )
            usr.set_unusable_password()
        usr.save()
        log.debug( 'user updated and saved.' )
        return usr

    ## end class LoginDecoratorHelper()



# def prep_shib_dct( request ):
#     """ Returns dct from shib-info.
#         Called by bul_login() """
#     log.debug( 'starting prep_shib_dct()' )
#     new_dct = copy.copy( request.META )
#     log.debug( 'new_dct, ```{}```'.format(pprint.pformat(new_dct)) )
#     for (key, val) in request.META.items():  # get rid of mod_wsgi dictionary items not serializable
#         if 'passenger' in key:
#             new_dct.pop( key )
#         elif 'wsgi.' in key:
#             new_dct.pop( key )
#     return new_dct

# def manage_usr_obj( request, data ):
#     """ Pull information for the Shib request and get/create and login Django User object.
#         Called by bul_login() """
#     ( username, netid ) = set_basics( request.get_host(), data )
#     if not username or not netid:
#         return
#     u = update_userobj( username, netid )
#     backend = get_backends()[0]
#     u.backend = '{module}.{classname}'.format( module=backend.__module__, classname=backend.__class__.__name__ )
#     login( request, u )  #Brute force login, see - http://djangosnippets.org/snippets/1552/
#     log.debug( 'login complete' )
#     return u

# def set_basics( host, request_dct ):
#     """ Grabs username and netid.
#         Called by manage_usr_obj() """
#     if host == '127.0.0.1':
#         username = settings_app.TEST_USERNAME
#         netid = settings_app.TEST_NETID
#     else:
#         username = request_dct.get('Shibboleth-eppn', None)
#         netid = request_dct.get('Shibboleth-brownNetId', None)
#     log.debug( 'username, `{usr}`; netid, `{net}`'.format( usr=username, net=netid ) )
#     return ( username, netid )

# def update_userobj( username, netid ):
#     """ Grabs user object, updates and saves it.
#         Called by manage_usr_obj() """
#     u, created = User.objects.get_or_create( username=username.replace('@brown.edu', '').strip() )
#     if netid in settings_app.SUPER_USERS: u.is_superuser = True
#     if netid in settings_app.STAFF_USERS: u.is_staff = True
#     if created:
#         u.first_name = data.get('Shibboleth-givenName', '')
#         u.last_name = data.get('Shibboleth-sn', '')
#         u.email = data.get('Shibboleth-mail', None)
#         u.set_unusable_password()
#     u.save()
#     log.debug( 'user updated and saved.' )
#     return u



######################################



# def pull_shib_info( request, data ):
#     """ Pull information for the Shib request and get/create and login Django User object.
#         Called by bul_login() """
#     log.debug( 'starting pull_shib_info()' )
#     log.debug( 'request.get_host(), ```{}```'.format( request.get_host() ) )
#     try:
#         if request.get_host() == '127.0.0.1':
#             testing = True
#             u = User.objects.get(username=settings_app.TEST_USER)
#             backend = get_backends()[0]
#             # u.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
#             u.backend = '{module}.{classname}'.format( module=backend.__module__, classname=backend.__class__.__name__ )
#             login(request, u)
#             return u
#         else:
#             pass
#     except ImportError:
#         pass
#     log.debug( 'no test-user situation; data, ```{}```'.format(pprint.pformat(data)) )
#     username = data.get('Shibboleth-eppn', None)
#     netid = data.get('Shibboleth-brownNetId', None)
#     log.debug( 'username, `{usr}`; netid, `{net}`'.format( usr=username, net=netid ) )
#     if not username or not netid:
#         return
#     else:
#         username = username.replace('@brown.edu', '').strip()
#         u, created = User.objects.get_or_create( username=username )
#         log.debug( 'u, ```{}```'.format(u) )
#         log.debug( 'created, ```{}```'.format(created) )
#         if netid in settings_app.SUPER_USERS:
#             u.is_superuser = True
#             log.debug( 'set is_superuser to True' )
#         if netid in settings_app.STAFF_USERS:
#             u.is_staff = True
#             log.debug( 'set is_staff to True' )
#         if created:
#             u.first_name = data.get('Shibboleth-givenName', '')
#             u.last_name = data.get('Shibboleth-sn', '')
#             u.email = data.get('Shibboleth-mail', None)
#             u.set_unusable_password()
#             log.debug( 'set user-attributes for newly created user' )
#         log.debug( 'so far so good' )
#         u.save()
#         #Brute force login, see - http://djangosnippets.org/snippets/1552/
#         backend = get_backends()[0]
#         u.backend = '{module}.{classname}'.format( module=backend.__module__, classname=backend.__class__.__name__ )
#         login( request, u )
#         log.debug( 'login complete' )
#         return u
