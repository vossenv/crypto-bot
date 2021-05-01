import logging.config
import os

from ruamel import yaml
from schema import Schema, Or, Optional

yaml = yaml.YAML()
yaml.indent(sequence=4, offset=2)

from crypto_bot.resources import get_resource


class ConfigLoader:

    def __init__(self, config_path):
        self.config_path = config_path
        self.active_config = self.load_config(config_path)
        self.save_config()

    def config_schema(self) -> Schema:
        return Schema({
            'exchanges': {
                Optional('coingecko'): {
                    'priority': int,
                    Optional('coin_overrides'): {str: str}
                },
                Optional('kucoin'): {
                    'update_rate': Or(float, int),
                    'priority': int,
                },
                Optional('binance_us'): {
                    'update_rate': Or(float, int),
                    'priority': int,
                }
            },
            'process': {
                'log_level': Or('info', 'debug', 'INFO', 'DEBUG'),
                'update_rate': Or(float, int),
            },
            'discord': {
                'home_server': int,
                Optional('price_bot_avatar'): str,
                Optional('price_bots'): {str: str},
                Optional('info_bots'): {str: {
                    'name': str,
                    Optional('avatar'): str,
                    Optional('countdowns'): [{
                        'alert_time': str,
                        'name': str,
                        Optional('schedule'): Or(
                            [Or(float, int)],
                            {Or(float, int): Or(str, None)}),
                        Optional('alert_date'): str,
                        Optional('message'): str,
                        Optional('channels'): [int]
                    }]}
                },
                'command_roles': Or([str], {str})
            }
        })

    def load_config(self, path):
        with open(path) as f:
            cfg = yaml.load(f)
        self._validate(cfg)

        paths = []
        info_bots = cfg['discord'].get('info_bots')
        if info_bots:
            for b in info_bots.values():
                av = b.get('avatar')
                if av:
                    paths.append(av)

        price_bots = cfg['discord'].get('price_bots')
        if price_bots:
            av = cfg['discord'].get('price_bot_avatar')
            if av:
                paths.append(av)

        for p in paths:
            if not os.path.exists(p):
                raise FileNotFoundError(
                    "Avatar '{}' could not be found. Please check the path".format(p))

        return cfg

    def _validate(self, raw_config: dict):
        from schema import SchemaError
        try:
            self.config_schema().validate(raw_config)

            price_bots = raw_config['discord'].get('price_bots')
            info_bots = raw_config['discord'].get('info_bots')

            if not price_bots and not info_bots:
                raise ConfigValidationError("No bots were defined - please define at least 1 price or info bot")

        except SchemaError as e:
            raise ConfigValidationError(e.code) from e

    def save_config(self):
        with open(self.config_path, 'w') as f:
            yaml.dump(self.active_config, f)

    def update_bot_coin(self, token, coin):
        self.active_config['discord']['price_bots'][token] = coin.upper()
        self.save_config()

    def is_home_id(self, sid):
        return self.active_config['discord']['home_server'] == sid


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
