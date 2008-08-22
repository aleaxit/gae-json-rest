''' Json-Rest-handlin' integration helper.

This module offers a JSON+REST-handling integration class meant to be used with
Google App Engine (hooked into a webapp.RequestHandler subclass) but can in
fact be hooked up by simply passing an object with attributes self.request and
self.response that are duck-like those of webapp.RequestHandler.

On hookup, the integration-helper class overrides the get/set/put/delete
methods of the object hooking up to it so that they respond appropriately to
REST requests (as documented in json_rest.txt) based on registrations performed
in restutil, parsing and formatting JSON payloads based on jsonutil.

IOW, this helper integrates functionality found in other modules of the
gae-json-rest package:
  parsutil
  restutil
  jsonutil
"putting it all together" into a highly-reusable (but still modestly
customizable) REST-style, JSON-transport server web-app for GAE.
'''
import logging

import jsonutil
import parsutil
import restutil


class JsonRestMixin(object):

  prefix_to_ignore = '/'
  __delete_parser = __put_parser = __post_parser = __get_parser = None

  def hookup(self, handler):
    """ TODO: write method hookup! """

  def hookdown(self):
    """ TODO: write method hookdown! """

  def _serve(self, data):
    return jsonutil.send_json(self.response, data)

  def get_model(self, modelname):
    model = restutil.modelClassFromName(modelname)
    if model is None:
      self.response.set_status(400, 'Model %r not found' % modelname)
    return model

  def get_special(self, specialname):
    special = restutil.specialFromName(specialname)
    if special is None:
      self.response.set_status(400, 'Model %r not found' % modelname)
    return model

  def get_entity(self, modelname, strid):
    model = self.get_model(modelname)
    if model is None: return None
    entity = model.get_by_id(int(strid))
    if entity is None:
      self.response.set_status(404, "Entity %s/%s not found" %
                               (modelname, strird))
    return entity 

  def do_delete(self, modelname, strid, query):
    entity = self.get_entity(modelname, strid)
    if entity is not None:
      entity.delete()
    return {}

  def delete(self, prefix=None):
    """ Delete an entity given by path modelname/strid
        Response is JSON for an empty jobj.
    """
    if self.__delete_parser is None:
      self.__delete_parser = parsutil.RestUrlParser(self.prefix_to_ignore,
          do_model_strid=self.do_delete)
    path = self.request.path
    result = self.__delete_parser.process(path, prefix)
    if result is None or isintance(result, tuple):
      self.response.set_status(400, 'Invalid URL for DELETE: %r' % path)
    return self._serve(result)

  def do_put(self, modelname, strid, query):
    jobj = jsonutil.receive_json(self.request)
    jobj = jsonutil.update_entity(entity, jobj)
    updated_entity_path = "/%s/%s" % (self._classname, jobj['id'])
    self.response.set_status(200, 'Updated entity %s' % updated_entity_path)
    return jobj

  def put(self, prefix=None):
    """ Update an entity given by path modelname/strid
        Request body is JSON for the needed changes
        Response is JSON for the updated entity.
    """
    if self.__put_parser is None:
      self.__put_parser = parsutil.RestUrlParser(self.prefix_to_ignore,
          do_model_strid=self.do_put)
    path = self.request.path
    result = self.__put_parser.process(path, prefix)
    if result is None or isintance(result, tuple):
      self.response.set_status(400, 'Invalid URL for POST: %r' % path)
      return self._serve({})
    return self._serve(result)

  def do_post_special_method(self, specialname, methodname):
    """ TODO: write the various do_post_... methods! """

  def post(self, prefix=None):
    """ Create an entity ("call a model") or perform other non-R/O "call".

        Request body is JSON for the needed entity or other call "args".
        Response is JSON for the updated entity (or "call result").
    """
    if self.__post_parser is None:
      self.__post_parser = parsutil.RestUrlParser(self.prefix_to_ignore,
          do_special_method=self.do_post_special_method,
          do_model=self.do_post_model,
          do_model_method=self.do_post_model_method)
    path = self.request.path
    result = self.__post_parser.process(path, prefix)
    if result is None or isintance(result, tuple):
      self.response.set_status(400, 'Invalid URL for PUT: %r' % path)
      return self._serve({})
    try:
      strid = result['id']
    except (KeyError, TypeError):
      pass
    else:
      new_entity_path = "/%s/%s" % (self._classname, strid)
      logging.info('Post (%r) created %r', path, new_entity_path)
      self.response.headers['Location'] = new_entity_path
      self.response.set_status(201, 'Created entity %s' % new_entity_path)
    self._serve(result)


  def get(self):
    """ TODO: rewrite get! """
    """ Get JSON data for model names, entity IDs of a model, or an entity.

    Depending on the request path, serve as JSON to the response object:
    - for a path of /classname/id, a jobj for that entity
    - for a path of /classname, a list of id-only jobjs for that model
    - for a path of /, a list of all model classnames
    """
    failed, model, entity = self._get_model_and_entity(False, False)
    if failed: return
    if model is None:
      return self._serve(restutil.allModelClassNames())
    if entity is None:
      return self._serve([jsonutil.id_of(x) for x in model.all()])
    jobj = jsonutil.make_jobj(entity)
    return self._serve(jobj)

  def post(self):
    """ Create an entity of model given by path /classname.

        Request body is JSON for a jobj for a new entity (without id!).
        Response is JSON for a jobj for a newly created entity.
        Also sets HTTP Location: header to /classname/id for new entity.
    """
    failed, model, entity = self._get_model_and_entity(True, False)
    if failed: return
    if entity is not None:
      self.response.set_status(400, 'Cannot create entity with fixed ID.')
      return
    jobj = jsonutil.receive_json(self.request)
    jobj = jsonutil.make_entity(model, jobj)
    self._serve(jobj)
    new_entity_path = "/%s/%s" % (self._classname, jobj['id'])
    logging.info('Post created %r', new_entity_path)
    self.response.headers['Location'] = new_entity_path
    self.response.set_status(201, 'Created entity %s' % new_entity_path)


def main():
  application = webapp.WSGIApplication([('/.*', CrudRestHandler)],
      debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
