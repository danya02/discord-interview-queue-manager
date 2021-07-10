import discord
from discord.ext import commands
import os
import logging
import asyncio
import datetime

logger = logging.getLogger(__name__)

DISBOARD_ID = 302050872383242240
TIMEOUT = 120*60
MY_REACTION = '⌛'

class DisboardReaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logging.info("Disboard reminder cog initialized!")

    async def add_reaction(self, message):
        has_reaction = False
        for react in message.reactions:
            if react.emoji == MY_REACTION and react.me: has_reaction = True
        if not has_reaction:
            logger.debug(f"Reaction added to {message}")
            await self.bot.chat_log(embed=discord.Embed(description=f"Adding reaction to [this]({message.jump_url}) message by Disboard."))
            await message.add_reaction(MY_REACTION)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == DISBOARD_ID:
            loop = asyncio.get_event_loop()
            now = datetime.datetime.now()
            msg_at = message.created_at
            send_at = msg_at + datetime.timedelta(seconds=TIMEOUT)
            time_left = send_at - now
            if time_left.total_seconds()<0:
                logger.info(f"Received a message from Disboard, and the reaction should have occurred {-time_left.total_seconds()} seconds ago, running now.")
                await self.add_reaction(message)
                return
            logger.info(f"Received a message from Disboard, scheduling reaction to run in {time_left}.")
            loop.call_later(time_left.total_seconds(), self.add_reaction(message))

    @commands.Cog.listener()
    async def on_ready(self):
        logger.debug("Checking channels for new messages from Disboard.")
        for chan in self.bot.get_all_channels():
            if not isinstance(chan, discord.TextChannel): continue
            member_ids = [i.id for i in chan.members]
            if DISBOARD_ID not in member_ids: continue
            logger.debug(f"{chan} is a channel that Disboard can access.")
            async for msg in chan.history():
                if msg.author.id == DISBOARD_ID:
                    await self.on_message(msg)
