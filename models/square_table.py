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