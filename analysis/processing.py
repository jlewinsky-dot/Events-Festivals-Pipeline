import logging
from requests.exceptions import RequestException
from playwright.sync_api import Error as PlaywrightError
from openai import APIError
from scraping.organizer_site_url import get_organizer_url
from scraping.get_pages import get_contact_page
from scraping.get_contact_information import extract_event_info, fill_missing_contact_fields, search_missing_fields

logger = logging.getLogger(__name__)


# will run on its own thread
def process_event(event, location):
    title = event.get("title")
    address_parts = event.get("address", [])
    date_field = event.get("date")
    date_when = date_field.get("when") if isinstance(date_field, dict) else date_field

    # Defaults
    url = contact_page = None
    info = [None] * 8  # email, phone, mailing, food, alcohol, vip, attendees, source

    try:
        url = get_organizer_url(f"{title},{location}")
    except RequestException as e:
        logger.error(f"Failed to get organizer URL for '{title}': {e}")

    if url:
        try:
            pages = get_contact_page(url)
            contact_page = pages[0]
            if pages[1]:  # home_html present
                info = extract_event_info(title, pages[1], pages[2], about_html=pages[3], organizer_url=url)
                info = fill_missing_contact_fields(title, location, info)
        except (PlaywrightError, APIError) as e:
            logger.error(f"Scrape/extract failed for '{title}': {e}")

    # Single fallback call handles both the no-URL case and any missing fields
    try:
        info = search_missing_fields(title, location, info)
    except Exception as e:
        logger.error(f"Fallback search failed for '{title}': {e}")

    return {
        "city_state": address_parts[-1] if address_parts else location,
        "search_city": location,
        "title": title,
        "date": date_when,
        "address": ", ".join(address_parts),
        "url": url,
        "contact_page": contact_page,
        "email": info[0],
        "phone": info[1],
        "sells_food": info[3],
        "sells_alcohol": info[4],
        "sells_vip": info[5],
        "estimated_attendees": info[6],
        "attendees_source": info[7],
    }