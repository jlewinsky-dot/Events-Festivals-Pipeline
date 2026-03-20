import os
import re
import time
import logging
import threading

import serpapi
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException

from .relevance import filter_relevant_events
from .ticketmaster import get_tickmaster_events
from analysis.processing import process_event
from analysis.profitability import classify_profitability_batch
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
]


def normalize_title(title):
    title = title.lower()
    title = re.sub(r'20\d{2}', '', title)           # strip years (2024, 2025, 2026, etc.)
    title = re.sub(r'[^a-z0-9 ]', '', title)         # strip punctuation
    title = re.sub(r'\s+', ' ', title).strip()       # collapse whitespace
    return title


def get_serp_events(locations: list) -> list:
    load_dotenv()
    all_events = []
    seen = set()
    seen_lock = threading.Lock()
    raw_events = []  # collecting all deduplicated events first, filtering after
    total_counter = [0, 0]  # [total, dupes]

    for location in locations:
        logger.info("------------------------")
        logger.info(f"NOW SEARCHING {location}")
        logger.info("------------------------")

        queries = [f"{q} {location}" for q in QUERIES]

        def run_query(query):
            local_events = []
            start = 0

            while start < 2000:
                try:
                    results = serpapi.GoogleSearch({
                        "engine": "google_events",
                        "q": query,
                        "location": location,
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

                    local_events.append((event, location))
                    logger.info(f" {total_counter[0]} - {event['title']}")

                start += 10
                time.sleep(0.5)

            return local_events

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_query, q) for q in queries]
            for future in as_completed(futures):
                try:
                    raw_events.extend(future.result())
                except Exception as e:
                    logger.error(f"Query thread failed: {e}")

    # Pull in Ticketmaster events and deduplicate
    try:
        ticketmaster_events = get_tickmaster_events(locations)
        for event, loc in ticketmaster_events:
            key = normalize_title(event.get("title", ""))
            if key in seen:
                total_counter[1] += 1
                continue
            seen.add(key)
            raw_events.append((event, loc))
            total_counter[0] += 1
    except Exception as e:
        logger.error(f"Ticketmaster fetch failed: {e}")

    logger.info(f"Duplicates skipped: {total_counter[1]}")
    logger.info(f"Total unique events before relevance filter: {len(raw_events)}")

    # GPT relevance filter — replaces is_outdoor_event keyword matching
    relevant_pairs = filter_relevant_events(raw_events)
    logger.info(f"Events after relevance filter: {len(relevant_pairs)} / {len(raw_events)}")

    #  process all the relevant events with thread pool
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {
            executor.submit(process_event, event, loc): event.get("title")
            for event, loc in relevant_pairs
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

    # Batch classify profitability with gpt-4.1-mini
    all_events = classify_profitability_batch(all_events)

    return all_events