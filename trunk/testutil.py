# common needs of JSON-REST-based client-side Python tests
# (intended to be run while gae-json-rest is being served at localhost:8080)!
import httplib
import optparse
import socket
import sys
import cookielib
import urllib2

import simplejson

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 8080


def body(**k):
  return simplejson.dumps(k)


def getAny(conn, classname):
  """ Returns the ID of any one existing entity of the model, or None
  """
  data = silent_request(conn, 'GET', '/%s/' % classname)
  if data: return data[0]['id']
  else: return None


class Tester(object):
  def __init__(self, f):
    self.f = f
    self.cj = cookielib.CookieJar()

    # get command-line options
    #TODO - add command line for autostarting GAE web server
    parser = optparse.OptionParser()
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="print detailed info to stdout")
    parser.add_option("-s", "--host", dest="host", default=DEFAULT_HOST,
                      help="what host the server is running on")
    parser.add_option("-p", "--port", dest="port", default=DEFAULT_PORT,
                      type="int", help="what port the server is running on")
    options, args = parser.parse_args()
    if args:
      print 'Unknown arguments:', args
      sys.exit(1)
 
    self.verbose = options.verbose
    self.host = options.host
    self.port = options.port

  def getAny(self, classname):
    """ Returns the ID of any one existing entity of the model, or None
    """
    data = silent_request(conn, 'GET', '/%s/' % classname)
    if data: return data[0]['id']
    else: return None

  def silent_request(self, verb, path, body=None):
    """ Makes an HTTP request, always silently.

        Returns the JSON-deserialized of the response body, or None.
    """
    prev = self.verbose
    self.verbose = False
    retval = self.request_and_show(verb, path, body)
    self.verbose = prev
    return retval

  def request_and_show(self, verb, path, body=None):
    """ Makes an HTTP request, optionally prints data about the interaction.

        Returns the JSON-deserialized of the response body, or None.
    """
    try:
      if body is None: self.conn.request(verb, path)
      else: self.conn.request(verb, path, body)
    except socket.error, e:
      print 'Cannot request %r %r: %s' % (verb, path, e)
      sys.exit(1)
    rl = self.conn.getresponse()
    if self.verbose or rl.status//100 != 2:
      print '%s %s gave: %s %r' % (verb, path, rl.status, rl.reason)
    if rl.status//100 == 2:
      if self.verbose:
        print 'HEADERS:'
        for h, v in rl.getheaders(): print ' ', h, v
        print 'CONTENTS:'
      body = rl.read()
      if self.verbose:
        for line in body.splitlines():
          print ' ', line
        print
      return simplejson.loads(body)
    else:
      return None

  def test_cookie(self):
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
    opener.open("http://localhost:8080")
    return [(c.name, c.value) for c in self.cj]

  def execute(self):
    try:
      self.conn = httplib.HTTPConnection(self.host, self.port, strict=True)
    except socket.error, e:
      print "Cannot connect: %s"
      sys.exit(1)
    self.f(self, self.verbose)
    print 'All done OK!'

