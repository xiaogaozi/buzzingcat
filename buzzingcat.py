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

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import xmpp_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

import os
from google.appengine.ext.webapp import template

from bc import errorhandler
from bc.api import twitter
from bc.api import renren
from bc.oauth import TwitterClient

consumer_key = "vZiUjHaqOQ4ndNiZ2yQ"
consumer_secret = "23SVfKMA2eETgPXZPGFnamsEuJreAsKDNinVW6s2Y"
oauth_token = "25787139-HriI8I9xxhzG8OMP97FDybg2voocmRxYkMJ4xW14M"
oauth_token_secret = "BCuyyqYZ467lmecjtXtt4ZFQRaBOUcgmVfoarRHIXE"
email = "gaochangjian@gmail.com"
password = "Fw6300f*2@i"

class XMPPHandler(xmpp_handlers.CommandHandler):
    """Handles many kinds of commands via XMPP."""

    # ---------------------------------------------
    # Common Commands
    # ---------------------------------------------

    def help_command(self, message=None):
        """Handles /help requests."""
        message.reply("Welcome to use Buzzing Cat!\n\n" + message.sender)

    def text_message(self, message=None):
        """Handles plain text messages."""
        self.t_command(message)
        self.rr_command(message)

    def unhandled_command(self, message=None):
        """Handles unknown command."""
        message.reply("Unknown command. Use /help for more information.")

    # ---------------------------------------------
    # Twitter Commands
    # ---------------------------------------------

    def t_command(self, message=None):
        """Handles /t (twitter) requests."""
        t = twitter.TwitterAPI(consumer_key, consumer_secret,
                               oauth_token, oauth_token_secret)
        response = t.statuses_update(message.arg)

        if response.status_code == 200:
            message.reply("Your tweet has sended.")
        else:
            message.reply(errorhandler.response_error(response, "Twitter"))

    def tl_command(self, message=None):
        """Handles /tl (timeline) requests."""
        t = twitter.TwitterAPI(consumer_key, consumer_secret,
                               oauth_token, oauth_token_secret)
        response = t.statuses_home_timeline()

        if response.status_code == 200:
            message.reply(response.content)
        else:
            message.reply(errorhandler.response_error(response, "Twitter"))

    # ---------------------------------------------
    # Renren Commands
    # ---------------------------------------------

    def rr_command(self, message=None):
        """Handles /rr (renren) requests."""
        r = renren.RenrenAPI(email, password)
        response = r.login()
        if response.status_code != 302:
            message.reply("Renren: login error.")
            return

        response = r.statuses_update(message.arg, response)
        if response.status_code == 200:
            message.reply("Your Renren status has updated.")
        else:
            message.reply(errorhandler.response_error(response, "Renren"))

class Test(webapp.RequestHandler):
    def get(self):
        r = renren.RenrenAPI(email, password)
        response = r.login()
        if response.status_code != 302:
            self.response.out.write("Renren: login error.")
            return

        response = r.statuses_update("Holy shit!", response)
        if response.status_code == 200:
            self.response.out.write("Your Renren status has updated.")
        else:
            self.response.out.write(errorhandler.response_error(response, "Renren"))

class MainPage(webapp.RequestHandler):
    def get(self):
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class TwitterSignIn(webapp.RequestHandler):
    """OAuth step 1 and step 2"""
    def get(self):
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

application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/', XMPPHandler),
                                      ('/', MainPage),
                                      ('/signin/t', TwitterSignIn),
                                      ('/callback/t', TwitterCallback),
                                      ('/test', Test)],
                                     debug=True)
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
