import logging

import discord
from discord.ext.commands import Bot


class BaseBot(Bot):

    def __init__(self,
                 token,
                 name,
                 status,
                 avatar=None,
                 *args,
                 **kwargs):
        super(BaseBot, self).__init__(case_insensitive=True, *args, **kwargs)
        self.token = token
        self.name = name
        self.avatar = avatar
        self.status = status
        self.command_roles = set()
        self.logger = logging.getLogger("{} bot".format(self.name))
        self.logger.info("Starting {} bot...".format(self.name))

    async def message_channels(self, msg, channels):
        for c in channels:
            z = self.get_channel(c)
            try:
                if not z:
                    raise AssertionError("Channel {} does not exist".format(c))
                await z.send(msg)
                self.logger.debug("Sent message '{}...' to channel {} ({}) on {}".format(msg[:20], z.name, c, z.guild.name))
            except Exception as e:

                info = "({}) on server {}".format(z.name, z.guild.name) if z else ""
                self.logger.error("Failed sending to channel {} - {} due to {}".format(c, info, e))

    async def update_nick(self):
        for g in self.guilds:
            m = [u for u in g.members if u.id == self.user.id]
            if not m:
                self.logger.warning("No matching member id found for {}".format(g.id))
                continue
            elif len(m) > 1:
                self.logger.warning("Multiple matches found for id for {} - using first match".format(g.id))

            act = discord.Activity(type=discord.ActivityType.unknown, name="you")
            await m[0].edit(nick="{}".format(self.name))
            await self.change_presence(status=discord.Status.online, activity=act)
            if self.avatar:
                self.logger.info("Updating avatar to: {}".format(self.avatar))
                with open(self.avatar, 'rb') as image:
                    await self.user.edit(avatar=image.read())
                    self.logger.info("Updated avatar")

    def user_role_allowed(self, ctx):

        if not self.command_roles:
            return True

        overlap = {r.name.lstrip('@').lower() for r in ctx.author.roles} & self.command_roles
        return len(overlap) != 0

    def parse_command_roles(self, command_roles):
        return {c.lower() for c in command_roles} if command_roles else set()

    async def start(self):
        await super().start(self.token)
