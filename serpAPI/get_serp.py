import serpapi
import os
from dotenv import load_dotenv
from .locations import sites
from .outdoor import is_outdoor_event
from .organizer_site_url import get_organizer_url
from .get_contact_page_url import get_contact_page
from .get_contact_information import extract_contact_info, fill_missing_fields

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
                while start < 15:
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

                        if is_outdoor_event(event.get("title", "")):

                            url = get_organizer_url(f"{key},{location}")
                            contact_page_url = get_contact_page(url)
                            if contact_page_url[1]:  # only call LLM if we got homepage HTML
                                contact_information = extract_contact_info(contact_page_url[1], contact_page_url[2])
                                contact_information = fill_missing_fields(key, location, contact_information)
                            else:
                                contact_information = [None, None, None]
                            event = {
                                "title": event.get("title"),
                                "date": event.get("date", {}).get("when"),
                                "address": ", ".join(event.get("address", [])),
                                "url": url,
                                'contact_page': contact_page_url[0],
                                'email': contact_information[0],
                                'phone': contact_information[1],
                                'mailing_address': contact_information[2]
                            }
                            print(event)
                            all_events.append(event)

                    start += 10

    return all_events