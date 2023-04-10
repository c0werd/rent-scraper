import requests as requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import math

import os
from discord.ext import commands
from dotenv import load_dotenv
import random


min_ppm = 0
max_ppm = 4000
max_pppw = 250
bedrooms = 4



class RightmoveScraper:
    def __init__(self, min_price, max_price, num_bedrooms):
        self.min_price = min_price
        self.max_price = max_price
        self.num_bedrooms = num_bedrooms

    def num_of_pages(self):
        url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={self.num_bedrooms}&minBedrooms={self.num_bedrooms}&maxPrice={self.max_price}&minPrice={self.min_price}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished'        
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        num_of_results = soup.find('span', {'class': 'searchHeader-resultCount'}).text
        num_of_pages = int(num_of_results) // 24 + 1

        return num_of_pages

    def scrape(self):
        properties = []
        for page in range(0, self.num_of_pages()):
            # Make HTTP request to Rightmove with search parameters
            url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={bedrooms}&minBedrooms={bedrooms}&maxPrice={max_ppm}&minPrice={min_ppm}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished&index={24 * page}'        
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract property information from HTML
            property_listings = soup.find_all('div', class_='l-searchResult')
            for listing in property_listings:
                pricepm = listing.find('span', class_='propertyCard-priceValue').text.replace("£", "").replace(",", "").replace("pcm", "").strip()
                pricepw = listing.find('span', class_='propertyCard-secondaryPriceValue').text.replace("£", "").replace(",", "").replace("pw", "").strip()
                link = "https://rightmove.co.uk" + listing.find('a', class_='propertyCard-link')['href']
                location = listing.find('address', class_='propertyCard-address').text.replace("\n", "")
                date_added = listing.find('span', class_='propertyCard-branchSummary-addedOrReduced').text.replace("\n", "").replace("Added on ", "").replace("Reduced on ", "").strip()
                # .find('div', class_="property-information").find_all('span')[-1].text

                if (({'pricepm': pricepm, 'pricepw': pricepw, 'link': link, 'location': location, 'date_added': date_added} not in properties) and (pricepm != "" and pricepw != "" and link != "" and location != "")):     
                    properties.append({'pricepm': pricepm, 'pricepw': pricepw, 'link': link, 'location': location, 'date_added': date_added})
        
        df = pd.DataFrame(properties)
        today = datetime.now()
        yesterday = datetime.now() - timedelta(days=1) # Calculate yesterday's date
        df['date_added'] = df['date_added'].replace('Added yesterday', yesterday.strftime('%d/%m/%Y'))
        df['date_added'] = df['date_added'].replace('Added today', today.strftime('%d/%m/%Y'))
        df['date_added'] = pd.to_datetime(df['date_added'])
        
        df['pricepm'] = df['pricepm'].astype(int)
        df['pricepw'] = df['pricepw'].astype(int)
        df.sort_values(by=['date_added'], ascending=False, inplace=True)
        df['date_added'] = df['date_added'].dt.strftime('%d/%m/%Y')

        return df

class UniHomesScraper:

    def __init__(self, max_pppw, num_bedrooms):
        self.max_pppw = max_pppw
        self.num_bedrooms = num_bedrooms

    def scrape(self):
        properties = []

        url = f'https://www.unihomes.co.uk/student-accommodation/london/near-kings-college-london?bedrooms={self.num_bedrooms}&max-price={self.max_pppw}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        property_listings = soup.find_all('div', class_='property-listing-column')
        for listing in property_listings:
            pricepw = math.ceil(float(listing.find('div', class_='property_details').find('span', class_="font-weight-700").text.replace("£", "")))
            pricepm = math.ceil(pricepw * 4.33)
            link = listing.find('a')['href']
            location = listing.find('div', class_="property_rooms_address").find('p', class_="font-size-14px").text
            # .find('div', class_="property-information").find_all('span')[-1].text

            if (({'pricepm': pricepm, 'pricepw': pricepw, 'link': link, 'location': location} not in properties) and (pricepm != "" and pricepw != "" and link != "" and location != "")):     
                properties.append({'pricepm': pricepm, 'pricepw': pricepw, 'link': link, 'location': location})
        
        df = pd.DataFrame(properties)
        return df

#get and store latest properties
RMProperties = RightmoveScraper(min_ppm, max_ppm, bedrooms).scrape()
UHProperties = UniHomesScraper(max_pppw, bedrooms).scrape()

# discord bot
load_dotenv()

bot = commands.Bot(command_prefix='!')
TOKEN = os.getenv('DISCORD_TOKEN')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'{bot.user.name} is connected to the following guilds:\n')
    for guild in bot.guilds:
        print(guild)


@bot.command(name='RMlatest')
async def scrapeRM(ctx):
    print('rightmoving')
    response = RMProperties.iloc[0]
    await ctx.send(response.to_string())

@bot.command(name='UHlatest')
async def scrapeUH(ctx):
    print('unihoming')
    response = UHProperties.iloc[0]
    await ctx.send(response.to_string())

@bot.command(name='nuke')
async def nuke(ctx):
    await ctx.channel.purge()

@bot.command(name="update")
async def rescrape(ctx):
    global RMProperties 
    RMProperties = RightmoveScraper(min_ppm, max_ppm, bedrooms).scrape()
    global UHProperties
    UHProperties = UniHomesScraper(max_pppw, bedrooms).scrape()
    await ctx.send("updated latest properties")

@bot.command(name="unihomes")
async def unihomes(ctx):
    await ctx.send(UHProperties.to_string())

bot.run(TOKEN)
print('hey')



# print("Rightmove")
# print(RightmoveScraper(min_ppm, max_ppm, bedrooms).scrape())
# print("UniHomes")
# print(UniHomesScraper(max_pppw, bedrooms).scrape())