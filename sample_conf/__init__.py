import os


__all__ = ['Config']


config_module_path = os.environ.get('SMSSERVER_CONFIG', 'sample')


config_module = __import__(config_module_path, fromlist=['Config'])
Config = config_module.Config
