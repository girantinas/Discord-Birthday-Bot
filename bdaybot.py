import os
import json
import discord
import time, datetime
import asyncio
from dotenv import load_dotenv
from discord.ext import commands, tasks
from bdayhelpers import posixtime_to_str, USTimeZone

### Environment Setup ###

load_dotenv()
# Change these in .env file
TOKEN = os.getenv('DISCORD_TOKEN')
FOLDER_PATH = os.getenv('BIRTHDAY_FILE_PATH')
if not os.path.isdir(FOLDER_PATH):
    os.mkdir(FOLDER_PATH)

UTC_OFFSET = int(os.getenv('UTC_TIME_OFFSET_BIRTHDAY'))
IS_US_TIMEZONE = bool(os.getenv('IS_US_TIMEZONE_BIRTHDAY'))
if IS_US_TIMEZONE:
    TIMEZONE = USTimeZone(UTC_OFFSET)
else:
    TIMEZONE = datetime.timezone(datetime.timedelta(hours=UTC_OFFSET))

bot = commands.Bot(command_prefix='b!d ')

### Events ###

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    else:
        await bot.process_commands(message)
        if message.content == 'b!d':
            await message.channel.send("**So silly.** Do b!d help for help.")

### Commands ###

@bot.command(
    help = "Sets a user's birthday. Date must be in mm/dd[/yyyy] format. The year is optional.",
    brief = "Sets a user's birthday."
)
async def set(ctx, message):
    birthday_path = f'{FOLDER_PATH}/{ctx.guild.id}.txt'
    with open(birthday_path) as f:
        birthdays = json.load(f)
    try:
        date_given = message.split("/")
        assert 2 <= len(date_given) <= 3
        month, day = int(date_given[0]), int(date_given[1])
        # Year 0 means no year given.
        year = int(date_given[2]) if len(date_given) == 3 else 0
        dt = datetime.datetime(year, month, day)
        birthday = {'name': ctx.message.author.name, 
                    'bday': dt.replace(tzinfo=datetime.timezone.utc).timestamp()} # Gives a POSIX int timestamp to store, asssuming UTC timezone
        birthdays[str(ctx.message.author.id)] = birthday
        with open(birthday_path, 'w') as f:
            json.dump(birthdays, f)
        await ctx.channel.send(f"Your birthday has been set to {posixtime_to_str(birthday['bday'])}")
    except:
        await ctx.channel.send("Invalid birthday format. The format is ```b!d set mm/dd[/yyyy]```")

@bot.command(
    help = "Lists all users with their birthdays registered.",
    brief = "Lists all users with their birthdays registered."
)
async def list(ctx):
    birthday_path = f'{FOLDER_PATH}/{ctx.guild.id}.txt'
    try:
        with open(birthday_path) as f:
            birthdays = json.load(f)
    except json.decoder.JSONDecodeError:
        # Empty file or file doesn't exist.
        await ctx.channel.send('No birthdays set on this server.')
        return
    # Birthday (username, day) tuples in different lists for each month.
    birthday_list_month = [[],[],[],[],[],[],[],[],[],[],[],[]]
    for userid in birthdays:
        # Coversion from POSIX to datetime object
        birthday_dt = datetime.datetime.utcfromtimestamp(birthdays[str(userid)]['bday'])
        # Putting (userid, day) tuples in order of month (0-indexed: 0 = January)
        birthday_list_month[birthday_dt.month - 1] += [(userid, birthday_dt.day)]
    for month in birthday_list_month:
        # Sort tuples by day
        month.sort(key=lambda e: e[1])
    response = ''
    for month in birthday_list_month:
        for userid, day in month:
            # Assemble a response from the userids in order.
            response += '\n{}: {}'.format(birthdays[str(userid)]['name'], posixtime_to_str(birthdays[str(userid)]['bday']))
    await ctx.channel.send(response)

@bot.command(
    help = "Sets the current channel as the channel for birthday announcements to appear in.",
    brief = "Sets the channel for birthday announcements."
)
async def setchannel(ctx):
    channel_path = f'{FOLDER_PATH}/announcements.txt'
    with open(channel_path, 'w+'):
        try:
            channels = json.load(f)
        except:
            channels = {}
    channels[str(ctx.guild.id)] = str(ctx.channel.id)
    with open(channel_path, 'w') as f:
        json.dump(channels, f)
    await ctx.channel.send(f"<#{ctx.channel.id}> has been set to the channel for birthday announcements to appear in.")

### Tasks ###
async def celebrate_birthdays(serverid):
    """Takes a serverid and celebrates all birthdays in that server.
    Pings a user with a nice message in its designated announcements channel.
    """
    birthday_path = f'{FOLDER_PATH}/{serverid}.txt'
    with open(birthday_path) as f:
        try:
            birthdays = json.load(f)
        except json.decoder.JSONDecodeError:
            return
    channel_path = f'{FOLDER_PATH}/announcements.txt'
    with open(channel_path) as f:
        try:
            channels = json.load(f)
        except json.decoder.JSONDecodeError:
            return
    channelid = int(channels[str(serverid)])
    channel = bot.get_channel(channelid)
    now_dt = datetime.datetime.now(tz=TIMEZONE)
    for userid in birthdays:
        #The POSIX Times are naive based on UTC time enterred in.
        birthday_dt = datetime.datetime.fromtimestamp(birthdays[userid]['bday'], tz=datetime.timezone.utc)
        if birthday_dt.month == now_dt.month and birthday_dt.day == now_dt.day:
            print(f"{userid}'s bday was celebrated")
            await channel.send(f'🎊 Happy Birthday <@{userid}>!!!!!!!!!!!!!! 🎊')

@tasks.loop(hours=24)
async def celebrate_all_server_birthdays():
    """Celebrates every server's birthdays.
    """
    for filename in os.listdir(FOLDER_PATH):
        if filename != 'announcements.txt':
            serverid = int(filename[:-4])
            print(f"Celebrating ServerID {serverid}'s birthdays")
            await celebrate_birthdays(serverid)

@celebrate_all_server_birthdays.before_loop
async def before():
    await bot.wait_until_ready()
    now_dt = datetime.datetime.now(tz=TIMEZONE)
    print("Initialized at {0:0=2d}:{1:1=2d}:{2:2=2d} on {3}/{4}/{5} (In the set Timezone)".format(now_dt.hour, now_dt.minute, now_dt.second, 
                                                                                            now_dt.month, now_dt.day, now_dt.year))
    # Want to execute at 12:01 AM the next day.
    midnight_dt = (now_dt + datetime.timedelta(days=1)).replace(hour=0, minute=1, second=0)
    await asyncio.sleep(midnight_dt.timestamp() - time.time())

celebrate_all_server_birthdays.start()        
bot.run(TOKEN)