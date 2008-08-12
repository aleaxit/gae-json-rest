import wsgiref.handlers
from google.appengine.ext import webapp
import models
import jsonutil
import restutil


# TODO: post, put, delete, queries, and MUCH better error-handling!-)

class CrudRestHandler(webapp.RequestHandler):

  def _serve(self, data):
    return jsonutil.send_json(self.response, data)

  def get(self):
    classname, strid = jsonutil.path_to_classname_and_id(self.request.path))
    if not classname:
      return self._serve(restutil.allModelClassNames())
    cls = restutil.modelClassFromName(classname)
    if not strid:
      return self._serve([jsonutil.id_of(x) for x in cls.all()])
    numid = int(strid)
    instance = cls.get_by_id(numid)
    json_dict = jsonutil.make_json_dict(cls, instance)
    return self._serve(json_dict)


def main():
  application = webapp.WSGIApplication([('/', CrudRestHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
