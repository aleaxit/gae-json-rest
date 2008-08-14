""" A very simple "smoke test" for gae-json-rest toy app. """
import simplejson
import testutil

def doTemplateTest(conn):
  # what models do we have? shd be Doctor and Pager
  print 'Getting names for Models:'
  modelnames = testutil.request_and_show(conn, 'GET', '/')
  try:
    assert set(modelnames) == set(('Doctor', 'Pager'))
  except:
    print 'modelnames is', set(modelnames)
    raise

  # do we know any Doctors?
  print 'IDs of Doctors before:'
  doctorids = testutil.request_and_show(conn, 'GET', '/Doctor/')
  # get the highest-known Doctor ID, if any, to ensure a unique number
  if doctorids:
    unique = max(int(obj['id']) for obj in doctorids) + 1
  else:
    unique = 1
  # form name based on unique number
  docname = 'Dr. John %s' % unique
  # make entity with that name
  body = testutil.body(name=docname)
  testutil.request_and_show(conn, 'POST', '/Doctor/', body)
  print 'IDs of Doctors after:'
  testutil.request_and_show(conn, 'GET', '/Doctor/')

  testutil.request_and_show(conn, 'PUT', '/Doctor/1', body)
  print 'IDs of Doctors after:'
  testutil.request_and_show(conn, 'GET', '/Doctor/')


testutil.main(doTemplateTest)
