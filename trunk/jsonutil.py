""" Utilities for JSON REST CRUD support for GAE db models.
"""
import logging
import re

import restutil
from django.utils import simplejson


def id_of(x):
  """ Make a {'id':<num>} dict for model instance x. """
  return dict(id=restutil.id_of(x))


# RE to match a classname, optionally followed by / and an ID of 0+ numeric digits
CLASSNAME_ID_RE = re.compile(r'^/?(\w+)/?(\d*)$')

def path_to_classname_and_id(path):
  """ Get a (classname, id) pair from a path (id empty-string if absent from the path) or (None, ''). """
  mo = CLASSNAME_ID_RE.match(path)
  if mo: return mo.groups()
  else: return (None, '')


def send_json(response_obj, data):
  """ Send data in JSON form to an HTTP-response object. """
  response.content_type = 'application/json'
  simplejson.dump(data, response.out)


def receive_json(request_obj):
  """ Receive data in JSON form from an HTTP-request object."""
  return simplejson.loads(self.request.body)


def make_json_dict(cls, instance):
  """ Make a dict suitable for send_json given a db.Model subclass and an instance thereof. """
  result = id_of(x)
  props = restutil.allProperties(cls)
  for property_name, property_value in props:
    instance_value = getattr(instance, property_name, None)
    if instance_value is not None:
      to_string = getattr(aclass, property_name + '_to_string')
      result[property_name] = to_string(instance_value)
  return result


def parse_json_dict(cls, json_dict):
   """ Make a dict suitable for calling cls given a db.Model subclass and a JSON-form dict."""
   result = dict()
   for property_name, property_value in json_dict.iteritems():
     # make sure we have an ASCII string, not a Unicode one
     property_name = str(property_name)
     from_string = getattr(classobj, property_name+'_from_string')
     property_value = from_string(property_value)
     if property_value is not None:
       result[property_name] = property_value
   return result


def make_instance(cls, json_data):
  """ Make a db.Model subclass instance given the class object and a JSON-form dict, return new JSON-form dict. """
  instance_data = parse_json_dict(cls, json_data)
  instance = cls(**instance_data)
  key = instance.put()
  json_data = make_json_dict(cls, instance)
  json_data.update(id_of(instance))
  return json_data


def update_instance(cls, instance, json_data):
  """ Update a db.Model subclass instance given class, instance, and a JSON-form dict, return new JSON-form dict. """
  new_instance_data = parse_json_dict(cls, json_data)
  for property_name, property_value in new_instance_data.iteritems():
    setattr(instance, property_name, property_value)
  instance.put()
  return make_json_dict(cls, instance)


