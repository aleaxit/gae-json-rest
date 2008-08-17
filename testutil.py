# common needs of JSON-REST-based client-side Python tests
# (intended to be run while gae-json-rest is being served at localhost:8080)!
import httplib
import optparse
import socket
import sys

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


def silent_request(conn, verb, path, body=None):
  """ Makes an HTTP request, always silently.

      Returns the JSON-deserialized of the response body, or None.
  """
  return request_and_show(conn, verb, path, False, body)


def request_and_show(conn, verb, path, verbose, body=None):
  """ Makes an HTTP request, optionally prints data about the interaction.

      Returns the JSON-deserialized of the response body, or None.
  """
  try:
    if body is None: conn.request(verb, path)
    else: conn.request(verb, path, body)
  except socket.error, e:
    print 'Cannot request %r %r: %s' % (verb, path, e)
    sys.exit(1)
  rl = conn.getresponse()
  if verbose or rl.status//100 != 2:
    print '%s %s gave: %s %r' % (verb, path, rl.status, rl.reason)
  if rl.status//100 == 2:
    if verbose:
      print 'HEADERS:'
      for h, v in rl.getheaders(): print ' ', h, v
      print 'CONTENTS:'
    body = rl.read()
    if verbose:
      for line in body.splitlines():
        print ' ', line
      print
    return simplejson.loads(body)
  else:
    return None


def main(f):
  # get command-line options
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
  try:
    conn = httplib.HTTPConnection(options.host, options.port, strict=True)
  except socket.error, e:
    print "Cannot connect: %s"
    sys.exit(1)
  f(conn, options.verbose)
  print 'All done OK!'

