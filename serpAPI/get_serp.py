import serpapi
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from .outdoor import is_outdoor_event
from .processing import process_event

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
        ]
        count = 0
        for query in queries:  # loop through each query
            start = 0
            while start < 50:
                try:
                    results = serpapi.GoogleSearch({
                        "engine": "google_events",
                        "q": query,
                        "api_key": os.getenv("SERPAPI_KEY"),
                        "start": start
                    }).get_dict()
                except Exception as e:
                    print(f"SerpAPI request failed for '{query}' start={start}: {e}")
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

    # now process all the outdoor events concurrently with thread pool
    with ThreadPoolExecutor(max_workers=5) as executor:
        # submit returns a Future immediately so it doesnt block
        futures = {
            executor.submit(process_event, event, location): event.get("title")
            for event, location in outdoor_events
        }

        # as_completed gives us results as they finish, not in the order we submitted them
        for future in as_completed(futures):
            title = futures[future]
            try:
                result = future.result()  # grabbing return value from process_event
                print(result)
                all_events.append(result)
            except Exception as e:
                print(f"Event processing failed for '{title}': {e}")
    print(count)
    return all_events