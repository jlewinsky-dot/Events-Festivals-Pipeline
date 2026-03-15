import logging
from requests.exceptions import RequestException
from playwright.sync_api import Error as PlaywrightError
from openai import APIError
from scraping.organizer_site_url import get_organizer_url
from scraping.get_contact_page_url import get_contact_page
from scraping.get_contact_information import extract_contact_info, fill_missing_fields, search_missing_fields
from .profitability import classify_profitability
#from .email_validation import email_confidence

logger = logging.getLogger(__name__)


# will run on its own thread
def process_event(event, location):
    key = event.get("title")

    try:
        url = get_organizer_url(f"{key},{location}")
    except RequestException as e:
        logger.error(f"Failed to get organizer URL for '{key}': {e}")
        url = None

    if not url:
        return {
            "title": key,
            "date": event.get("date", {}).get("when"),
            "address": ", ".join(event.get("address", [])),
            "url": None,
            "contact_page": None,
            "email": None,
            "sells_food": None,
            "sells_alcohol": None,
            "sells_vip": None,
        }

    try:
        contact_page_url = get_contact_page(url)
    except PlaywrightError as e:
        logger.error(f"Failed to get contact page for '{key}': {e}")
        contact_page_url = [None, None, None]

    contact_information = [None, None, None, None, None, None]
    profitability = None

    try:
        if contact_page_url[1]:  # only call LLM if we got homepage HTML
            contact_information = extract_contact_info(key, contact_page_url[1], contact_page_url[2], organizer_url=url)
            contact_information = fill_missing_fields(key, location, contact_information)
            contact_information = search_missing_fields(key, location, contact_information)
            profitability = classify_profitability(key, location)
    except APIError as e:
        logger.error(f"Failed to extract contact info for '{key}': {e}")

    return {
        "title": key,
        "date": event.get("date", {}).get("when"),
        "address": ", ".join(event.get("address", [])),
        "url": url,
        "contact_page": contact_page_url[0],
        "email": contact_information[0],
        "sells_food": contact_information[3],
        "sells_alcohol": contact_information[4],
        "sells_vip": contact_information[5],
        "profitability": profitability,
    }
