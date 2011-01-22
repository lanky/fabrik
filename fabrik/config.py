#!/usr/bin/env python
"""
This is the top-level configuration for Fabrik.
The variables set in here determine how data is collected and provide defaults for some of the fields.
"""
import re

# pattern matching IPV4 IP Addresses
IPV4_RE     = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')

## ------------- Cobbler Configuration Variables --------------- ##
# settings for cobblerweb
# COBBLER_SERVER = 'your.cobbler.server'
COBBLER_SERVER = 'localhost.localdomain'
# ensure this user exists in your cobbler users.digest
# or central auth DB , whatever cobbler uses...
# COBBLERUSER = "someuser"
# COBBLERPASS = "somepass"
COBBLERUSER = "xmlrpc"
COBBLERPASS = "password"

## ------------------ Networking Variables --------------------- ##
# to allow for different cabling setups
# privde the defaults for the 'Add System' Interface
# 
PRIMARY_IF  = 'eth0'
BACKUP_IF   = 'eth1'
DEFAULT_MASK = '255.255.255.0'
DEFAULT_GW  = '169.82.114.1'
DEFAULT_DOMAIN = 'domain.tld'
DEFAULT_DNS = '169.82.112.62'

## ------------------ ISO Generation Variables ----------------- ##
# destdir for ISO images
# Thid directory *must* be writeable for cobbler and apache.
# don't forget SELinux :)
ISODIR = '/var/www/html/pub'
ISOROOT = '/pub'


## ------------------ puppet-related variables ------------------ ##
# PUPPET_ROOT = '/etc/puppet/ENVS'
# placeholder for puppet environment, as we don't know which one it will be yet
# PUPPET_ENV  = '%%ENV%%'
# COBBLER_ROOT = '/etc/cobbler'

# config files used to populate system form choices
# if puppet and fabrik are "divorced", this data will need to be
# stored locally on the fabrik server and kept updated.
# NODE_INFO   = '%s/%s/manifests/nodes.pp'         % (PUPPET_ROOT,  PUPPET_ENV)
# NIS_INFO    = '%s/nisdomains.conf'   % (COBBLER_ROOT)
# DC_INFO     = '%s/datacenters.conf'  % (COBBLER_ROOT)
# pattern matching the #@ name : description tags in nodes.pp
# CLASS_RE    = re.compile(r'[# ]*@([\w\s]+):([\w\s]+)')

# These values, if given to to_python(), will trigger the self.required check.
EMPTY_VALUES = (None, '')

