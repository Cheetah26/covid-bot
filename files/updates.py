import os

# For getting the pdf
from datetime import datetime, timedelta
import requests

# For making the image from the pdf
import pdf2image
import io

# For the config file
import configparser

# For loading token
from dotenv import load_dotenv

# For discord
from discord.ext import commands, tasks
import discord

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

config = configparser.ConfigParser()
config.read('/usr/src/app/data/data.ini')

bot = commands.Bot(command_prefix="!cb ")

@bot.command(
    brief="Get the latest report",
    help="Sends the most recent known COVID report"
)
async def latest(ctx):
    await ctx.send(file=discord.File('/usr/src/app/data/latest.png'))
    if ctx.guild:
        print('{}: Sent update in {}: {}'.format(datetime.now(), ctx.channel.guild.name, ctx.channel.name))
    else:
        print('{}: Sent update to user {}'.format(datetime.now(), ctx.author))

@bot.command(
    brief="Start updates",
    help="Enable this channel to begin recieving updates"
)
async def start(ctx):
    # Determine where the message was sent
    if ctx.guild:
        # Check author's permissions
        if ctx.author.guild_permissions.manage_channels:
            await ctx.send("I will send updates here!")
            write_config('channels', ctx.channel.id, 'yes')
        else:
            await ctx.send("Sorry, you don't have permission to do that")
    elif ctx.guild == None:
        # Handle command in DM
        await ctx.send("Ok, I'll start DM'ing you updates!")
        write_config('users', ctx.author.id, 'yes')
    else:
        # Catch-all
        await ctx.send("I'm not sure how to that here")

@bot.command(
    brief="Stop updates",
    help="Remove this channel from future updates"
)
async def stop(ctx):
    # Determine where the message was sent
    if isinstance(ctx.author, discord.Member):
        # Check author's permissions
        if ctx.author.guild_permissions.manage_channels:
            await ctx.send("I'll stop sending updates here")
            write_config('channels', ctx.channel.id, 'no')
        else:
            await ctx.send("Sorry, you don't have permission to do that")
    elif ctx.message.guild == None:
        # Handle command in DM
        await ctx.send("I'll stop sending updates here")
        write_config('users', ctx.author.id, 'no')
    else:
        # Catch-all
        await ctx.send("I'm not sure how to that here")

# The main runner
@bot.event
async def on_ready():
    print('ready {}'.format(datetime.now()))
    send_update.start()

@tasks.loop(minutes=10)
async def send_update():
    # Determine if it is a new weekday
    last = datetime.strptime(config['main']['lastupdate'], '%Y-%m-%d')
    today = datetime.today()
    if today.weekday() < 5 and (today - last).days > 0:
        if datetime.now().hour > 7:
            print("{}: Valid day and time".format(datetime.now()))
            # Has a new pdf been released
            url = 'https://www.unh.edu/sites/default/files/departments/coronavirus_covid-19/unh_covid-19_test_results_{}.{}.{}_7am.pdf'.format(today.month, today.day, today.strftime("%y"))
            print("Checking url: " + url)
            req = requests.get(url)
            if req.status_code == 200:
                # Convert and save the image
                pages = pdf2image.convert_from_bytes(req.content)
                pages[0].save('/usr/src/app/data/latest.png', 'PNG')
                # Send the image to all recipients
                await send_to_channels()
                await send_to_users()
                # Update the data file
                write_config('main', 'lastupdate', today.strftime('%Y-%m-%d'))
            else:
                print('{}: Request failed with status {}'.format(datetime.now(), req.status_code))

# Channel things
async def get_channels():
    channels = []
    for channelID in config['channels']:
        if config['channels'][channelID] == 'yes':
            channels.append(await bot.fetch_channel(channelID))
    return channels

async def send_to_channels():
    activeChannels = await get_channels()
    print("Sending image to channels:\n\t", end="")
    print_list = []
    for channel in activeChannels:
        print_list.append("{}: {}".format(channel.guild.name, channel.name))
        await channel.send(file=discord.File('/usr/src/app/data/latest.png'))
    print(*print_list, sep = ", ")

# User things
async def get_users():
    users = []
    for userID in config['users']:
        if config['users'][userID] == 'yes':
            users.append(await bot.fetch_user(userID))
    return users

async def send_to_users():
    activeUsers = await get_users()
    print("Sending image to users:\n\t", end="")
    print_list = []
    for user in activeUsers:
        print_list.append(user.name)
        await user.send(file=discord.File('/usr/src/app/data/latest.png'))
    print(*print_list, sep=',')

# Everything things
def write_config(section, field, data):
    config.set(str(section), str(field), str(data))
    with open('/usr/src/app/data/data.ini', 'w') as configfile:
        config.write(configfile)

bot.run(DISCORD_TOKEN)