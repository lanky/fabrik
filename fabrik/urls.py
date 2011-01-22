#!/usr/bin/env python
# top-level docstrings
"""
apps.fabrik.urls
This file provides the top-level mappings between 
URLs requested under the django-root: (in this case http://cobblerserver/apps/fabrik/<URL> )
and functions exposed in views.py
URL patterns are regular expressions
"""

from django.conf.urls.defaults import *
# separated the views into ajax and 'normal' for ease of reading.
from fabrik.views import ajax, std

# Uncomment the next two lines to enable the admin:
# This is unused in this instance - it mainly allows for
# object creation in databases. We have none.
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^apps/', include('apps.foo.urls')),
    # default index is the system list:
    (r'^$', std.system_table),
#    (r'buildiso/', std.build_iso),
    (r'add/', std.add_system),
    (r'iso/', std.build_iso),
    (r'list/', std.system_table),
# not currently used, but can be tested if you wish... 
# uncommenting the following 2 lines will enable /apps/fabrik/auto
# for an autocompleting system search. Obsoleted by  the system list page.
#    (r'ajax/systems/search', ajax.autocomplete_systems),
#    (r'auto/', ajax.auto_test),
# rearranged AJAXy URLs for clarity:
# resolve a hostname to an IP address
# e.g. http://myserver/apps/fabrik/ajax/resolve/test1.example.com
    (r'ajax/resolve/(?P<hostname>[\w.]+)$', ajax.resolve_name),
    # fetch a system record by name
    (r'ajax/systems/get/(?P<systemname>[\w\-\/.]+)$',ajax.get_system),
    # delete a system record by name    
    (r'ajax/systems/delete', ajax.del_system),
    # convert a system record to a profile    
    (r'ajax/systems/convert', ajax.sys_to_profile),
    # dump all systems as JSON. Currently unused.    
    (r'ajax/systems/all', ajax.dump_systems),
    # list all system record names    
    (r'ajax/systems/list', ajax.list_systems),
    # rename a system - requires JSON data { 'systemname' : name, 'newname': newname }    
    (r'ajax/systems/rename', ajax.rename_system),
    # fetch ksmeta for a given profile and return disksnippet or customlayout if set
    (r'ajax/profiles/layout/(?P<profilename>[\w\-\/.]+)$', ajax.get_profile_layout),
    # list profile names (used to populate select boxes)    
    (r'ajax/profiles/list', ajax.list_profiles),
    # Disklayout management
    # get the content of an existing layout file (searches /var/lib/cobbler/snippets/disklayouts + layout name)
    (r'ajax/layouts/get/(?P<layoutname>[\w\-\/.]+)$',ajax.get_layout),
    # return a list of existing layout file (searches /var/lib/cobbler/snippets/disklayouts, plus subdirectories)
    (r'ajax/layouts/list', ajax.list_layouts),
    # saves a layout specified in the 'Disklayout' box,
    # to /var/lib/cobbler/snippets/disklayouts/custom.
    (r'ajax/layouts/save', ajax.save_layout),
)
