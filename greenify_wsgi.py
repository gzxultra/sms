# coding: utf-8
import os
import greenify
greenify.greenify()


ungreen_lib_path = os.environ['UNGREEN_LIB_PATH']  # path of 'libmysqlclient.so'
for path in ungreen_lib_path.split(':'):
    assert greenify.patch_lib(path)


from smsserver import app       # noqa
