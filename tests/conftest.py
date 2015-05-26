# coding: utf8
import re
import pytest
from smsserver.models import mc, db


TABLE_REGEXP = re.compile(r'''(insert into|update)\s+[`']?(.*?)[`']?\s''', re.IGNORECASE)


def extract_table_name(sql):
    match = TABLE_REGEXP.match(sql)
    if match:
        return match.group(2)


@pytest.yield_fixture(autouse=True)
def run_around_tests():
    # Code that will run before your test, for example:
    tables = set()

    def callback(sql, *args, **kwargs):
        table = extract_table_name(sql)
        if table:
            tables.add(table)

    db.hook_execution(callback)

    # A test function will be run at this point
    yield

    # Code that will run after your test, for example:
    db.hook_execution(None)

    for t in tables:
        db.cursor(t).execute('truncate %s' % t)
    mc.flushall()
