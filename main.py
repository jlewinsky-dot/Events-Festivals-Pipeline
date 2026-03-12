from serpAPI.get_serp import get_serp_events
from serpAPI.cost_tracker import tracker
from serpAPI.get_cities import ctities
from serpAPI.locations import sites_2
import logging
import csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # for each site, I am getting serp events and writing to csv
    sites = ctities(sites_2)

    for site in sites:
        logger.info(f"Starting pipeline for {site}")
        logger.info("Fetching Serp events")
        serp_events = get_serp_events(sites[site])
        logger.info("Finished fetching Serp events")

        filename = f"{site.replace(' ', '_').lower()}_events.csv"
        with open(filename, 'w', newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "date", "address", "url", "contact_page", "email",
                                                   #"email_confidence", "phone", "mailing_address"
                                                   ])
            writer.writeheader()
            writer.writerows(serp_events)

        logger.info(f"Saved to {filename}")
        tracker.print_summary()
        tracker.reset()


if __name__ == '__main__':
    main()

