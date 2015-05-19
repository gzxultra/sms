# coding:utf-8
import cmemcached
import random


def _escape(key):
    if isinstance(key, unicode):
        key = key.encode('utf8')

    # ignore space charater in key
    key = ''.join([c for c in key if ord(c) > 32 and c != '\x7fb'])

    return key

escape = _escape


def mc_do(mc, action, keys, *args, **kwargs):
    if not mc or not action:
        raise Exception('mc or action name can not be None')
    return getattr(mc, action)(keys, *args, **kwargs)


class MemcacheClientBase(object):
    def start_log(self):
        from mypy.profile_middleware import CallLogger
        self.mc = CallLogger(self.mc)

    def stop_log(self):
        from mypy.profile_middleware import CallLogger
        if isinstance(self.mc, CallLogger):
            self.mc = self.mc.obj

    def get_log(self):
        from collections import defaultdict
        d = defaultdict(int)
        nd = defaultdict(lambda: [0, 0])
        for call, ncall, cost in self.mc.log:
            d[call] += 1
            x = nd[ncall]
            x[0] += 1
            x[1] += cost
        return "Memcache access (%s/%s calls):\n\n%s\nDetail:\n\n%s\n" % \
            (len(d), sum(d.itervalues()),
                ''.join("%s: %d times, %f seconds\n" % (
                        ncall, times, cost) for ncall, (times, cost)
                        in sorted(nd.iteritems())),
                ''.join("%s: %d times\n" % (key, n)
                        for key, n in sorted(d.iteritems())))


def _make_function1(action):
    # _make_function1 is used to overcome python's late binding
    # refer to: http://stackoverflow.com/questions/3431676/creating-functions-in-a-loop
    def _(self, key, *args, **kwargs):
        for srv in self.srvs:
            ret = mc_do(srv, action, key, *args, **kwargs)
        return ret
    return _


def _make_function2(action):
    # same as _make_function1
    def _(self, key, *args, **kwargs):
        count = len(self.srvs)
        chosed = random.randrange(count)
        for index in range(chosed, chosed + count):
            srv = self.srvs[index % count]
            ret = mc_do(srv, action, key, *args, **kwargs)
            if ret is not None:
                return ret
    return _


class ReplicatedMeta(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(ReplicatedMeta, cls).__new__(cls, name, bases, attrs)

        for action in ('add', 'replace', 'delete', 'incr', 'decr', 'prepend',
                'append', 'append_multi', 'prepend_multi', 'delete_multi', 'set_multi', 'set'):
            setattr(new_class, action, _make_function1(action))

        for action in ('get', 'get_multi'):
            setattr(new_class, action, _make_function2(action))

        return new_class


class Replicated(object):
    "replacated memcached for fail-over"
    __metaclass__ = ReplicatedMeta

    def __init__(self, *srvs):
        self.srvs = srvs

    def __repr__(self):
        return "<Replicated %s>" % (str(self.srvs))

    def reset(self):
        pass

    def close(self):
        pass


class FakeMemcacheClient(MemcacheClientBase):
    def __init__(self):
        self.dataset = {}

    def reopen(self):
        pass

    def reset(self):
        self.dataset.clear()

    def set(self, key, val, time=0):
        key = _escape(key)
        self.dataset[key] = val

    def get(self, key):
        key = _escape(key)
        return self.dataset.get(key)

    def get_multi(self, keys):
        keys = [_escape(key) for key in keys]
        return dict([(k, self.dataset.get(k)) for k in keys])

    def get_list(self, keys):
        rs = self.get_multi(keys)
        return [rs.get(k) for k in keys]

    def append(self, key, val):
        key = _escape(key)
        self.dataset.pop(key, None)

    def prepend(self, key, val):
        key = _escape(key)
        self.dataset.pop(key, None)

    def delete(self, key):
        key = _escape(key)
        self.dataset.pop(key, None)

    def decr(self, key, val=1):
        key = _escape(key)
        self.dataset.pop(key, None)

    def incr(self, key, val=1):
        key = _escape(key)
        self.dataset.pop(key, None)

    def flushall(self):
        self.dataset = {}


class MemcacheClientProxy(MemcacheClientBase):
    def __init__(self, memcached_addrs, enable_local_cached=True):
        self.dataset = {}
        self.memcached_addrs = memcached_addrs
        self.enable_local_cached = enable_local_cached
        clients = [_setup_mc(addr_group) for addr_group in self.memcached_addrs]
        self.mc = Replicated(*clients)

    def reopen(self):
        clients = [_setup_mc(addr_group) for addr_group in self.memcached_addrs]
        self.mc = Replicated(*clients)

    def reset(self):
        self.dataset.clear()

    def set(self, key, val, time=0):
        key = _escape(key)
        if self.enable_local_cached:
            self.dataset[key] = val
        self.mc.set(key, val, time)

    def get(self, key):
        key = _escape(key)
        r = None
        if self.enable_local_cached:
            r = self.dataset.get(key)
        if r is None:
            r = self.mc.get(key)
        if r is not None and self.enable_local_cached:
            self.dataset[key] = r
        return r

    def get_multi(self, keys):
        keys = [_escape(key) for key in keys]
        rs = []
        if self.enable_local_cached:
            rs = [(k, self.dataset.get(k)) for k in keys]
            r = dict((k, v) for k, v in rs if v is not None)
            rs = self.mc.get_multi([k for k, v in rs if v is None])
            r.update(rs)
            self.dataset.update(rs)
        else:
            r = self.mc.get_multi(keys)
        return r

    def get_list(self, keys):
        rs = self.get_multi(keys)
        return [rs.get(k) for k in keys]

    def append(self, key, val):
        key = _escape(key)
        if self.enable_local_cached:
            self.dataset.pop(key, None)
        return self.mc.append(key, val)

    def prepend(self, key, val):
        key = _escape(key)
        if self.enable_local_cached:
            self.dataset.pop(key, None)
        return self.mc.prepend(key, val)

    def delete(self, key):
        key = _escape(key)
        if self.enable_local_cached:
            self.dataset.pop(key, None)
        return self.mc.delete(key)

    def decr(self, key, val=1):
        key = _escape(key)
        if self.enable_local_cached:
            self.dataset.pop(key, None)
        return self.mc.decr(key, val)

    def incr(self, key, val=1):
        key = _escape(key)
        if self.enable_local_cached:
            self.dataset.pop(key, None)
        return self.mc.incr(key, val)

    def __getattr__(self, name):
        return getattr(self.mc, name)


def _setup_mc(mc_addr):
    if not mc_addr:
        return
    mc = cmemcached.Client(mc_addr, comp_threshold=1024)
    mc.set_behavior(cmemcached.BEHAVIOR_CONNECT_TIMEOUT, 10)   # 0.01s
    mc.set_behavior(cmemcached.BEHAVIOR_POLL_TIMEOUT, 300)    # 0.3s
    mc.set_behavior(cmemcached.BEHAVIOR_RETRY_TIMEOUT, 20)    # 20 sec
    mc.set_behavior(cmemcached.BEHAVIOR_SERVER_FAILURE_LIMIT, 2)    # 0.2 * 4 * 2 sec
    return mc


def setup_memcache(memcached_addrs=[], enable_local_cached=True, fake=False):
    if fake:
        return FakeMemcacheClient()
    else:
        return MemcacheClientProxy(memcached_addrs, enable_local_cached)
