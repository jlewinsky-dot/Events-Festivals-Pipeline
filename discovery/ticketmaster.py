import requests
import os
import json
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def get_tickmaster_events(sites):
    load_dotenv()
    KEY = os.getenv('TICKET_MASTER_CONSUMER')
    raw_events = []

    for site in sites:
        logger.info(f"Ticketmaster: searching {site}")
        page = 0
        city, state = site.split(',')

        while True:
            response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params={
                "city": city.strip(),
                "stateCode": state.strip(),
                "radius": 50,
                "unit": "miles",
                "countryCode": "US",
                "size": 200,
                "apikey": KEY,
                "page": page,
            })
            data = response.json()
            events = data.get("_embedded", {}).get("events", [])

            for event in events:
                venue = event.get("_embedded", {}).get("venues", [{}])[0]
                raw_events.append((
                    {
                        "title": event.get("name"),
                        "date": {"when": event.get("dates", {}).get("start", {}).get("localDate")},
                        "address": [venue.get("name", ""), venue.get("city", {}).get("name", ""), venue.get("state", {}).get("stateCode", "")],
                    },
                    site
                ))

            total_pages = data.get("page", {}).get("totalPages", 0)
            if page >= total_pages - 1 or page >= 10:
                break
            page += 1

    return raw_events