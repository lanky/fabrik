Top-level Fabrik documentation
==============================

This directory contains the key python code for the fabrik web interface.
The interface is a django application, using jQuery for javascript and AJAX calls where appropriate.

Django is a web framework, also used by the cobbler web interface.

software requirements
---------------------
versions are those used here, but later ones will probably be fine

* mod_wsgi-3.2-1.el5.x86_64
* Django-1.2.3-1.noarch
* httpd
* cobbler >= 2

Filesystem Requirements
-----------------------

The 'apache' group requires write access to /var/www/html/pub (or another web-accessible directory) for placing ISO images.
'apache' also requires write access on the upload location for new disk layouts (/var/lib/cobbler/disklayouts/custom)

useful references
-----------------
* http://www.djangoproject.com
* http://www.jquery.org


Key Python files in the 'fabrik' directory
------------------------------------------
* urls.py

maps URL patterns to functions in views.py. URL expressions are regex.
They pass the HTTP_REQUEST object, plus other opional parameters to the specified function.

### views

The 'views' module contains 3 separate python modules for manageability.

* std.py
 contains views for listing and adding systems, plus ISO generation.

* ajax.py
functions that receive and send data via AJAX (mostly using JSON format)

* auth.py
currently unused authentication functionality


### forms.py

Django form fields do their own validation and input checking.
Overriding the clean() method allows you to add to this, depending on the logic of your app.

### utils.py

custom utility code for reuse in views

### cobblerweb.py

an abstraction of some elements of the Cobbler XMLRPC API
This includes methods to produce output in a form consumable by django
form elements.
This way you only require to create an instance of cobblerweb.CobblerWebApi()
and many functions are available to you (including some that are not provided directly by cobbler.

The actual cobbler XMLRPC api is sparsely documented, but the code lives in
/usr/lib/python2.4/site-packages/cobbler/remote.py
and the local api (used only for ISO image generation right now) in
/usr/lib/python2.4/site-packages/cobbler/api.py
    
### config.py

configuration file, mainly key = value pairs
used by most parts of the fabrik interface.
includes settings for cobbler server, plus some unused settings for integrating with puppet etc.

The key variables in here are

    COBBLER_SERVER = 'your.cobbler.server'
    # COBBLER_SERVER = 'localhost.localdomain'
    # the interface does authenticate you, but this is more complex than you'd think, so
    # once authenticated we fall back to this:
    # future versions may use pass-through.
    COBBLERUSER = "xmlrpc"
    COBBLERPASS = "password"

    # destdir for ISO images
    ISODIR = '/var/www/html/pub'
    # how this appears in a URL
    ISOROOT = '/pub'

Templating
---------

### templatetags
files defining new tags for use in django templates.
see templatetags/README.
Currently this is not in use, but various Django snippets and plugins can be installed to make templating easier.

### templates
template files used by views.py to render content.
see templates/README
