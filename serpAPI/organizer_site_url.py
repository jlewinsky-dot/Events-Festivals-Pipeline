import serpapi
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

BLOCKLIST = {
    # Ticketing
    "eventbrite.com", "ticketmaster.com", "stubhub.com", "seatgeek.com",
    "viagogo.com", "tickpick.com", "tix4cause.com", "eventticketscenter.com",
    "premiumseatsusa.com", "vipticketscanada.ca", "rateyourseats.com",
    "axs.com", "ticketweb.com", "livenation.com", "bandsintown.com",

    # Socials
    "twitter.com", "x.com", "yelp.com", "worldtattooevents.com", "do615.com",
    "predicthq.com", "cantonfair.net", "spotify.com", "shazam.com",
    "hauntpay.com",
}

def get_organizer_url(event_title):
    load_dotenv()
    query = f"{event_title}, official site"
    results = serpapi.GoogleSearch({
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_KEY"),
    }).get_dict()

    for result in results.get("organic_results", [])[:5]:
        domain = urlparse(result["link"]).netloc.replace("www.", "")
        if domain not in BLOCKLIST:
            return result["link"]
    return None