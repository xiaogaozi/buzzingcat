import time
import random

from bc.oauth import OAuthClient

api_url = {
    "statuses_update": "http://api.twitter.com/1/statuses/update.json",
    "statuses_home_timeline": "http://api.twitter.com/1/statuses/home_timeline.json"
}

class TwitterAPI(OAuthClient):
    def __init__(self, consumer_key, consumer_secret,
                 oauth_token, oauth_token_secret):
        OAuthClient.__init__(self, consumer_key, consumer_secret,
                             "Twitter")
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret
        self.parameters = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_token": self.oauth_token,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": str(random.getrandbits(64)),
            "oauth_version": "1.0"
        }

    def statuses_update(self, status):
        """http://apiwiki.twitter.com/Twitter-REST-API-Method%3A-statuses%C2%A0update"""
        self.parameters["status"] = status
        response = self.get_response(api_url["statuses_update"],
                                     self.parameters,
                                     token_secret=self.oauth_token_secret,
                                     method="POST",
                                     headers={ "Authorization": "OAuth" })
        return response

    def statuses_home_timeline(self):
        """http://apiwiki.twitter.com/Twitter-REST-API-Method%3A-statuses-home_timeline"""
        response = self.get_response(api_url["statuses_home_timeline"],
                                     self.parameters,
                                     token_secret=self.oauth_token_secret,
                                     headers={ "Authorization": "OAuth" })
        return response
