import os
import discord
from discord.ext import tasks

import logging
logging.basicConfig(level=logging.DEBUG)

MY_GUILD = os.getenv('MY_GUILD')
TOKEN = os.getenv('DISCORD_TOKEN')
LISTEN_CHAN = int(os.getenv('LISTEN_CHANNEL'))
WAIT_ROLE = int(os.getenv('WAITING_ROLE'))


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # start the task to run in the background
        self.say_hello.start()

    async def on_ready():
        logging.warn('Discord client ready!')

    async def on_message(self, message):
        if message.channel.id == LISTEN_CHAN:
            logging.info('Message in listening channel received!')
            await message.author.add_roles(discord.Object(WAIT_ROLE))

    @tasks.loop(seconds=5)
    async def say_hello(self):
        guild = self.get_guild(MY_GUILD)
        logging.warning('Hello World!')

    @say_hello.before_loop
    async def before_task(self):
        await self.wait_until_ready()

client = MyClient()
client.run(TOKEN)
