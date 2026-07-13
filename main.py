import logging

from config.cost_tracker import tracker
from config.locations import sites
from discovery.get_cities import get_cities
from pipeline.run import run_pipeline_for_site
from analysis.enrichment import enrich_events, find_empty_cities
from analysis.date_normalizer import normalize_event_dates
from output.report_writer import write_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Radius comes from the last coordinate entry of each site
def extract_aerial_mileage(sites):
    return {
        site: coords[-1][2]
        for site, coords in sites.items()
        if coords and len(coords[-1]) > 2
    }


def main():
    site_cities, city_to_yard = get_cities(sites)
    aerial_mileage_by_site = extract_aerial_mileage(sites)

    for site, cities in site_cities.items():
        logger.info(f"Starting pipeline for {site} - {cities}")

        events = run_pipeline_for_site(cities)
        events = enrich_events(events, site, city_to_yard, aerial_mileage_by_site)
        events = normalize_event_dates(events)
        empty_cities = find_empty_cities(cities, events)

        write_report(site, events, empty_cities, tracker)

        tracker.print_summary()
        tracker.reset()


if __name__ == "__main__":
    main()