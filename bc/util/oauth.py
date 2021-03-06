# Buzzing Cat - OAuth Authentication Module <https://github.com/xiaogaozi/buzzingcat>
# Copyright (C) 2010  xiaogaozi <gaochangjian@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# OAuth Authentication is done in three steps:
#   1. The Consumer obtains an unauthorized Request Token.
#   2. The User authorizes the Request Token.
#   3. The Consumer exchanges the Request Token for an Access Token.
#
# For more information about OAuth, visit http://tools.ietf.org/html/draft-hammer-oauth-10

import time
import random
import urllib
import hmac
import hashlib
import cgi

from google.appengine.api import urlfetch
from google.appengine.api import memcache

class OAuthClient():
    """Base OAuth"""
    def __init__(self, consumer_key, consumer_secret,
                 service_name, callback_url="",
                 request_token_url="",
                 user_authorization_url="",
                 access_token_url=""):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.service_name = service_name
        self.callback_url = callback_url
        self.request_token_url = request_token_url
        self.user_authorization_url = user_authorization_url
        self.access_token_url = access_token_url

    def __escape(self, s):
        return urllib.quote(s, "~")

    def __encode_utf8(self, s):
        if isinstance(s, unicode):
            return s.encode("utf-8")
        else:
            return str(s)

    def __generate_Signature_Base_String(self, method, request_url,
                                         parameters):
        """Generate the Signature Base String as text of HMAC algorithm."""
        concatenate_param = "&".join(["%s=%s" % (self.__escape(key),
                                                 self.__escape(parameters[key]))
                                      for key in sorted(parameters)])
        return "&".join([method, self.__escape(request_url),
                         self.__escape(concatenate_param)])

    def __generate_key(self, consumer_secret, token_secret):
        """Generate the key of HMAC algorithm."""
        return "&".join([consumer_secret, token_secret])

    def __generate_oauth_signature(self, signature_method, key, text):
        """Generate the 'oauth_signature'."""
        if signature_method == "HMAC-SHA1":
            return hmac.new(key, text, hashlib.sha1).digest().encode("base64").strip()

    def __fetch_url(self, request_url, params, method, headers):
        """Fetch URL."""
        url = "%s?%s" % (request_url, urllib.urlencode(params))

        if method == "GET":
            m = urlfetch.GET
        elif method == "POST":
            m = urlfetch.POST

        return urlfetch.fetch(url, method=m, headers=headers)

    def __add_to_cache(self):
        """Store current object in memcache for future requests.
        
        The stored key is 'oauth_token', value is this OAuth object,
        and expiration time is 3600 seconds (equal to 1 hour)."""
        memcache.set(self.request_token["oauth_token"][0], self, time=3600)

    def get_response(self, request_url, params, token_secret="", method="GET",
                     headers={}):
        """Generate the 'oauth_signature' and return response."""
        # Encode string with UTF-8.
        l = [(self.__encode_utf8(k), self.__encode_utf8(v)) for k, v in params.items()]
        params.clear()
        params.update(l)

        # Generate the Signature Base String as text of HMAC algorithm.
        text = self.__generate_Signature_Base_String(method, request_url, params)

        # Generate the key of HMAC algorithm.
        key = self.__generate_key(self.consumer_secret, token_secret)

        # Generate the oauth_signature.
        k = self.__encode_utf8("oauth_signature")
        v = self.__encode_utf8(self.__generate_oauth_signature(params["oauth_signature_method"],
                                                               key, text))
        params[k] = v

        # Return response.
        response = self.__fetch_url(request_url, params, method, headers)
        return response

    # --------------------------------------------------------------------------
    # Step 1: The Consumer obtains an unauthorized Request Token.
    # --------------------------------------------------------------------------
    def obtain_request_token(self):
        """Get unauthorized Request Token."""
        # Initialize parameters.
        parameters = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": str(random.getrandbits(64)),
            "oauth_version": "1.0"
        }
        if self.service_name == "Twitter":
            parameters["oauth_signature_method"] = "HMAC-SHA1"

        # Save this unauthorized Request Token.
        response = self.get_response(self.request_token_url, parameters)
        self.request_token = cgi.parse_qs(response.content)

    # --------------------------------------------------------------------------
    # Step 2: The User authorizes the Request Token.
    # --------------------------------------------------------------------------
    def authorize_request_token(self):
        """Direct the user to the service provider."""
        # Initialize parameters.
        parameters = {
            "oauth_token": self.request_token["oauth_token"][0],
            "oauth_callback": self.callback_url
        }

        url = "%s?%s" % (self.user_authorization_url, urllib.urlencode(parameters))
        return url

    def get_authorization_url(self):
        """Return user authorization URL."""
        self.obtain_request_token()
        self.__add_to_cache()
        return self.authorize_request_token()

    # --------------------------------------------------------------------------
    # Step 3: The Consumer exchanges the Request Token for an Access Token.
    # --------------------------------------------------------------------------
    def obtain_access_token(self):
        """Exchange the Request Token for an Access Token."""
        # Initialize parameters.
        parameters = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_token": self.request_token["oauth_token"][0],
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": str(random.getrandbits(64)),
            "oauth_version": "1.0"
        }
        if self.service_name == "Twitter":
            parameters["oauth_signature_method"] = "HMAC-SHA1"

        # Save this Access Token.
        response = self.get_response(self.access_token_url, parameters,
                                     token_secret=self.request_token["oauth_token_secret"][0])
        self.access_token = cgi.parse_qs(response.content)

    def get_access_token(self):
        return self.access_token

class TwitterClient(OAuthClient):
    """Twitter OAuth"""
    def __init__(self, consumer_key, consumer_secret, callback_url):
        OAuthClient.__init__(self, consumer_key, consumer_secret,
                             "Twitter", callback_url,
                             "http://twitter.com/oauth/request_token",
                             "http://twitter.com/oauth/authenticate",
                             "http://twitter.com/oauth/access_token")
