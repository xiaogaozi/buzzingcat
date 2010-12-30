# Buzzing Cat <https://github.com/xiaogaozi/buzzingcat>
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

import time
import random

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache

from bc.util import oauth
from bc.util import datastore

API_URL = {
    'statuses_update': "http://api.twitter.com/1/statuses/update.json",
    'statuses_home_timeline': "http://api.twitter.com/1/statuses/home_timeline.json"
}

class TwitterSignIn(webapp.RequestHandler):
    """OAuth step 1 and step 2"""
    def get(self):
        callback_url = "http://buzzingcat.appspot.com/callback/t"
        consumer_key, consumer_secret = datastore.get_oauth_consumer('t_')
        t = oauth.TwitterClient(consumer_key, consumer_secret, callback_url)
        self.redirect(t.get_authorization_url())

class TwitterCallback(webapp.RequestHandler):
    """OAuth step 3, the final step."""
    def get(self):
        arguments = self.request.arguments()

        if 'denied' in arguments:
            # User has denied the authentication.
            self.response.out.write("Welcome to use Buzzing Cat next time.")
            return
        elif len(arguments) == 0 or 'oauth_token' not in arguments:
            # The URL is illegal.
            self.response.out.write('error')
            return

        oauth_token = self.request.get('oauth_token')
        t = memcache.get(oauth_token)
        if t is None:
            # User hasn't signed in.
            self.response.out.write("You should sign in first.")
        else:
            t.obtain_access_token()
            if len(t.get_access_token()) == 0:
                # The 'oauth_token' hasn't be authorized.
                self.response.out.write("You should allow Buzzing Cat access first.")
            else:
                # Yeah, it's ok.
                user = users.get_current_user()
                if user:
                    email = user.email()
                    if datastore.has_services(email, ['Twitter']) == False:
                        access_token = t.get_access_token()
                        oauth_token = access_token['oauth_token'][0]
                        oauth_token_secret = access_token['oauth_token_secret'][0]
                        datastore.add_twitter(email, oauth_token,
                                              oauth_token_secret)
                self.redirect('/')

class TwitterAPI(oauth.OAuthClient):
    def __init__(self, consumer_key, consumer_secret,
                 oauth_token, oauth_token_secret):
        oauth.OAuthClient.__init__(self, consumer_key, consumer_secret,
                                   'Twitter')
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret
        self.parameters = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_token': self.oauth_token,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': str(random.getrandbits(64)),
            'oauth_version': '1.0'
        }

    def statuses_update(self, status):
        """http://apiwiki.twitter.com/Twitter-REST-API-Method%3A-statuses%C2%A0update"""
        self.parameters['status'] = status
        response = self.get_response(API_URL['statuses_update'],
                                     self.parameters,
                                     token_secret=self.oauth_token_secret,
                                     method='POST',
                                     headers={'Authorization': 'OAuth'})
        return response

    def statuses_home_timeline(self):
        """http://apiwiki.twitter.com/Twitter-REST-API-Method%3A-statuses-home_timeline"""
        response = self.get_response(API_URL['statuses_home_timeline'],
                                     self.parameters,
                                     token_secret=self.oauth_token_secret,
                                     headers={'Authorization': 'OAuth'})
        return response
