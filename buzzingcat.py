# YouBuzz
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

from google.appengine.api import xmpp
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import os
from google.appengine.ext.webapp import template

from oauth import TwitterClient

class XMPPHandler(webapp.RequestHandler):
    def post(self):
        message = xmpp.Message(self.request.POST)
        message.reply("Hi, this is Buzzing Cat!")

class MainPage(webapp.RequestHandler):
    def get(self):
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class TwitterSignIn(webapp.RequestHandler):
    """OAuth step 1 and step 2"""
    def get(self):
        consumer_key = "vZiUjHaqOQ4ndNiZ2yQ"
        consumer_secret = "23SVfKMA2eETgPXZPGFnamsEuJreAsKDNinVW6s2Y"
        callback_url = "http://buzzingcat.appspot.com/callback/t"
        t = TwitterClient(consumer_key, consumer_secret, callback_url)
        self.redirect(t.get_authorization_url())

class TwitterCallback(webapp.RequestHandler):
    """OAuth step 3, the final step."""
    def get(self):
        arguments = self.request.arguments()

        if "denied" in arguments:
            # User has denied the authentication.
            self.response.out.write("Welcome to use 'Buzzing Cat' next time.")
            return
        elif len(arguments) == 0 or "oauth_token" not in arguments:
            # The URL is illegal.
            self.response.out.write("error")
            return

        oauth_token = self.request.get("oauth_token")
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
                self.response.out.write(t.get_access_token())

class TwitterTest(webapp.RequestHandler):
    """Just one test."""
    def get(self):
        pass

application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/', XMPPHandler),
                                      ('/', MainPage),
                                      ('/signin/t', TwitterSignIn),
                                      ('/callback/t', TwitterCallback),
                                      ('/t/test', TwitterTest)],
                                     debug=True)
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
