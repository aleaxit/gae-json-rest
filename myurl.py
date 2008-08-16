import logging
import re

class URLHandler(object):
  """ This class can invoke a method depending on what URL was requested.
      
      Call register_patterns from the constructor with appropriate 
      (regex, callback) args that need to be handled by the particular handler.
  """
  
  def __init__(self, prefix, *args):
    """ Takes a prefix to be ignored and a list of (regex, callback) args.
    """
    self.callbacks = dict()
    for arg in args:
      self.callbacks[re.compile(r'%s%s' % (prefix, arg[0]))] = arg[1]

  def process(self, path):
    """ Match the path to one of the regexs and call the appropriate callback.
    """
    for r in self.callbacks.keys():
      mo = r.match(path)
      if mo:
        self.callbacks[r]()


if __name__ == '__main__':
  def index():
    print "inside index"

  def hello():
    print "inside hello"

  handler = URLHandler('', ('/', index), ('/hello', hello))
  handler.process('/hello')
