import urllib
import Cookie

from google.appengine.api import urlfetch

api_url = {
    "login": "http://www.renren.com/PLogin.do",
    "statuses_update": "http://status.renren.com/doing/update.do"
}

class RenrenAPI():
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def login(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # Validate username (namely email) and password.
        form_fields = {
            "email": self.email,
            "password": self.password,
            "domain": "renren.com",
            "origURL": "http://www.renren.com/Home.do"
        }
        form_data = urllib.urlencode(form_fields)
        response = urlfetch.fetch(api_url["login"],
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
            status = status.encode("utf-8")

        form_fields = {
            "c": status,
            "isAtHome": 0,
            "raw": status
        }
        form_data = urllib.urlencode(form_fields)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        cookie = Cookie.SimpleCookie(response.headers['set-cookie'])
        headers['Cookie'] = ';'.join(["%s=%s" % (c.key, c.value)
                                      for c in cookie.values()])

        response = urlfetch.fetch(api_url["statuses_update"],
                                  payload=form_data,
                                  method=urlfetch.POST,
                                  headers=headers)
        return response
