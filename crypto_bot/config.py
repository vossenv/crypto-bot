import logging.config
import os

import yaml
from schema import Schema, Or

from crypto_bot.resources import get_resource

config_defaults = {
    'api_url': 'https://api.coingecko.com/api/v3',
    'log_level': 'INFO',
    'bots': [],
    'command_roles': ['everyone']
}


def config_schema() -> Schema:
    return Schema({
        'api_url': str,
        'log_level': Or('info', 'debug', 'INFO', 'DEBUG'),
        'bots': [{
            'token': str,
            'coin': str
        }],
        'command_roles': Or([str], {str})
    })


def load_config(path):
    cfg = config_defaults
    if path:
        with open(path) as f:
            cfg.update(yaml.safe_load(f))

    envs = {decode(k, True): decode(v) for k, v in os.environ._data.items() if decode(k, True)}
    botenv = envs.get('bots')
    if botenv:
        for val in botenv.split(','):
            if not val.strip():
                continue
            t = val.split("=")
            if len(t) < 2:
                raise ConfigValidationError("Improper bot config: {}".format(val))
            cfg['bots'].append({'coin': t[0], 'token': t[1]})

    for k in cfg:
        if k == 'bots':
            continue
        v = envs.get(k)
        if v:
            cfg[k] = envs[k]
    if isinstance(cfg['command_roles'], str):
        cfg['command_roles'] = cfg['command_roles'].split(',')

    _validate(cfg)
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


def decode(text, lower=False):
    if not text:
        return
    try:
        text = text.decode()
    except:
        pass

    text = str(text).strip()
    return text.lower() if lower else text


def init_logger(level):
    if not os.path.exists("logs"):
        os.mkdir("logs")
    with open(get_resource("logger_config.yaml")) as cfg:
        data = yaml.safe_load(cfg)
        data['loggers']['']['level'] = level.upper()
        logging.config.dictConfig(data)
        return logging.getLogger()
