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
  print 'IDs of Doctors before any operations:'
  doctorids = testutil.request_and_show(conn, 'GET', '/Doctor/')
  # get the highest-known Doctor ID, if any, to ensure a unique number
  if doctorids:
    unique = max(int(obj['id']) for obj in doctorids) + 1
  else:
    unique = 1
  # now, we want to delete about half the doctors we know
  for i in range(0, len(doctorids), 2):
    strid = doctorids[i]['id']
    testutil.silent_request(conn, 'DELETE', '/Doctor/%s' % strid)
  print 'IDs of Doctors after some deletions:'
  doctorids = testutil.silent_request(conn, 'GET', '/Doctor/')
  print doctorids

  # form name based on unique number
  docname = 'Dr. John %s' % unique
  # make entity with that name
  post_body = testutil.body(name=docname)
  post_result = testutil.request_and_show(conn, 'POST', '/Doctor/', post_body)
  new_doctor_id = post_result['id']
  new_doctor_path = '/Doctor/%s' % new_doctor_id
  print 'Created %r' % new_doctor_path
  # show new doctor just created
  print 'New Doctor just created:'
  testutil.request_and_show(conn, 'GET', new_doctor_path)
  # show IDs after the POST
  print 'IDs of Doctors after POST:'
  testutil.request_and_show(conn, 'GET', '/Doctor/')

  # Now change the name of the doctor
  docname = '%s changed' % docname
  put_body = testutil.body(name=docname)
  testutil.request_and_show(conn, 'PUT', new_doctor_path, put_body)
  # show new doctor just changed
  print 'New Doctor just changed:'
  testutil.request_and_show(conn, 'GET', new_doctor_path)
  print 'IDs of Doctors after PUT:'
  testutil.request_and_show(conn, 'GET', '/Doctor/')

  # check idempotence of PUT
  print 'Check PUT idempotence'
  testutil.request_and_show(conn, 'PUT', new_doctor_path, put_body)
  # show new doctor just not-changed
  print 'New Doctor just not-changed:'
  testutil.request_and_show(conn, 'GET', new_doctor_path)
  print 'IDs of Doctors after second PUT:'
  testutil.request_and_show(conn, 'GET', '/Doctor/')



testutil.main(doTemplateTest)
