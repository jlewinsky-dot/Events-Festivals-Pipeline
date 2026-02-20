from serpAPI.get_serp import get_serp_events
from serpAPI.locations import sites
import logging
import os
import csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting pipeline")
    logger.info("Fethcing Serp events")
    serp_events = get_serp_events(sites)
    logger.info("Finished fetching Serp events")

    with open('serpapi_events.csv', 'w', newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "date", "address", "url", "contact_page", "email", "phone", "mailing_address"])
        writer.writeheader()
        writer.writerows(serp_events)

if __name__ == '__main__':
    main()

