import os
import discord
import asyncio
from apscheduler.schedulers.async_ import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.workers.async_ import AsyncWorker

import logging
logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv('DISCORD_TOKEN')
LISTEN_CHAN = int(os.getenv('LISTEN_CHANNEL'))
WAIT_ROLE = int(os.getenv('WAITING_ROLE'))

client = discord.Client()


@client.event
async def on_message(message):
    if message.channel.id == LISTEN_CHAN:
      await message.author.add_roles(discord.Object(WAIT_ROLE))

async def say_hello():
    print('Hello World!')

async def scheduler():
    async with AsyncScheduler() as scheduler, AsyncWorker(scheduler.data_store):
        await scheduler.add_schedule(say_hello, IntervalTrigger(seconds=60))
        await scheduler.wait_until_stopped()

def main():
    loop = asyncio.get_event_loop()
    discord_task = asyncio.create_task(client.start(TOKEN))
    scheduler_task = asyncio.create_task(scheduler())

    gathered = await asyncio.gather(discord_task, scheduler_task)

client.run(TOKEN)
