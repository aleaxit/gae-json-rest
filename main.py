#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import wsgiref.handlers
from google.appengine.ext import webapp
import models
import restutil


class RestHandler(webapp.RequestHandler):

  def serve(self, stuff):
    self.response.content_type = 'text/plain'
    self.response.out.write(str(stuff))


  def get(self):
    path = self.request.path.strip('/')
    if not path:
      self.serve(restutil.allModelClassNames())
    else:
      cls = restutil.modelClassFromName(path)
      if cls is None:
        self.serve('No class named %r' % path)
      else:
        objs = cls.get_all()
        n = len(objs)
        self.serve('%s object%s of class %r' % (n, 's'[n==1:]))

def main():
  application = webapp.WSGIApplication([('/', RestHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
