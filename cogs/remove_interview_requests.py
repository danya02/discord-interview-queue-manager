import discord
from discord.ext import commands
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

WAITING_ROLE = int(os.getenv('WAITING_ROLE'))
PASSED_ROLE = int(os.getenv('PASSED_ROLE'))
FAILED_ROLE = int(os.getenv('FAILED_ROLE'))
CHAN = int(os.getenv('LISTEN_CHANNEL'))

class RemoveStaleInterviewRequests(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Remove stale interview requests cog initialized!")
        self.chan = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.chan = self.bot.get_channel(CHAN)

        self.passed_role = self.chan.guild.get_role(PASSED_ROLE)
        self.failed_role = self.chan.guild.get_role(FAILED_ROLE)

    def is_stale(self, message):
        logger.debug(f"Checking message {message}")
        if message.pinned:
            logger.debug(f"It is pinned, so it should not be deleted")
            return False
        if message.flags.urgent:
            logger.debug(f"It is urgent, so it should not be deleted")
            return False
        if message.author not in message.channel.guild.members:
            logger.debug("The member is not in the guild now, so delete it")
            return True
        roles = message.author.roles
        if self.passed_role in roles or self.failed_role in roles:
            logger.debug(f"The member does has a passed or failed role, delete it")
            return True

    async def delete_stale(self):
        if self.chan is None:
            logger.warning("Trying to delete stale messages too early, when channel is None.")
            return

        if self.passed_role is None or self.failed_role is None:
            logger.error("One of the roles is not present! For safety, not continuting with deleting!")
            return

        await self.chan.guild.chunk()  # Refresh member cache to be sure that member information is up-to-date
        await self.chan.purge(limit=None, check=self.is_stale)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        logger.info(f"{member} joined, running stale pruning")
        await self.delete_stale()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        logger.info(f"{member} left, running stale pruning")
        await self.delete_stale()


    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        difference = set(before.roles).symmetric_difference(set(after.roles))
        if self.passed_role is None or self.failed_role is None:
            await self.on_ready()
        
        logger.info(f"{after} updated relevant roles, running stale pruning")

        if self.passed_role in difference or self.failed_role in difference:
            await self.delete_stale()


