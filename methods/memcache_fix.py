# TODO remove
from google.appengine.api import memcache

_old_get = memcache.get
_old_set = memcache.set


def _get(name, *args, **kwargs):
    return _old_get("_refactor_" + name, *args, **kwargs)


def _set(name, *args, **kwargs):
    return _old_set("_refactor_" + name, *args, **kwargs)


memcache.get = _get
memcache.set = _set
