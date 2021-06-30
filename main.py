import os
import discord
from discord.ext import tasks
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import logging
logging.basicConfig(level=logging.DEBUG)

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
        logging.warning('Hello World!')

    @say_hello.before_loop
    async def before_task(self):
        await self.wait_until_ready()

client = MyClient()
client.run(TOKEN)
