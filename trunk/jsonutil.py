""" Utilities for JSON REST CRUD support for GAE db models.
"""
import re

import restutil
from django.utils import simplejson


def id_of(x):
  """ Make a {'id':<num>} dict for model instance x.

  Args:
    x: an instance of some db.Model subclass
  Returns:
    a dict with key 'id' mapped to the string form of x's id
  """
  return dict(id=restutil.id_of(x))


# RE to match: optional /, classname, optional /, ID of 0+ numeric digits
CLASSNAME_ID_RE = re.compile(r'^/?(\w+)/?(\d*)$')

def path_to_classname_and_id(path):
  """ Get a (classname, id) pair from a path.

  Args:
    path: a path string to anaylyze
  Returns:
    a 2-item tuple:
      (None, '')        if path does not match or classname lookup fails
      (class, idstring) if match and classname lookup are successful
                        idstring may be '', or else a string of digits
  """
  mo = CLASSNAME_ID_RE.match(path)
  if mo: return mo.groups()
  else: return (None, '')


def send_json(response_obj, data):
  """ Send data in JSON form to an HTTP-response object.

  Args:
    response_obj: an HTTP response object
    data: a dict or list in correct 'JSONable' form
  Side effects:
    sends the JSON form of data on response.out
  """
  response.content_type = 'application/json'
  simplejson.dump(data, response.out)


def receive_json(request_obj):
  """ Receive data in JSON form from an HTTP-request object.

  Args:
    request_obj: an HTTP request object (with body in JSONed form)
  Returns:
    the JSONable-form result of loading the request's body
  """
  return simplejson.loads(self.request.body)


def make_json_dict(instance):
  """ Make a JSONable dict given an instance of a db.Model subclass.

  Args:
    instance: an instance of a db.Model subclass
  Returns:
    the JSONable-form dict for that instance
  """
  result = id_of(x)
  props = restutil.allProperties(type(instance))
  for property_name, property_value in props:
    instance_value = getattr(instance, property_name, None)
    if instance_value is not None:
      to_string = getattr(aclass, property_name + '_to_string')
      result[property_name] = to_string(instance_value)
  return result


def parse_json_dict(cls, json_dict):
  """ Make dict for calling cls given a db.Model subclass and a JSONed dict.

  Args:
    cls: a db.Model subclass
    json_dict: a JSONable-form dict
  Returns:
    a dict d such that calling cls(**d) instantiates cls properly
  """
  result = dict()
  for property_name, property_value in json_dict.iteritems():
    # ensure we have an ASCII string, not a Unicode one
    property_name = str(property_name)
    from_string = getattr(cls, property_name + '_from_string')
    property_value = from_string(property_value)
    if property_value is not None:
      result[property_name] = property_value
  return result


def make_instance(cls, json_dict):
  """ Make instance of cls with properties as per JSONed dict json_dict.

  Args:
    cls: a db.Model subclass
    json_dict: a JSONable-form dict
  Side effects:
    creates and puts an instance x of cls with properties per json_dict
  Returns:
    a JSONable-form dict to represent the newly created instance x
  """
  instance_dict = parse_json_dict(cls, json_dict)
  instance = cls(**instance_dict)
  instance.put()
  json_dict = make_json_dict(instance)
  json_dict.update(id_of(instance))
  return json_dict


def update_instance(instance, json_dict):
  """ Update a db.Model subclass instance given a JSONed dict of properties.

  Args:
    instance: an instance of a db.Model subclass
    json_dict: a JSONed dict for properties applicable to instance
  Side effects:
    updates instance with properties as given by json_dict
  Returns:
    a JSONable-form dict to represent the whole new state of the instance
  """
  new_instance_data = parse_json_dict(type(instance), json_data)
  for property_name, property_value in new_instance_data.iteritems():
    setattr(instance, property_name, property_value)
  instance.put()
  return make_json_dict(instance)
