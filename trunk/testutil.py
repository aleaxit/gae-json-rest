# common needs of JSON-REST-based client-side Python tests
# (intended to be run while gae-json-rest is being served at localhost:8080)!
import httplib
import simplejson

HOST = 'localhost'
PORT = 8080


def body(**k):
    return simplejson.dumps(k)


def getAny(conn, classname):
    """ Returns the ID of any one existing entity of the model, or None
    """
    data = silent_request(conn, 'GET', '/%s/' % classname)
    if data: return data[0]['id']
    else: return None


def silent_request(conn, verb, path, body=None):
    """ Returns the JSON-deserialized of the response body, or None
    """
    if body is None: conn.request(verb, path)
    else: conn.request(verb, path, body)
    rl = conn.getresponse()
    if rl.status//100 != 2: return None
    return simplejson.loads(rl.read())


def request_and_show(conn, verb, path, body=None):
    """ Makes an HTTP request, prints data about the interaction.
    """
    if body is None: conn.request(verb, path)
    else: conn.request(verb, path, body)
    rl = conn.getresponse()
    print '%s %s gave: %s %r' % (verb, path, rl.status, rl.reason)
    if rl.status//100 == 2:
        print 'HEADERS:'
        for h, v in rl.getheaders(): print ' ', h, v
        print 'CONTENTS:'
        body = rl.read()
        for line in body.splitlines():
            print ' ', line
        print
        return simplejson.loads(body)
    else:
        return None


def main(f, host=HOST, port=PORT):
    conn = httplib.HTTPConnection(host, port, strict=True)
    f(conn)
    print 'All done!'

