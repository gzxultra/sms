# coding:utf-8
from decorator import decorator
from mylib.sqlbean.db.query import Query, escape
from mylib.sqlbean.metamodel import ModelBase
# from mylib.sqlbean.metamodel import cache, lower_name, ModelBase, get_or_create, save, get, __eq__, __ne__
from datetime import datetime


def block_specific_methods(func):
    '''Never call 'save', '_new_save', '_update', 'update', 'delete' in
    before_insert, after_insert, before_update, after_update, before_delete,
    after_delete methods, so we block them during the call '''
    empty_func = lambda *args, **kwargs: None
    block_list = ('save', '_new_save', '_update', 'update', 'delete')

    def func_after_block(self, *args, **kwargs):
        blocked_func = {}
        for func_name in block_list:
            blocked_func[func_name] = getattr(self, func_name)
            setattr(self, func_name, empty_func)

        ret = func.__get__(self)(*args, **kwargs)

        for func_name, method in blocked_func.items():
            setattr(self, func_name, method)

        return ret

    return func_after_block


class OnlyBeUsedInModel(Exception):
    pass


@decorator
def with_transaction(f, *args, **kwargs):
    '''只允许用在 Model 子类的 classmethod 和 method 上面'''
    if not args or getattr(args[0], '__metaclass__', None) is not ModelBase:
        raise OnlyBeUsedInModel

    clz = args[0]

    try:
        clz.begin()
        ret = f(*args, **kwargs)
        clz.commit()
    except:
        clz.rollback()
        raise
    return ret


class Model(object):
    '''
    Allows for automatic attributes based on table columns.

    Syntax::

        from mylib.sqlbean.model import Model
        class MyModel(Model):
            class Meta:
                # If field is blank, this sets a default value on save
                class default:
                    field = 1

                # Table name is lower-case model name by default
                # Or we can set the table name
                table = 'mytable'

        # Create new instance using args based on the order of columns
        m = MyModel(1, 'A string')

        # Or using kwargs
        m = MyModel(field=1, text='A string')

        # Saving inserts into the database (assuming it validates [see below])
        m.save()

        # Updating attributes
        m.field = 123

        # Updates database record
        m.save()

        # Deleting removes from the database
        m.delete()

        m = MyModel(field=0)

        m.save()

        # Retrieval is simple using Model.get
        # Returns a Query object that can be sliced
        MyModel.get(id)

        # Returns a MyModel object with an id of 7
        m = MyModel.get(7)

        # Limits the query results using SQL's LIMIT clause
        # Returns a list of MyModel objects
        m = MyModel.where()[:5]   # LIMIT 0, 5
        m = MyModel.where()[10:15] # LIMIT 10, 5

        # We can get all objects by slicing, using list, or iterating
        m = MyModel.get()[:]
        m = list(MyModel.where(name="zsp").where("age<%s",18))
        for m in MyModel.where():
            # do something here...

        # We can where our Query
        m = MyModel.where(field=1)
        m = m.where(another_field=2)

        # This is the same as
        m = MyModel.where(field=1, another_field=2)

        # Set the order by clause
        m = MyModel.where(field=1).order_by('-field')
        # Removing the second argument defaults the order to ASC

    '''
    __metaclass__ = ModelBase
    debug = False

    def __getstate__(self):
        value = []
        for i in self._fields:
            v = self.__dict__.get(i, None)
            if type(v) is datetime:
                v = v.strftime("%Y-%m-%d %H:%M:%S")
            value.append(v)
        return tuple(value)

    def __setstate__(self, value):
        '''Model原来使用的是默认的 __setstate__ 方法，后来自定义了这个方法，
        但是缓存里面有一些是用默认方法序列化的，这里这么处理是兼容缓存里面的老数据'''
        if isinstance(value, tuple):
            self.__init__(*value)
            self._new_record = False
        else:
            return super(Model, self).__setstate__(value)

    def __init__(self, *args, **kwargs):
        'Allows setting of fields using kwargs'
        self.__dict__[self.Meta.pk] = None
        self._new_record = True
        for i, arg in enumerate(args[:len(self._fields)]):
            self.__dict__[self._fields[i]] = arg
        for i in self._fields[len(args):]:
            self.__dict__[i] = kwargs.get(i)
        self.__dict__["_changed"] = set()

    def __setattr__(self, name, value):
        'Records when fields have changed'
        dc = self.__dict__
        fields = self._fields
        if name[0] == "_" or name not in fields:
            dc[name] = value
            return

        dc_value = dc[name]
        if dc_value is None or value is None:
            self._changed.add(name)
        else:
            try:
                value = type(dc_value)(value)
            except:
                value = str(value)

            if dc_value != value:
                self._changed.add(name)
        dc[name] = value

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        if other is not None:
            sid = self.id
            oid = other.id
            if sid is not None and oid is not None:
                return sid == oid
        return False

    def __hash__(self):
        return self.id

    def __repr__(self):
        s = ', '.join(['%s=%s' % (field, value) for field, value in self.__dict__.iteritems() if field in self._fields])
        return u'%s(%s)' % (self.__class__.__name__, s)

    @classmethod
    def get(cls, __obj_pk=None, **kwargs):
        if __obj_pk is None:
            if not kwargs:
                return
        else:
            kwargs = {
                cls.Meta.pk: __obj_pk
            }
        q = Query(model=cls, conditions=kwargs)
        q.limit = (0, 1)
        q = q.execute_query()
        q = q.fetchone()
        if q:
            obj = cls(*q)
            obj.__dict__['_new_record'] = False
            return obj

    @classmethod
    def get_or_create(cls, **kwds):
        ins = cls.get(**kwds)
        if ins:
            return ins
        else:
            ins = cls(**kwds)
            return ins.save()

    @classmethod
    def raw_sql(cls, query, *args):
        result = Query.raw_sql(query, args, cls.db)
        return result

    @classmethod
    def replace_into(cls, **kwds):
        pk = cls.Meta.pk
        if pk in kwds:
            id = kwds[pk]
            ins = cls.get(id)
            if ins is None:
                ins = cls(id=id)
            del kwds[pk]
        else:
            ins = cls()

        for k, v in kwds.iteritems():
            setattr(ins, k, v)
        ins.save()

        return ins

    @classmethod
    def where(cls, *args, **kwargs):
        'Returns Query object'
        return Query(
            model=cls,
            args=args,
            conditions=kwargs
        )

    @classmethod
    def count(cls, *args, **kwargs):
        return Query(
            model=cls,
            args=args,
            conditions=kwargs
        ).count(1)

    @classmethod
    def begin(cls):
        """
        begin() and commit() let you explicitly specify an SQL transaction.
        Be sure to call commit() after you call begin().
        """
        cls.db.begin()

    @classmethod
    def commit(cls):
        cls.db.commit()

    @classmethod
    def rollback(cls):
        cls.db.rollback()

    def _get_pk(self):
        'Sets the current value of the primary key'
        return getattr(self, self.Meta.pk, None)

    def _set_pk(self, value):
        'Sets the primary key'
        return setattr(self, self.Meta.pk, value)

    def save(self):
        if self._new_record:
            self._set_default()
            self._new_save()
            self._new_record = False
        elif self._changed:
            self._update()
        else:
            return self
        self._changed.clear()

        return self

    def _update(self):
        if not self._changed:
            return

        self._before_update()

        'Uses SQL UPDATE to update record'
        query = 'UPDATE %s SET ' % self.Meta.table_safe
        query += ','.join(['%s=%%s' % escape(f) for f in self._changed])
        query += ' WHERE %s=%%s ' % (escape(self.Meta.pk))

        values = [getattr(self, f) for f in self._changed]
        values.append(self._get_pk())

        Query.raw_sql(query, values, self.db)
        self._after_update()

    def _new_save(self):
        'Uses SQL INSERT to create new record'
        # if pk field is set, we want to insert it too
        # if pk field is None, we want to auto-create it from lastrowid
        self._before_insert()

        pk = self._get_pk()
        auto_pk = 1 and (pk is None) or 0
        fields = [
            f for f in self._fields
            if f != self.Meta.pk or not auto_pk
        ]

        used_fields = []
        values = []
        for i in fields:
            v = getattr(self, i, None)
            if v is not None:
                used_fields.append(escape(i))
                values.append(v)
        query = 'INSERT INTO %s (%s) VALUES (%s)' % (self.Meta.table_safe,
                ', '.join(used_fields),
                ', '.join(["%s"] * len(used_fields))
        )
        cursor = Query.raw_sql(query, values, self.db)

        if not pk:
            self._set_pk(cursor.lastrowid)
        self._after_insert()
        return True

    def _set_default(self):
        if hasattr(self.Meta, 'default'):
            default = self.Meta.default
            i = default()

            for k, v in default.__dict__.iteritems():
                if k[0] == '_':
                    continue
                if getattr(self, k, None) is None:
                    if callable(v):
                        v = getattr(i, k)()
                    setattr(self, k, v)

    def delete(self):
        self._before_delete()

        'Deletes record from database'
        query = 'DELETE FROM %s WHERE `%s` = %%s' % (self.Meta.table_safe, self.Meta.pk)
        values = [getattr(self, self.Meta.pk)]
        Query.raw_sql(query, values, self.db)
        self._after_delete()

    def update(self, **kwds):
        for k, v in kwds.iteritems():
            setattr(self, k, v)
        self._before_update()
        self.save()
        self._after_update()

    @block_specific_methods
    def _before_insert(self):
        return self.before_insert()

    @block_specific_methods
    def _after_insert(self):
        return self.after_insert()

    @block_specific_methods
    def _before_update(self):
        return self.before_update()

    @block_specific_methods
    def _after_update(self):
        return self.after_update()

    @block_specific_methods
    def _before_delete(self):
        return self.before_delete()

    @block_specific_methods
    def _after_delete(self):
        return self.after_delete()

    def before_insert(self):
        pass

    def after_insert(self):
        pass

    def before_update(self):
        pass

    def after_update(self):
        pass

    def before_delete(self):
        pass

    def after_delete(self):
        pass
