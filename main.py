import csv
import logging

from config.cost_tracker import tracker
from config.locations import sites_2
from discovery.get_cities import ctities
from discovery.get_serp import get_serp_events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CSV_FIELDS = [
    "title", "date", "address", "url", "contact_page", "email",
    "sells_food", "sells_alcohol", "sells_vip",
    "estimated_attendees", "attendees_source",
    "profitability",
    #"email_confidence", "phone", "mailing_address",
]


def main():
    # for each site, I am getting serp events and writing to csv
    sites = ctities(sites_2)
    #sites = {'FusionSite Nashville': ['Nashville, TN', 'Murfreesboro, TN', 'Franklin, TN', 'Brentwood, TN', 'Clarksville, TN'],
             #'Stamback Services': ['Tucson, AZ', 'Marana, AZ', 'Oro Valley, AZ', 'Sahuarita, AZ', 'Wilcox, AZ'],
             #'Event Solutions': ['Lafayette, LA', 'Broussard, LA', 'Youngsville, LA', 'Carencro, LA', 'Scott, LA', 'Lake Charles, LA ']}

    for site, cities in sites.items():
        logger.info(f"Starting pipeline for {site} - {cities}")
        logger.info("Fetching Serp events")
        events = get_serp_events(cities)
        logger.info("Finished fetching Serp events")

        filename = f"{site.replace(' ', '_').lower()}_events.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(events)

        logger.info(f"Saved to {filename}")
        tracker.print_summary()
        tracker.save_to_csv()
        tracker.reset()


if __name__ == "__main__":
    main()

