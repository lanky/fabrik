#!/usr/bin/env python
"""
views.std
This file contains methods used to generate and render templated pages upon request
The AJAX bits are in views.ajax
"""

## ----- imports from the local python distribution --- ##
# generic python imports
import os

# used for dumping errors if things go horribly wrong.
# also used for serialiaztion of objects
import simplejson
from fnmatch import fnmatch
from operator import itemgetter

## -------- imported Django modules and methods ---------- ##
from django.http import HttpResponse
from django.shortcuts import render_to_response


# bring in our custom forms
from fabrik.forms import *

# local 'utility; functions
from fabrik.utils import *

# configuration fils for common vars:
from fabrik.config import *

# separate webapi class in ${APPDIR}/cobblerweb.py
from fabrik.cobblerweb import CobblerWebApi

# cobbler utils for passthru auth etc
import cobbler.utils as cobblerutils
import fabrik.views.auth as auth

# for get_user_pass
import base64

# this should be on a per-user basis, eventually, but...
global apihandle
apihandle = CobblerWebApi()
# these two methods come directly from cobbler_web
# will need munging a little

## ------------------- URL producing methods follow ------------------------ ##
## - Ajaxy callback functions - ##
# All AJAX URL-producing methods have been moved into views/ajax.py
def get_user_pass(request):
    """
    suck username and password out of the HTTP_AUTHORIZATION header
    """
    authstr = request.META.get('HTTP_AUTHORIZATION', None)
    if authstr is not None:
        dummy, data = authstr.split()
        username, password = base64.decodestring(data).split(':')
    else:
        username, password = 'None', 'None'
    return username, password

## ----------------------  Add a new System  ------------------------------- ##
def add_system(request):
    """
    Creates an instance of AddSystemForm, which is used by admins to add new
    system records to the cobbler instance, using the cobbler XMLRPC API.

    Creates a dict suitable to use with the system management API, based upon the
    data entered into the form.

    Some data is generated on the fly as the form instance is created.
    """
#    auth.check_auth(request)
    if request.method == 'POST':
        form = AddSystemForm(request.POST)
        if form.is_valid():
            obj = CobblerWebApi()
           
            # use the createSystemTemplate method from utils
            # to construct the system template in an appropriate way:
            # some elements are 'nested' (e.g. interface information)
            # and we need to parse them.
            # Also processes the custom ksmeta keys
            systempl = createSystemTemplate(form.cleaned_data)
            
            # the cobblerweb API call to add a new system returns True if successful 
            if obj.newSystem(systempl) == True:
                obj.sync()
                
                # if we asked for an ISO image, generate one...
                # this uses geniso from utils - the XMLRPC version is not all that reliable
                if form.cleaned_data['gen_iso'] == True:
                    
                    form.cleaned_data['iso_info'] = geniso(isoname=systempl['name'], 
                        systemlist=systempl['name'], isodir='/var/www/html/pub/')
                    
                    form.cleaned_data['iso_name'] = systempl['name'] + ".iso"

                # if successful, render the system data into a summary form to confirm:
                return render_to_response('system_summary.tmpl', { 'form' : form.cleaned_data,
                                                                  'cobbler_server' : COBBLER_SERVER,
                                                                  'iso_root' : ISOROOT })
        else:
            # return render_to_response('system_add.tmpl', { 'form' : form})
            return render_to_response('system_add.tmpl', { 'form' : form})
    
    else:
        form = AddSystemForm()

        # return render_to_response('system_add.tmpl', { 'form' : form })
        
        username, password = get_user_pass(request)
        if username is not None:
            return render_to_response('system_add.tmpl', { 'form' : form, 'remoteuser' : username })
        else:
            return render_to_response('system_add.tmpl', { 'form' : form })

## ------------------------- ISO Building Form ----------------------------- ##
def build_iso(request):
    """
    A page for building an installation/boot ISO for a given system
    consists of a single drop-down list to select a system name.

    Uses the BuildISOForm class from forms.py
    """
    if request.method == 'POST':
        
        form = BuildISOForm(request.POST)
        if form.is_valid():
            # only one system can be submitted, so...
            isosystem = form.cleaned_data['systems']

            mysystems = ','.join(form.cleaned_data.get('systems', ''))
            proflist = ','.join(form.cleaned_data.get('profiles', ''))
            # iso filename is <system>.iso
            isofile = form.cleaned_data.get('ISOname', 'cobbler-generated-iso')
            if not isofile.endswith('.iso'):
                isofile += '.iso'
            # remove the existing file, if it's there!
            if os.path.exists('ISODIR/%s' % isofile):
                os.unlink('ISODIR/%s' % isofile)
            iso_path = geniso( isoname = isofile, systemlist = mysystems, isodir = ISODIR, profilelist = proflist)
            return render_to_response('iso_summary.tmpl', {'systems' : mysystems,
                                                           'profiles': proflist,
                                                          'iso_name' : isofile,
                                                          'iso_root' : ISOROOT,
                                                          'cobbler_server' : COBBLER_SERVER } )
        else:
            return HttpResponse('form fails validation. Aargh.')
    else:
        form = BuildISOForm()
        username, password = get_user_pass(request)
        if username is not None:
            return render_to_response('iso_create.tmpl', { 'form' : form , 'remoteuser' : username } )
        else:
            return render_to_response('iso_create.tmpl', { 'form' : form } )


## --------------------- Delete An Existing System ------------------------- ##
def delete_system(request):
    """
    displays DeleteSystemForm and a confirm dialog where necessary
    """
    if request.POST:
        form = DeleteSystemForm(request.POST)

        if form.is_valid():
            # let's attempt to fetch the system profile information from cobbler:
            try:
                for key, val in apihandle.systemSummary(form.cleaned_data['systemname']).iteritems():
                    form.cleaned_data[key] = val
            except:
                pass
            # is this the second run through?
            if request.POST.has_key('confirmed') and request.POST['confirmed'] == '1':
                if obj.deleteSystem(form.cleaned_data['systemname']):
                    form.cleaned_data['message'] = 'System Deleted'
                else:
                    form.cleaned_data['message'] = 'Failed to delete system'
                return render_to_response('delete_summary.tmpl', { 'form' : form.cleaned_data })
            else:
                # so, it's valid. And we've already made a run through.
                # Get system details from the cobbler web API
                # for key, val in obj.systemSummary(form.cleaned_data['systemname']).iteritems():
                #    form.cleaned_data[key] = val
                return render_to_response('delete_confirm.tmpl', {'form' : form.cleaned_data, 'confirmed' : '1' } )
    else:
        form = DeleteSystemForm()
        return render_to_response('system_delete.tmpl', { 'form' : form } )

## -------------------------- List System Records -------------------------- ##
def system_table(request):
    """
    Placeholder for system list functionality.
    Display an HTML table of the existing systems in cobbler, with the following details:
    Name | IP Addresses | Profile | nisdomain | Datacenter
    """
    username, password = get_user_pass(request)
    if username is not None:
        return render_to_response('system_list.tmpl', {  'data' : getSystemTable(),
                                                        'cobbler_server' : COBBLER_SERVER,
                                                        'remoteuser' : username })
    else:                                                        
        return render_to_response('system_list.tmpl', { 'data' : getSystemTable(),
                                                    'cobbler_server' : COBBLER_SERVER,
                                                    'remoteuser' : 'unknown'})

def auto_test(request):
    form = AutocompleteForm()
    return render_to_response('system_test.tmpl', { 'form' : form } )


