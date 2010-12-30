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

import os
import re
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from bc.api import twitter
from bc.api import renren
from bc.util import datastore
from bc.handler import xmpp

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        signin = False
        t = False
        rr = False
        if user:
            email = user.email()
            if datastore.lookup_user(email) == True:
                signin = True
                if datastore.has_services(email, ['Twitter']) == True:
                    t = True
                if datastore.has_services(email, ['Renren']) == True:
                    rr = True

        template_values = {
            'signin': signin,
            'user': user,
            'twitter': t,
            'renren': rr
        }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class SignIn(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            email = user.email()
            if datastore.lookup_user(email) == True:
                self.redirect('/')
            else:
                if re.match(r"^.*@gmail\.com$", email) is not None:
                    datastore.add_user(email)
                    logging.info("New User: " + email)
                    self.redirect('/')
                else:
                    url = users.create_logout_url('/')
                    path = os.path.join(os.path.dirname(__file__), 'webpages/signin.html')
                    self.response.out.write(template.render(path, {'logout': url}))
        else:
            self.redirect(users.create_login_url('/signin'))

class Admin(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            if users.is_current_user_admin():
                path = os.path.join(os.path.dirname(__file__), 'webpages/admin.html')
                self.response.out.write(template.render(path, {}))
            else:
                self.redirect('/')
        else:
            self.redirect('/')

    def post(self):
        user = users.get_current_user()
        if user:
            if users.is_current_user_admin():
                t_consumer_key = self.request.get('t_consumer_key')
                t_consumer_secret = self.request.get('t_consumer_secret')
                datastore.update_admin(t_consumer_key, t_consumer_secret)
                self.redirect('/admin')
            else:
                self.redirect('/')
        else:
            self.redirect('/')

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/signin', SignIn),
                                      ('/signin/t', twitter.TwitterSignIn),
                                      ('/signin/rr', renren.RenrenSignIn),
                                      ('/callback/t', twitter.TwitterCallback),
                                      ('/_ah/xmpp/message/chat/', xmpp.XMPPHandler),
                                      ('/admin', Admin)],
                                     debug=False)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
