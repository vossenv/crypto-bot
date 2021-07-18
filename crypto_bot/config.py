import logging.config
import os

import yaml
from ruamel import yaml as ryaml
from schema import Schema, Or, Optional

ryaml = ryaml.YAML()
ryaml.indent(sequence=4, offset=2)

from crypto_bot.resources import get_resource


class ConfigLoader:

    def __init__(self, config_path):
        self.config_path = config_path
        self.active_config = self.load_config(config_path)
        self.save_config()

    def config_schema(self) -> Schema:
        return Schema({
            Optional('exchanges'): {
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
            Optional('twitter'): {
                'access_token': str,
                'access_token_secret': str,
                'consumer_key': str,
                'consumer_secret': str,
                'update_rate': Or(int, float)
            },
            'discord': {
                Optional('price_bots'): {
                    Optional('avatar'): str,
                    Optional('command_roles'): Or([str], {str}),
                    Optional('use_coin_avatar'): Or(None, bool),
                    'home_server': int,
                    'instances': {str: str},
                },
                Optional('info_bots'): {str: {
                    'name': str,
                    Optional('status'): {
                        'activity': Or("playing","streaming","listening","watching","competing"),
                        'name': object
                    },
                    Optional('new_coin_notifications'): {'channels': [int]},
                    Optional('avatar'): str,
                    Optional('twitter_notifications'): {
                        'users': [str],
                        'channels': [int],
                        Optional('tags'): [int]
                    },
                    Optional('countdowns'):
                        {str: [int]}
                }},
                Optional('countdowns'): {
                    str: {
                        'alert_time': str,
                        'name': str,
                        Optional('schedule'): Or(
                            [Or(float, int)],
                            {Or(float, int): Or(str, None)}),
                        Optional('alert_date'): str,
                        Optional('message'): str,
                        Optional('channels'): [int]
                    }
                },
                Optional('message_bots'): {str: {
                    'name': str,
                    Optional('avatar'): str,
                    Optional('command_roles'): Or([str], {str}),
                    Optional('log_channel_mismatch'): Or(None, bool),
                    'channel_mappings': [{
                        'read_channels': Or([int], {'file': str, 'columns': Or(str, [str]), Optional('ignore'): Or(str, [str])}),
                        'write_channels': Or([int], {'file': str, 'columns': Or(str, [str]), Optional('ignore'): Or(str, [str])}),
                    }],
                }},
            }
        })

    def load_config(self, path):
        with open(path) as f:
            cfg = ryaml.load(f)
        self._validate(cfg)

        paths = []
        info_bots = cfg['discord'].get('info_bots')
        if info_bots:
            for b in info_bots.values():
                av = b.get('avatar')
                if av:
                    paths.append(av)
                if 'countdowns' in b:
                    alerts = cfg['discord'].get('countdowns')
                    for c in b['countdowns']:
                        if c not in alerts:
                            raise ConfigValidationError("Countdown '{}' for {} is not defined".format(c, b['name']))

        price_bots = cfg['discord'].get('price_bots')
        if price_bots:
            av = cfg['discord'].get('price_bot_avatar')
            if av:
                paths.append(av)
        if (info_bots or price_bots) and not cfg.get('exchanges'):
            raise ConfigValidationError("Must include exchanges section for price and info bots")

        for p in paths:
            if not os.path.exists(p):
                raise FileNotFoundError(
                    "Avatar '{}' could not be found. Please check the path".format(p))

        return cfg

    def _validate(self, raw_config: dict):
        from schema import SchemaError
        try:
            self.config_schema().validate(raw_config)
        except SchemaError as e:
            raise ConfigValidationError(e.code) from e

    def save_config(self):

        if 'price_bots' in self.active_config['discord']:
            with open(self.config_path, 'r') as f:
                settings = ryaml.load(f)
                settings['discord']['price_bots']['instances'] = self.active_config['discord']['price_bots'][
                    'instances']

            with open(self.config_path, 'w') as f:
                ryaml.dump(settings, f)

    def update_bot_coin(self, token, coin):
        self.active_config['discord']['price_bots']['instances'][token] = coin.upper()
        self.save_config()

    def is_home_id(self, sid):
        return self.active_config['discord']['price_bots']['home_server'] == sid


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
        data = ryaml.load(cfg)
        data['loggers']['']['level'] = level.upper()
        logging.config.dictConfig(data)
        return logging.getLogger()
