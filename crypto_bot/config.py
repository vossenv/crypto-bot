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
        Optional('command_roles'): [str],
        Optional('logging'): {
            'level': Or('info', 'debug', 'INFO', 'DEBUG')
        }})


def load_config(path):
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    _validate(cfg)

    botenv = os.environ.get('BOTS')
    if botenv:
        for val in botenv.split(','):
            if not val.strip():
                continue
            t = val.split("=")
            if len(t) < 2:
                raise ConfigValidationError("Improper bot config: {}".format(val))
            cfg['bots'].append({'coin: ': t[0], 'token': t[1]})
    cmd = os.environ.get('COMMAND_ROLES').split(',')
    if cmd:
        cfg['command_roles'].extend(cmd)
    cfg['command_roles'] = set(cfg['command_roles'])
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
