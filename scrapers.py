import math
import pandas as pd
from bs4 import BeautifulSoup
import requests

from datetime import datetime, timedelta


class DataStorage:
    
    def __init__(self):
        self.properties = []

    def create_dataframe(self):
        self.df = pd.DataFrame(self.properties)

    def get_dataframe(self):
        return self.df
    
    def generate_property_id(self, property):
        property_id = f'{property.getDateAdded()[:2]}{property.getPricePM()[:2]}{property.getLocation().replace(" ", "")[:2].upper()}'
        return property_id

    def add_property(self, property):

        propertyId = self.generate_property_id(property)
        dateAdded = property.getDateAdded()
        pricepm = property.getPricePM()
        pricepw = property.getPricePW()
        location = property.getLocation()
        link = property.getLink()

        self.properties.append({
            'propertyId': propertyId,
            'dateAdded': dateAdded,
            'pricepm': pricepm,
            'pricepw': pricepw,
            'location': location,
            'link': link
        })

    def add_properties(self, properties):
        for property in properties:
            if property['propertyId'] not in [prop['propertyId'] for prop in self.properties]:
                self.add_property(property)

    def check_new_properties(self, new_properties):
        new_properties = [prop for prop in new_properties if prop['propertyId'] not in [prop['propertyId'] for prop in self.properties]]
        return new_properties
    
    def get_properties(self):
        return self.properties

# Base scraper class
class Scraper:

    def __init__(self, data_storage):
        self.data_storage = data_storage

    def scrape(self):
        raise NotImplementedError("Subclasses should implement this!")
    
    def get_page_soup(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    
    
    
# Property class
class Property:

    def __init__(self):
        self.date_added = None
        pass

    def __str__(self):
        return f'Property {self.propertyId} in {self.location}'
    
    def addDateAdded(self, date_added):
        self.date_added = date_added

    def addPricePM(self, pricepm):
        self.pricepm = pricepm

    def addPricePW(self, pricepw):
        self.pricepw = pricepw

    def addLocation(self, location):
        self.location = location

    def addLink(self, link):
        self.link = link

    def getDateAdded(self):
        return self.date_added
    
    def getPricePM(self):
        return self.pricepm
    
    def getPricePW(self):
        return self.pricepw
    
    def getLocation(self):
        return self.location
    
    def getLink(self):
        return self.link


class RightMoveScraper(Scraper):

    def __init__(self, data_storage, min_price_per_month, max_price_per_month, num_bedrooms):
        super().__init__(data_storage)
        self.min_price = min_price_per_month
        self.max_price = max_price_per_month
        self.num_bedrooms = num_bedrooms
        
        self.url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={self.num_bedrooms}&minBedrooms={self.num_bedrooms}&maxPrice={self.max_price}&minPrice={self.min_price}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished'
        self.soup = self.get_page_soup(self.url)

        self.today = datetime.now()
        self.yesterday = datetime.now() - timedelta(days=1)
        

    def reset_scraper(self):
        self.url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={self.num_bedrooms}&minBedrooms={self.num_bedrooms}&maxPrice={self.max_price}&minPrice={self.min_price}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished'
        self.soup = self.get_page_soup(self.url)

    def num_of_pages(self):
        num_of_results = self.soup.find('span', {'class': 'searchHeader-resultCount'}).text
        num_of_pages = int(num_of_results) // 24 + 1
        return num_of_pages
    
    def parse_date(self, date_string):
        if 'yesterday' in date_string:
            return self.yesterday.strftime('%d/%m/%Y')
        elif 'today' in date_string:
            return self.today.strftime('%d/%m/%Y')
        else:
            return date_string

    def scrape(self):
        properties_found = []
        num_of_pages = self.num_of_pages()
        
        for page in range(0, num_of_pages):
            page_url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={self.num_bedrooms}&minBedrooms={self.num_bedrooms}&maxPrice={self.max_price}&minPrice={self.min_price}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished&index={24 * page}'
            page_soup = self.get_page_soup(page_url)

            property_listings = page_soup.find_all('div', class_='l-searchResult')
            for listing in property_listings:
                foundProperty = Property()
                
                pricepm = listing.find('span', class_='propertyCard-priceValue').text.replace("£", "").replace(",", "").replace("pcm", "").strip()
                foundProperty.addPricePM(pricepm)
                
                pricepw = listing.find('span', class_='propertyCard-secondaryPriceValue').text.replace("£", "").replace(",", "").replace("pw", "").strip()
                foundProperty.addPricePW(pricepw)
                
                foundProperty.addLink("https://rightmove.co.uk" + listing.find('a', class_='propertyCard-link')['href'])
                
                location = listing.find('address', class_='propertyCard-address').text.replace("\n", "")
                foundProperty.addLocation(location)
                
                property_date = self.parse_date(listing.find('span', class_='propertyCard-branchSummary-addedOrReduced').text.replace("\n", "").replace("Added on ", "").replace("Reduced on ", "").strip())
                foundProperty.addDateAdded(property_date)

                properties_found.append(foundProperty)
        
        return properties_found
        

class UniHomesScraper(Scraper):

    def __init__(self, data_storage, min_price, max_price, num_bedrooms):
        super().__init__(data_storage)
        self.min_price = min_price
        self.max_pppw = max_price
        self.num_bedrooms = num_bedrooms
        
        self.url = f'https://www.unihomes.co.uk/student-accommodation/london/near-kings-college-london?bedrooms={self.num_bedrooms}&max-price={self.max_pppw}'
        self.soup = self.get_page_soup(self.url)

        self.today = datetime.now()

    def reset_scraper(self):
        self.url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={self.num_bedrooms}&minBedrooms={self.num_bedrooms}&maxPrice={self.max_price}&minPrice={self.min_price}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished'
        self.soup = self.get_page_soup(self.url)

    def scrape(self):
        properties_found = []
        property_listings = self.soup.find_all('div', class_='property-listing-column')
        for listing in property_listings:
            foundProperty = Property()
            
            pricepw = math.ceil(float(listing.find('div', class_='property_details').find('span', class_="font-weight-700").text.replace("£", "")))
            foundProperty.addPricePW(pricepw)

            pricepm = math.ceil(pricepw * 4.34524)
            foundProperty.addPricePM(pricepm)

            link = listing.find('a')['href']
            foundProperty.addLink(link)

            location = listing.find('div', class_="property_rooms_address").find('p', class_="font-size-14px").text
            foundProperty.addLocation(location)

            properties_found.append(foundProperty)

        return properties_found

def test():
    data_storage = DataStorage()
    scraper = RightMoveScraper(data_storage, 0, 9000, 1)
    data_storage.add_properties(scraper.scrape())
    
    for property in data_storage.get_properties():
        print(property["propertyId"])

# test()