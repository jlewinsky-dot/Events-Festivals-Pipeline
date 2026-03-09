import serpapi
import os
import logging
from dotenv import load_dotenv
from urllib.parse import urlparse
from requests.exceptions import RequestException
from .cost_tracker import tracker

logger = logging.getLogger(__name__)

BLOCKLIST = {
    # Ticketing
    "eventbrite.com", "ticketmaster.com", "stubhub.com", "seatgeek.com",
    "viagogo.com", "tickpick.com", "tix4cause.com", "eventticketscenter.com",
    "premiumseatsusa.com", "vipticketscanada.ca", "rateyourseats.com",
    "axs.com", "ticketweb.com", "livenation.com", "bandsintown.com",
    # Socials & aggregators
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "yelp.com", "meetup.com", "wikipedia.org",
    "allevents.in", "10times.com", "eventeny.com",
    "worldtattooevents.com", "do615.com",
    "predicthq.com", "cantonfair.net", "spotify.com", "shazam.com",
    "hauntpay.com",
}

# This function is just searching for the event organizers or realated event website
def get_organizer_url(event_title):
    load_dotenv()
    query = f"{event_title}, official site"

    try:
        results = serpapi.GoogleSearch({
            "engine": "google",
            "q": query,
            "api_key": os.getenv("SERPAPI_KEY"),
        }).get_dict()
        tracker.track_serpapi()
    except RequestException as e:
        logger.error(f"SerpAPI search failed for '{event_title}': {e}")
        return None
    
    for result in results.get("organic_results", [])[:5]:
        try:
            # Stripping out the slug
            domain = urlparse(result["link"]).netloc.replace("www.", "")
            # If the domain not in blocklist, return that url
            if domain not in BLOCKLIST:
                return result["link"]
        except ValueError as e:
            logger.error(f"Failed to parse result link for '{event_title}': {e}")
            continue

    return None