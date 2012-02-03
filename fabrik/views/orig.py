#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Fabrik - a custom django/javascript frontend to cobbler
#
# Copyright 2009-2012 Stuart Sears
#
# This file is part of fabrik
#
# fabrik is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# fabrik is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with fabrik. If not, see http://www.gnu.org/licenses/.
# top-level docstrings
# standard module documentation:
"""
views.py
This file contains methods used to generate and render templated pages upon request
Forms are defined in forms.py
the URL -> method mappings are in urls.py
Other local modules arwe
"""

## ----- imports from the local python distribution --- ##
# generic python imports
import os

# used for dumping errors if things go horribly wrong.
# also used for serialiaztion of objects
try:
    import json
except ImportError:
    import simplejson as json

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

global apihandle
apihandle = CobblerWebApi()
# these two methods come directly from cobbler_web
# will need munging a little
def authenhandler(req):
    """
    Mod python security handler.   Logs into XMLRPC and saves the token
    for later use.
    """

    global remote
    global token
    global username
    global url_cobbler_api

    password = req.get_basic_auth_pw()
    username = req.user     
    try:
        # Load server ip and port from local config
        if url_cobbler_api is None:
            url_cobbler_api = utils.local_get_cobbler_api_url()

        remote = xmlrpclib.Server(url_cobbler_api, allow_none=True)
        token = remote.login(username, password)
        remote.update(token)
        return apache.OK
    except:
        return apache.HTTP_UNAUTHORIZED

#==================================================================================

def check_auth(request):
    """
    A method to enable authentication by authn_passthru.  Checks the
    proper headers and ensures that the environment is setup.
    """
    global remote
    global token
    global username
    global url_cobbler_api

    if url_cobbler_api is None:
        url_cobbler_api = cobblerutils.local_get_cobbler_api_url()

    remote = xmlrpclib.Server(url_cobbler_api, allow_none=True)

    if token is not None:
        try:
            token_user = remote.get_user_from_token(token)
        except:
            token_user = None
    else:
        token_user = None

    if request.META.has_key('REMOTE_USER'):
        if token_user == request.META['REMOTE_USER']:
            return
        username = request.META['REMOTE_USER']
        #REMOTE_USER is set, so no credentials are going to be available
        #So we get the shared secret and let authn_passthru authenticate us
        password = cobblerutils.get_shared_secret()
        # Load server ip and port from local config
        token = remote.login(username, password)
        remote.update(token)

## ------------------- URL producing methods follow ------------------------ ##
## - Ajaxy callback functions - ##

def resolve_name (request, hostname):
    """
    calls resolve_host from the utils module
    """
    results = resolve_host(hostname)
    return HttpResponse(results)

def get_layout (request, layoutname):
    """
    calls getlayout from utils to get layout file content
    """
    results = getlayout(layoutname)
    return HttpResponse(results)

# delete, rename and convert to profile....

def del_system(request, systemname):
    """
    used to delete system record via javascript callback
    """
    if apihandle.deleteSystem(systemname):
        return HttpResponse("Success", mimetype="text/javascript")
    else:
        return HttpResponse("Failure", mimetype="text/javascript")

def rename_system(request):
    """
    AJAXy callback for renaming systems
    """
    # check_auth(request)
    data = json.loads(request.raw_post_data)
    
    result = apihandle.renameSystem(data['systemname'], data['newname'])

    if result == True:
        return HttpResponse('system renamed')
    else:
        return HttpResponse('Failed to rename system')

def sys_to_profile(request):
    """
    converts a system record to a profile (deletes interfaces etc)
    Currently this essentially copies ksmeta, distro etc
    The new profile becomes a child of the original system's profile.
    Anything else becomes a complex procedure.
    This expects JSON data: { 'systemname' : name, 'profilename': name }
    """
    data = json.loads(request.raw_post_data)

    res =  apihandle.systemToProfile(data['profilename'], data['systemname'])
    if res == True:
        return HttpResponse('profile %s creted from system %s' %(data['profilename'], data['systemname']) )
    else:
        return HttpResponse(res)

    
def list_systems(request):
    """
    fetches list of systems as JSON
    """
    res = []
    syslist = apihandle.getSystemNames()

    for x in syslist:
        res.append({ 'val' : x, 'name' : x })
    data = json.dumps(res)
    return HttpResponse(data, mimetype='application/javascript')

def get_sysip(sysrecord):
    res = []
    for iface, data in sysrecord['interfaces'].iteritems():
        res.append('%s (%s)' %( data['ip_address'], iface ))
    return ','.join(res)
    

def system_array(request):
    """
    Return a slightly different format of JSON for use with DataTables
    """
    res = { "aaData" : [] }
    syslist = allsystems()
    # returning [ Name, profile, IP info, links ]
    for entry in syslist:
        ipinfo = get_sysip(entry)
        sname = entry['name']
        sprof = entry['profile']
        linkstr = ''.join([ '<span class="action" onclick="delSystem(\'%s\')" title="Delete system.">Delete</span>' % sname,
                    '<span class="action" onclick="renameSystem(\'%s\')" title="Rename system.">Rename</span>' % sname,
                    '<span class="action" onclick="makeProfile(\'%s\')" title="Create a profile based on this system">Create Profile</span>' % sname ])

        res["aaData"].append([ sname ,sprof, ipinfo, linkstr])
    return HttpResponse(json.dumps(res), mimetype="text/javascript")


def list_profiles(request):
    """
    fetches list of profiles as JSON
    """
    res = []
    proflist = apihandle.getProfileNames()

    for x in proflist:
        res.append({ 'val' : x, 'name' : x })
    data = json.dumps(res)
    return HttpResponse(data, mimetype='application/javascript')

def list_layouts(request, topdir = '/var/lib/cobbler/snippets/disklayouts'):
    """
    returns list of existing disk layouts (custom & core) as JSON
    """
    res = []
    for base, dirs, files in os.walk(topdir):
        lpath = re.sub(r'%s/?' % topdir, '', base)
        for f in files:
               res.append({'name' : f, 'val' : os.path.join(lpath, f) })
    data = json.dumps(sorted(res, key=itemgetter('name')))
    return HttpResponse(data, mimetype = 'application/javascript')

def dump_systems(request):
    results = allsystems()
    return HttpResponse(json.dumps(results), mimetype="text/javascript")

def get_system(request,systemname):
    results = apihandle.systemDetails(systemname)
    return HttpResponse(json.dumps(results), mimetype="text/javascript")

def autocomplete_systems(request):
    def iter_results(results):
        if results:
            for r in results:
                yield '%s\n' % r

    if not request.GET.get('term'):
        return HttpResponse(mimetype='text/plain')

    term = request.GET.get('term')
    syslist = [ x for x in apihandle.getSystemNames() if fnmatch(x, '*%s*' % term) ]

    return HttpResponse(json.dumps(syslist), mimetype='text/javascript')


def autocomplete_profiles(request):
    def iter_results(results):
        if results:
            for r in results:
                yield '%s\n' % r

    if not request.GET.get('term'):
        return HttpResponse(mimetype='text/plain')

    term = request.GET.get('term')
    syslist = [ x for x in apihandle.getProfileNames() if fnmatch(x, '*%s*' % term) ]

    return HttpResponse(json.dumps(syslist), mimetype='text/javascript')

def filter_systems(request, term, systemdata):
    sysdata = sorted([ apihandle.systemSummary(x) for x in apihandle.getSystemNames() if fnmatch(x, '*%s*' % term) ], key=itemgetter('name'))
    return HttpResponse(json.dumps(sysdata), mimetype="text/javascript")
    

## ---------- Save a disk layout ------------------ ##
def save_layout(request):
    """
    takes the JSON data posted from jQuery and tries to save it :)
    """
    data = json.loads(request.raw_post_data)
    result = savelayout(data)
    if result == True:
        return HttpResponse('Layout saved')
    else:
        return HttpResponse(result)

## ----------------------  Add a new System  ------------------------------- ##
def add_system(request):
    """
    Creates an instance of AddSystemForm, which is used by admins to add new
    system records to the cobbler instance, using the cobbler XMLRPC API.

    Creates a dict suitable to use with the system management API, based upon the
    data entered into the form.

    Some data is generated on the fly as the form instance is created.
    """
    if request.method == 'POST':
        form = AddSystemForm(request.POST)
        if form.is_valid():
            obj = CobblerWebApi()
           
            # use the createSystemTemplate method from utils
            # to construct the system template in an appropriate way:
            # some elements are 'nested' (e.g. interface information)

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
    return render_to_response('system_list.tmpl', { 'data' : getSystemTable(), 'cobbler_server' : COBBLER_SERVER })

def auto_test(request):
    form = AutocompleteForm()
    return render_to_response('system_test.tmpl', { 'form' : form } )


