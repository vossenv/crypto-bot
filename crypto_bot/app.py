# Init application
import asyncio
import sys

from crypto_bot import bots
from crypto_bot.config import ConfigLoader, init_logger
from crypto_bot.exchanges import Exchange
from crypto_bot.price_indexer import PriceIndexer

try:
    cfg = sys.argv[1]
except:
    cfg = None

bot_list = []
bots.config_loader = ConfigLoader(cfg)
config = bots.config_loader.active_config

logger = init_logger(config['process']['log_level'])
logger.info("Config loaded")

exchanges = [Exchange(dict(c)) for c in config['exchanges']]
indexer = PriceIndexer(exchanges, config['process']['update_rate'])

logger.info("Start Bots")
loop = asyncio.get_event_loop()
for i, c in enumerate(config['discord']['bots'].items()):
    chat_id = str(i + 1) if i + 1 > 9 else "0{}".format(i + 1)
    bot = bots.create_bot(*c, chat_id, config['discord']['command_roles'], indexer)
    loop.create_task(bot.start())
    bot_list.append(bot)

indexer.run()
loop.run_forever()
