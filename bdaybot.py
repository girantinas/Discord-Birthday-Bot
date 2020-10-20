import os
import json
import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks
import time, datetime
import asyncio

### Helper Functions ###

_MONTHNAMES = [None, 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                    'September', 'October', 'November', 'December']

def posixtime_to_str(posix_time):
    """Takes a posixtime and returns its representation in the following format:
    <Month Name> <Day> <Ordinal Suffix>, <Optional Year>. 
    Year 0 does not exist so it is used to indicate a date with no definite year.
    """
    dt = datetime.datetime.utcfromtimestamp(posix_time)
    suffix = 'th'
    if dt.day % 10 == 1:
        suffix = 'st'
    elif dt.day % 10 == 2:
        suffix = 'nd'
    elif dt.day % 10 == 3:
        suffix = 'rd'

    date_string = f"{_MONTHNAMES[dt.month]} {dt.day}{suffix}"

    # Only nonzero years are displayed
    if dt.year:
        date_string = f"{date_string}, {dt.year}"
    
    return date_string

# An implementation of current DST (Daylight Savings Time) rules for major US time zones 2007 and later.
# Adapted from: https://docs.python.org/3/library/datetime.html#datetime.tzinfo

ZERO = datetime.timedelta(0)
HOUR = datetime.timedelta(hours=1)
SECOND = datetime.timedelta(seconds=1)

def first_sunday_on_or_after(dt):
    """Finds the first sunday on or after a specific datetime.
    """
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        dt += datetime.timedelta(days_to_go)
    return dt

def us_dst_range(year):
    """ Returns start and end times for US DST on a given year after 2006.
    ---------------------------------------------------------------------
    US DST Rules

    This is a simplified (i.e., wrong for a few cases) set of rules for US
    DST start and end times. For a complete and up-to-date set of DST rules
    and timezone definitions, visit the Olson Database (or try pytz):
    http://www.twinsun.com/tz/tz-link.htm
    http://sourceforge.net/projects/pytz/ (might not be up-to-date)

    In the US, since 2007, DST starts at 2am (standard time) on the second
    Sunday in March, which is the first Sunday on or after Mar 8.
    and ends at 2am (DST time) on the first Sunday of Nov.
    """
    start = first_sunday_on_or_after(datetime.datetime(1, 3, 8, 2).replace(year=year))
    end = first_sunday_on_or_after(datetime.datetime(1, 11, 1, 2).replace(year=year))
    return start, end

class USTimeZone(datetime.tzinfo):
    """A Class representing a USTimeZone, complete with DST. Inherits from datetime.tzinfo.
    """

    def __init__(self, hours):
        self.stdoffset = datetime.timedelta(hours=hours)

    def utcoffset(self, dt):
        return self.stdoffset + self.dst(dt)

    def dst(self, dt):
        """Calculates the timezone offset due to DST. Overriden from the tzinfo interface.
        """
        assert dt is not None and dt.tzinfo is self, "Invalid Datetime Object"
        start, end = us_dst_range(dt.year)
        # Can't compare naive to aware objects, so strip the timezone from
        # dt first.
        dt = dt.replace(tzinfo=None)
        if start + HOUR <= dt < end - HOUR:
            # DST is in effect.
            return HOUR
        if end - HOUR <= dt < end:
            # Fold (an ambiguous hour): use dt.fold to disambiguate.
            return ZERO if dt.fold else HOUR
        if start <= dt < start + HOUR:
            # Gap (a non-existent hour): reverse the fold rule.
            return HOUR if dt.fold else ZERO
        # DST is off.
        return ZERO

    def fromutc(self, dt):
        """Overriding the fromutc function in tzinfo.
        """
        assert dt.tzinfo is self
        start, end = us_dst_range(dt.year)
        start = start.replace(tzinfo=self)
        end = end.replace(tzinfo=self)
        std_time = dt + self.stdoffset
        dst_time = std_time + HOUR
        if end <= dst_time < end + HOUR:
            # Repeated hour
            return std_time.replace(fold=1)
        if std_time < start or dst_time >= end:
            # Standard time
            return std_time
        if start <= std_time < end - HOUR:
            # Daylight savings time
            return dst_time

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
            await channel.send(f'🎊 Happy Birthday <@{userid}> 🎊')

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
    print("Initialized at{0:2d}:{1:2d}:{2:2d} on {3}/{4}/{5} (In the set Timezone)".format(now_dt.hour, now_dt.minute, now_dt.second, 
                                                                                            now_dt.month, now_dt.day, now_dt.year))
    # Want to execute at 12:01 AM the next day.
    midnight_dt = (now_dt + datetime.timedelta(days=1)).replace(hour=0, minute=1, second=0)
    #await asyncio.sleep(midnight_dt.timestamp() - time.time())

celebrate_all_server_birthdays.start()        
bot.run(TOKEN)