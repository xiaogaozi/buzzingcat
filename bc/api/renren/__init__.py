# Buzzing Cat
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

import urllib
import Cookie

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import urlfetch

from bc.util import datastore

API_URL = {
    'login': "http://www.renren.com/PLogin.do",
    'statuses_update': "http://status.renren.com/doing/update.do"
}

class RenrenSignIn(webapp.RequestHandler):
    def get(self):
        self.redirect('/')

    def post(self):
        user = users.get_current_user()
        if user:
            email = user.email()
            if datastore.has_services(email, ['Renren']) == False:
                username = self.request.get('username')
                password = self.request.get('password')
                datastore.add_renren(email, username, password)
        self.redirect('/')

class RenrenAPI():
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def login(self):
        headers = {
            'Content-Type': "application/x-www-form-urlencoded"
        }

        # Validate username (namely email) and password.
        form_fields = {
            'email': self.email,
            'password': self.password,
            'domain': "renren.com",
            'origURL': "http://www.renren.com/home"
        }
        form_data = urllib.urlencode(form_fields)
        response = urlfetch.fetch(API_URL['login'],
                                  payload=form_data,
                                  method=urlfetch.POST,
                                  headers=headers,
                                  follow_redirects=False)
        # 302 Found: redirection
        if response.status_code != 302:
            return

        # If validation is successful, then request the redirection
        # URL so that gets some useful cookie information.
        redirect_url = response.headers['location']
        cookie = Cookie.SimpleCookie(response.headers['set-cookie'])
        headers['Cookie'] = ';'.join(["%s=%s" % (c.key, c.value)
                                      for c in cookie.values()])
        response = urlfetch.fetch(redirect_url,
                                  headers=headers,
                                  follow_redirects=False)
        return response

    def statuses_update(self, status, response):
        """Update user's status on Renren website."""
        if isinstance(status, unicode):
            status = status.encode('utf-8')

        form_fields = {
            'c': status,
            'raw': status,
            'publisher_form_ticket': -453288708,
            'requestToken': -453288708
        }
        form_data = urllib.urlencode(form_fields)

        headers = {
            'Content-Type': "application/x-www-form-urlencoded"
        }
        cookie = Cookie.SimpleCookie(response.headers['set-cookie'])
        headers['Cookie'] = ';'.join(["%s=%s" % (c.key, c.value)
                                      for c in cookie.values()])

        response = urlfetch.fetch(API_URL['statuses_update'],
                                  payload=form_data,
                                  method=urlfetch.POST,
                                  headers=headers)
        return response
