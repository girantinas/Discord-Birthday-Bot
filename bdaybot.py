import os
import json
import discord
from date import BirthDay
from dotenv import load_dotenv
from discord.ext import commands
import datetime

### Main Commands to Run the bot ###

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='b!d ')

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

@bot.command(
    help = "Sets a user's birthday. Date must be in mm/dd[/yyyy] format. The year is optional.",
    brief = "Sets a user's birthday."
)
async def set(ctx, message):
    if not date_given:
        await ctx.channel.send("Usage: ```b!d set mm/dd[/yyyy]``` The year is optional.")
    else:
        with open('birthdays.txt') as f:
            birthdays = json.load(f)
        try:
            date_given = message.split("/")
            assert 2 <= len(date_given) <= 3
            month, day = date_given[0], date_given[1]
            #Year 0 means no year given.
            year = date_given[2] if len(date_given) == 3 else 0
            assert 0 <= day <= 31
            assert 1 <= month <= 12
            dt = datetime.datetime(year, month, day)
            birthday = {'name': ctx.message.author.name, 
                        'bday': dt.replace(tzinfo=timezone.utc).timestamp()} #Gives a POSIX int timestamp to store, asssuming UTC timezone
            birthdays[ctx.message.author.id] = birthday
            with open('birthdays.txt', 'w') as f:
                json.dump(birthdays, f)
            await ctx.channel.send("Your birthday has been set to " + posixtime_to_str(birthday['bday']))
        except:
            await ctx.channel.send("Invalid birthday format. The format is ```b!d set mm/dd[/yyyy]```")

@bot.command(
    help = "Lists all users with their birthdays registered.",
    brief = "Lists all users with their birthdays registered."
)
async def list(ctx):
    with open('birthdays.txt') as f:
        birthdays = json.load(f)
    response = ''
    #Birthday (username, day) tuples in different lists for each month.
    birthday_list_month = [[],[],[],[],[],[],[],[],[],[],[],[]]
    for userid in birthdays:
        #Coversion from POSIX to datetime object
        birthday_dt = datetime.datetime.utcfromtimestamp(birthdays[userid]['bday'])
        #Putting (userid, day tuples) in order of month (0-indexed: 0 = January)
        birthday_list_month[birthday_dt.month - 1] += [(userid, birthday_dt.day)]
    for month in birthday_list_month:
        #Sort tuples by day
        month.sort(key=lambda e: e[1])
    for month in birthday_list_month:
        for userid, day in month:
            #Assemble a response from the userids in order.
            response += '\n' + username + ': ' + posixtime_to_str(birthdays[userid]['bday'])
    await ctx.channel.send(response)

@bot.command(
    help = "This command has not been implemented yet.",
    brief = "To be implemented."
)
async def until(ctx):     
    await ctx.channel.send("This command has not been implemented yet.")

bot.run(TOKEN)

### Helper Functions ###

_MONTHNAMES = [None, 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                    'September', 'October', 'November', 'December']

def posixtime_to_str(time):
    """Takes a posixtime and returns its representation in the following format:
    <Month Name> <Day> <Ordinal Suffix>, <Optional Year>. 
    Year 0 does not exist so it is used to indicate a date with no definite year.
    """
    dt = datetime.datetime.utcfromtimestamp(time)
    suffix = 'th'
    if dt.day % 10 == 1:
        suffix = 'st'
    elif dt.day % 10 == 2:
        suffix = 'nd'
    elif dt.day % 10 == 3:
        suffix = 'rd'

    date_string = "{0} {1}{2}".format(_MONTHNAMES[dt.month], dt.day, suffix)

    #Only nonzero years are displayed
    if dt.day.year:
        date_string = "{0}, {1}".format(date_string, dt.year)
    
    return date_string