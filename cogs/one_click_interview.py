import discord
from discord.ext import commands
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

WAITING_ROLE = int(os.getenv('WAITING_ROLE'))
PASSED_ROLE = int(os.getenv('PASSED_ROLE'))
FAILED_ROLE = int(os.getenv('FAILED_ROLE'))
ACTION_CHAN = int(os.getenv('INTERVIEW_ACTION_CHANNEL'))

OK_EMOJI = '✅'
FAIL_EMOJI = '⛔'

class OneClickInterview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("One-click interview cog initialized!")
        self.chan = None
        self.my_message = None
        self.current_confirmation_msg = None
        self.current_confirmation_target = None
        self.current_confirmation_action = None

    @commands.Cog.listener(name='on_ready')
    async def reset_everything(self):
        self.chan = self.bot.get_channel(ACTION_CHAN)
        if not self.chan:
            logger.error("Action channel was not in cache, fetching it now!")
            self.chan = await self.bot.fetch_channel(ACTION_CHAN)
            if self.chan is None:
                logger.error("Action channel could not be fetched, does it exist/can this bot access it?")
                raise ValueError("Error while finding channel")
        if not isinstance(self.chan, discord.TextChannel):
            logger.error(f"Action channel was not a text channel, it was a {type(chan)} {chan} -- WTF?!")
            raise TypeError("Found channel has wrong type?!")
        await self.reset_channel()

    
    async def reset_channel(self):
        await self.bot.chat_log("Resetting interview action channel")
        self.current_confirmation_msg = None
        self.current_confirmation_target = None
        self.current_confirmation_action = None
        
        await self.chan.purge(limit=None)
        self.my_message = await self.chan.send(f"If you are in an interview right now, you can use the {OK_EMOJI} button to pass the interview or {FAIL_EMOJI} to fail the interview.")
        await self.reset_reactions()

    async def reset_reactions(self):
        await self.my_message.clear_reactions()
        await self.my_message.add_reaction(OK_EMOJI)
        await self.my_message.add_reaction(FAIL_EMOJI)


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id: return
        if payload.channel_id != ACTION_CHAN:
            return

        logger.debug(f"Reaction deleted in my channel: {payload}")
        if self.my_message is None or payload.message_id == self.my_message.id:
            await self.bot.chat_log("Reaction deleted from my original message, resetting interaction.")
            logger.info("Reaction deleted from original message, resetting one-click interaction.")
            await self.reset_everything()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id: return
        if payload.channel_id != ACTION_CHAN:
            return
        
        logger.debug(f"Reaction added in my channel: {payload}")
        emoji = str(payload.emoji)
        if payload.message_id == self.my_message.id:
            if emoji in [OK_EMOJI, FAIL_EMOJI]:
                if self.current_confirmation_msg is not None:
                    await self.bot.chat_log(f"Received a reaction on the main message while we already had an active confirmation message?!")
                    await self.reset_everything()
                    return
                await self.construct_confirmation(payload)
                return

        elif self.current_confirmation_msg is not None and self.current_confirmation_msg.id == payload.message_id and self.current_confirmation_action == emoji:
            await self.execute_action()

    async def execute_action(self):
        await self.bot.chat_log(f"Received okay on performing action {self.current_confirmation_action} on member {self.current_confirmation_target.mention}")
        guild = self.my_message.channel.guild
        passed_role = guild.get_role(PASSED_ROLE)
        failed_role = guild.get_role(FAILED_ROLE)
        to_assign = passed_role if self.current_confirmation_action == OK_EMOJI else failed_role
        to_unassign = passed_role if self.current_confirmation_action != OK_EMOJI else failed_role

        target = self.current_confirmation_target

        if to_unassign in target.roles:
            await target.remove_roles(to_unassign)

        await target.add_roles(to_assign)
        await self.reset_everything()

    async def respond_then_reset(self, message):
        await self.chan.send(message)
        await asyncio.sleep(10)
        await self.reset_channel()

    async def send_confirmation_message(self):
        guild = self.my_message.channel.guild
        passed_role = guild.get_role(PASSED_ROLE)
        failed_role = guild.get_role(FAILED_ROLE)
        to_assign = passed_role if self.current_confirmation_action == OK_EMOJI else failed_role

        self.current_confirmation_msg = await self.chan.send(f"You are about to give the role {to_assign.mention} to {self.current_confirmation_target.mention}. If this is not what you wanted, remove the reaction on the original message.", allowed_mentions=discord.AllowedMentions.none())
        await self.current_confirmation_msg.add_reaction(self.current_confirmation_action)

    async def construct_confirmation(self, payload):
        guild = self.my_message.channel.guild
        member = guild.get_member(payload.user_id)
        if not member:
            logger.info("Unable to find the member who reacted.")
            return

        if member.voice is None or member.voice.channel is None:
            await self.respond_then_reset(f"{member.mention}, you do not appear to be in a voice channel. You have to be in a voice channel for this to work.")
            return

        vc = member.voice.channel
        members = vc.members
        members.remove(member)
        waiting_role = guild.get_role(WAITING_ROLE)
        passed_role = guild.get_role(PASSED_ROLE)
        failed_role = guild.get_role(FAILED_ROLE)
        waiting_targets = [i for i in members if waiting_role in i.roles]
        logger.debug(f"These members are waiting for their interviews and are in the VC: {waiting_targets}")
        if len(waiting_targets) == 1:
            await self.bot.chat_log(f"Found target with waiting role.")
            logger.debug("Only one member, that is the target.")
            self.current_confirmation_action = str(payload.emoji)
            self.current_confirmation_target = waiting_targets[0]
            return await self.send_confirmation_message()
        elif len(waiting_targets) >= 2:
            logger.debug("Too many possible targets.")
            targets_str = ", ".join([i.mention for i in waiting_targets])
            await self.respond_then_reset(f"{member.mention}, I cannot find a single target for your action. Here are the candidates: {targets_str}")
            return

        unassigned_targets = [i for i in members if passed_role not in i.roles and failed_role not in i.roles]
        logger.debug(f"These members have neither passed nor failed roles: {unassigned_targets}.")
        if len(unassigned_targets) == 1:
            await self.bot.chat_log(f"Found target with no pass-or-fail status.")
            logger.debug("Only one member, that is the target.")
            self.current_confirmation_action = str(payload.emoji)
            self.current_confirmation_target = unassigned_targets[0]
            return await self.send_confirmation_message()
        elif len(unassigned_targets) >= 2:
            logger.debug("Too many possible targets.")
            targets_str = ", ".join([i.mention for i in unassigned_targets])
            await self.respond_then_reset(f"{member.mention}, I cannot find a single target for your action. Here are the candidates: {targets_str}")
            return

        to_assign = passed_role if str(payload.emoji) == OK_EMOJI else failed_role
        logger.debug(f"This is an intention to assign role {to_assign}")
        opposite_polarity_targets = [i for i in members if to_assign not in i.roles]
        logger.debug(f"These members do not have it: {opposite_polarity_targets}")
        if len(opposite_polarity_targets) == 1:
            await self.bot.chat_log(f"Found target of opposite polarity to their current role.")
            logger.debug("Only one member, that is the target.")
            self.current_confirmation_action = str(payload.emoji)
            self.current_confirmation_target = opposite_polarity_targets[0]
            return await self.send_confirmation_message()
        elif len(opposite_polarity_targets) >= 2:
            logger.debug("Too many possible targets.")
            targets_str = ", ".join([i.mention for i in opposite_polarity_targets])
            await self.respond_then_reset(f"{member.mention}, I cannot find a single target for your action. Here are the candidates: {targets_str}")
            return

        await self.bot.chat_log(f"Fell through test cases, could not find target for action of {payload.emoji}.")
        await self.respond_then_reset(f"{member.mention}, I was unable to find any targets for your action.")
