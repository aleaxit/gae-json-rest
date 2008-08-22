""" A very simple "smoke test" for gae-json-rest toy app. """
import sys
import simplejson
import testutil

def doTemplateTest(tester, verbose):
  # what models do we have? shd be Doctor and Pager
  if verbose: print 'Getting names for Models:'
  modelnames = tester.request_and_show('GET', '/', verbose)
  try:
    assert set(modelnames) == set(('Doctor', 'Pager'))
  except:
    print 'modelnames is', set(modelnames)
    raise

  # do we know any Doctors?
  if verbose: print 'IDs of Doctors before any operations:'
  doctorids = tester.request_and_show('GET', '/Doctor/', verbose)
  # get the highest-known Doctor ID, if any, to ensure a unique number
  if doctorids:
    unique = max(int(obj['id']) for obj in doctorids) + 1
  else:
    unique = 1
  # now, we want to delete about half the doctors we know
  num_doctors = len(doctorids)
  deletions = 0
  for i in range(0, num_doctors, 2):
    strid = doctorids[i]['id']
    tester.silent_request('DELETE', '/Doctor/%s' % strid)
    deletions += 1
  if verbose: print 'IDs of Doctors after some deletions:'
  doctorids = tester.silent_request('GET', '/Doctor/')
  if verbose: print doctorids
  if len(doctorids) != num_doctors - deletions:
    print 'Had %d doctors, deleted %d, should have %d but have %d' % (
        num_doctors, deletions, num_doctors-deletions, len(doctorids))
    sys.exit(1)
  num_doctors = len(doctorids)

  # form name based on unique number
  docname = 'Dr. John %s' % unique
  # make entity with that name
  post_body = testutil.body(name=docname)
  post_result = tester.request_and_show('POST', '/Doctor/', verbose,
      post_body)
  new_doctor_id = post_result['id']
  new_doctor_path = '/Doctor/%s' % new_doctor_id
  if verbose: print 'Created %r' % new_doctor_path
  # show new doctor just created
  if verbose: print 'New Doctor just created:'
  new_doctor = tester.request_and_show('GET', new_doctor_path, verbose)
  if new_doctor['name'] != docname:
    print 'New doctor name should be %r, is %r instead after POST' % (
        docname, new_doctor['name'])
    sys.exit(1)
  # show IDs after the POST
  if verbose: print 'IDs of Doctors after POST:'
  doctorids = tester.request_and_show('GET', '/Doctor/', verbose)
  if len(doctorids) != num_doctors + 1:
    print 'Had %d doctors, created %d, should have %d but have %d' % (
        num_doctors, 1, num_doctors+1, len(doctorids))
    sys.exit(1)
  num_doctors = len(doctorids)

  # Now change the name of the doctor
  docname = '%s changed' % docname
  put_body = testutil.body(name=docname)
  put_result = tester.request_and_show('PUT', new_doctor_path, verbose,
      put_body)
  # show new doctor just changed
  if verbose: print 'New Doctor just changed:'
  new_doctor = tester.request_and_show('GET', new_doctor_path, verbose)
  if new_doctor['name'] != docname:
    print 'New doctor name should be %r, is %r instead after PUT' % (
        docname, new_doctor['name'])
    sys.exit(1)
  if verbose: print 'IDs of Doctors after PUT:'
  doctorids = tester.request_and_show('GET', '/Doctor/', verbose)
  if len(doctorids) != num_doctors:
    print 'Had %d doctors, put %d, should have %d but have %d' % (
        num_doctors, 1, num_doctors, len(doctorids))
    sys.exit(1)

  # check idempotence of PUT
  if verbose: print 'Check PUT idempotence'
  tester.request_and_show('PUT', new_doctor_path, verbose, put_body)
  # show new doctor just not-changed
  if verbose: print 'New Doctor just not-changed:'
  new_doctor = tester.request_and_show('GET', new_doctor_path, verbose)
  if new_doctor['name'] != docname:
    print 'New doctor name should be %r, is %r instead after 2nd PUT' % (
        docname, new_doctor['name'])
    sys.exit(1)
  if verbose: print 'IDs of Doctors after second PUT:'
  doctorids = tester.request_and_show('GET', '/Doctor/', verbose)
  if len(doctorids) != num_doctors:
    print 'Had %d doctors, put %d again, should have %d but have %d' % (
        num_doctors, 1, num_doctors, len(doctorids))
    sys.exit(1)


t = testutil.Tester(doTemplateTest)
t.execute()

#testutil.main(doTemplateTest)

