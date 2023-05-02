from scrapers import *

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from apscheduler.schedulers.asyncio import AsyncIOScheduler

load_dotenv()
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_TOKEN = os.getenv('CHANNEL_TOKEN')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

max_price_per_week = 0
min_price_per_week = 0
max_price_per_month = 0
min_price_per_month = 0
num_bedrooms = 0

@bot.event
async def on_ready():
    channel = bot.get_channel(CHANNEL_TOKEN)
    print(f'{bot.user.name} has connected to Discord!')
    print(f'{bot.user.name} is connected to the following guilds:\n')
    for guild in bot.guilds:
        print(guild)
    # await channel.send("heyyy :3")

@bot.command(name='initialise', help="Initialises the bot with the given parameters: min_price_per_week, max_price_per_week, min_price_per_month, max_price_per_month, num_bedrooms")
async def args(ctx, *args):
    global max_price_per_week
    global min_price_per_week
    global max_price_per_month
    global min_price_per_month
    global num_bedrooms
    try:
        max_price_per_week = int(args[0])
        num_bedrooms = int(args[1])
        max_price_per_month = 4.34524 * max_price_per_week
        await ctx.send(f'Initialised with parameters: £{max_price_per_week} per person per week, {num_bedrooms} bedrooms.')
    except:
        await ctx.send("Incorrect arguments. Please try again.")
        return
    
    
    
    


bot.run(BOT_TOKEN)