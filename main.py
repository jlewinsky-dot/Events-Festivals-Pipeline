from serpAPI.serpAPI import get_serp_events
from serpAPI.locations import sites
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting pipeline")
    logger.info("Fethcing Serp events")
    serp_events = get_serp_events(sites)
    logger.info("Finished fetching Serp events")
    print(serp_events)

if __name__ == '__main__':
    main()

