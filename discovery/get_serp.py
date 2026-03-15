import serpapi
import os
import re
import logging
import time
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException
from .relevance import filter_relevant_events
from analysis.processing import process_event
from config.cost_tracker import tracker

logger = logging.getLogger(__name__)


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
    raw_events = []  # collecting all deduplicated events first, filtering after
    total = 0
    count = 0
    for location in locations:
        logger.info("------------------------")
        logger.info(f"NOW SEARCHING {location}")
        logger.info("------------------------")
        '''
        queries = [  # Queries to loop through
            f"festivals {location}",
            f"fairs {location}",
            f"outdoor events {location}",
            f"marathon {location}",
            f"rodeo {location}",
            f"parade {location}",
            f"tailgate {location}"
        ]
        '''
        queries = [
            f"festivals {location}",
            f"fairs {location}",
            f"outdoor events {location}",
            f"marathon {location}",
            f"rodeo {location}",
            f"parade {location}",
            #f"tailgate {location}",
            #f"car show {location}",
            f"beer fest {location}",
            f"5k run {location}",
            f"triathlon {location}",
            f"concert outdoor {location}",
            #f"food truck event {location}",
            #f"fireworks {location}",
            #f"block party {location}",
            f"wine festival {location}",
            #f"bbq competition {location}",
            #f"crawfish boil {location}",
            f"color run {location}",
            #f"mud run {location}",
            #f"obstacle course race {location}",
            f"community event outdoor {location}",
            f"street festival {location}",
            #f"harvest festival {location}",
            #f"christmas event outdoor {location}",
            #f"easter egg hunt {location}",
            #f"pumpkin festival {location}",
            #f"flea market {location}",
            #f"swap meet {location}",
            f"renaissance faire {location}",
            #f"horse show {location}",
           # f"air show {location}",
            f"county fair {location}",
            f"state fair {location}",
            f"fundraiser walk {location}",
            f"charity run {location}",
            f"music festival outdoor {location}",
            #f"craft fair outdoor {location}",
            #f"sporting tournament {location}",
            #f"lacrosse tournament {location}",
            #f"softball tournament {location}",
            #f"soccer tournament {location}",
        ]
        for query in queries:  # loop through each query
            start = 0
            while start < 2000:
                try:
                    results = serpapi.GoogleSearch({
                        "engine": "google_events",
                        "q": query,
                        "location": location,
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
                    key = normalize_title(event.get("title", ""))  # Creating key for deduplication among queries

                    if key in seen:
                        count += 1
                          # if event in seen events, skip
                        continue

                    seen.add(key)  # if not seen, add to seen
                    raw_events.append((event, location))
                    total += 1
                    logger.info(f" {total} - {event['title']}")

                start += 10
                time.sleep(1)

    logger.info(f"Duplicates skipped: {count}")
    logger.info(f"Total unique events before relevance filter: {len(raw_events)}")

    # GPT relevance filter — replaces is_outdoor_event keyword matching
    relevant_pairs = filter_relevant_events(raw_events)
    logger.info(f"Events after relevance filter: {len(relevant_pairs)} / {len(raw_events)}")

    #  process all the relevant events with thread pool
    with ThreadPoolExecutor(max_workers=5) as executor:

        futures = {
            executor.submit(process_event, event, location): event.get("title")
            for event, location in relevant_pairs
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