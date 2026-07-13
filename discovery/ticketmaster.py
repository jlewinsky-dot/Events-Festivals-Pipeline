import requests
import os
from dotenv import load_dotenv
import logging
from config.settings import TICKET_MASTER_RADIUS
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

SEGMENT_IDS = [
    "KZFzniwnSyZfZ7v7n1",  # festivals, fairs, community events
    "KZFzniwnSyZfZ7v7nE",  # marathons, rodeos, runs, tournaments
    "KZFzniwnSyZfZ7v7na",  # carnivals, circuses, outdoor theater
    "KZFzniwnSyZfZ7v7ni",  # parades, fairs
]

def get_tickmaster_events(sites):
    load_dotenv()
    KEY = os.getenv('TICKET_MASTER_CONSUMER')
    raw_events = []
    start_dt = (datetime.utcnow() + timedelta(weeks=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    for site in sites:
        logger.info(f"Ticketmaster: searching {site}")
        city, state = site.split(',')

        for segment_id in SEGMENT_IDS:
            page = 0

            while True:
                response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params={
                    "city": city.strip(),
                    "stateCode": state.strip(),
                    "radius": TICKET_MASTER_RADIUS,
                    "unit": "miles",
                    "countryCode": "US",
                    "size": 200,
                    "apikey": KEY,
                    "page": page,
                    "segmentId": segment_id,
                    "source": "ticketmaster,universe,frontgate",
                    "sort": "date,asc",
                    "startDateTime": start_dt,
                })
                try:
                    data = response.json()
                except Exception as e:
                    logger.error(f"Ticketmaster response parse failed: {e}")
                    break
                events = data.get("_embedded", {}).get("events", [])

                for event in events:
                    venue = event.get("_embedded", {}).get("venues", [{}])[0]
                    raw_events.append({
                        "title": event.get("name"),
                        "date": {"when": event.get("dates", {}).get("start", {}).get("localDate")},
                        "address": [venue.get("name", ""), venue.get("city", {}).get("name", ""), venue.get("state", {}).get("stateCode", "")],
                        "search_city": site,
                    })

                total_pages = data.get("page", {}).get("totalPages", 0)
                if page >= total_pages - 1 or page >= 40:
                    break
                page += 1

    return raw_events