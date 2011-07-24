# -*- coding: utf-8 -*-
'''
OAuth 2.0 Python module
by Haisheng HU <hanson2010@gmail.com>
https://github.com/hanson2010/jiepang-python

version 0.1
 * basic functions

OAuth 2.0 doc
http://oauth.net/2/
'''

import urllib, urllib2

try:
    import json
    simplejson = json
except ImportError:
    try: 
        import simplejson
    except ImportError:
        from django.utils import simplejson

class OAuthHelper(object):
    _authorization_uri = ''
    _token_uri = ''

    _client_id = ''
    _client_secret = ''
    _redirect_uri = ''

    def __init__(self, authorization_uri, token_uri, client_id, client_secret, redirect_uri):
        self._authorization_uri = authorization_uri
        self._token_uri = token_uri
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def _urlencode(self, query):
        return urllib.urlencode(query)

    def _urlopen(self, url):
        error = ''
        data = ''
        req = urllib2.Request(url)
        try:
            response = urllib2.urlopen(req)
            data = response.read()
        except urllib2.HTTPError, e:
            error = 'The server couldn\'t fulfill the request with error code %d' % (e.code)
        except urllib2.URLError, e:
            error = 'We failed to reach a server because %s' % (e.reason)
        return {
            'error': error,
            'data': data
        }

    def get_redirect_uri(self):
        return self._redirect_uri

    def get_authorization_uri(self):
        query = {
            'response_type': 'code',
            'client_id': self._client_id,
            'redirect_uri': self._redirect_uri
        }
        query_str = self._urlencode(query)
        return '%s?%s' % (self._authorization_uri, query_str)

    def get_token_uri(self, code):
        query = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self._client_id,
            'client_secret': self._client_secret,
            'redirect_uri': self._redirect_uri
        }
        query_str = self._urlencode(query)
        return '%s?%s' % (self._token_uri, query_str)

    def get_access_token(self, code):
        error = ''
        token = ''
        r = self._urlopen(self.get_token_uri(code))
        if r['error'] == '':
            json = simplejson.loads(r['data'])
            if 'access_token' in json:
                token = str(json['access_token'])
        else:
            error = r['error']
        return {
            'error': error,
            'token': token
        }
