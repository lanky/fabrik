#!/usr/bin/env python
# top-level module docs:
"""
apps.fabrik.utils
a small python module to provide helper functions for the Fabrik
web interface, mostly using the cobbler XMLRPC or local API functionality
"""

## ------------ module imports ------------------ ##
import os
import re
from operator import itemgetter
import socket

# dealing with config file management:
from ConfigParser import SafeConfigParser

# generic cobbler local API - used for ISO generation
from cobbler import api as capi

# the cobbler XMLRPC API abstraction ($APPDIR/cobblerweb.py)
from fabrik.cobblerweb import CobblerWebApi
from fabrik.config import *

# global api handle, as we use it a lot :)
# Actually to handle auth, I'll probably end up passing a handle as an
# argument to these methods in the end.
global apihandle
apihandle = CobblerWebApi()

# ------- AJAXy functions used by views -------- #
# these are associated with URLS, called by javascript.
def resolve_host(hostname):
    """
    Looks up IP for given hostname
    """
    try:
        ip_address = socket.gethostbyname(hostname)
    except:
        ip_address = 'Not Found'
    #return { 'hostname' : hostname, 'ip_address' : ip_address }
    return ip_address

def getlayout(layoutname, topdir='/var/lib/cobbler/snippets/disklayouts'):
    """
    fetch content of a disk layout file
    """
    abpath = os.path.join(topdir, layoutname)
    try:
        lines = open(abpath).read()
    except:
        lines = 'unable to read layout file (or file is empty)'
    return lines
    
def savelayout(layoutinfo, path = '/var/lib/cobbler/snippets/disklayouts/custom'):
    """
    Attempt to save the disklayout to the specified filename.
    returns True if successful, an error string otherwise.
    """
    absname = os.path.join(path, layoutinfo['name'])
    if os.path.isfile(absname):
        return 'A disklayout file with that name already exists'
    # well, if we got this far, attempt to open the file
    try:
        outfile = open(absname, 'wb')
    except:
        return 'Could not open file %s for writing. Permissions issue?' % absname

    try:
        outfile.write(layoutinfo['layout'])
        outfile.write('# custom disk layout end\n')
        outfile.close()
        return True
    except:
        return 'unable to write to file'

def allsystems():
    """
    return basic information for all systems.
    Or we could just dump everything as json?
    """
    return apihandle.session.get_systems(apihandle.tok)

## ------------ helper functions ---------------- ##
# commented out until cobbler upstream accepts the patches
# def geniso(isoname, systemlist, isodir, menutemplate='/etc/cobbler/isolinux.cfg.template'):

def geniso(isoname, systemlist, isodir, profilelist = None):
    """
    Create an ISO image for a given cobbler system record.
    isodir must be writeable for the user apache.
    """
    tmpdir = isodir
    if not os.path.isdir(tmpdir):
        os.mkdir(tmpdir)
    handle = capi.BootAPI()
    if not isoname.endswith('.iso'):
        isoname = isoname + '.iso'
    isopath = os.path.join(isodir, isoname)
    # if handle.build_iso(isopath, systems=systemlist, profiles='', tempdir=isodir, menutemplate='/etc/cobbler/isolinux.cfg.template'):
    # now we try and build the ISO image    
    if handle.build_iso(isopath, systems=systemlist, profiles=profilelist, tempdir=isodir):
        return isopath
    else:
        return 'Creating ISO image %s in dir %s failed. Please check access permissions and disk space' %(isoname, isodir)

def geniso_XMLRPC(isoname, systemlist, isodir):
    """
    create an ISO image using the Cobbler XMLRPC API.
    Need to check when it is complete... check how the cobbler web interface does this!
    currently doesn't work, as I haven't written it yet.
    """
    pass

def getClasses(datafile, pattern):
    """
    fetch a list of tuples [(name, description), (name, description),...]
    from a local configuration file.
    If we wish to divorce fabrik from running locally on the puppet server,
    then 'datafile' needs to be created on the fabrik server.
    expects a line representing each class in this format:
    #@ name : description
    the @ is important :)

    params:
    datafile - local file path (to nodes.pp)
    pattern  - a compiled re pattern object. Should return 2 groups.
    """
    output = []
    for line in open(datafile).readlines():
        if pattern.match(line):
            n, d = pattern.match(line).groups()
            output.append( (n.strip(), d.strip()) )
    return output

def getConfigItem(configfile, section, varname):
    """
    Fetch items from an INI-style config file:
    [SECTION]
    varname = value

    If a section does not exist, return the value from the 'DEFAULT' section
    params:
    configfile: absolute path to the configuration file to read
    section:    which [section] to look in for data
    varname:    the variable we are seeking (returned as a string)
    pairs (bool): whether to return (section, value) pairs or just values
    """
    parser = SafeConfigParser()
    parser.read(configfile)
    try:
        return parser.get( section, varname)
    except:
        # if anything fails nastily, return the 'None' string
        return 'None'

def getConfigItems(configfile, varname):
    """
    Fetch items from an INI-style config file:
    [SECTION]
    varname = value

    Returns a list of (section, value) pairs - useful for generating lists of
    items for drop-down or bullet lists.
    If a varname is not available in the section, return nothing for that entry.

    configfile: absolute path to the configuration file to read
    section:    which [section] to look in for data
    varname:    the variable we are seeking (returned as a string)
    pairs (bool): whether to return (section, value) pairs or just values
    """
    parser = SafeConfigParser()
    parser.read(configfile)
    output = []
    for section in parser.sections():
        val = parser.get(section, varname)
        if str(val) != 'None':
            output.append((section, val))
    
    # return the list sorted by field 2 (comment/description)
    return sorted( output, key=itemgetter(1))

def createSystemTemplate(inputdict):
    """
    Run through the data provided by our AddSystemForm and convert it into an appropriate structure
    for the XMLRPC API functions for modifying systems.
    This has been removed from the views module to avoid having far too much code in one method.
    """
    system_template = {}

    # processing all fields individually as a test:
    # there is probably a more efficient means of doing this.
    for k in ['name', 'profile', 'gateway', 'name_servers']:
        system_template[k] = inputdict[k]

    system_template['mgmt_classes'] = inputdict.get('mgmt_classes','')

    system_template['comment'] = inputdict['name']
    system_template['hostname'] = '.'.join([ inputdict['name'], inputdict['domain'] ])

    # parse the ksmeta options:
    # ksmeta starts as an empty list, to which we can append key=val pairs
    # items must be of the form 'key=val' or 'key'
    # with NO space around the = sign (if there is one)
    # spaces lead to Very Bad Things.
    # custom ksmeta keys:
    # customrepo, buildregion, disksnippet, cleardisks, customsnippets
    # custompkgs

    ksmeta = []


    if inputdict.get('togglelayout', False):
        if inputdict.get('customlayout', None) is not None:
            ksmeta.append("customlayout='%s'" % '|'.join([ x.strip() for x in inputdict['customlayout'].split('\n')] ) )

    # process the true/false checkboxes in a loop, for brevity:
    # weirdly, if the box is checked, the value should be 'no'
    for yesnokey in [ 'skip_network', 'skip_post', 'cleardisks']:
        if not inputdict.get(yesnokey, False):
            ksmeta.append('%s=no' % yesnokey )

    # Then the Value/None options...
    # if we specified one, add it to ksmeta
    for nonekey in [ 'customrepo', 'disksnippet', 'buildclass']:
        if inputdict.get(nonekey, False):
            ksmeta.append('%s=%s' %(nonekey, inputdict[nonekey]))

    for listkey in ['customsnippets', 'custompkgs' ]:
        if inputdict.get(listkey, False):
            ksmeta.append('%s=%s' %(listkey, inputdict[listkey]))



    # unfortunately (despite storing the info internally as a dict)
    # cobbler wants it passed as a space-separated string of key=value pairs
    system_template['ks_meta'] = ' '.join(ksmeta)

    # interface info is mandatory!
    # primary interface is now a configuration option in apps.fabrik.config
    # PRIMARY_IF. Default on deployment is 'eth0'
    #  we now prompt for this in the add system interface.
    system_template['interfaces'] = { inputdict.get('primary_if', PRIMARY_IF) : {
        'dns_name' : system_template['hostname'],
        'ip_address' : inputdict['ip_address'],
        'subnet' : inputdict['subnet'],
        'static' : True,
    #    'mac_address' : inputdict['mac_address'],
        }
    }
    # We may not have a backup IP:
    # add it if it is there
    # This is now a configuration option in apps.fabrik.config:
    # BACKUP_IF. Default on deployment is 'eth3'
    if inputdict.get('backup_ip', '') != '':
         dc_routes = getConfigItem(DC_INFO, inputdict['datacenter'],'static_routes')
         if dc_routes != 'None':
            staticroutes = dc_routes.split()
         else:
            staticroutes = []

         system_template['interfaces'][BACKUP_IF] = {
         'ip_address' : inputdict['backup_ip'],
         'subnet' : inputdict['backup_mask'],
         'staticroutes' : staticroutes,
         'static' : True,
         }
    return system_template

def getSystemTable():
    """
    Use the Cobbler XMLRPC API to fetch a list of system summaries for all systems
    """
    obj = CobblerWebApi()
    output = []
    for sysname in obj.getSystemNames():
        output.append(obj.systemSummary(sysname))
    return output

def getDiskLayouts(path='/var/lib/cobbler/snippets/disklayouts'):
    """
    fetch a list of available disk layouts from 'path'
    This assumes that only valide disk layout files are in there.
    Either that or we'll have to enforce a file extension like .disks
    """
    # the (path, name) tuples
    output = []
    # a { filename : content } dictionary
    contents = {}
    allfiles = [ x for x in os.listdir(path) if os.path.isfile(os.path.join(path,x))]
    for fname in allfiles:
        absfile = os.path.join(path,fname)
        output.append((fname, fname))
        try:
            contents[fname] = open(absfile).read()
        except:
            contents[fname] = 'Could not read file. Permissions Issue?'
    return sorted(output, key=itemgetter(0)), contents

