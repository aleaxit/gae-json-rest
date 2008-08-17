''' Cookie-handlin' request handler; inspired by WebOb.

Meant to be used with Google App Engine.
'''
# Copyright (C) 2008 aleaxit@gmail.com
# licensed under CC-by license, http://creativecommons.org/licenses/by/3.0/

import Cookie
import datetime
import time

from google.appengine.ext import webapp


def _serialize_cookie_date(dt):
    if dt is None:
        return None
    if isinstance(dt, unicode):
        dt = dt.encode('ascii')
    if isinstance(dt, datetime.timedelta):
        dt = datetime.datetime.now() + dt
    if isinstance(dt, (datetime.datetime, datetime.date)):
        dt = dt.timetuple()
    return time.strftime('%a, %d-%b-%Y %H:%M:%S GMT', dt)


class CookieHandler(webapp.RequestHandler):

  def get_cookie(self, key, default_value=None):
    return self.request.cookies.get(key, default_value)

  def set_cookie(self, key, value='', max_age=None,
       path='/', domain=None, secure=None, httponly=False,
       version=None, comment=None, expires=None):
    """ Set (add) a cookie to the response object. """
    if isinstance(value, unicode):  #and self.charset is not None:
        value = '"%s"' % value.encode('utf9') #self.charset)
    cookies = Cookie.BaseCookie()
    cookies[key] = value
    if isinstance(max_age, datetime.timedelta):
        max_age = datetime.timedelta.seconds + datetime.timedelta.days*24*60*60
    if max_age is not None and expires is None:
        expires = datetime.datetime.utcnow() + \
                  datetime.timedelta(seconds=max_age)
    if isinstance(expires, datetime.timedelta):
        expires = datetime.datetime.utcnow() + expires
    if isinstance(expires, datetime.datetime):
        expires = '"'+_serialize_cookie_date(expires)+'"'
    for var_name, var_value in [
        ('max_age', max_age),
        ('path', path),
        ('domain', domain),
        ('secure', secure),
        ('HttpOnly', httponly),
        ('version', version),
        ('comment', comment),
        ('expires', expires),
        ]:
        if var_value is not None and var_value is not False:
            cookies[key][var_name.replace('_', '-')] = str(var_value)
    header_value = cookies[key].output(header='').lstrip()
    self.response.headers.add_header('Set-Cookie', header_value)

  def delete_cookie(self, key, path='/', domain=None):
      """ Delete a cookie from the client.
      
      Path and domain must match how the cookie was originally set.  This method
      sets the cookie to the empty string, and max_age=0 so that it should 
      expire immediately.
      """
      self.set_cookie(key, '', path=path, domain=domain,
                      max_age=0, expires=timedelta(days=-5))

  def unset_cookie(self, key):
      """ Unset a cookie with the given name (remove from the response).
      
      If there are multiple cookies (e.g., two cookies with the same name and
      different paths or domains), all such cookies will be deleted.
      """
      existing = self.response.headers.getall('Set-Cookie')
      if not existing:
          raise KeyError(
              "No cookies at all have been set")
      del self.headers['Set-Cookie']
      found = False
      for header in existing:
        cookies = BaseCookie()
        cookies.load(header)
        if key in cookies:
          found = True
          del cookies[key]
          header = cookies.output(header='').lstrip()
        if header:
          self.response,headers.add_header('Set-Cookie', header)
      if not found:
          raise KeyError(
              "No cookie has been set with the name %r" % key)


