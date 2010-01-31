from oauth import OAuthClient

class TwitterAPI(OAuthClient):
    def __init__(self, consumer_key, consumer_secret):
        OAuthClient.__init__(self, consumer_key, consumer_secret,
                             service_name="Twitter")

    def get_home_timeline(self):
        """http://apiwiki.twitter.com/Twitter-REST-API-Method%3A-statuses-home_timeline"""
        pass
