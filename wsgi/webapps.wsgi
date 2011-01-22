# /opt/app/django/apps/apache/django.wsgi
# python configuration file for mod_wsgi

import os
import sys

sys.path.append('/opt/webapps')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

