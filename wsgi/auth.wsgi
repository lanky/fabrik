# !/usr/bin/env python
# /opt/app/django/apps/apache/django.wsgi
# Authentication for mod_wsgi - attempt to login to cobbler over xmlrpc

import os
import sys

sys.path.append('/opt/webapps')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


from fabrik.cobblerweb import CobblerWebApi
from fabrik.config import COBBLER_SERVER

def check_password(environ, user, password, *args, **kwargs):
    """
    We'll probably never use the addition arguments, but...
    Attempts to authenticate using the cobbler web Api
    """
    try:
        remote = CobblerWebApi(server = COBBLER_SERVER, username = user, password = password)
    except:
        remote = None

    if remote is not None:
        return True
    else:
        return False

# vim :setf python
