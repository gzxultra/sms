# coding: utf-8
import os
import greenify
greenify.greenify()

libmysqlclient_path = os.environ['LIB_MYSQLCLIENT_PATH']
assert greenify.patch_lib(libmysqlclient_path)

from smsserver import app       # noqa
