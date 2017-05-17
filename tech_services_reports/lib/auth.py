# -*- coding: utf-8 -*-

import logging, pprint
from tech_services_reports import settings_app


log = logging.getLogger("webapp")


def bul_login(func):
    """ Decorator to create a user object for the Shib user and/or log the user in to Django.
        Utility code function knows how to assign proper Django User object status. """
    log.debug( 'starting bul_login() decorator' )
    def decorator(request, *args, **kwargs):
        import copy
        # from tech_services_reports.utility_code import pull_shib_info
        from django.contrib.auth import authenticate, login
        #Call Birkin's auth function
        shib_dict = auth(request, data_only=True)
        #data = simplejson.dumps( new_dict, sort_keys=True, indent=2 )
        # user_obj = utility_code.pull_shib_info(request, shib_dict)
        user_obj = pull_shib_info(request, shib_dict)
        if not user_obj:
            return HttpResponseForbidden('403 / Forbidden')
        #else:
            #user = authenticate(username=user_obj.username)
        #login(request, user)
        return func(request, *args, **kwargs)
    return decorator


def auth(request, data_only=None, SSL=None):
  log.debug( 'starting auth()' )
  # from django.utils import simplejson
  import copy
  # get rid of mod_wsgi dictionary items not serializable
  new_dict = copy.copy(request.META)
  log.debug( 'new_dict, ```{}```'.format(pprint.pformat(new_dict)) )
  for (key, val) in request.META.items():
    if 'passenger' in key:
        new_dict.pop( key )
    elif 'wsgi.' in key:
        new_dict.pop( key )
  # new_dict.pop('wsgi.errors')
  # new_dict.pop('wsgi.file_wrapper')
  # new_dict.pop('wsgi.input')
  if data_only:
      return new_dict
  # data = simplejson.dumps( new_dict, sort_keys=True, indent=2 )
  data = json.dumps( new_dict, sort_keys=True, indent=2 )
  return HttpResponse(data, mimetype='text/javascript' )


def pull_shib_info(request, data):
    """Pull information for the Shib request and get/create and login
    Django User object."""
    log.debug( 'starting pull_shib_info()' )
    from django.contrib.auth.models import User
    from django.contrib.auth import login, get_backends
    # import settings_app

    log.debug( 'request.get_host(), ```{}```'.format( request.get_host() ) )
    try:
        if request.get_host() == '127.0.0.1':
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

    # try:
    #     from settings_app import ENV
    #     if ENV == 'testing':
    #         testing = True
    #         u = User.objects.get(username=settings_app.TEST_USER)
    #         backend = get_backends()[0]
    #         u.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
    #         login(request, u)
    #         return u
    #     else:
    #         pass
    # except ImportError:
    #     pass
    log.debug( 'no test-user situation; data, ```{}```'.format(pprint.pformat(data)) )
    username = data.get('Shibboleth-eppn', None)
    netid = data.get('Shibboleth-brownNetId', None)
    log.debug( 'username, `{usr}`; netid, `{net}`'.format( usr=username, net=netid ) )
    #Quite now because user is not authenticated for some reason.
    if not username or not netid:
        return
    else:
        #strip @brown.edu from username.
        username = username.replace('@brown.edu', '').strip()
        u, created = User.objects.get_or_create(username=username)
        log.debug( 'u, ```{}```'.format(u) )
        log.debug( 'created, ```{}```'.format(created) )
        #Fill in user details after first login.
        #if created:
        u.first_name = data.get('Shibboleth-givenName', '')
        u.last_name = data.get('Shibboleth-sn', '')
        u.email = data.get('Shibboleth-mail', None)
        #Each login check super or staff status to allow for changes
        #to the setting fail.
        log.debug( 'so far so good' )
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
