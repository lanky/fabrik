#!/usr/bin/env python
# Docstring
"""
cobblerweb.py
An abstraction of some key features of the XMLRPC API for cobbler.
This is used to populate forms, add new systems and gather information
from cobbler.
"""

# used to connect to cobbler's XMLRPC API
import xmlrpclib
# generic functionality
import sys
import os
# used to dump records in the event of disaster
import simplejson
# used to sort lists of lists/dicts by arbitrary keys
from operator import itemgetter

# source our local configuration file
from fabrik.config import *

class CobblerWebApi:

    def __init__(self, server = COBBLER_SERVER, username = COBBLERUSER, password = COBBLERPASS):
        """
        Constructor: initialises an authenticated XMLRPC session.
        COBBLER_SERVER, COBBLERUSER and COBBLERPASS are set in config.py
        """
        self.session = xmlrpclib.ServerProxy('http://%s/cobbler_api' % server)
        self.tok = self.session.login(username, password)
        self.user = username

    # ------------------------- Generic functionality ---------------------------- #
    def sync(self):
        """
        Run cobbler sync to generate PXE menus etc
        """
        options = {'verbose' : False}
        return self.session.background_sync(options, self.tok)

    def getAllocatedIPs(self):
        """
        Extract the IP addresses allocated to each system and return them
        as a list.
        """
        ipdata = []
        sysdata = [ x['interfaces'] for x in self.session.get_systems() ]
        for ifentry in sysdata:
            for ifname in ifentry:
                 ipdata.append(ifentry[ifname]['ip_address'])
        return ipdata

    def checkIP(self, ipaddr):
        """
        Checks if the supplied IP address is already assigned to a system profile
        """
        sysdata = [ (x['name'], x['interfaces']) for x in self.session.get_systems() ]
        for name, ifdata in sysdata:
            for ifname in ifdata.keys():
                if ifdata[ifname]['ip_address'] == ipaddr:
                    return 'ip address %s already in use by system %s' % (ipaddr, name)
        return 'ok'

    # -------------------------   Profile Management  ---------------------------- #

    def listProfiles(self, max_length=50):
        """
        Return a list of existing profiles as (name, comment) tuples.
        The list is sorted on the 'comment' field
        """
        return sorted([ (x['name'], x['name']) for x in self.session.get_profiles()])

    def getProfileNames(self):
        """
        Return an alphabetically sorted list of profile names:
        """
        return sorted([ x['name'] for x in self.session.get_profiles() ])

    def getProfile(self, profilename):
        """
        A wrapper around get_profile
        """
        return self.session.get_profile(profilename)

    def newProfile(self, profilename, details, parent=None):
        """
        create a new profile from the given dictionary
        As it happens, we're going to only create subprofiles this way,
        or there'll be interesting issues.
        """
        if parent is not None:
            profid = self.session.new_subprofile(self.tok)
            self.session.modify_profile(profid, 'parent', parent, self.tok)
        else:
            # this is more complicated.
            # this is going to require a kickstart/distro
            profid = self.session.new_profile(self.tok)

        # assume we've provided everything we require in the details dict:
        # walk through the dict, setting properties
        errordict = {}
        for key, val in details.iteritems():
            try:
                self.session.modify_profile(profid, key, val, self.tok)
            except Exception, E:
                errordict[key] = { 'key' : key, 'val' : val, 'Error' : Exception, 'ErrorDetails' : E }

        if self.session.save_profile(profid, self.tok):
            return True, errordict
        else:
            return False, errordict


    # -------------------------   System  Management  ---------------------------- #

    def getSystemNames(self):
        """
        Return an alphabetically sorted list of system names:
        """
        return sorted([ x['name'] for x in self.session.get_systems() ])

    def sysFromIP(self, ipaddr):
        """
        Returns the system name using the given IP, or 'None'
        """
        sysdata = [ (x['name'], x['interfaces']) for x in self.session.get_systems() ]
        for name, ifdata in sysdata:
            for ifname in ifdata.keys():
                if ifdata[ifname]['ip_address'] == ipaddr:
                    return name
        return None

    def checkSystem(self, name):
        """
        checks if a system object already exists with the supplied name
        returns True if it does, False if not
        """
        if self.session.get_system(name) != '~':
            return 'name %s already in use' % name
        else:
            return 'ok'

    def newSystem(self, sysinfo, verbose=False):
        """
        Add a new system to cobbler using the provided template (hash == dict)
        hash should have a key called 'interfaces' : { 'etho' : {details}}
        required information: Ip address, netmask, MAC address

        This can be generated using utils.createSystemTemplate on submitted
        form data.

        example:

        sysinfo = {'comment': 'My shiny new system',
        'gateway': '28.97.72.1',
        'hostname': 'lonrs06004.fm.rbsgrp.net',
        'mgmt_classes': ['puppet::client'],
        'name': 'lonrs06002',
        'name_servers': ['147.114.195.220', '147.114.10.40', '11.160.32.59'],
        'profile': 'rhel54-core',
        'interfaces': {
                       'eth0': {
                                'dns_name': 'lonrs06002.fm.rbsgrp.net',
                                'ip_address': '28.97.72.33',
                                'mac_address': '01:02:03:04:05:06',
                                'static': True,
                                'subnet': '255.255.254.0',
                                },
                       },
                       'eth3': {
                                'ip_address': '28.97.72.34',
                                'subnet': '255.255.254.0',
                       }
        }
        """
        # get a new system handle:
        sysid = self.session.new_system(self.tok)

        # to allow appending to ks_meta, start with an empty list
        # and append as appropriate below
        # ksmeta = []

        # walk through all top-level parameters, setting them appropriately.
        for key, val in sysinfo.iteritems():
            if verbose:
                sys.stderr.write(simplejson.dumps({key : val}))
            # deal with the special cases first:
            # interfaces are dicts of dicts, keyed by interface name
            if key == 'interfaces':
                for iface in sysinfo[key].keys():
                    for param, value in sysinfo[key][iface].iteritems():
                        self.session.modify_system(sysid, 'modify_interface',
                        {
                        "%s-%s" %(param, iface) : value,
                        }, self.tok )
            else:
                self.session.modify_system(sysid, key, val, self.tok)
        # and finally, save it!
        if self.session.save_system(sysid, self.tok):
            return True
        # and if that doesn't work....
        return False

    def systemToProfile(self, profilename, systemname, verbose=False):
        """
        creates a new profile from a system record, as a child of the original system's profile.
        (essentially copying ksmeta and profile name)
        """
        if profilename in self.getProfileNames():
            return "Profile %s already exists. Please use the main cobbler interface to edit it or choose a different name" % profilename
        profid = self.session.new_subprofile(self.tok)
        sysinfo = self.session.get_system(systemname)
        # modify_profile(ID, key, value, tok)
        self.session.modify_profile(profid, 'name', profilename, self.tok)
        self.session.modify_profile(profid, 'parent', sysinfo['profile'], self.tok)
        # other common fields that we may need to copy, if amended
        # why not just loop over them all - if 'inherited', ignore them
        for key in [ 'ks_meta', 'kernel_options', 'kernel_options_post',
                     'name_servers', 'name_servers_search', 'redhat_management_key',
                     'redhat_management_server', 'repos mgmt_classes' ]:
            if sysinfo.has_key(key) and sysinfo[key] != '<<inherit>>':
                if verbose:
                    print "cloning parameter %s into %s"  %(key, profilename)
                self.session.modify_profile(profid, key, sysinfo[key], self.tok)

        if self.session.save_profile(profid, self.tok):
            return True
        else:
            return False

    def deleteSystem(self, sysname):
        """
        Deletes a systenm record by name
        """
        return self.session.remove_system(sysname, self.tok)
    
    def genSystemISO(self, isoname, syslist):
        """
        Generate an ISO image in the desired directory, only for the given System image.
        This will generate an ISO on the cobbler server.
        Ideally we want to return a redirect, so we'll assume that this is available
        on the cobbler server at /iso...
        """
        # not needed yet...
        # isoname = '%s.iso' % sysname
        options = { 'iso' : '%s/%s.iso' % (ISODIR, isoname),
                    'systems' : syslist,
                    'profiles' : '',
                  }
        return self.session.background_buildiso(options, self.tok)


    def systemSummary(self, systemname):
        """
        Return a simplified dict containing the following info (for reporting and deleting)
        This is a hack, but should work okay...
        name. 
        IP address
        profile + profile description
        datacenter
        nis domain
        """
        # get the cobbler records for the given system.
        sysinfo = self.session.get_system(systemname)
        profiledata = self.session.get_profile(sysinfo['profile'])
        output = {'name' : systemname}
        # Profile info in the web form is based on the 'comment' field
        output['profiledesc'] = profiledata.get('comment', 'No description available')
        output['profile'] = sysinfo.get('profile', 'None')
        output['distro'] = profiledata.get('distro', '')
        if output.get('distro') == '<<inherit>>':
            output['distro'] = '(as parent)'
        # add an IP/subnet pair for every configured interface
        # used by the list output:
        nicinfo = []
        for iface, ifaceinfo in sysinfo['interfaces'].iteritems():
            ipaddr = ifaceinfo.get('ip_address', '').strip()
            subnet = ifaceinfo.get('subnet', '').strip()
            if len(ipaddr) != 0  and len(subnet) !=0:
                nicinfo.append({'nic' : iface, 'ipaddr' : ipaddr, 'subnet' : subnet})
        if len(nicinfo) != 0:    
            output['ipinfo'] = nicinfo
        output['kargs'] = sysinfo.get('kernel_option', '')
        # we should flatten ksmeta... but not yet
        output['ksmeta'] = sysinfo.get('ks_meta', '')
        return output

    def getSystem(self, systemname):
        """
        just a wrapper arounf the get_system call
        """
        return self.session.get_system(systemname)

    def systemDetails(self, systemname):
        """
        Return a dict of the relevant info for pre-filling the AddSystemForm fields,
        to allow for editing an existing system.
        """
        # fetch the cobbler system details:
        sysinfo = self.session.get_system(systemname)

        # initialise the output dict:
        output = {}

        # copy the relevant key, val pairs into the new dict directly:
        for k in ['gateway', 'name', 'profile']:
            output[k] = sysinfo.get(k)

        output['name_servers'] = ','.join(sysinfo.get('name_servers'))

        output['reuse_name'] = True

        # ip address information:
        # eth0 should exist, as it's our primary interface
        # PRIMARY_IF is set in apps.fabrik.config. Default on deployment is 'eth0'
        if sysinfo['interfaces'].has_key(PRIMARY_IF):
            output['ip_address'] = sysinfo['interfaces'][PRIMARY_IF]['ip_address']
            output['subnet'] = sysinfo['interfaces'][PRIMARY_IF]['subnet']
            output['domain'] = '.'.join(sysinfo['interfaces'][PRIMARY_IF].get('dns_name').split('.')[1:])
        
        # backup IP, if it is configured, goes on BACKUP_IF
        # BACKUP_IF is set in apps.fabrik.config, default on deployment is 'eth3'
        # (according to the cabling diagrams in factory)
        if sysinfo['interfaces'].has_key(BACKUP_IF):
            output['backup_ip'] = sysinfo['interfaces'][BACKUP_IF]['ip_address']
            output['backup_mask'] = sysinfo['interfaces'][BACKUP_IF]['subnet']

        # ksmeta variables:
        output['bonding'] = bool(sysinfo['ks_meta'].get('bonding', False))
        output['no_op']  = bool(sysinfo['ks_meta'].get('local_config', False))

        # nis domain and DC:
        output['nisdomain'] = sysinfo['ks_meta'].get('nisdomain', '')
        output['datacenter'] = sysinfo['ks_meta'].get('datacenter', '')

        return output

    def renameSystem(self, systemname, newname):
        """
        Rename a system :)
        """
        try: 
            sysid = self.session.get_system_handle(systemname, self.tok)
        except:
            return False
        result = self.session.rename_system(sysid, newname, self.tok)
        return result
















