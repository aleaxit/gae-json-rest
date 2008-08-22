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


class JsonRestHelper(object):

  prefix_to_ignore = '/'
  __delete_parser = __put_parser = __post_parser = __get_parser = None

  def hookup(self, handler):
    """ "Hooks up" this helper to a handler object.

    Args:
      handler: an instance of a webapp.RequestHandler subclass
    Side effects:
      - sets self.request and self.response from the handler,
      - sets self.handler to handler
      - sets the handler's get, put, post and delete methods from self
      - sets the handler's jrh attribute to self
    Note this creates reference loops and MUST be undone in hookdown!
    """
    self.request = handler.request
    self.response = handler.response
    self.handler = handler
    handler.get = self.get
    handler.put = self.put
    handler.post = self.post
    handler.delete = self.delete
    handler.jrh = self
        
  def hookdown(self):
    """ Undoes the effects of self.hookup """
    h = self.handler
    h.jrh = self.request = self.response = self.handler = None
    del h.get, h.put, h.post, h.delete

  def _serve(self, data):
    """ Serves a result in JSON, and hooks-down from the handler """
    try: return jsonutil.send_json(self.response, data)
    finally: self.hookdown()

  def get_model(self, modelname):
    """ Gets a model (or None) given a model name.

    Args:
      modelname: a string that should name a model
    Returns:
      a model class, or None (if no model's registered with that name)
    Side effects:
      sets response status to 400 if no model's registered with that name
    """
    model = restutil.modelClassFromName(modelname)
    if model is None:
      self.response.set_status(400, 'Model %r not found' % modelname)
    return model

  def get_special(self, specialname):
    """ Gets a special (or None) given a special name.

    Args:
      specialname: a string that should name a special
    Returns:
      a special object, or None (if no special's registered with that name)
    Side effects:
      sets response status to 400 if no special's registered with that name
    """
    special = restutil.specialFromName(specialname)
    if special is None:
      self.response.set_status(400, 'Model %r not found' % specialname)
    return special

  def get_entity(self, modelname, strid):
    """ Gets an entity (or None) given a model name and entity ID as string.

    Args:
      modelname: a string that should name a model
      strid: the str(id) for the numeric id of an entity of that model
    Returns:
      an entity, or None (if something went wrong)
    Side effects:
      sets response status to 400 or 404 if various things went wrong
    """
    model = self.get_model(modelname)
    if model is None:
      return None
    entity = model.get_by_id(int(strid))
    if entity is None:
      self.response.set_status(404, "Entity %s/%s not found" %
                               (modelname, strird))
    return entity 

  def get_special_method(self, specialname, methodname):
    special = self.get_special(specialname)
    if special is None: return ''
    method = special.get(methodname)
    if method is None: 
      self.response.set_status(400, 'Method %r not found in special' % (
        methodname, specialname))
    return method

  def _methodhelper(self, modelname, methodname, _getter):
    """ Gets a model or instance method given model and method names & getter.

    Args:
      modelname: a string that should name a model
      methodname: a sring that should name a method of that model
    Returns:
      a method object, or None if either model or method were not found
    Side effects:
      sets response status to 400 if either model or method were not found
    """
    model = self.get_model(modelname)
    if model is None: return ''
    method = _getter(model, methodname)
    if method is None: 
      self.response.set_status(400, 'Method %r not found in model' % (
        methodname, modelname))
    return method

  def get_model_method(self, modelname, methodname):
    """ Gets a model's method given model and method names.

    Args:
      modelname: a string that should name a model
      methodname: a sring that should name a method of that model
    Returns:
      a method object, or None if either model or method were not found
    Side effects:
      sets response status to 400 if either model or method were not found
    """
    return self._methodhelper(model, methodname, restutil.modelMethodByName)

  def get_instance_method(self, modelname, methodname):
    """ Gets an instance method given model and method names.

    Args:
      modelname: a string that should name a model
      methodname: a sring that should name an instance method of that model
    Returns:
      a method object, or None if either model or method were not found
    Side effects:
      sets response status to 400 if either model or method were not found
    """
    return self._methodhelper(model, methodname, restutil.instanceMethodByName)


  def do_delete(self, modelname, strid, query):
    """ Hook method to delete an entity given modelname, strid & query.

        This version actually ignores the query string.
    """
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
    if result is None or isinstance(result, tuple):
      self.response.set_status(400, 'Invalid URL for DELETE: %r' % path)
    return self._serve(result)

  def do_put(self, modelname, strid, query):
    """ Hook method to update an entity given modelname, strid & query.

        This version actually ignores the query string.
    """
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
    if result is None or isinstance(result, tuple):
      self.response.set_status(400, 'Invalid URL for POST: %r' % path)
      return self._serve({})
    return self._serve(result)

  def do_post_special_method(self, specialname, methodname, query):
    """ Hook method to call a method on a special object given names.

        This version actually ignores the query string.
    """
    method = self.get_special_method(specialname, methodname)
    if special is None: return ''
    try: return method()
    except Exception, e:
      self.response.set_status(400, "Can't call %r/%r: %s" % (
        specialname, methodname, e))
      return ''

  def do_post_model(self, modelname, query):
    """ Hook method to "call a model" (to create an entity)

        This version actually ignores the query string.
    """
    model = self.get_model(modelname)
    if model is None: return ''
    # TODO: complete this!

  def do_post_model_method(self, modelname, methodname, query):
    """ Hook method to call a method on a model given names.

        This version actually ignores the query string.
    """
    method = self.get_model_method(modelname, methodname)
    if method is None: return ''
    try: return method()
    except Exception, e:
      self.response.set_status(400, "Can't call %r/%r: %s" % (
        modelname, methodname, e))
      return ''

  def do_post_entity_method(self, modelname, strid, methodname, query):
    """ Hook method to call a method on an entity given names and strid.

        This version actually ignores the query string.
    """
    method = self.get_instance_method(modelname, methodname)
    if method is None: return ''
    entity = self.get_entity(modelname, strid)
    if entity is None: return ''
    try: return method(entity)
    except Exception, e:
      self.response.set_status(400, "Can't call %r/%r/%r: %s" % (
        modelname, strid, methodname, e))
      return ''

  def post(self, prefix=None):
    """ Create an entity ("call a model") or perform other non-R/O "call".

        Request body is JSON for the needed entity or other call "args".
        Response is JSON for the updated entity (or "call result").
    """
    # TODO: fix post's body!
    if self.__post_parser is None:
      self.__post_parser = parsutil.RestUrlParser(self.prefix_to_ignore,
          do_special_method=self.do_post_special_method,
          do_model=self.do_post_model,
          do_model_method=self.do_post_model_method,
          do_model_strid_method=self.do_post_entity_method,
          )
    path = self.request.path
    result = self.__post_parser.process(path, prefix)
    if result is None or isinstance(result, tuple):
      self.response.set_status(400, 'Invalid URL for POST: %r' % path)
      return self._serve({})
    try:
      strid = result['id']
    except (KeyError, AttributeError, TypeError):
      pass
    else:
      new_entity_path = "/%s/%s" % (self._classname, strid)
      logging.info('Post (%r) created %r', path, new_entity_path)
      self.response.headers['Location'] = new_entity_path
      self.response.set_status(201, 'Created entity %s' % new_entity_path)
    return self._serve(result)


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
