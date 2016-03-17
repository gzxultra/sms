# sms


运行时需要指定环境变量`SMSSERVER_CONFIG`，来指定对应的配置文件。如 `SMSSERVER_CONFIG=conf.develop`

如果使用 `gunicorn` 的`gevent worker` 方式执行应用，需要使用 `greenify_wsgi:app`, 并设置环境变量 `UNGREEN_LIB_PATH` 为不能被gevent monkey patch 的C库，多个路径以`:`分割(当前只需要patch MySQLdb 使用的libmysqlclient.so)。如 `UNGREEN_LIB_PATH=/usr/lib/x86_64-linux-gnu/libmysqlclient.so.18`
