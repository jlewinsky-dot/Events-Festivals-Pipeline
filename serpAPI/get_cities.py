import os
from dotenv import load_dotenv
import requests
import time
import logging
logger = logging.getLogger(__name__)

def ctities(sites_2):
    load_dotenv()
    limit = 5
    min_population = 2000
    site_city = {}
    for site in sites_2:
        logger.info(f"Fetching cities for {site}")
        for lat_long in sites_2[site]:
            
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
                    site_city[site] = site_city.get(site, [])
                    site_city[site].append(item['city'])
                
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")

            time.sleep(1)
        while True:
            print("-----------------------------------------------------------------")
            manually_added = input("Are there any cities you can to manually add? (press q to quit): ")
            if manually_added == 'q':
                break
            else:
                if manually_added not in site_city[site]: 
                    site_city[site].append(manually_added)

    return site_city



print(ctities({'FusionSite Nashville': [[36.1381, -86.7514, 100]]}))

