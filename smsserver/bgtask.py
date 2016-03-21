# coding: utf-8

import uuid
import gevent

from gevent.queue import Queue
from gevent.pool import Pool
from conf import Config
from smsserver.models import db


bgtasks_queue = Queue()


def spawn_bgtask(func, *args, **kw):
    bgtasks_queue.put((uuid.uuid4().hex, func, args, kw))


class BGTaskManager(object):

    def __init__(self, max_workers):
        self.max_workers = max_workers
        self._pool = Pool(size=max_workers)

    def run(self):
        while True:
            task_id, func, args, kw = bgtasks_queue.get()
            func = db.execution_context(with_transaction=False)(func)
            self._pool.spawn(func, *args, **kw)

    def active_worker_count(self):
        return self._pool.size - self._pool.free_count()


manager = BGTaskManager(Config.BGTASK_MAX_WORKERS)
gevent.spawn(manager.run)


def get_bgtasks_stats():
    d = {'size': manager.max_workers,
         'active_worker_count': manager.active_worker_count(),
         'queue_size': bgtasks_queue.qsize()}
    return d
