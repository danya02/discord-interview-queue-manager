import discord
from discord.ext import commands
import os
import logging
import asyncio

WAITING_ROLE = int(os.getenv('WAITING_ROLE'))
PASSED_ROLE = int(os.getenv('PASSED_ROLE'))
FAILED_ROLE = int(os.getenv('FAILED_ROLE'))

class RemoveWaitingOnInterviewComplete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logging.info("Delete waiting role cog initialized!")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        role_ids = [i.id for i in after.roles]
        if PASSED_ROLE in role_ids or FAILED_ROLE in role_ids:
            if WAITING_ROLE in role_ids:
                logging.info(f"Removing waiting role for {after}")
                await after.remove_roles(discord.Object(WAITING_ROLE), reason="Waiting role is incompatible with" + ("passed role" if PASSED_ROLE in role_ids else "failed role"))

