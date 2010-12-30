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

from google.appengine.ext import db
from google.appengine.api import memcache

class User(db.Model):
    useraccount = db.EmailProperty(required=True)
    services = db.StringListProperty()

class Admin(db.Model):
    t_consumer_key = db.StringProperty()
    t_consumer_secret = db.StringProperty()

class Twitter(db.Model):
    useraccount = db.EmailProperty(required=True)
    oauth_token = db.StringProperty()
    oauth_token_secret = db.StringProperty()

class Renren(db.Model):
    useraccount = db.EmailProperty(required=True)
    username = db.StringProperty()
    password = db.StringProperty()

def lookup_user(email):
    """Check if user has registered."""
    query = db.GqlQuery("SELECT * FROM User "
                        "WHERE useraccount = :1",
                        email)
    if query.count() == 0:
        return False
    else:
        return True

def has_services(email, services):
    """Check if user has enabled these services."""
    query = db.GqlQuery("SELECT * FROM User "
                        "WHERE useraccount = :1",
                        email)
    result = query.get().services

    for s in services:
        if s not in result:
            return False

    return True

def add_services(email, services):
    """Add services."""
    query = db.GqlQuery("SELECT * FROM User "
                        "WHERE useraccount = :1",
                        email)
    result = query.get()

    for s in services:
        result.services.append(s)

    result.put()

def add_user(email):
    """Add Buzzing Cat user account."""
    user = User(useraccount=email)
    try:
        user.put()
    except db.Error:
        return

def update_admin(t_consumer_key='', t_consumer_secret=''):
    """Update admin information."""
    q = Admin.all()
    for r in q:
        db.delete(r)

    admin = Admin(t_consumer_key=t_consumer_key,
                  t_consumer_secret=t_consumer_secret)
    try:
        admin.put()
    except db.Error:
        return

def add_twitter(email, oauth_token, oauth_token_secret):
    """Add Twitter user account."""
    twitter = Twitter(useraccount=email,
                      oauth_token=oauth_token,
                      oauth_token_secret=oauth_token_secret)
    try:
        twitter.put()
    except db.Error:
        return

    add_services(email, ['Twitter'])

def add_renren(email, username, password):
    """Add Renren user account."""
    renren = Renren(useraccount=email,
                    username=username,
                    password=password)
    try:
        renren.put()
    except db.Error:
        return

    add_services(email, ['Renren'])

def get_prop(model, properties, email=None):
    """Get properties of model instance."""
    query = None
    if email:
        query = db.GqlQuery("SELECT * FROM " + model + " "
                            "WHERE useraccount = :1",
                            email)
    else:
        query = db.GqlQuery("SELECT * FROM " + model)
    result = query.get()

    if len(properties) == 1:
        return getattr(result, properties[0])
    else:
        return [getattr(result, prop) for prop in properties]

def get_oauth_consumer(prefix):
    """Get Consumer Key and Consumer Secret, along with memcache."""
    consumer_key = ''
    consumer_secret = ''
    consumer = memcache.get_multi(['consumer_key', 'consumer_secret'], key_prefix=prefix)
    if len(consumer) > 0:
        consumer_key = consumer['consumer_key']
        consumer_secret = consumer['consumer_secret']
    else:
        consumer_key, consumer_secret = get_prop('Admin', [prefix + 'consumer_key', prefix + 'consumer_secret'])
        memcache.add_multi({'consumer_key': consumer_key, 'consumer_secret': consumer_secret},
                           time=86400, key_prefix=prefix)  # 86400 seconds = 1 day
    return consumer_key, consumer_secret

def get_oauth_token_and_secret(email, service):
    """Get OAuth Token and OAuth Token Secret, along with memcache."""
    oauth_token = ''
    oauth_token_secret = ''
    oauth = memcache.get(email, namespace=service)
    if oauth is not None:
        oauth_token = oauth['oauth_token']
        oauth_token_secret = oauth['oauth_token_secret']
    else:
        oauth_token, oauth_token_secret = get_prop(service, ['oauth_token', 'oauth_token_secret'], email)
        value = {
            'oauth_token': oauth_token,
            'oauth_token_secret': oauth_token_secret
        }
        memcache.add(email, value, time=86400, namespace=service)  # 86400 seconds = 1 day
    return oauth_token, oauth_token_secret

def get_username_and_pass(email, service):
    """Get username and password, along with memcache."""
    username = ''
    password = ''
    user = memcache.get(email, namespace=service)
    if user is not None:
        username = user['username']
        password = user['password']
    else:
        username, password = get_prop(service, ['username', 'password'], email)
        value = {
            'username': username,
            'password': password
        }
        memcache.add(email, value, time=86400, namespace=service)  # 86400 seconds = 1 day
    return username, password

def get_services(email):
    """Get user's actived services."""
    services = memcache.get(email)
    if services is None:
        services = get_prop('User', ['services'], email)
        memcache.add(email, services, time=86400)  # 86400 seconds = 1 day
    return services
