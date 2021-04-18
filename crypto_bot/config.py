import logging.config
import os

from ruamel import yaml
# import yaml
from schema import Schema, Or

yaml = yaml.YAML()
yaml.indent(sequence=4, offset=2)

from crypto_bot.resources import get_resource

config_defaults = {
    'exchanges': [],
    'process': {
        'log_level': 'INFO',
        'update_rate': 3,
    },
    'discord': {
        'bots': {},
        'command_roles': ['everyone']
    }
}


class ConfigLoader:

    def __init__(self, config_path="config.yml"):
        self.config_path = config_path
        self.active_config = self.load_config(config_path)
        self.save_config()

    def config_schema(self) -> Schema:
        return Schema({
            'exchanges': [{
                'name': str,
                'priority': int,
                'api_url': str
            }],
            'process': {
                'log_level': Or('info', 'debug', 'INFO', 'DEBUG'),
                'update_rate': Or(float, int),
            },
            'discord': {
                'bots': {str: str},
                'command_roles': Or([str], {str})
            }
        })

    def load_config(self, path):
        cfg = config_defaults
        with open(path) as f:
            cfg.update(yaml.load(f))
        self._validate(cfg)

        return cfg

    def _validate(self, raw_config: dict):
        from schema import SchemaError
        try:
            self.config_schema().validate(raw_config)
        except SchemaError as e:
            raise ConfigValidationError(e.code) from e

    def save_config(self):
        with open(self.config_path, 'w') as f:
            yaml.dump(self.active_config, f)

    def update_bot_coin(self, token, coin):
        self.active_config['discord']['bots'][token] = coin.upper()
        self.save_config()


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
        data = yaml.load(cfg)
        data['loggers']['']['level'] = level.upper()
        logging.config.dictConfig(data)
        return logging.getLogger()
