import django.conf.urls.defaults as d
import pprint

def index():
  print 'Inside index'

def hello():
  print 'Inside hello'


urlpatterns = d.patterns('',
    (r'^$', index),
    (r'^hello/', hello),
    )

pprint.pprint(urlpatterns)

for pattern in urlpatterns:
  m = pattern.resolve('hello/')
  if m:
    pprint.pprint(m)
    m[0]()
