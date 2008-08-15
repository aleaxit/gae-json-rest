""" Utilities for URL parsing for REST applications (esp. for GAE).

The general format of URL paths that this module knows how to parse is as
follows (with ?  following each optional component):

<prefix-ignored>/$?<model>/?<numeric_id>?/?<method>?<parameters>?

The <prefix-ignored> part of the URL path defaults to empty, but is often
changed (at program start-up, right after 'import urlxutil') by calling
urlxutil.set_prefix_ignored('/some/re/pattern').

The optional $ right before the model identifier, if present, means that we're
dealing with a 'pseudo-model' (not simple CRUD REST functionality, but rather
various kinds of 'method calls' -- meant for GET and POST only).

<model>, is the published name of a db.Model subclass (see restutil.py for the
way to "publish", aka "register", a name for such a subclass).

<numeric_id>, if present, is the numeric ID of an existing entity of the
specified <model> -- NOT supported for POST (except if a method is also
present), mandatory for PUT and DELETE

<method>, if present, is the published name of a 'method' of the given model or
entity (see restutil.py for the way to "publish", aka "register", a name for a
method of a model or entity); not supported for PUT and DELETE, mandatory for
POST if a <numeric_id> is present; some methods may support only GET, others may
support only POST, others yet may support both.

<parameters>, if present, are a URL "query string": starting with a question
mark, followed by 0 or more <name>=<value> pairs separated by &.
"""
import cgi
import re

def set_prefix_ignored(igno_re):
  """ Rebuild the parse_re by changing the ignored prefix.

  Args:
    igno_re: a str that's a RE pattern (NOT a re object) for ignored-prefix.
             (if you need to ignore a constant string prefix, re.escape it!)
  Returns:
    the RE object suitable for parsing
  """
  return re.compile(r'%s/(\$?\w+)/?(\d*)/?(\w*)(\?.*)?' % igno_re)

parse_re = set_prefix_ignored('')

def parse_path(path):
  """ Match the path with the parse_re to extract the various parts.

  Args:
    path: str, the URL path to parse (leading / to the bitter end)
  Returns:
    tuple with 4 items -- if the match has succeeded, the items are:
      model-identifier  (may start with $, then 1+ word characters)
      id-digits         (0+ decimal digits)
      method-identifier (0+ word characters)
      parsed-query      (0+ name-value pairs for the querystring, if any)
   if the match has failed, the items are 3 '' empty strings + 1 empty list
  """
  mo = parse_re.match(path)
  if not mo:
    return '', '', '', []
  querystring = mo.group(4)
  if querystring:
    return mo.group(1, 2, 3) + (cgi.parse_qsl(querystring[1:]),)
  else:
    return mo.groups([])

