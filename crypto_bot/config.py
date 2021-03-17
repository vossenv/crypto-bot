import logging.config
import os

import yaml
from schema import Schema, Optional, Or

from crypto_bot.resources import get_resource


def config_schema() -> Schema:
    return Schema({
        'connection': {
            'base_url': str,
            'update': int
        },
        'bots': [{
            'token': str,
            'coin': str
        }],
        Optional('logging'): {
            'level': Or('info', 'debug', 'INFO', 'DEBUG')
        }})


def load_config(path):
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    _validate(cfg)

    for val in os.environ.get('bots').split(','):
        if not val.strip():
            continue
        t = val.split("=")
        if len(t) < 2:
            raise ConfigValidationError("Improper bot config: {}".format(val))
        cfg['bots'].append({'coin: ': t[0], 'token': t[1]})

    return cfg


def _validate(raw_config: dict):
    from schema import SchemaError
    try:
        config_schema().validate(raw_config)
    except SchemaError as e:
        raise ConfigValidationError(e.code) from e


class ConfigValidationError(Exception):
    def __init__(self, message):
        super(ConfigValidationError, self).__init__(message)


def init_logger(config):
    if not os.path.exists("logs"):
        os.mkdir("logs")
    config = config or {}
    level = config.get('level') or 'INFO'
    with open(get_resource("logger_config.yaml")) as cfg:
        data = yaml.safe_load(cfg)
        data['loggers']['']['level'] = level.upper()
        logging.config.dictConfig(data)
        return logging.getLogger()

def env_overrides(self, key="cfg."):
    overrides = {}
    reduced = {decode(k, True): decode(v, True) for k, v in os.environ._data.items() if decode(k, True)}
    reduced = {k.lstrip(key): v for k, v in reduced.items() if k.startswith(key)}

    for k, v in reduced.items():
        entry = Config.make_dict(k.split("."), v)
        Config.merge_dict(overrides, entry)
    Config.merge_dict(self.data, overrides)