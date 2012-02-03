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

__doc__ = """
This is the top-level configuration for Fabrik.
The variables set in here determine how data is collected and provide defaults for some of the fields.
"""

__author__ = "Stuart Sears <stuart@sjsears.com>"
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
DEFAULT_GW  = '192.168.1.1'
DEFAULT_DOMAIN = 'domain.tld'
DEFAULT_DNS = '192.168.1.1'

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

