# coding=utf-8
import logging
import pickle
from google.appengine.ext import ndb


class JsonStorage(ndb.Model):
    data = ndb.JsonProperty()

    @classmethod
    def get(cls, storage_id):
        entity = cls.get_by_id(storage_id)
        if entity:
            return entity.data
        return None

    @classmethod
    def get_multi(cls, storage_ids):
        keys = [ndb.Key(cls, sid) for sid in storage_ids]
        entities = ndb.get_multi(keys)
        return [entity.data if entity else None
                for entity in entities]

    @classmethod
    def save(cls, storage_id, data):
        if data is None:
            cls.delete(storage_id)
        else:
            cls(id=storage_id, data=data).put()

    @classmethod
    def delete(cls, storage_id):
        ndb.Key(cls, storage_id).delete()


class PickleStorage(ndb.Model):
    count = ndb.IntegerProperty(indexed=False)

    @classmethod
    def get(cls, storage_id):
        info = cls.get_by_id(storage_id)
        if info:
            return PickleStorageChunk.get(storage_id, info.count)
        return None

    @classmethod
    def save(cls, storage_id, data):
        if PickleStorageChunk.KEY_SEPARATOR in storage_id:
            raise ValueError("storage_id for PickleStorage cannot contain %r" % PickleStorageChunk.KEY_SEPARATOR)
        if data is None:
            cls.delete(storage_id)
        else:
            count = PickleStorageChunk.save(storage_id, data)
            cls(id=storage_id, count=count).put()

    @classmethod
    def delete(cls, storage_id):
        info = cls.get_by_id(storage_id)
        if info:
            PickleStorageChunk.delete(storage_id, info.count)
            info.key.delete()


class PickleStorageChunk(ndb.Model):
    KEY_SEPARATOR = "$"
    CHUNK_SIZE = 1000000

    data = ndb.BlobProperty()

    @classmethod
    def _key_name(cls, storage_id, chunk_number):
        return "%s%s%s" % (storage_id, cls.KEY_SEPARATOR, chunk_number)

    @classmethod
    def _make_keys(cls, storage_id, count):
        return [ndb.Key(cls, cls._key_name(storage_id, i)) for i in xrange(count)]

    @classmethod
    def get(cls, storage_id, count):
        keys = cls._make_keys(storage_id, count)
        entities = ndb.get_multi(keys)
        pickled = "".join(entity.data for entity in entities)
        return pickle.loads(pickled)

    @classmethod
    def save(cls, storage_id, data):
        pickled = pickle.dumps(data)
        chunks = []
        for i in xrange(0, len(pickled), cls.CHUNK_SIZE):
            chunks.append(pickled[i:i + cls.CHUNK_SIZE])
        entities = [cls(id=cls._key_name(storage_id, i), data=chunk)
                    for i, chunk in enumerate(chunks)]
        ndb.put_multi(entities)
        return len(entities)

    @classmethod
    def delete(cls, storage_id, count):
        keys = cls._make_keys(storage_id, count)
        ndb.delete_multi(keys)
