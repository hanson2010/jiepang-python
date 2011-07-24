# -*- coding: utf-8 -*-
'''
Jiepang API Python module
by Haisheng HU <hanson2010@gmail.com>
https://github.com/hanson2010/jiepang-python

version 0.1
 * basic functions

Jiepang API doc
http://dev.jiepang.com/doc
http://code.google.com/p/jiepang-api/wiki/Documentation
'''
 
import httplib
import urllib
import string
import sys
import logging
import base64
from django.utils import simplejson

API_PROTOCOL = 'http'
API_SERVER   = 'api.jiepang.com'
API_VERSION  = 'v1'
API_SOURCE   = 'checkinsync'

API_URL_TEMPLATE = string.Template(
    API_PROTOCOL + '://' + API_SERVER + '/' + API_VERSION + '/${method}'
)
POST_HEADERS = {
    'Content-type': 'application/x-www-form-urlencoded',
    'Accept'      : 'text/plain'
}
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

def merge_dicts(a, b):
    if a == None:
        return b
    if b == None:
        return a
    r = {}
    for key, value in a.items():
        r[key] = value
    for key, value in b.items():
        r[key] = value
    return r

class Credentials:
    pass

class BasicCredentials(Credentials):
    def __init__(self, username, password):
        self.username = username
        self.password = password
 
    def build_request(self, http_method, url, parameters):
        # Need to strip the newline off.
        auth_string = base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
        query = urllib.urlencode(parameters)
        if http_method == 'POST':
            args = query
        else:
            args = None
        return url+ '?' + query, args, {'Authorization': 'Basic %s' % (auth_string,)}
 
    def authorized(self):
        return True

class NullCredentials(Credentials):
    def __init__(self):
        pass

    def authorized(self):
        return False

    def build_request(self, http_method, url, parameters):
        query = urllib.urlencode(parameters)
        if http_method == 'POST':
            args = query
        else:
            args = None
        return url + '?' + query, args, {}

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
calling the foursquare_obj's callMethod()
'''
class JiepangAccumulator:
    def __init__(self, jiepang_obj, name):
        self.jiepang_obj = jiepang_obj
        self.name = name
    
    def __repr__(self):
        return self.name
    
    def __call__(self, *args, **kw):
        return self.jiepang_obj.call_method(self.name, *args, **kw)

class Jiepang:
    def __init__(self, credentials=None):
        if credentials:
            self.credentials = credentials
        else:
            self.credentials = NullCredentials()
 
        for method in JIEPANG_METHODS:
            if not hasattr(self, method):
                setattr(self, method, JiepangAccumulator(self, method))

    def get_http_connection(self, server):
        return httplib.HTTPConnection(server)

    def fetch_response(self, server, http_method, url, body=None, headers=None):
        http_connection = self.get_http_connection(server)
        if (body is not None) or (headers is not None):
            http_connection.request(http_method, url, body, merge_dicts(POST_HEADERS, headers))
        else:
            http_connection.request(http_method, url)
        response = http_connection.getresponse()
        response_body = response.read()
        if response.status != 200:
            raise JiepangRemoteException(url, response.status, response_body)
        return response_body

    def call_method(self, method, *args, **kw):
        logging.debug('Calling jiepang method %s %s %s' % (method, args, kw))
        meta = JIEPANG_METHODS[method]
        if meta['auth_required'] and (not self.credentials or not self.credentials.authorized()):
            raise JiepangException('Remote method %s requires authorization.' % (`method`,))
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
        kw['source'] = API_SOURCE
        cred_url, cred_args, cred_headers = self.credentials.build_request(
                meta['http_method'],
                meta['url_template'].substitute(method=method.replace('__', '/')),
                kw
            )
        if meta['http_method'] == 'POST':
            response = self.fetch_response(API_SERVER,
                                           meta['http_method'],
                                           cred_url,
                                           body=cred_args,
                                           headers=cred_headers)
        else:
            response = self.fetch_response(API_SERVER,
                                           meta['http_method'],
                                           cred_url,
                                           headers=cred_headers)
        results = simplejson.loads(response)
        return results
