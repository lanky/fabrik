#!/usr/bin/env python
# A simple python script to setup environment for testing django/fabrik elements in iPython
# or the standard python shell
#
# usage: [i]python djangosession.py

import os
import sys
# where our django content is...
sys.path.append('/opt/webapps')
# export $DJANGO_SETTINGS_MODULE='settings' 
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
