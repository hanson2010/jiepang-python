# -*- coding: utf-8 -*-
'''
Jiepang API Python module
by Haisheng HU <hanson2010@gmail.com>
https://github.com/hanson2010/jiepang-python

version 0.2
 * OAuth 2.0 support
version 0.1
 * Basic functions

Jiepang API doc
http://dev.jiepang.com/doc
http://code.google.com/p/jiepang-api/wiki/Documentation
'''
 
import httplib
import urllib
import string

try:
    import json
    simplejson = json
except ImportError:
    try: 
        import simplejson
    except ImportError:
        from django.utils import simplejson

#import logging

AUTHORIZATION_URI = 'https://jiepang.com/oauth/authorize'
TOKEN_URI = 'https://jiepang.com/oauth/token'

API_SERVER   = 'api.jiepang.com'
API_URL_TEMPLATE = string.Template('http://%s/v1/${method}' % (API_SERVER))

JIEPANG_METHODS = {}

def def_method(name,
               http_method='GET',
               url_template=API_URL_TEMPLATE,
               auth_required=False,
               optional=[],
               required=[]):
    JIEPANG_METHODS[name] = {
            'http_method': http_method,
            'url_template': url_template,
            'auth_required': auth_required,
            'required': required,
            'optional': optional,
        }

'''
Geo methods
'''
def_method('cities')

def_method('checkcity',
           required=['geolat', 'geolong'])

def_method('switchcity',
           auth_required=True,
           http_method='POST',
           required=['cityid'])

'''
Check in methods
'''
def_method('statuses__list',
           auth_required=True,
           required=['type'],
           optional=['count', 'id'])

def_method('checkin',
           auth_required=True,
           http_method='POST',
           optional=['vid', 'venue', 'shout', 'private',
                     'twitter', 'facebook', 'geolat', 'geolong'])

def_method('history',
           auth_required=True,
           optional=['l', 'sinceid'])

'''
User methods
'''
def_method('account__verify_credentials',
           auth_required=True)

def_method('user',
           auth_required=True,
           optional=['uid', 'badges', 'mayor'])

def_method('friends',
           auth_required=True,
           optional=['uid'])

'''
Venue methods
'''
def_method('venues',
           required=['geolat', 'geolong'],
           optional=['l', 'q'])

def_method('locations__show',
           required=['guid'])

def_method('addvenue',
           auth_required=True,
           http_method='POST',
           required=['name', 'address', 'crossstreet',
                     'city', 'state', 'cityid'],
           optional=['zip', 'phone', 'geolat', 'geolong'])

def_method('venue_proposeedit',
           auth_required=True,
           http_method='POST',
           # Documentation does not specify if crosstreet is required
           # or optional.
           required=['vid', 'name', 'address', 'crossstreet', 'city',
                     'state', 'geolat', 'geolong'],
           optional=['zip', 'phone'])

def_method('venue_flagclosed',
           auth_required=True,
           http_method='POST',
           required=['vid'])

'''
Tip methods
'''
def_method('tips',
           required=['geolat', 'geolong'],
           optional=['l'])

def_method('addtip',
           auth_required=True,
           http_method='POST',
           required=['vid', 'text'],
           optional=['type', 'geolat', 'geolong'])

def_method('tip_marktodo',
           auth_required=True,
           http_method='POST',
           required=['tid'])

def_method('tip_markdone',
           auth_required=True,
           http_method='POST',
           required=['tid'])

'''
Settings methods
'''
def_method('setpings',
           auth_required=True,
           http_method='POST',
           required=['self', 'uid'])

'''
Friend methods
'''
def_method('friend_requests',
           auth_required=True)

def_method('friend_approve',
           auth_required=True,
           http_method='POST',
           required=['uid'])

def_method('friend_deny',
           auth_required=True,
           http_method='POST',
           required=['uid'])

def_method('friend_sendrequest',
           auth_required=True,
           http_method='POST',
           required=['uid'])

def_method('findfriends_byname',
           auth_required=True,
           required=['q'])

def_method('findfriends_byphone',
           auth_required=True,
           required=['q'])

def_method('findfriends_bytwitter',
           auth_required=True,
           optional=['q'])

class JiepangException(Exception):
    pass
 
class JiepangRemoteException(JiepangException):
    def __init__(self, method, code, msg):
        self.method = method
        self.code = code
        self.msg = msg

    def __str__(self):
        return 'Error signaled by remote method %s: %s (%s)' % (self.method, self.msg, self.code)

'''
Used as a proxy for methods of the Jiepang class; when methods
are called, __call__ in JiepangAccumulator is called, ultimately
calling the jiepang_obj's callMethod()
'''
class JiepangAccumulator(object):
    def __init__(self, jiepang_obj, name):
        self.jiepang_obj = jiepang_obj
        self.name = name
    
    def __repr__(self):
        return self.name
    
    def __call__(self, *args, **kw):
        return self.jiepang_obj.call_method(self.name, *args, **kw)

class JiepangClient(object):
    _access_token = ''

    def __init__(self, access_token=''):
        if access_token:
            self._access_token = access_token
        for method in JIEPANG_METHODS:
            if not hasattr(self, method):
                setattr(self, method, JiepangAccumulator(self, method))

    def get_access_token(self):
        return self._access_token

    def build_request(self, http_method, url, params):
        query = urllib.urlencode(params)
        if http_method == 'POST':
            body = query
        else:
            body = None
        return '%s?%s' % (url, query), body

    def get_http_connection(self, server):
        return httplib.HTTPConnection(server)

    def fetch_response(self, server, http_method, url, body=None):
        http_connection = self.get_http_connection(server)
        if body:
            http_connection.request(http_method, url, body)
        else:
            http_connection.request(http_method, url)
        response = http_connection.getresponse()
        response_body = response.read()
        if response.status != 200:
            raise JiepangRemoteException(url, response.status, response_body)
        return response_body

    def call_method(self, method, *args, **kw):
#        logging.debug('Calling jiepang method %s %s %s' % (method, args, kw))
        meta = JIEPANG_METHODS[method]
        if args:
            names = meta['required'] + meta['optional']
            for i in xrange(len(args)):
                kw[names[i]] = args[i]
        # Check we have all required arguments
        if len(set(meta['required']) - set(kw.keys())) > 0:
            raise JiepangException('Too few arguments were supplied for the method %s; required arguments are %s.' % (method, ', '.join(meta['required'])))
        for arg in kw:
            if (not arg in meta['required']) and (not arg in meta['optional']):
                raise JiepangException('Unknown argument %s supplied to method %s. Required arguments are %s, optional arguments are %s.' % (arg, method, ', '.join(meta['required']), ', '.join(meta['optional'])))
        # Add oauth access token
        if meta['auth_required']:
            if not self.get_access_token():
                raise JiepangException('Remote method %s requires authorization.' % (method))
            kw['access_token'] = self.get_access_token()
        cred_url, cred_args = self.build_request(
                meta['http_method'],
                meta['url_template'].substitute(method=method.replace('__', '/')),
                kw
            )
        if meta['http_method'] == 'POST':
            response = self.fetch_response(API_SERVER,
                                           meta['http_method'],
                                           cred_url,
                                           body=cred_args)
        else:
            response = self.fetch_response(API_SERVER,
                                           meta['http_method'],
                                           cred_url)
        results = simplejson.loads(response)
        return results
