import django.conf.urls.defaults as d
import pprint as pp
import logging
import re

class URLHandlerMixin(object):
  """ This class is designed to be mixed in with a WSGI app request handler.
      
      register_patterns should be called with the appropriate regexes that 
      need to handled by the particular handler this class is mixed-in with.
  """
  
  def register_patterns(*args):
    self.patterns = d.patterns(*args)
  
  def resolve(self, re, path):
    for pattern in patterns:
      m = pattern.resolve(path)
      if m:
        return m
      return None
