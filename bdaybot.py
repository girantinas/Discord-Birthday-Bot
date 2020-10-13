import os
import json
import discord
from date import Date
from dotenv import load_dotenv
from discord.ext import commands

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
async def set(ctx, date_given):
    if not date_given:
        await ctx.channel.send("Usage: ```b!d set mm/dd[/yyyy]``` The year is optional.")
    else:
        with open('birthdays.txt') as f:
            birthdays = json.load(f)
        try:
            month, day = int(date_given[:2]), int(date_given[3:5])
            assert 0 <= day <= 31
            assert 1 <= month <= 12
            year = int(date_given[6:]) if len(date_given) > 5 else 0
            birthday = Date(year, month, day)
            birthdays[ctx.author.name] = birthday.get_list()
            with open('birthdays.txt', 'w') as f:
                json.dump(birthdays, f)
            await ctx.channel.send("Your birthday has been set to " + birthday.to_str())
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
    for username in birthdays:
        birthday = Date(lst=birthdays[username])
        #Putting (username, day tuples) in order of month (0-indexed: 0 = January)
        birthday_list_month[birthday.get_month() - 1] += [(username, birthday.get_day())]
    for month in birthday_list_month:
        #Sort tuples by day
        month.sort(key=lambda e: e[1])
    for month in birthday_list_month:
        for username, day in month:
            #Assemble a response from the usernames in order.
            response += '\n' + username + ': ' + Date(lst=birthdays[username]).to_str()
    await ctx.channel.send(response)

@bot.command(
    help = "This command has not been implemented yet.",
    brief = "To be implemented."
)
async def until(ctx):     
    await ctx.channel.send("This command has not been implemented yet.")

bot.run(TOKEN)
