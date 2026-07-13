import os
import re
import time
import logging
import threading

import serpapi
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException

from discovery.relevance import filter_relevant_events
from discovery.ticketmaster import get_tickmaster_events
from analysis.processing import process_event
from config.cost_tracker import tracker

logger = logging.getLogger(__name__)

QUERIES = [
    "festivals", "festival", "fairs", "outdoor events",
    "marathon", "rodeo", "parade", "tailgate",
    "food festival", "music festival", "beer festival", "wine festival",
    "street festival", "cultural festival", "harvest festival",
    "fall festival", "spring festival",
    "county fair", "state fair", "renaissance faire",
    "bbq festival", "crawfish festival", "seafood festival",
    "chili cookoff", "ribfest",
    "art festival outdoor", "fiesta", "carnival", "jubilee",
    # farmers markets & outdoor markets
    "farmers market", "flea market", "trade days",
    # races & runs
    "5k run", "triathlon", "mud run", "color run",
    # community & seasonal
    "block party", "community festival", "july 4th celebration",
    "oktoberfest", "greek festival", "irish festival",
    # large outdoor
    "hot air balloon festival", "air show", "car show",
    "monster truck", "motocross event", "demolition derby",
    "polo match", "horse show", "equestrian event",
]


# strips years, punctuation, and whitespace of event title
def normalize_title(title):
    title = title.lower()
    title = re.sub(r'20\d{2}', '', title) # strip years
    title = re.sub(r'[^a-z0-9 ]', '', title) # strip punctuation
    title = re.sub(r'\s+', ' ', title).strip() # strip whitespace
    return title



#  single SerpAPI search query for a specific location

# loc = location for the query
# seen = set of normalized event titles
# seen_lock = All 5 events share the same seen set and same total counter
# total_counter = total dups counter
def run_query(query, loc, seen, seen_lock, total_counter):
    local_events = []
    start = 0

    while start < 2000:
        try:
            results = serpapi.GoogleSearch({
                "engine": "google_events",
                "q": f"{query} in {loc}",
                "location": loc,
                "api_key": os.getenv("SERPAPI_KEY"),
                "start": start,
            }).get_dict()
            tracker.track_serpapi()
        except RequestException as e:
            logger.error(f"SerpAPI request failed for '{query}' start={start}: {e}")
            break

        events = results.get("events_results", [])
        if not events:
            break

        for event in events:
            key = normalize_title(event.get("title", ""))

            with seen_lock:
                if key in seen:
                    total_counter[1] += 1
                    continue
                seen.add(key)
                total_counter[0] += 1

            event["search_city"] = loc
            local_events.append(event)
            logger.info(f" {total_counter[0]} - {event['title']}")

        start += 10
        time.sleep(0.5)

    return local_events


#  multiple search queries concurrently across different locations.
def fetch_google_events(locations, seen, seen_lock, total_counter):
    fetched_events = []
    for location in locations:
        logger.info("------------------------")
        logger.info(f"NOW SEARCHING {location}")
        logger.info("------------------------")

        queries = [query for query in QUERIES]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_query, query, location, seen, seen_lock, total_counter) for query in queries]
            for future in as_completed(futures):
                try:
                    fetched_events.extend(future.result())
                except Exception as e:
                    logger.error(f"Query thread failed: {e}")
                    
    return fetched_events


# Fetches events from Ticketmaster and appends unique ones to the raw events list.
def fetch_ticketmaster_events(locations, raw_events, seen, total_counter):
    try:
        ticketmaster_events = get_tickmaster_events(locations)
        for event in ticketmaster_events:
            key = normalize_title(event.get("title", ""))
            if key in seen:
                total_counter[1] += 1
                continue
            seen.add(key)
            raw_events.append(event)
            total_counter[0] += 1
    except Exception as e:
        logger.error(f"Ticketmaster fetch failed: {e}")


# Processes the final list of relevant events concurrently.
def process_all_events(relevant_events):
    all_events = []
    #  process all the relevant events with thread pool
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(process_event, event, event["search_city"]): event.get("title")
            for event in relevant_events
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
                
    return all_events


# Main
def get_serp_events(locations):
    load_dotenv()
    seen = set()
    seen_lock = threading.Lock()
    raw_events = []  # collecting all deduplicated events first, filtering after
    total_counter = [0, 0]  # [total, dupes]

    raw_events.extend(fetch_google_events(locations, seen, seen_lock, total_counter))
    
    fetch_ticketmaster_events(locations, raw_events, seen, total_counter)

    logger.info(f"Duplicates skipped: {total_counter[1]}")
    logger.info(f"Total unique events before relevance filter: {len(raw_events)}")

    relevant_events = filter_relevant_events(raw_events)
    logger.info(f"Events after relevance filter: {len(relevant_events)} / {len(raw_events)}")

    all_events = process_all_events(relevant_events)

    return all_events