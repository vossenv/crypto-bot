import csv
import os

from discord import Message

from crypto_bot.bots import bot_globals
from crypto_bot.bots.base_bot import BaseBot


class MessageBot(BaseBot):

    def __init__(self,
                 mappings,
                 command_roles,
                 log_channel_mismatch,
                 *args,
                 **kwargs):
        super(MessageBot, self).__init__(*args, **kwargs)
        self.command_roles = self.parse_command_roles(command_roles)
        self.mappings_by_channel = mc = {}
        self.log_channel_mismatch = log_channel_mismatch

        for m in mappings:

            rc = self.process_mapping(m['read_channels'])
            wc = self.process_mapping(m['write_channels'])

            for c in rc:
                if c not in mc:
                    mc[c] = []
                mc[c].extend(wc)

    def process_mapping(self, mapping) -> list:

        if isinstance(mapping, list):
            return mapping

        path = mapping['file']

        ignore = mapping.get("ignore") or []
        ignore = [ignore] if isinstance(ignore, str) else ignore

        if not os.path.exists(path):
            raise FileNotFoundError("Path {} does not exist".format(path))
        with open(path, "r", newline='') as f:
            reader = csv.DictReader(f)
            raw = [r for r in reader]
            channels_by_header = {k: [] for k in reader.fieldnames}

            for r in raw:
                for i in r:
                    if i in ignore:
                        continue
                    try:
                        channels_by_header[i].append(int(r[i]))
                    except ValueError:
                        self.logger.debug("Skipping value {} in column {} as it is not an integer".format(r[i], i))

        selected_channels = []

        cols = mapping['columns']
        cols = [cols] if isinstance(cols, str) else cols

        for c in cols:
            if c not in channels_by_header:
                raise AssertionError("Column {} not found in csv: {}".format(c, path))
            selected_channels.extend(channels_by_header[c])

        return selected_channels

    async def ready(self):
        self.cmd_callbacks = {c.name: c.callback for c in self.commands}
        await self.update_nick()

    async def handle_message(self, message):

        if not self.user_role_allowed(message):
            return

        if message.author.id == self.user.id:
            return

        content = str(message.content)
        if content.startswith(self.command_prefix):
            return

        # content
        # cmd = content[1:].lower().strip()

        for a in message.attachments:
            content += "\n"
            content += a.url

        from_id = message.channel.id
        read_ch = message.channel.name
        read_sv = message.guild.name

        if from_id in self.mappings_by_channel:
            for m in self.mappings_by_channel[from_id]:
                if self.log_channel_mismatch:
                    write_ch = self.get_channel(m)
                    if write_ch.name != read_ch:
                        write_sv = self.get_channel(m).guild.name
                        self.logger.warning("Channel name mismatch: Reading from '{}' on '{}' "
                                            "and writing to '{}' on '{}'".format(read_ch, read_sv, write_ch, write_sv))
            await self.message_channels(content, self.mappings_by_channel[from_id])


def create_bot(**kwargs):
    bot = MessageBot(command_prefix="!", **kwargs)
    bot_globals.add_shared_setup(bot)

    @bot.event
    async def on_message(message: Message, *args, **kwargs):
        await bot.handle_message(message)

    return bot
