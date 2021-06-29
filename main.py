import os
import discord
import logging
logging.basicConfig(level=logging.DEBUG)

TOKEN = os.getenv('DISCORD_TOKEN')
CHAN = int(os.getenv('TARGET_CHANNEL'))
ROLE = int(os.getenv('TARGET_ROLE'))

client = discord.Client()

@client.event
async def on_message(message):
    if message.channel.id == CHAN:
      await message.author.add_roles(discord.Object(ROLE))

client.run(TOKEN)
