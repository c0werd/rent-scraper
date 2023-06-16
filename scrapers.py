from __future__ import annotations
import math
from bs4 import BeautifulSoup
import requests
from typing import List
from datetime import datetime, timedelta


class DataStorage:
    """Class to store the properties found by the bot
    """
    
    def __init__(self):
        """Initialises the DataStorage object
        """
        self.properties = []
        self.removed_properties = []

    def add_property(self, property: Property):
        """Adds the given property to the properties list

        Args:
            property (Property): The property to be added to the properties list
        """

        propertyId = property.getPropertyId()
        dateAdded = property.getDateAdded()
        pricepm = int(property.getPricePM())
        priceppw = int(property.getPricePW())
        location = property.getLocation()
        link = property.getLink()

        self.properties.append({
            'propertyId': propertyId,
            'dateAdded': datetime.strptime(dateAdded, '%d/%m/%Y'),
            'ppm': pricepm,
            'pppw': priceppw,
            'location': location,
            'link': link
        })

    def remove_property(self, propertyID: str):
        removed_property = [prop for prop in self.properties if prop['propertyId'] == propertyID]
        self.removed_properties.append(removed_property)
        self.properties = [prop for prop in self.properties if prop['propertyId'] != propertyID]
        self.properties = sorted(self.properties, key=lambda k: k['dateAdded'], reverse=True)

    def remove_all_properties(self):
        self.removed_properties.append(self.properties)
        self.properties = []

    def add_properties(self, properties: List[Property]) -> None:
        for property in properties:
            if (property.getPricePM() != "") and (property.getPropertyId() not in [prop['propertyId'] for prop in self.properties]) and (property.getPropertyId() not in [prop['propertyId'] for prop in self.removed_properties]):
                self.add_property(property)
        self.properties = sorted(self.properties, key=lambda k: k['dateAdded'], reverse=True)

    def check_new_properties(self, new_properties: List[Property]) -> List[Property]:
        existing_property_ids = [prop['propertyId'] for prop in self.properties]
        new_properties = [prop for prop in new_properties if prop.getPropertyId() not in existing_property_ids]
        return new_properties
    
    def get_properties(self) -> List[dict]:
        return self.properties


# Base scraper class
class Scraper:

    def __init__(self):
        pass

    def scrape(self):
        raise NotImplementedError("Subclasses should implement this!")
    
    def get_page_soup(self, url: str) -> BeautifulSoup:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    
    
# Property class
class Property:
    # The number of weeks in a month
    weeks_per_month = 4.43524

    def __init__(self, num_people: int):
        self.date_added = None
        self.num_people = num_people
        self.pricepm = None
        self.pricepw = None
        pass

    def __str__(self):
        return f'Property {self.propertyId} in {self.location}'
    
    def addDateAdded(self, date_added: str):
        self.date_added = date_added

    def addPricePM(self, pricepm: str):
        self.pricepm = int(pricepm)

    def addPricePW(self, pricepw: str):
        self.pricepw = math.ceil(float(pricepw))
        if self.pricepm is None:
            self.pricepm = int(self.pricepw * Property.weeks_per_month * self.num_people)

    def addLocation(self, location: str):
        self.location = location

    def addLink(self, link: str):
        self.link = link

    def addPropertyId(self, date: str = None, pricepm: int = None, location: str = None):
        if date is None:
            date = self.date_added
        if pricepm is None:
            pricepm = self.pricepm
        if location is None:
            location = self.location
        self.propertyId = f'{date[:2]}{str(pricepm)[:2]}{location.replace(" ", "")[:2].upper()}'

    def getPropertyId(self) -> str:
        return self.propertyId

    def getDateAdded(self) -> str:
        return self.date_added
    
    def getPricePM(self) -> int:
        return self.pricepm
    
    def getPricePW(self) -> int:
        return self.pricepw
    
    def getLocation(self) -> str:
        return self.location
    
    def getLink(self) -> str:
        return self.link


class RightMoveScraper(Scraper):

    def __init__(self, min_price_per_month: int, max_price_per_month: int, num_bedrooms: int, num_people: int):
        super().__init__()
        self.min_price = min_price_per_month
        self.max_price = max_price_per_month
        self.num_bedrooms = num_bedrooms
        self.num_people = num_people
        
        self.url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={self.num_bedrooms}&minBedrooms={self.num_bedrooms}&maxPrice={self.max_price}&minPrice={self.min_price}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished'
        self.soup = self.get_page_soup(self.url)

        self.today = datetime.now()
        self.yesterday = self.today - timedelta(days=1)
        

    def reset_scraper(self):
        self.url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={self.num_bedrooms}&minBedrooms={self.num_bedrooms}&maxPrice={self.max_price}&minPrice={self.min_price}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished'
        self.soup = self.get_page_soup(self.url)

    def num_of_pages(self) -> int:
        num_of_results = self.soup.find('span', {'class': 'searchHeader-resultCount'}).text
        num_of_pages = int(num_of_results) // 24 + 1
        return num_of_pages
    
    def parse_date(self, date_string: str) -> str:
        if 'yesterday' in date_string:
            return self.yesterday.strftime('%d/%m/%Y')
        elif 'today' in date_string:
            return self.today.strftime('%d/%m/%Y')
        else:
            return date_string

    def scrape(self) -> List[Property]:
        properties_found = []
        num_of_pages = self.num_of_pages()
        
        for page in range(0, num_of_pages):
            page_url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={self.num_bedrooms}&minBedrooms={self.num_bedrooms}&maxPrice={self.max_price}&minPrice={self.min_price}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished&index={24 * page}'
            page_soup = self.get_page_soup(page_url)

            property_listings = page_soup.find_all('div', class_='l-searchResult')
            for listing in property_listings:
                foundProperty = Property(self.num_people)
                
                pricepm = listing.find('span', class_='propertyCard-priceValue').text.replace("£", "").replace(",", "").replace("pcm", "").strip()
                if pricepm != '':
                    foundProperty.addPricePM(pricepm)
                
                pricepw = listing.find('span', class_='propertyCard-secondaryPriceValue').text.replace("£", "").replace(",", "").replace("pw", "").strip()
                if pricepw != '':
                    foundProperty.addPricePW(pricepw)
                
                link = "https://rightmove.co.uk" + listing.find('a', class_='propertyCard-link')['href']
                foundProperty.addLink(link)
                
                location = listing.find('address', class_='propertyCard-address').text.replace("\n", "")
                foundProperty.addLocation(location)
                
                property_date = self.parse_date(listing.find('span', class_='propertyCard-branchSummary-addedOrReduced').text.replace("\n", "").replace("Added on ", "").replace("Reduced on ", "").strip())
                foundProperty.addDateAdded(property_date)

                foundProperty.addPropertyId(property_date, pricepm, location)

                properties_found.append(foundProperty)
        
        return properties_found
        

class UniHomesScraper(Scraper):

    def __init__(self, min_price: int, max_price: int, num_bedrooms: int, num_people: int):
        super().__init__()
        self.min_price = min_price
        self.max_pppw = max_price
        self.num_bedrooms = num_bedrooms
        self.num_people = num_people
        
        self.url = f'https://www.unihomes.co.uk/student-accommodation/london/near-kings-college-london?bedrooms={self.num_bedrooms}&max-price={self.max_pppw}'
        self.soup = self.get_page_soup(self.url)

        self.today = datetime.now()

    def reset_scraper(self):
        self.url = f'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=STATION%5E9662&sortType=6&savedSearchId=46395805&maxBedrooms={self.num_bedrooms}&minBedrooms={self.num_bedrooms}&maxPrice={self.max_price}&minPrice={self.min_price}&radius=5&includeLetAgreed=false&letType=student&furnishTypes=furnished'
        self.soup = self.get_page_soup(self.url)

    def scrape(self) -> List[Property]:
        properties_found = []
        property_listings = self.soup.find_all('div', class_='property-listing-column')
        for listing in property_listings:
            foundProperty = Property(self.num_people)
            
            pricepw = listing.find('div', class_='property_details').find('span', class_="font-weight-700").text.replace("£", "").strip()
            foundProperty.addPricePW(pricepw)

            link = listing.find('a')['href']
            foundProperty.addLink(link)

            location = listing.find('div', class_="property_rooms_address").find('p', class_="font-size-14px").text
            foundProperty.addLocation(location)

            date_added = self.today.strftime('%d/%m/%Y')
            foundProperty.addDateAdded(date_added)

            foundProperty.addPropertyId(date_added, None, location)

            properties_found.append(foundProperty)

        return properties_found

def test():
    RMdata_storage = DataStorage()
    scraper = RightMoveScraper(0, 9000, 1)
    RMdata_storage.add_properties(scraper.scrape())

    UHdata_storage = DataStorage()
    scraper = UniHomesScraper(0, 9000, 1)
    UHdata_storage.add_properties(scraper.scrape())
    
    return

# test()