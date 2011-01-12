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

import re

from google.appengine.ext.webapp import xmpp_handlers

from bc.api import twitter
from bc.api import renren
from bc.handler import error
from bc.util import datastore

class XMPPHandler(xmpp_handlers.CommandHandler):
    """Handles many kinds of commands via XMPP."""
    def has_service(self, message, service):
        m = re.search(r"^.*@gmail\.com(?=/)", message.sender)
        if m is not None:
            email = m.group(0)
            if datastore.lookup_user(email) == False:
                message.reply("You should sign in first, please visit http://buzzingcat.appspot.com/")
                return None
            else:
                if datastore.has_services(email, [service]) == False:
                    message.reply("You should active " + service + " first, please visit http://buzzingcat.appspot.com/")
                    return None
                return email
        else:
            message.replay("Not Gmail account.")
            return None

    # ---------------------------------------------
    # Common Commands
    # ---------------------------------------------

    def help_command(self, message=None):
        """Handles /help requests."""
        message.reply("Welcome to use Buzzing Cat!\n\n"
                      "Commands:\n"
                      "- /t <message>   New Tweet\n"
                      "- /rr <message>  New Renren status\n"
                      "- <message>      Sync with all your actived services\n"
                      "- /tl            Rencent Twitter timeline\n"
                      "- /help          Give this help list")

    def text_message(self, message=None):
        """Handles plain text messages."""
        if self.has_service(message, 'Twitter') is None or self.has_service(message, 'Renren') is None:
            return
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
        email = self.has_service(message, 'Twitter')
        if email is None:
            return
        consumer_key, consumer_secret = datastore.get_oauth_consumer('t_')
        oauth_token, oauth_token_secret = datastore.get_oauth_token_and_secret(email, 'Twitter')
        t = twitter.TwitterAPI(consumer_key, consumer_secret,
                               oauth_token, oauth_token_secret)
        response = t.statuses_update(message.arg)

        if response.status_code == 200:
            message.reply("Your tweet has sended.")
        else:
            message.reply(error.response_error(response, "Twitter"))

    def tl_command(self, message=None):
        """Handles /tl (timeline) requests."""
        email = self.has_service(message, 'Twitter')
        if email is None:
            return
        consumer_key, consumer_secret = datastore.get_oauth_consumer('t_')
        oauth_token, oauth_token_secret = datastore.get_oauth_token_and_secret(email, 'Twitter')
        t = twitter.TwitterAPI(consumer_key, consumer_secret,
                               oauth_token, oauth_token_secret)
        response = t.statuses_home_timeline()

        if response.status_code == 200:
            message.reply(response.content)
        else:
            message.reply(error.response_error(response, 'Twitter'))

    # ---------------------------------------------
    # Renren Commands
    # ---------------------------------------------

    def rr_command(self, message=None):
        """Handles /rr (renren) requests."""
        email = self.has_service(message, 'Renren')
        if email is None:
            return
        username, password = datastore.get_username_and_pass(email, 'Renren')
        r = renren.RenrenAPI(username, password)
        response = r.login()
        if response.status_code != 302:
            message.reply("Error: Renren: login failed")
            return

        response = r.statuses_update(message.arg, response)
        if response is None:
            message.reply("Error: Renren: get_check not found")
        else:
            if response.status_code == 200:
                message.reply("Your Renren status has updated.")
            else:
                message.reply(error.response_error(response, 'Renren'))
