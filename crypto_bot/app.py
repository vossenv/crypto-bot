# Init application
import asyncio
import sys

from crypto_bot.bots import price_bot, bot_globals, info_bot
from crypto_bot.config import ConfigLoader, init_logger
from crypto_bot.exchanges import Exchange
from crypto_bot.price_indexer import PriceIndexer
from crypto_bot.twitter_collector import TwitterCollector

try:
    cfg = sys.argv[1]
except:
    cfg = "config.yml"

bot_globals.config_loader = ConfigLoader(cfg)
config = bot_globals.config_loader.active_config

logger = init_logger(config['process']['log_level'])
logger.info("Config loaded")

exchanges = [Exchange.create(c, dict(d)) for c, d in config['exchanges'].items()]
bot_globals.indexer = indexer = PriceIndexer(exchanges, config['process']['update_rate'])
indexer.wait_exchanges()

logger.info("Start Bots")
price_bots = config['discord'].get('price_bots')
info_bots = config['discord'].get('info_bots')
twitter_cfg = config.get('twitter')
twitter_collector = TwitterCollector(twitter_cfg) if twitter_cfg else None

loop = asyncio.get_event_loop()
bot_list = []

# Load price bots
if price_bots:
    logger.info("Preload initial coins")
    init_coins = price_bots.values()
    for c in init_coins:
        indexer.add_new_coin(c)

    for i, c in enumerate(price_bots.items()):
        chat_id = str(i + 1) if i + 1 > 9 else "0{}".format(i + 1)
        bot = price_bot.create_bot(*c, config['discord'].get('price_bot_avatar'),
                                   chat_id, config['discord']['command_roles'], indexer)
        loop.create_task(bot.start())
        bot_list.append(bot)

# Load info bots
if info_bots:
    for token, cfg in info_bots.items():
        cfg['command_roles'] = config['discord']['command_roles']
        cfg['token'] = token
        bot = info_bot.create_bot(cfg, indexer, twitter_collector)
        loop.create_task(bot.start())
        bot_list.append(bot)

indexer.run()
loop.run_forever()
