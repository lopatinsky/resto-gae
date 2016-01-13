# coding=utf-8
import json


class FakeFloat(float):
    def __init__(self, value):
        self._value = value

    def __repr__(self):
        return self._value


class BetterFloatJsonEncoder(json.JSONEncoder):
    def _replace(self, o):
        if isinstance(o, float):
            return FakeFloat("%.8f" % o)
        elif isinstance(o, dict):
            return {k: self._replace(v) for k, v in o.iteritems()}
        elif isinstance(o, (list, tuple)):
            return map(self._replace, o)
        else:
            return o

    def encode(self, o):
        return super(BetterFloatJsonEncoder, self).encode(self._replace(o))
