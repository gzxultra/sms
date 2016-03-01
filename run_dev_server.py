# coding: utf-8

import sys
import os

if not os.environ.get('SMSSERVER_CONFIG'):
    os.environ['SMSSERVER_CONFIG'] = 'conf.develop'

from smsserver import app


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    else:
        port = 8001

    app.run(host='0.0.0.0', port=port)
