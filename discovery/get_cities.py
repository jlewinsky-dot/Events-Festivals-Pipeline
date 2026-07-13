import os
from dotenv import load_dotenv
import requests
import time
import logging
from config.settings import GET_CITIES_LIMIT, MIN_POPULATION
from config.locations import yard_cities as _yard_cities

logger = logging.getLogger(__name__)

def normalize_city(s):
    s = s.strip() # Removing whitespace
    if "," not in s:
        return s
    city, state = s.split(",", 1)
    return f"{city.strip().title()}, {state.strip().upper()}"

# Grabs all cities near each lat/long in locations, with a prompt to manually add more
def get_cities(sites, yard_cities=None):
    yard_cities = yard_cities or _yard_cities
    load_dotenv()

    limit = GET_CITIES_LIMIT
    min_population = MIN_POPULATION

    site_city = {}
    city_to_yard = {}

    for site in sites:
        logger.info(f"Fetching cities for {site}")
        yards = yard_cities.get(site, [])

        for i, lat_long in enumerate(sites[site]):

            if i < len(yards):
                yard = yards[i]
            else:
                yard = ""

            lat = lat_long[0]
            long = lat_long[1]
            radius = lat_long[2]

            BASE_URL = "https://wft-geo-db.p.rapidapi.com/v1/geo/locations"

            url = f"{BASE_URL}/{lat}{long}/nearbyCities?radius={radius}&distanceUnit=MI&limit={limit}&minPopulation={min_population}&countryIds=US&types=CITY&sort=-population"
            headers = {
                "X-RapidAPI-Key": os.getenv('GEO_DB_API'),
                "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
            }

            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                for item in data.get('data'):
                    city = normalize_city(f"{item['city']}, {item['regionCode']}")
                    site_city.setdefault(site, []).append(city)
                    city_to_yard[city] = yard

            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
            time.sleep(1)

        # Manually add + 'q' to quit loop. 
        while True:
            print("-----------------------------------------------------------------")
            manually_added = input("Are there any cities you want to manually add? (press q to quit): ")

            if manually_added == 'q':
                break
            else:
                manually_added = normalize_city(manually_added)
                if manually_added not in site_city.get(site, []):
                    site_city.setdefault(site, []).append(manually_added)
                    city_to_yard[manually_added] = "Manually Added"

    return site_city, city_to_yard


