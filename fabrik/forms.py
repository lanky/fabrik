#!/usr/bin/env python
"""
forms.py
Definitions of webforms using the django Forms library
Each form is a class, with its own methods and properties.

General parameters to a form field:
label      : generic label
help_text  : additional information (made available using CSS and a 'title' tag
required   : Do we need the info from this field?
choices    : a list(array) of tuples (name, description) for lists/dropdowns
initial    : default values for a field, if required.

common methods (should be commented below)

__init__(self, *args, **kwargs)
- initialisation of a class, to allow autopopulating of fields on first load.
Much of this has now been shifted to AJAX (except the system list form, which caused a lot of difficulty that way)

clean(self)
the clean() method validates the entries on a form and adds errors if required. it can conditionally delete data (e.g. disksnippet if customlayout is chosen)
returns a dict called 'cleaned_data' back to the calling 'view'

"""
# generic imports
import re
import os

# pattern matching IPV4 IP Addresses (used in add_system cleaning)
IPV4_RE     = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')


# django imports
from django import forms
from django.forms.util import ErrorList

# local python modules
from fabrik.utils import *

# simple way to do local config files:
from fabrik.config import *

# import local CobblerWebApi class.
from fabrik.cobblerweb import CobblerWebApi

# new snippets for fieldsets on forms
from fabrik.snippets.betterforms import BetterForm

class AjaxChoiceField(forms.ChoiceField):
    """
    A field that has its choices provided by AJAX, so django knows nothing of them.
    In this instance, we simply return true for validate calls.
    """
    def clean(self, value):
        return value

class AjaxMultipleChoiceField(forms.ChoiceField):
    """
    A field that has its choices provided by AJAX, so django knows nothing of them.
    In this instance, we simply return true for validate calls.
    if we don't do this, we'll never be able to validate forms containing AJAX-populated fields.
    """
    def clean(self, value):
        return value
## --------------------- form definitions ----------------------- ##

# a generic top-level abstraction to allow this sort of thing might be nice.
# it would certainly reduce repetition of code elements (like 'as_table' below)


# class AddSystemForm(forms.Form):
class AddSystemForm(BetterForm):
    """
    A form for adding new system records to cobbler and classifying them for puppet
    Also provides the ability to 
    * build an ISO image as part of the registration process.
    """
    # the new 'fieldsets' attribute from the BetterForms class
    # makes for easier templating
    class Meta:
        fieldsets = ( ( 'system', { 'fields' : ('name','domain','reuse_name', 'ip_address','subnet',
                                                'primary_if', 'gateway', 'name_servers'),
                                    'legend' : '' }),
                      ( 'cobbler', { 'fields' : ('profile','buildclass', 
                                                 'gen_iso', 'disksnippet', 'togglelayout'),
                                     'legend' : '' }),
                      ( 'advanced', { 'fields' : ('repoenable', 'customrepo', 'skip_network',
                                                  'skip_post', 'cleardisks', 'customsnippets', 'custompkgs'),
                                      'legend' : '' }),
                    )

    def __init__(self, *args, **kwargs):
        """
        Override __init__ (the standard class constructor) to auotgenerate 
        fields for dynamic content.
        Without doing this, the form content is compiled on first run and cached.
        Profiles are picked up from cobbler using XMLRPC API calls
        File locations are specified in config.py
        For the Add System form, we've moved to AJAX for this.
        """
        # call the parent constructor
        super(AddSystemForm, self).__init__(*args, **kwargs)
        self.handle = CobblerWebApi()


## ---------------------- Override Core functions from parent. ----------------------- ##
    def clean(self):
        """
        Additional validation of form field content.
        This is only called if the form passes validation
        THis is used to check for existence of IP address or system name records.
        """
        # take a copy of the cleaned data to work with:
        cleaned_data = self.cleaned_data

        # compile the RE for splitting DNS info
        seps = re.compile(r'[^\.0-9]+')

        # extract hostnames, IPs, DNS servers for checking and cleaning:
        name = cleaned_data.get('name')
        ipaddr = cleaned_data.get('ip_address', None)
        dns_raw = cleaned_data.get('name_servers', None)
        reuse_name = cleaned_data.get('reuse_name', False)

        # first, is the system name already registered with cobbler?

        if reuse_name == False:
            if name in self.handle.getSystemNames():
                msg = 'Hostname already exists. Please choose another.'
                self._errors['name'] = ErrorList([msg])
                del cleaned_data['name']

        # second, is that IP Address already allocated, and to which system?
        # look the IP address up in cobbler to see if it is in use:
        ip_system = self.handle.sysFromIP(ipaddr)
        if ip_system is not None:
            if ip_system == name and reuse_name == True:
                # if it's in use by the old version of this system record...
                # then we don't care, as we'rereplacing it anyway
                pass
            else:
                msg = 'IP Address already in use by %s' % ip_system
                self._errors['ip_address'] = ErrorList([msg])
                del cleaned_data['ip_address']

        # clean the nameserver field.
        # 1. replace sequences of invalid chars with a single space
        # 2. check that each entry is a valid IP address (matches the syntax)
        # 3. remove duplicates

        if dns_raw is not None:
            dnsinfo = seps.sub(' ', dns_raw).split()
            cleaned_data['name_servers'] = [ x.strip() for x in dnsinfo if IPV4_RE.match(x.strip())]            

        if cleaned_data.get('toggle_layout', False):
            # clear the disksnippet setting as it is irrelevant now.
            del cleaned_data['disksnippet']
            res = cleaned_data.get('customlayout', 'default').split('\n')
            cleaned_data['customlayout'] = res

        return cleaned_data


## ---------------------- Form Field Definitions ----------------------- ##
    buildclass = forms.ChoiceField(
        label = 'Build Class',
        help_text = 'Build Class',
        choices = [('secure','secure'), ('internal', 'internal')],
        initial = 'internal',
    )


    # fully-qualified hostname - used as profile name, comment and dns_name
    name = forms.CharField(
               widget = forms.TextInput(attrs = {'class':'textinput'}),
               max_length = 50,
               required = True,
               help_text = "System Hostname. The first part will be the cobbler profile name.",
               label = "Hostname")

    domain =   forms.CharField(widget = forms.TextInput(attrs = {'class':'textinput'}),
               max_length = 50,
               required = True,
               initial = DEFAULT_DOMAIN,
               help_text = "DNS domain",
               label = "DNS Domain")

    reuse_name = forms.BooleanField(label="Replace existing system?",
                 help_text = "If a system already exists using the chosen hostname (or IP Address) replace it with these details",
                 required = False,
                 initial = False)

    ip_address = forms.IPAddressField(
               widget = forms.TextInput(attrs = {'class':'textinput'}),
               required = True,
               help_text = "Primary IP address",
               label = "IP Address")


    subnet =   forms.IPAddressField(required = True,
               widget = forms.TextInput(attrs = {'class':'textinput'}),
               initial = DEFAULT_MASK,
               help_text = "Netmask (VLSN format only)",
               label = "Subnet Mask",)
    # MAC Address Field (not required, but useful for PXE)
    primary_if  = forms.CharField(max_length = 18,
                required = False,
                help_text = "Name of primary interface",
                label = "Primary interface",
                initial = PRIMARY_IF)
    
    gateway =  forms.IPAddressField(required = False,
               widget = forms.TextInput(attrs = {'class':'textinput'}),
               help_text = "Default Route",
               initial = DEFAULT_GW,
               label = "Gateway")

    name_servers = forms.CharField(max_length = 50,
               widget = forms.TextInput(attrs = {'class':'textinput'}),
               required = True,
               initial = DEFAULT_DNS,
               help_text = "DNS Name servers. Multiple entries must be Comma or whitespace separated",
               label = "DNS nameserver(s)")

    profile =  AjaxChoiceField(choices = [('--','--')],
               help_text = "Select an installation profile",
               label = "Cobbler Profile",
               required = False,
               initial = 'lrh5v5')

    disksnippet = AjaxChoiceField(
        widget = forms.Select,
        label = "Existing Disk Layout",
        required = False,
        help_text = "Select an existing disk layout template to apply. You can read and edit it in the box below",
        choices = [('--', '--')],
        initial = 'default' )

    togglelayout = forms.BooleanField( label = "Manual Layout?",
        required = False,
        initial = False,
        help_text = "Type in your disk layout manually below in kickstart format.",
        )

    customlayout = forms.CharField( label = "Manual Disk Layout",
            widget = forms.Textarea(attrs = { 'wrap' : 'off', 'cols' : '60','rows' : '10', 'disabled' : 'true' } ),
            required = False,
            initial = 'disabled',
            help_text = "Manually specify disk layout in anaconda/kickstart  format" )

    layout_name = forms.CharField(
        help_text = 'Filename to use if saving this layout',
        required = False,
        initial = '<Unspecified>',
        )

    # ISO filename - will be generated in ISODIR (currently /var/www/html/pub for download)
    gen_iso = forms.BooleanField( label = "Generate a bootable ISO?",
              required = False,
              initial = False,
              help_text = "Generate a bootable iso image for this system, called <hostname>.iso.")


    # various kickstart metadata fields...
    
    # Prompt for networking during installation
    # without DHCP this still requires net info above.
    skip_network = forms.BooleanField( label = "Automatically configure networking",
            required = False,
            initial = True,
            help_text = "Configure networking according to the information given above. Unchecking this will mean you are prompted during installation." )
    # run post scripts? (default: Yes)
    skip_post = forms.BooleanField(label = 'Run Kickstart %post scripts',
        required = False,
        initial = True,
        help_text = 'If unchecked, no post-build configuration will happen. You normally do not want to turn this off' )

        
    # checkbox to enable 'customrepo'
    repoenable = forms.BooleanField(
        label = 'Custom Installation URL',
        help_text = 'use a custom installation URL',
        required = False,
        )

    customrepo = forms.URLField( label = "URL",
        widget = forms.TextInput(attrs = {'disabled' : 'true', 'class' : 'textinput'}),
        max_length = 80,
        initial = '<disabled>',
        required = False,
        help_text = 'Specify a custom URL to use for installation. The installer must be able to find an "lrh5" or "lrh4" directory at this URL' )

    # clear all disks before partitioning (default : Yes)
    cleardisks = forms.BooleanField(label = 'Clear all non-SAN disks',
        required = False,
        initial = True,
        help_text = 'Clear All local disks before partitioning. This is the default behaviour. Only change it if you know what you are doing.')

    customsnippets = forms.CharField(
       widget = forms.TextInput( attrs = { 'class' : 'longinput' }),
       label = 'Custom Snippets',
       required = False,
       help_text = 'Specify custom snippets to run in kickstart %post. comma-separated, without spaces.',
       )
    custompkgs = forms.CharField(
       widget = forms.TextInput( attrs = { 'class' : 'longinput' }),
       label = 'Custom Packages',
       required = False,
       help_text = 'Specify custom packages to install in %post. Comma-separated, no spaces.',
       )
############### ISO Building Form ##############################

class BuildISOForm(forms.Form):
    """
    Build an ISO image for an existing system record (or list of)
    """
    def __init__(self, *args, **kwargs):
        super(BuildISOForm, self).__init__(*args, **kwargs)

    def clean(self):
        """
        check and clean the submitted data.
        """
        # take a working copy of the data
        data = self.cleaned_data

        profiles = data['profiles']
        systems = data['systems']
        ISOname = data.get('ISOname', '').strip()

        if ISOname == '':
            if len(systems) > 0:
                data['ISOname'] = systems[0]
            elif len(profiles) > 0:
                data['ISOname']  = profiles[0]
            else:
                msg = 'You have not provided an ISO image name or selected any systems or profiles'
                self._errors['ISOname'] = ErrorList([msg])
                del data['ISOname']
        if len(systems) == 0 and len(profiles) == 0:
            msg = 'You must select at least one system or profile'
            self._errors['systems'] = ErrorList([msg])
            self._errors['profiles'] = ErrorList([msg])
            del data['systems']
            del data['profiles']

        return data
## ---------------------- Form Field Definitions ----------------------- ##
           
# ------ Form fields ---------- #           
    ISOname = forms.CharField(
        widget = forms.TextInput( attrs = { 'class' : 'textinput' }),
        required = False,
        label = "ISO image filename (without the .iso)",
        help_text = "The name for the final image. You'll be given a download link if this is successfully generated. This will be automatically generated, based on the first system (or profile name) you select, if you don't specify anything.",
        )
    systems = AjaxMultipleChoiceField(
        widget = forms.SelectMultiple(),
        choices = [('--','--')],
        required = True,
        label = "Available Systems",
        help_text = "Select Systems to include in the ISO",
        )
    profiles = AjaxMultipleChoiceField(
        widget = forms.SelectMultiple(),
        choices = [('--','--')],
        required = False,
        label = "Available Profiles",
        help_text = "choose from the list of profiles",
        )


# not used at the moment.
# class AutocompleteForm(forms.Form):
#     """
#     A form to capture the output of jqueryUI autocomplete boxes
#     """
#     system_search = forms.CharField(
#        widget = forms.TextInput( attrs = { 'class' : 'textinput' }),
#        required = False,
#     )
#     system =  forms.ChoiceField(choices = [('','')],
#        widget = forms.TextInput( attrs = { 'class' : 'textinput' }),
#        help_text = "Select a system",
#        label = "System Name",
#        initial = 'lrh5v5')
#     profile =  forms.ChoiceField(choices = [('','')],
#        widget = forms.TextInput( attrs = { 'class' : 'textinput' }),
#        help_text = "Select an installation profile",
#        label = "Cobbler Profile",
#        initial = 'lrh5v5')
# 
# 
# # not used at the moment.
# class SystemListForm(forms.Form):
#     """
#     A simple search/list form
#     """
#     system_search = forms.CharField(
#         widget = forms.TextInput( attrs = {'class' : 'textinput'}),
#         required = False,
#     )
