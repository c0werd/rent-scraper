from scrapers import *

from discord.ext import commands
from tabulate import tabulate
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class PropertyBot(commands.Bot):
    def __init__(self, command_prefix, intents, BOT_TOKEN, CHANNEL_ID):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.min_price_per_week, self.max_price_per_week = 0, 0

        self.min_price_per_month, self.max_price_per_month = 0, 0
        self.num_bedrooms = 0

        self.data_storage = DataStorage()
        self.scheduler = AsyncIOScheduler()

        self.BOT_TOKEN = BOT_TOKEN
        self.CHANNEL_ID = CHANNEL_ID
    
    async def on_ready(self):
        channel = self.get_channel(self.CHANNEL_ID)
        print(f'{self.user.name} has connected to Discord!')
        print(f'{self.user.name} is connected to the following guilds:\n')
        for guild in self.guilds:
            print(guild)
        await channel.send("Bot ready! Initialise scraping with the following command: !initialise [max price per week] [number of bedrooms]")

    def run_bot(self):
        self.run(self.BOT_TOKEN)
    
    def add_price_per_week(self, ppw: int):
        self.max_price_per_week = ppw
    
    def add_price_per_month(self, ppm: int):
        self.max_price_per_month = ppm

    def add_num_bedrooms(self, num_bedrooms: int):
        self.num_bedrooms = num_bedrooms
    
    def initialise_scrapers(self):
        self.RMscraper = RightMoveScraper(self.min_price_per_month, self.max_price_per_month, self.num_bedrooms)
        self.UHscraper = UniHomesScraper(self.min_price_per_week, self.max_price_per_week, self.num_bedrooms)

        # Add the scheduled job to run every hour
        self.scheduler.add_job(self.auto_rescrape, 'interval', hours=1, id="auto_rescrape")
        self.scheduler.start()
    
    def scrape(self) -> List[Property]:
        print("Scraping...")
        RMproperties = self.RMscraper.scrape()
        UHproperties = self.UHscraper.scrape()
        foundProperties = RMproperties + UHproperties

        newProperties = self.data_storage.check_new_properties(foundProperties)

        self.data_storage.add_properties(newProperties)

        return newProperties
    
    def properties_to_string(self, properties: List[Property]) -> str:
        property_string = f'```{tabulate(properties, headers="keys", tablefmt="pipe", numalign="left", stralign="center")}```'
        return property_string
    
    async def auto_rescrape(self):
        # Get new properties and add them to the data storage
        new_properties = self.scrape()
        
        if len(new_properties) > 0:
            # Format the new properties as a string and send to the Discord channel
            new_properties_string = self.properties_to_string(new_properties)
            channel = self.get_channel(self.CHANNEL_ID)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await channel.send(f"New properties found at {timestamp}:\n{new_properties_string}")

    def get_properties(self, num_properties: int) -> List[Property]:
        return self.data_storage.get_properties()[-(num_properties+1):]
    
    def get_all_properties(self) -> List[Property]:
        return self.data_storage.get_properties()