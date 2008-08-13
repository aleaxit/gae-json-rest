import wsgiref.handlers
from google.appengine.ext import webapp
import models
import jsonutil
import restutil


# TODO: put, delete, queries, and MUCH better error-handling!-)

class CrudRestHandler(webapp.RequestHandler):

  def _serve(self, data):
    return jsonutil.send_json(self.response, data)

  def get(self):
    """ Get JSON data for model names, entity IDs of a model, or an entity.

    Depending on the request path, serve as JSON to the response object:
    - for a path of /classname/id, a jobj for that entity
    - for a path of /classname, a list of id-only jobjs for that model
    - for a path of /, a list of all model classnames
    """
    classname, strid = jsonutil.path_to_classname_and_id(self.request.path)
    if not classname:
        return self._serve(restutil.allModelClassNames())
    model = restutil.modelClassFromName(classname)
    if model is None:
        self.response.set_status(400, 'Model %r not found' % classname)
        return
    if not strid:
        return self._serve([jsonutil.id_of(x) for x in model.all()])
    numid = int(strid)
    entity = model.get_by_id(numid)
    jobj = jsonutil.make_jobj(entity)
    return self._serve(jobj)

  def post(self):
    """ Create an entity of model given by path /classname.

        Request body is JSON for a jobj for a new entity (without id!).
        Response is JSON for a jobj for a newly created entity.
        Also sets HTTP Location: header to /classname/id for new entity.
    """
    classname, strid = jsonutil.path_to_classname_and_id(self.request.path)
    if strid:
        self.response.set_status(400, 'Cannot create entity with fixed ID.')
        return
    if not classname:
        self.response.set_status(400, 'Cannot create entity without model.')
        return
    model = restutil.modelClassFromName(classname)
    if model is None:
        self.response.set_status(400, 'Model %r not found' % classname)
        return
    jobj = jsonutil.receive_json(self.request)
    jobj = jsonutil.make_entity(model, jobj)
    self._serve(jobj)
    new_entity_path = "/%s/%s" % (classname, jobj['id'])
    self.response.headers['Location'] = new_entity_path
    self.response.set_status(201, 'Created entity %s' % new_entity_path)


def main():
  application = webapp.WSGIApplication([('/.*', CrudRestHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
