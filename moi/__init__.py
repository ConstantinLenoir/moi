import os.path
import json
import logging.config
import os

_top_level_dir = os.path.dirname(os.path.dirname(__file__))


_log_conf = os.path.join(_top_level_dir,
                         'logging.json')


_log_dir = os.path.join(_top_level_dir,
                        'log')


with open(_log_conf,
          mode = 'r',
          newline = '') as stream:
    #
    _config_dic = json.load(stream)
    for handler in  _config_dic['handlers']:   
        _path = _config_dic['handlers'][handler]['filename']
        # os.sep
        _path = _path.replace('_LOG_DIR_', _log_dir + os.sep)
        _config_dic['handlers'][handler]['filename'] = _path
    logging.config.dictConfig(_config_dic)
