import logging

import discord
from discord.ext.commands import Bot


class BaseBot(Bot):

    def __init__(self,
                 token,
                 name,
                 avatar=None,
                 *args,
                 **kwargs):
        super(BaseBot, self).__init__(case_insensitive=True, *args, **kwargs)
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
