''' Json-Rest-handlin' integration mix-in helper.

This module offers a JSON+REST-handling integration mixin class meant to be
used with Google App Engine (mixed into a webapp.RequestHandler subclass) but
can in fact be mixed into any class offering:
  - a self.request object offering:
    ...
  - a self.response object offering:
    ...

To customize the mixin's behavior, the subclass that mixes it in may/should:
  - define prefix_to_ignore as a regex pattern _without_ named groups
    if the URLs to analize are supposed start with such a prefix to
    be ignored (default is / -- no prefix is either expected or ignored)

The mixin class supplies methods to:
  - parse a REST url with parsutil, dispatching appropriately to...
  - ... get/set/put/delete methods that respond appropriately to
        such REST requests (as documented in json_rest.txt) based
        on registrations performed in restutil, parsing and
        formatting JSON payloads based on jsonutil
IOW, this mixin integrates functionaity found in other modules of
the gae-json-rest package:
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

  def _serve(self, data):
    return jsonutil.send_json(self.response, data)

  def do_delete(self, modelname, strid):
    entity = self.get_entity(modelname, strid)
    if entity is not None:
      entity.delete()
    return ''

  def delete(self):
    """ Delete an entity of model given by path /classname/id.
        Response is JSON for an empty jobj.
    """
    if self.__delete_parser is None:
      self.__delete_parser = parsutil.RestUrlParser(self.prefix_to_ignore,
          do_model_strid=self.do_delete)
    path = self.request.path
    result = self.__delete_parser.process(path)
    if result is None or isintance(result, tuple):
      self.response.set_status(400, 'Invalid URL for DELETE: %r' % path)
    self._serve({})

# TODO(aleax): keep writing this...!

  def _get_model_and_entity(self, need_model, need_id):
    """ Analyze self.request.path to get model and entity.

    Args:
      need_model: bool: if True, fail if classname is missing
      need_id: bool: if True, fail if ID is missing

    Returns 3-item tuple:
      failed: bool: True iff has failed
      model: class object or None
      entity: instance of model or None
    """
    classname, strid = jsonutil.path_to_classname_and_id(self.request.path)
    self._classname = classname
    if not classname:
      if need_model:
        self.response.set_status(400, 'Cannot do it without a model.')
      return need_model, None, None
    model = restutil.modelClassFromName(classname)
    if model is None:
      self.response.set_status(400, 'Model %r not found' % classname)
      return True, None, None
    if not strid:
      if need_id:
        self.response.set_status(400, 'Cannot do it without an ID.')
      return need_id, model, None
    try:
      numid = int(strid)
    except TypeError:
      self.response.set_status(400, 'ID %r is not numeric.' % strid)
      return True, model, None
    else:
      entity = model.get_by_id(numid)
      if entity is None:
        self.response.set_status(404, "Entity %s not found" % self.request.path)
        return True, model, None
    return False, model, entity
 
  def get(self):
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

  def put(self):
    """ Update an entity of model given by path /classname/id.

        Request body is JSON for a jobj for an existing entity.
        Response is JSON for a jobj for the updated entity.
    """
    failed, model, entity = self._get_model_and_entity(True, True)
    if failed: return
    jobj = jsonutil.receive_json(self.request)
    jobj = jsonutil.update_entity(entity, jobj)
    self._serve(jobj)
    updated_entity_path = "/%s/%s" % (self._classname, jobj['id'])
    self.response.set_status(200, 'Updated entity %s' % updated_entity_path)


def main():
  application = webapp.WSGIApplication([('/.*', CrudRestHandler)],
      debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
