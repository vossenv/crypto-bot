# Init application
import asyncio
import sys

from crypto_bot.bots import price_bot, bot_globals, info_bot, message_bot
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

loop = asyncio.get_event_loop()
bot_list = []

price_bots = config['discord'].get('price_bots')
info_bots = config['discord'].get('info_bots')
msg_bots = config['discord'].get('message_bots')

if price_bots or info_bots:
    exchanges = [Exchange.create(c, dict(d)) for c, d in config['exchanges'].items()]
    bot_globals.indexer = PriceIndexer(exchanges, config['process']['update_rate'])
    bot_globals.indexer.wait_exchanges()

    # Load price bots
    if price_bots:
        logger.info("Preload initial coins")

        for sid, server in price_bots.items():
            # init_coins = server['instances'].values()
            # for c in init_coins:
            #     bot_globals.indexer.add_new_coin(c)

            for i, c in enumerate(server['instances'].items()):
                bot_globals.indexer.add_new_coin(c[1])
                chat_id = str(i + 1) if i + 1 > 9 else "0{}".format(i + 1)
                bot = price_bot.create_bot(
                    token=c[0],
                    coin=c[1],
                    status=None,
                    avatar=server.get('avatar'),
                    chat_id=chat_id,
                    command_roles=server.get('command_roles'),
                    use_coin_avatar=server.get('use_coin_avatar'),
                    home_id=sid,
                    indexer=bot_globals.indexer,
                )

                loop.create_task(bot.start())
                bot_list.append(bot)

    # Load info bots
    if info_bots:
        twitter_cfg = config.get('twitter')
        twitter_collector = TwitterCollector(twitter_cfg) if twitter_cfg else None

        for token, cfg in info_bots.items():

            cfg['token'] = token
            countdowns = cfg.get('countdowns') or {}
            cfg['countdowns'] = []
            for c in countdowns:
                alert = config['discord']['countdowns'][c]
                alert['channels'] = countdowns[c]
                cfg['countdowns'].append(alert)

            bot = info_bot.create_bot(
                token=cfg['token'],
                name=cfg['name'],
                status=cfg.get('status'),
                avatar=cfg.get('avatar'),
                countdowns=cfg['countdowns'],
                new_coin_notifications=cfg.get('new_coin_notifications'),
                twitter_notifications=cfg.get('twitter_notifications'),
                indexer=bot_globals.indexer,
                twitter_collector=twitter_collector
            )
            loop.create_task(bot.start())
            bot_list.append(bot)

    bot_globals.indexer.run()

if msg_bots:

    for token, cfg in msg_bots.items():
        cfg['token'] = token

        bot = message_bot.create_bot(
            token=cfg['token'],
            name=cfg['name'],
            command_roles=cfg.get('command_roles'),
            log_channel_mismatch=cfg.get('log_channel_mismatch'),
            status=cfg.get('status'),
            avatar=cfg.get('avatar'),
            mappings=cfg['channel_mappings']
        )

        loop.create_task(bot.start())
        bot_list.append(bot)

if bot_list:
    loop.run_forever()
else:
    logger.warning("No bots were defined in the config.")
