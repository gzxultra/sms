#codint: utf8
from collections import deque


class Transaction(object):
    """Transaction Controller"""
    def __init__(self, conn):
        self.stack = deque()
        self.conn = conn

    def begin(self):
        self.stack.append(True)

    def force_commit(self):
        # print 'force_commit'
        self.stack.clear()
        self.conn.commit()

    def force_rollback(self):
        # print 'force_rollback'
        self.stack.clear()
        self.conn.rollback()

    def real_commit(self):
        # print 'real_commit'
        self.conn.commit()

    def real_rollback(self):
        # print 'real_rollback'
        self.conn.rollback()

    def is_in_transcation(self):
        return len(self.stack)

    def commit(self):
        try:
            self.stack.pop()
        except IndexError:
            pass

        if not self.is_in_transcation():
            self.real_commit()

    def rollback(self):
        try:
            self.stack.pop()
        except IndexError:
            pass
        if not self.is_in_transcation():
            self.real_rollback()
