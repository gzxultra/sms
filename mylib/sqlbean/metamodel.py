from mylib.sqlbean.db.query import escape
from mylib.sqlbean.db import connection


def lower_name(class_name):
    """
    >>>lower_name("UserCount")
    'user_count'

    >>>lower_name("user_count")
    'user_count'
    """
    result = []
    for c in class_name:
        i = ord(c)
        if 65 <= i <= 90:
            if result:
                if not 48 <= ord(result[-1]) <= 57:
                    result.append("_")
            i += 32
            c = chr(i)
        result.append(c)
    return "".join(result)


class ModelCache(object):
    models = {}

    def add(self, model):
        self.models[model.Meta.table] = model

    def get(self, table):
        return self.models[table]

cache = ModelCache()


class ModelBase(type):
    '''
    Metaclass for Model

    Sets up default table name and primary key
    Adds fields from table as attributes
    Creates ValidatorChains as necessary

    '''
    def __new__(cls, name, bases, attrs):
        #print "init",name
        if name == 'Model' or name == "McModel":
            return super(ModelBase, cls).__new__(cls, name, bases, attrs)

        new_class = super(ModelBase, cls).__new__(cls, name, bases, attrs)

        if not getattr(new_class, 'Meta', None):
            class Empty:
                pass
            new_class.Meta = Empty

        if not getattr(new_class.Meta, 'table', None):
            new_class.Meta.table = lower_name(name)
        new_class.Meta.table_safe = escape(new_class.Meta.table)

        # Assume id is the default
        if not getattr(new_class.Meta, 'pk', None):
            new_class.Meta.pk = 'id'
        if not getattr(new_class.Meta, 'mc_key', None):
            mc_ver = getattr(new_class.Meta, "mc_ver", "")
            if mc_ver:
                new_class.Meta.mc_key = "%s@%s:%%s" % (name, mc_ver)
            else:
                new_class.Meta.mc_key = "%s:%%s" % name

        db = new_class.db = connection.get_db_by_table(new_class.Meta.table)

        q = db.cursor()
        q.execute('SELECT * FROM %s LIMIT 0' % new_class.Meta.table_safe)

        new_class._fields = [f[0] for f in q.description]

        cache.add(new_class)
        return new_class
