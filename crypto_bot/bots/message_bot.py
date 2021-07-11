import logging

import discord
from discord.ext.commands import Bot, CommandNotFound, MissingRequiredArgument

class MessageBot(Bot):

    def __init__(self,
                 token,
                 name,
                 avatar=None,
                 *args,
                 **kwargs):
        super(MessageBot, self).__init__(*args, **kwargs)
        self.token = token
        self.name = name
        self.avatar = avatar
        self.logger = logging.getLogger("{} bot".format(self.name))
        self.logger.info("Starting {} bot...".format(self.name))

    async def ready(self):
        await self.update_nick()

    async def message_channels(self, msg, channels):
        for c in channels:
            try:
                z = self.get_channel(c)
                if not z:
                    raise AssertionError("Channel {} does not exist".format(c))
                await z.send(msg)
            except Exception as e:
                self.logger.error(e)

    async def update_nick(self):
        for g in self.guilds:
            m = [u for u in g.members if u.id == self.user.id]
            if not m:
                self.logger.warning("No matching member id found for {}".format(g.id))
                continue
            elif len(m) > 1:
                self.logger.warning("Multiple matches found for id for {} - using first match".format(g.id))

            act = discord.Activity(type=discord.ActivityType.watching, name="you")
            await m[0].edit(nick="{}".format(self.name))
            await self.change_presence(status=discord.Status.online, activity=act)
            if self.avatar:
                self.logger.info("Updating avatar to: {}".format(self.avatar))
                with open(self.avatar, 'rb') as image:
                    await self.user.edit(avatar=image.read())
                    self.logger.info("Updated avatar")

    async def start(self):
        await super().start(self.token)


def create_bot(config, indexer, twitter_collector):
    bot = CryptoBot(command_prefix="!",
                    token=config['token'],
                    name=config['name'],
                    avatar=config.get('avatar'),
                    countdowns=config['countdowns'],
                    new_coin_notifications=config.get('new_coin_notifications'),
                    twitter_notifications=config.get('twitter_notifications'),
                    indexer=indexer,
                    twitter_collector=twitter_collector,
                    case_insensitive=True)

    @bot.event
    async def on_ready():
        bot.logger.info("{} is ready!".format(bot.name))
        await bot.ready()


    # feed

    # rule


    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, CommandNotFound) or isinstance(error, MissingRequiredArgument):
            try:
                int(ctx.invoked_with)
                return
            except Exception:
                await ctx.send(error.args[0])
        raise error

    return bot
