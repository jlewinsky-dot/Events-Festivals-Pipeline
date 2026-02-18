import serpapi
import os
from dotenv import load_dotenv
from locations import sites
from outdoor import is_outdoor_event

def get_serp_events(sites):
    load_dotenv()
    all_events = []
    seen = set()

    for site in sites:
        for location in sites[site]:
            queries = [  # Queries to loop through
                f"festivals {location}",
                f"fairs {location}",
                f"outdoor events {location}",
            ]
            
            for query in queries: # loop through each query
                start = 0
                while True:
                    results = serpapi.GoogleSearch({
                        "engine": "google_events",
                        "q": query,
                        "api_key": os.getenv("SERPAPI_KEY"),
                        "start": start
                    }).get_dict()

                    events = results.get("events_results", []) # Gettings events from API response
                    if not events: # if no events, end
                        break

                    for event in events:
                        key = event.get("title") # Creating key for deduplicaton amoung queries
                        if key in seen: # if event in seen events, skip
                            continue
                        seen.add(key) # if not seen, add to seen

                        url = event.get("link")

                        for t in event.get("ticket_info", []):
                            if t.get("link_type") == "more info":
                                url = t.get("link")
                                break
            
                        if is_outdoor_event(event.get("title", "")):
                            all_events.append({
                                "title": event.get("title"),
                                "date": event.get("date", {}).get("when"),
                                "address": ", ".join(event.get("address", [])),
                                "url": url
                            })

                    start += 10

    return all_events