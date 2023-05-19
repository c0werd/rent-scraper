from scrapers import DataStorage, Scraper, Property, RightMoveScraper, UniHomesScraper
from bot import PropertyBot

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from datetime import datetime, timedelta, timezone
import math

from apscheduler.schedulers.asyncio import AsyncIOScheduler



load_dotenv()
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

PASTEBIN_API_KEY = os.getenv('PASTEBIN_API_KEY')
PASTEBIN_USERNAME = os.getenv('PASTEBIN_USERNAME')
PASTEBIN_PASSWORD = os.getenv('PASTEBIN_PASSWORD')


bot = PropertyBot(command_prefix='!', intents=discord.Intents.all(), BOT_TOKEN=BOT_TOKEN, CHANNEL_ID=CHANNEL_ID, PASTEBIN_API_KEY=PASTEBIN_API_KEY, PASTEBIN_USERNAME=PASTEBIN_USERNAME, PASTEBIN_PASSWORD=PASTEBIN_PASSWORD)

@bot.command(name='initialise', help="Initialises the bot with the given parameters: [max price per week] [number of bedrooms] [number of people]")
async def initialise(ctx, *args):
    try:
        max_price_per_week = int(args[0])
        num_bedrooms = int(args[1])
        num_ppl = int(args[2])
        bot.add_parameters(max_ppw=max_price_per_week, num_bedrooms=num_bedrooms, num_ppl=num_ppl)

        await ctx.send(f'Initialised with parameters: £{max_price_per_week} per person per week, {num_bedrooms} bedrooms, £{str(int(max_price_per_week * 4 * 4.34524))} per person per month.')

        bot.initialise_scrapers()
        bot.generate_pastebin_user_key()

    except Exception as e:
        print(e)
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

@bot.command(name="allProperties", help="Generates a pastebin for all properties found")
async def allProperties(ctx):
    pastebin_url = bot.generate_pastebin_paste(bot.properties_to_string(bot.get_all_properties(), for_Discord=False)) 
    await ctx.send(f'All properties found:\n{pastebin_url}')

@bot.command(name="removeProperty", help="Removes a property from the list of properties found using ID")
async def removeProperty(ctx, arg1):
    try:
        bot.remove_property(property_id=arg1)
        await ctx.send(f'Removed property with ID {arg1}')
    except:
        await ctx.send(f'Could not remove property with ID {arg1}')

bot.run_bot()