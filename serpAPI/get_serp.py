import serpapi
import os
import logging
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException
from .outdoor import is_outdoor_event
from .processing import process_event
from .cost_tracker import tracker

logger = logging.getLogger(__name__)

def get_serp_events(locations: list) -> list:
    load_dotenv()
    all_events = []
    seen = set()
    outdoor_events = []  # collecting outdoor events first, processing concurrently after

    for location in locations:
        queries = [  # Queries to loop through
            f"festivals {location}",
            f"fairs {location}",
            f"outdoor events {location}",
            f"marathon {location}",
            f"rodeo {location}",
            f"parade {location}",
            f"tailgate {location}"
        ]
        count = 0
        for query in queries:  # loop through each query
            start = 0
            while start < 2000:
                try:
                    results = serpapi.GoogleSearch({
                        "engine": "google_events",
                        "q": query,
                        "api_key": os.getenv("SERPAPI_KEY"),
                        "start": start
                    }).get_dict()
                    tracker.track_serpapi()
                except RequestException as e:
                    logger.error(f"SerpAPI request failed for '{query}' start={start}: {e}")
                    break

                events = results.get("events_results", [])  # Gettings events from API response

                if not events:  # if no events, end
                    break

                for event in events:
                    key = event.get("title")  # Creating key for deduplicaton amoung queries

                    if key in seen:
                        count += 1
                          # if event in seen events, skip
                        continue

                    seen.add(key)  # if not seen, add to seen

                    if is_outdoor_event(event.get("title", "")):
                        outdoor_events.append((event, location))

                start += 10

    #  process all the outdoor events with thread pool
    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = {
            executor.submit(process_event, event, location): event.get("title")
            for event, location in outdoor_events
        }

        # as_completed gives us results as they finish, not in the order we submitted them
        for future in as_completed(futures):
            title = futures[future]
            try:
                result = future.result()  # grabbing return value from process_event
                logger.info(result)
                all_events.append(result)
            except Exception as e:
                logger.error(f"Event processing failed for '{title}': {type(e).__name__}: {e}")
    logger.info(f"Duplicates skipped: {count}")
    return all_events