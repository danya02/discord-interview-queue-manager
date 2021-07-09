import discord
from discord.ext import commands
import os
import logging
import asyncio
import random

BALLS_EMOJI = '''🔮
⚽
🍙
🧶
⛹️
🎾
🏓
🎱
⚾
🥎
🏀
🏐
🏉
🏈
🎳'''.strip().split()

class BallsReaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logging.info("Balls cog initialized!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if 'balls' in message.content.lower():
            random.shuffle(BALLS_EMOJI)
            my_emojis = BALLS_EMOJI[:3]
            for i in my_emojis:
                logging.debug(f"Reacting to {message} with {i}")
                await message.add_reaction(i)
