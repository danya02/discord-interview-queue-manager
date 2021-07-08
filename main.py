import os
import discord
from discord.ext import tasks, commands
import datetime
import time

import logging
logging.basicConfig(level=logging.INFO)

import cogs.music_on_interview_complete as music
import cogs.remove_waiting_on_interview_complete as remove_waiting_on_interview_complete

MY_GUILD = os.getenv('MY_GUILD')
TOKEN = os.getenv('DISCORD_TOKEN')
LISTEN_CHAN = int(os.getenv('LISTEN_CHANNEL'))
WAIT_ROLE = int(os.getenv('WAITING_ROLE'))
PASS_ROLE = int(os.getenv('PASSED_ROLE'))
FAIL_ROLE = int(os.getenv('FAILED_ROLE'))

NO_APPLY_ROLES = [
        (86400, int(os.getenv('NO_APPLY_1DAY')), "one day"),
        (3*86400, int(os.getenv('NO_APPLY_3DAYS')), "3 days"),
        (7*86400, int(os.getenv('NO_APPLY_7DAYS')), "7 days"),
        (14*86400, int(os.getenv('NO_APPLY_14DAYS')), "14 days"),
        ]

NO_APPLY_CHAN = os.getenv('NO_APPLY_NOTIFICATION_CHANNEL')

CHECK_INTERVAL = 60

class MyClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, command_prefix='&&&&&&&&', **kwargs)
        self.last_checked = 0

        # start the task to run in the background
        self.check_for_old_members.start()

        self.add_cog(music.MusicOnInterviewComplete(self))
        self.add_cog(remove_waiting_on_interview_complete.RemoveWaitingOnInterviewComplete(self))

    async def on_ready(self):
        logging.warning('Discord client ready!')

    async def on_message(self, message):
        if message.channel.id == LISTEN_CHAN:
            logging.info('Message in listening channel received!')
            await message.author.add_roles(discord.Object(WAIT_ROLE))

    async def clear_no_apply_roles(self, member):
        logging.info(f'Clearing no-apply roles for {member.display_name}, they now have {member.roles}')
        role_ids = [i.id for i in member.roles if i]
        roles_to_remove = []
        for _, role, __ in NO_APPLY_ROLES:
            if role in role_ids:
                roles_to_remove.append(discord.Object(role))
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)


    @tasks.loop(seconds=30)
    async def check_for_old_members(self):
        self.last_checked = time.time()
        logging.info('Checking old members now!')
        guild = self.get_guild(MY_GUILD)
        logging.warn('Getting guild failed, fetching instead.')
        if guild is None:
            guild = await self.fetch_guild(MY_GUILD)
            if guild is None:
                logging.error('Guild received is None!')
                return
            members = await guild.chunk()
        else:
            members = guild.members
        notify_chan = await self.fetch_channel(NO_APPLY_CHAN)
        logging.info('Ready to examine members of guild')
        for member in members:
            logging.info(f'Examining member {member.display_name}, they joined at {member.joined_at}')
            # if member has any of the interview-related roles, do not notify.
            role_ids = [i.id for i in member.roles if i]
            logging.info(f'This member has these roles: {member.roles}')
            if WAIT_ROLE in role_ids or PASS_ROLE in role_ids or FAIL_ROLE in role_ids or member.bot:
                logging.info('This member has a role which prevents notifications')
                await self.clear_no_apply_roles(member)
                continue

            # if we cannot determine when the member joined, send a message saying so and add the final interval role.
            if member.joined_at is None:
                longest_delay_role = NO_APPLY_ROLE[-1][1]
                if longest_delay_role not in role_ids:
                    logging.info(f'Sending message to {member.display_name} about how we do not know their join date')
                    await chan.send(f'{member.mention}, I am not able to determine the date when you joined this server. Because of this, this is the only time I can remind you to apply for an interview. Please look at <#859356937979822100> for more information.')
                    await member.add_roles(discord.Object(longest_delay_role))
            else:
                joined_seconds_ago = (datetime.datetime.utcnow() - member.joined_at).total_seconds()
                longer_than_interval = [False for _ in NO_APPLY_ROLES]
                index_not_active = 0
                index_active = -1
                human_descriptions = []

                # find boundary between passed and not-passed intervals
                for index, data in enumerate(NO_APPLY_ROLES):
                    interval, role_id, human_desc = data
                    human_descriptions.append(human_desc)
                    if joined_seconds_ago > interval:
                        longer_than_interval[index] = True
                        index_active = index
                        index_not_active = index+1
                logging.info(f'Member {member.display_name} joined {joined_seconds_ago}s ago, intervals: {longer_than_interval}')

                # if the member already has the role saying they got this message, do not send it
                logging.info(f'This member should have this role now: {NO_APPLY_ROLES[index_active]}')
                if NO_APPLY_ROLES[index_active][1] in role_ids:
                    logging.info('This member already has the role they should at this time.')
                    continue

                if not any(longer_than_interval):
                    logging.info('This member is too young, not sending messages.')
                    continue

                text = f'{member.mention}, you have been a member of this server for {human_descriptions[index_active]}, but you have not yet applied for the onboarding interview. You must pass the interview to get access to the Minecraft server, and without it you will only be able to chat in public channels. Please look at <#859356937979822100> for more information.\n\n'
                if all(longer_than_interval):
                    text += 'This was your last notification, I will not notify you to apply for the onboarding interview anymore.'
                else:
                    times_left = len([i for i in longer_than_interval if not i])
                    S = 's' if times_left > 2 else ''
                    text += f'I will remind you about this {times_left} more time{S}, the next time will be when you\'ve been a member for {human_descriptions[index_not_active]}.'

                await notify_chan.send(text)
                await self.clear_no_apply_roles(member)
                await member.add_roles(discord.Object(NO_APPLY_ROLES[index_active][1]))



    @check_for_old_members.before_loop
    async def before_task(self):
        await self.wait_until_ready()

intents = discord.Intents.default()
intents.members=True
client = MyClient(intents=intents)
client.run(TOKEN)
