#coding:utf-8
from array import array
from mylib.sqlbean.db.mc_connection import mc
from mylib.sqlbean.model import Model

empty = 0


class McModel(Model):

    @classmethod
    def mc_get(cls, id):
        if not id:
            return None
        key = cls.Meta.mc_key % id
        value = mc.get(key)
        if value is None:
            value = cls.get(id) or empty
            mc.set(key, value)
        if value is empty:
            value = None
        return value

    @classmethod
    def mc_get_multi(cls, id_list):
        if type(id_list) not in (array, list, tuple, dict):
            id_list = tuple(id_list)
        mc_key = cls.Meta.mc_key
        result = mc.get_multi([mc_key % i for i in id_list])
        r = {}
        for i in id_list:
            t = result.get(mc_key % i)
            if t is None:
                t = cls.get(i) or empty
                mc.set(mc_key % i, t)
            if t is empty:
                t = None
            r[i] = t
        return r

    @classmethod
    def mc_get_list(cls, id_list):
        id_list = tuple(id_list)
        rs = cls.mc_get_multi(id_list)
        return [rs[i] for i in id_list]

    @classmethod
    def mc_delete(cls, id):
        mc.delete(cls.Meta.mc_key % id)

    @classmethod
    def mc_bind(cls, xxx_list, property, key="id"):
        d = []
        e = []
        for i in xxx_list:
            k = getattr(i, key)
            if k:
                d.append(k)
                e.append((k, i))
            else:
                i.__dict__[property] = None

        r = cls.mc_get_multi(set(d))
        for k, v in e:
            v.__dict__[property] = r.get(k)

    def mc_flush(self):
        mc.delete(self.Meta.mc_key % self.id)

    def mc_set(self):
        key = self.Meta.mc_key % self.id
        mc.set(key, self)

    def _update(self):
        super(McModel, self)._update()
        self.mc_flush()

    def delete(self):
        super(McModel, self).delete()
        self.mc_flush()

    def save(self):
        ret = super(McModel, self).save()
        self.mc_flush()
        return ret
