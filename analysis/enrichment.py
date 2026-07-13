import re


# Strip a city_state string to 'City, ST' format
def clean_city_state(city_state):
    if not isinstance(city_state, str):
        return city_state
    m = re.search(r"([A-Za-z .\'-]+, *[A-Z]{2})", city_state)
    return m.group(1).strip() if m else city_state.strip()

# Add aerial_mileage, yard_city_state, and cleaned city_state to each event.
def enrich_events(events, site, city_to_yard, aerial_mileage_by_site):
    for event in events:
        event["city_state"] = clean_city_state(event.get("city_state", "")) # Cleaning city state
        event["aerial_mileage"] = aerial_mileage_by_site.get(site)
        event["yard_city_state"] = city_to_yard.get(event.get("search_city", ""), "")
    return events

# this is building a list of cities that I searched for and had no results returned for
def find_empty_cities(searched_cities, events):
    found_cities = {clean_city_state(e.get("city_state", "")) for e in events}
    return [c for c in searched_cities if clean_city_state(c) not in found_cities]