#!/usr/bin/env python
"""
views.auth
methods used for authentication.
At the moment these have not been integrated and are more or less ripped off directly from cobbler.
Eventually we'll use them in a decorator to check access to certain objects if/when permitted
for a given user.
"""
from fabrik.config import *
from fabrik.cobblerweb import CobblerWebApi
import cobbler.utils
url_cobbler_api = "http://%s/cobbler_api" % COBBLER_SERVER
import xmlrpclib
token = None

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

    # create an XMLRPC connection to the server
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
        password = cobbler.utils.get_shared_secret()
        # Load server ip and port from local config
        token = remote.login(username, password)
        # this doesn't actually do anything (always returns true):
        remote.update(token)
