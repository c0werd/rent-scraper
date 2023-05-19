from scrapers import *
import requests
from discord.ext import commands
from tabulate import tabulate
from apscheduler.schedulers.asyncio import AsyncIOScheduler

"""
Unihomes: Per person per week
RightMove: Total per month, total per week

Passed parameters: Per person per week

Unihome caculations: None

Rightmove calculations: pppw * 4 * 4.34524 = pm
"""

class PropertyBot(commands.Bot):
    PB_API_USERKEY_URL = 'https://pastebin.com/api/api_login.php'
    PB_API_PASTE_URL = 'https://pastebin.com/api/api_post.php'

    weeks_per_month = 4.34524
    
    def __init__(self, command_prefix, intents, BOT_TOKEN, COMMAND_CHANNEL_ID, UPDATE_CHANNEL_ID, PASTEBIN_API_KEY, PASTEBIN_USERNAME, PASTEBIN_PASSWORD):
        super().__init__(command_prefix=command_prefix, intents=intents)
        """Initialises the bot with the given command prefix, intents, and token

        Initialises various variables used for calculations and initialising scrapers later
        (e.g. min_price_per_week, max_price_per_week, num_bedrooms)

        Creates objects for storing data and scheduling jobs

        Retrieves the bot's token and channel ids from the .env file and stores them in instance variables

        """

        self.min_price_per_week, self.max_price_per_week = 0, 0

        self.min_price_per_month, self.max_price_per_month = 0, 0
        self.num_bedrooms = 0
        self.num_people = 0

        self.data_storage = DataStorage()
        self.scheduler = AsyncIOScheduler()

        self.BOT_TOKEN = BOT_TOKEN
        self.COMMAND_CHANNEL_ID = COMMAND_CHANNEL_ID
        self.UPDATE_CHANNEL_ID = UPDATE_CHANNEL_ID
        self.PB_API_KEY = PASTEBIN_API_KEY
        self.PB_USERNAME = PASTEBIN_USERNAME
        self.PB_PASSWORD = PASTEBIN_PASSWORD
        
    async def on_ready(self):
        """Prints the bot's name and guilds to the console when the bot is ready to use
        """
        
        self.command_channel = self.get_channel(self.COMMAND_CHANNEL_ID)
        self.update_channel = self.get_channel(self.UPDATE_CHANNEL_ID)

        print(f'{self.user.name} has connected to Discord!')
        print(f'{self.user.name} is connected to the following guilds:\n')
        for guild in self.guilds:
            print(guild)
        await self.update_channel.send("Bot ready! Initialise scraping with the following command: !initialise [max price per week] [number of bedrooms] [number of people]")

    def run_bot(self):
        """Runs the bot with the given token
        """

        self.run(self.BOT_TOKEN)

    def add_parameters(self, max_ppw: int, num_bedrooms: int, num_ppl: int):
        """Adds the given parameters to the bot's instance variables

        Performs a calculation to convert max_ppw to a price per month

        Args:
            max_ppw (int): The maximum price per person per week
            num_bedrooms (int): The number of bedrooms
        """
        self.add_num_people(num_ppl)
        self.add_price_per_week(max_ppw)
        self.add_num_bedrooms(num_bedrooms)
        self.add_price_per_month(int(max_ppw * PropertyBot.weeks_per_month * num_ppl))
    
    def add_num_people(self, num_people: int):
        """Adds the given number of people to the bot's instance va riable num_people

        Args:
            num_people (int): The number of people to add
        """

        self.num_people = num_people

    def add_price_per_week(self, ppw: int):
        """Adds the given price per week to the bot's instance variable max_price_per_week

        Args:
            ppw (int): The price per week to add
        """

        self.max_price_per_week = ppw
    
    def add_price_per_month(self, ppm: int):
        """Adds the given price per month to the bot's instance variable max_price_per_month

        Args:
            ppm (int): The price per month to add
        """

        self.max_price_per_month = ppm

    def add_num_bedrooms(self, num_bedrooms: int):
        """Adds the given number of bedrooms to the bot's instance variable num_bedrooms

        Args:
            num_bedrooms (int): The number of bedrooms to add
        """

        self.num_bedrooms = num_bedrooms
    
    def initialise_scrapers(self):
        """Initialises the RightMoveScraper and UniHomesScraper objects and schedules the auto_rescrape() method to run every hour
        """

        self.RMscraper = RightMoveScraper(self.min_price_per_month, self.max_price_per_month, self.num_bedrooms, self.num_people)
        self.UHscraper = UniHomesScraper(self.min_price_per_week, self.max_price_per_week, self.num_bedrooms, self.num_people)

        self.scrape()

        # Add the scheduled job to run every hour
        self.scheduler.add_job(self.auto_rescrape, 'interval', hours=1, id="auto_rescrape")
        self.scheduler.start()
    
    def scrape(self) -> List[Property]:
        """Scrapes the RightMove and UniHomes websites for properties and adds them to the bot's instance variable data_storage

        Returns:
            List[Property]: A list of Property objects, each representing a property found by the scrapers
        """

        print("Scraping...")
        RMproperties = self.RMscraper.scrape()
        UHproperties = self.UHscraper.scrape()
        foundProperties = RMproperties + UHproperties

        newProperties = self.data_storage.check_new_properties(foundProperties)

        self.data_storage.add_properties(newProperties)

        return newProperties
    
    def properties_to_string(self, properties: List[Property], for_Discord: bool) -> str:
        """Converts a list of Property objects to a string

        Uses the tabulate library to format the properties as a table in text

        Args:
            properties (List[Property]): A list of properties to convert
            for_Discord (bool): Whether or not the string is being formatted for Discord
                (i.e. including a ``` or not)

        Returns:
            str: The properties as a tabulated string
        """

        if for_Discord:
            property_string = f'```{tabulate(properties, headers="keys", tablefmt="pipe", numalign="left", stralign="center")}```'
        else:
            property_string = f'{tabulate(properties, headers="keys", tablefmt="psql", numalign="left", stralign="center")}'
        return property_string
    
    async def auto_rescrape(self):
        """Runs the scrape() method and sends a message to the Discord channel if new properties are found
        """

        # Get new properties and add them to the data storage
        new_properties = self.scrape()
        
        if len(new_properties) > 0:
            # Format the new properties as a string and send to the Discord channel
            new_properties_string = self.properties_to_string(new_properties)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await self.update_channel.send(f"New properties found at {timestamp}:\n{new_properties_string}")

    def remove_property(self, property_id: str):
        """Removes the property with the given id from the bot's instance variable data_storage
        """

        self.data_storage.remove_property(property_id)

    def get_properties(self, num_properties: int) -> List[Property]:
        """Returns the last num_properties properties stored in the bot's instance variable data_storage

        Args:
            num_properties (int): The number of properties to return

        Returns:
            List[Property]: A list of Property objects, each representing a property stored in the bot
        """

        return self.data_storage.get_properties()[-(num_properties+1):]
    
    def get_all_properties(self) -> List[Property]:
        """Returns all the properties stored in the bot's instance variable data_storage

        Returns:
            List[Property]: A list of Property objects, each representing a property stored in the bot
        """

        return self.data_storage.get_properties()
    
    def generate_pastebin_user_key(self):
        """Generates a user key for the pastebin API and stores it in the bot's instance variable PB_USERKEY
        """

        POST_params = {
            "api_dev_key": self.PB_API_KEY,
            "api_user_name": self.PB_USERNAME,
            "api_user_password": self.PB_PASSWORD
        }
        response = requests.post(PropertyBot.PB_API_USERKEY_URL, data=POST_params)
        self.PB_USERKEY = response.text

    def generate_pastebin_paste(self, paste_code: str) -> str:
        """_summary_

        Args:
            paste_code (str): The text to be pasted in the pastebin 

        Returns:
            str: The url of the pastebin paste
        """

        POST_params = {
            "api_dev_key": self.PB_API_KEY,
            "api_paste_code": paste_code,
            "api_paste_private": 1,
            "api_paste_name": "PropertyBot's currently stored properties",
            "api_past_expire_date": "1H",
            "api_option": "paste",
            "api_user_key": self.PB_USERKEY
        }
        response = requests.post(PropertyBot.PB_API_PASTE_URL, data=POST_params)
        pastebin_raw_url = response.text.replace("https://pastebin.com/", "https://pastebin.com/raw/")
        return pastebin_raw_url