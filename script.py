from scrapers import DataStorage, Scraper, Property, RightMoveScraper, UniHomesScraper
from bot import PropertyBot

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from datetime import datetime, timedelta, timezone
import math

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pastebin import PastebinAPI



load_dotenv()
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

PASTEBIN_API_KEY = os.getenv('PASTEBIN_API_KEY')
PASTEBIN_USERNAME = os.getenv('PASTEBIN_USERNAME')
PASTEBIN_PASSWORD = os.getenv('PASTEBIN_PASSWORD')
PastebinAPI = PastebinAPI()
PASTEBIN_SESSION_KEY = PastebinAPI.generate_user_key(PASTEBIN_API_KEY, PASTEBIN_USERNAME, PASTEBIN_PASSWORD)


bot = PropertyBot(command_prefix='!', intents=discord.Intents.all(), BOT_TOKEN=BOT_TOKEN, CHANNEL_ID=CHANNEL_ID)

@bot.command(name='initialise', help="Initialises the bot with the given parameters: [max price per week] [number of bedrooms]")
async def initialise(ctx, *args):
    try:
        max_price_per_week = int(args[0])
        bot.add_price_per_week(max_price_per_week)

        num_bedrooms = int(args[1])
        bot.add_num_bedrooms(num_bedrooms)

        max_price_per_month = 4.34524 * max_price_per_week
        bot.add_price_per_month(max_price_per_month)
        await ctx.send(f'Initialised with parameters: £{max_price_per_week} per person per week, {num_bedrooms} bedrooms, £{max_price_per_month} per person per month.')
        bot.initialise_scrapers()
        
    except Exception as e:
        await ctx.send("Incorrect arguments. Please try again.")
        return

@bot.command(name='countdown', help="Displays countdown to next scrape")
async def countdownTo(ctx) -> str:
    # Get the next run time for all jobs in the scheduler
    next_run_time = bot.scheduler.get_job('auto_rescrape').next_run_time
    if next_run_time:
        # Calculate the time remaining until the next scheduled run
        now = datetime.now(timezone.utc)
        time_remaining = next_run_time - now

        # Convert the time remaining to hours, minutes, and seconds
        hours, remainder = divmod(time_remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Format the time remaining as a string
        time_remaining_str = f'Time remaining until next auto_rescrape: {hours} hours, {minutes} minutes, {seconds} seconds'

        await ctx.send(time_remaining_str)
    else:
        await ctx.send("The auto_rescrape job has not been added to the scheduler yet.")

@bot.command(name='nuke',  help='Deletes all messages in the channel (use with caution!)')
async def nuke(ctx):
    await ctx.channel.purge()

@bot.command(name='latest', help='Displays the latest properties found')
async def latest(ctx, arg1 = None):
    acceptable_values = list(range(1, 21))
    if arg1 in acceptable_values:
        num_properties = int(arg1)
        retrieved_properties = bot.get_properties(num_properties)
        await ctx.send(f'Latest {num_properties} properties found:\n{bot.properties_to_string(retrieved_properties)}')
    else: 
        latest(ctx, 21)

@bot.command(name="showAllProperties", help="Displays all properties found in a pastebin link")
async def showAllProperties(ctx):
    PastebinAPI.paste(api_dev_key=PASTEBIN_API_KEY, api_user_key=PASTEBIN_SESSION_KEY, paste_name="All Properties", paste_code=bot.properties_to_string(bot.properties))

# Runs the bot
print(PastebinAPI.paste(api_dev_key=PASTEBIN_API_KEY, api_user_key=PASTEBIN_SESSION_KEY, paste_name="All Properties", paste_code="penis penis test"))
