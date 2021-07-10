import discord
from discord.ext import commands
import os
import logging
import asyncio

PASSED_ROLE = int(os.getenv('PASSED_ROLE'))
FAILED_ROLE = int(os.getenv('FAILED_ROLE'))
INT_CHAN = int(os.getenv('INTERVIEW_VC'))

class MusicOnInterviewComplete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logging.info("Music cog initialized!")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        added_roles = set(after.roles) - set(before.roles)
        state = 0 # 0 for no change, 1 for passed, -1 for failed
        for role in added_roles:
            if role.id == FAILED_ROLE:
                state = -1
            elif role.id == PASSED_ROLE and state == 0:  # failed beats passed; if there is a "failed" role, then the sound effect to play is still "failed".
                state = 1

        if not state: return

        if after.voice is None or after.voice.channel is None:
            logging.debug(f"Member {after} is not in a voice channel, not playing music.")

        if state:
            logging.info(f"Passed status changed for member {after}: {state}")
            filenames = {1: '/interview-ok.mkv', -1: '/interview-fail.mkv'}
            await self.bot.chat_log(f"Member {after.mention} changed their interview state to {state} while in a voice channel, playing `{filenames[state]}`")
            source = discord.FFmpegOpusAudio(filenames[state])
            client = await after.voice.channel.connect()
            client.play(source)
            while client.is_playing():
                await asyncio.sleep(0.5)

            await client.disconnect()

            if after.voice.channel.id == INT_CHAN:
                await self.bot.chat_log(f"{after.mention} is currently in the interview channel, disconnecting them.")
                await after.move_to(None, reason="Member completed interview while in an interview channel")
