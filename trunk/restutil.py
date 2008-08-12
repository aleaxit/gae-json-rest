""" Utilities for REST CRUD support for GAE db models.
"""
import datetime
import inspect
import logging
import sys

from google.appengine.ext import db
from google.appengine.api import users


def isProperty(x):
  """ Is class attribute x a 'real' property (not a reverse reference)?

  Args:
    x: a class attribute (from some db.Model subclass)
  Returns:
    True iff x's type is that of a "real" property (not a rev.ref.)
  """
  return isinstance(x, db.Property
         ) and not isinstance(x, db._ReverseReferenceProperty)


model_class_registry = dict()

def registerClassByName(cls, name=None):
  """ Register a db.Model subclass with the given name (def. its own name). """
  if name is None: name = cls.__name__
  if name in model_class_registry:
    raise KeyError, 'Duplicate name %r for model class registry' % name
  model_class_registry[name] = cls

def isModelClass(x):
  """ Is object x a subclass of db.Model?

  Args:
    x: any
  Returns:
    true iff x is a subclass of db.Model
"""
  try: return issubclass(x, db.Model)
  except TypeError: return False

def registerAllModelClasses(module_obj):
  """ Register non-private db.Model subclasses from the given module object. """
  for name, cls in inspect.getmembers(module_obj, isModelClass):
    if name[0] != '_':
      registerClassByName(cls, name)

def registerAllModelClassesFromModuleNamed(module_name):
  """ Register all db.Model subclasses from module w/given name. """
  registerAllModelClasses(__import__(module_name))

def modelClassFromName(classname):
  """ Get the db.Model subclass with the given name (None if none).

  Only handles db.Model subclasses enregistered into model_class_registry.

  Args:
    classname: a string that should name a db.Model subclass
  Returns:
    class object with that name, or None if there's no such class
  """
  return model_class_registry.get(classname)

def allModelClassNames():
  """ Return a list of strings, all model class names in registry. """
  return sorted(model_class_registry)


def modelInstanceByClassAndId(s):
  """ Get a model instance given its class name and numeric ID, or None.

      Args:
        s: str of the form 'Classname/1234'
      Returns:
        model instance from the class of that name, with that ID (or None)
  """
  classname, theid = s.split('/')
  theclass = modelClassFromName(classname)
  if theclass is None: return None
  return theclass.get_by_id(int(theid))

def classAndIdFromModelInstance(x, classname=None):
  """ Get a string with class name and numeric ID given a model instance.

      Args:
        x: a model instance or None
      Returns:
        str of the form 'Classname/1234' (or None if x is None)
  """
  if x is None: return None
  if classname is None: classname = type(x).__name__
  theclass = modelClassFromName(classname)
  if theclass is not type(x): return None
  theid = x.key().id()
  return '%s/%s' % (classname, theid)


DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def datetimeFromString(s):
  """ Get a datetime object given a str ('right now' for empty str).

  As per appengine convention, all datetime objs must be UTC.

      Args:
        s: str in DATETIME_FORMAT or ''
      Returns:
        appropriate datetime object
  """
  if s:
    return datetime.datetime.strptime(s, DATETIME_FORMAT)
  else:
    return datetime.datetime.now()


def stringFromDatetime(dt):
  """ Get an appropriately formatted str given a datetime object.

      Args:
        dt: datetime instance
      Returns:
        str formatted as per DATETIME_FORMAT
  """
  return dt.strftime(DATETIME_FORMAT)


# mapping from property types to appropriate str->value function if any
# property types not in the mapping must accept a properly formatted str
setter_registry = {
  db.BooleanProperty: 'False'.__ne__,
  db.DateTimeProperty: staticmethod(datetimeFromString),
  db.IntegerProperty: int,
  db.FloatProperty: float,
  db.ReferenceProperty: staticmethod(modelInstanceByClassAndId),
  db.StringListProperty: str.split,
  db.UserProperty: users.User,
}

# mapping from property types to appropriate value->str function if any
# str(value) is used for property types that are not in the mapping
getter_registry = {
  db.DateTimeProperty: staticmethod(stringFromDatetime),
  db.ReferenceProperty: staticmethod(classAndIdFromModelInstance),
  db.StringListProperty: ' '.join,
}

def allProperties(cls):
  """ Get all (name, value) pairs of properties given a db.Model subclass.

      Args:
        cls: a class object (a db.Model subclass)
      Returns:
        list of (name, value) pairs of properties of that class
  """
  return inspect.getmembers(cls, isProperty)


def addHelperMethods(cls):
  """ Add _from_string and _to_string methods to a db.Model subclass.

      Args:
        cls: a class object (db.Model subclass), adds methods to it.
  """
  props = allProperties(cls)
  for name, value in props:
    fs_name = name + '_from_string'
    ts_name = name + '_to_string'
    if not hasattr(cls, fs_name):
      setter = setter_registry.get(type(value))
      if setter is not None: setattr(cls, fs_name, setter)
    if not hasattr(cls, ts_name):
      getter = getter_registry.get(type(value))
      if getter is not None: setattr(cls, ts_name, getter)

def decorateModuleNamed(module_name):
  """ Do all needed work for non-private model classes in module thus named. """
  module_obj = __import__(module_name)
  for name, cls in inspect.getmembers(module_obj, isModelClass):
    if name[0] != '_':
      registerClassByName(cls, name)
      addHelperMethods(cls)
