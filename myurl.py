import django.conf.urls.defaults as d
import pprint as pp
import logging

def index(*args, **kwargs):
  print 'Inside index'

def hello(*args, **kwargs):
  pp.pprint(*args)
  pp.pprint(kwargs)

urlpatterns = d.patterns('',
    (r'^$', index),
    (r'^hello/(\d+)$', hello),
    )

def resolve(path):
  for pattern in urlpatterns:
    m = pattern.resolve(path)
    if m: return m
  return ('', (), {})

if __name__ == '__main__':
  resolve('hello/123')
  resolve('')
