from .organizer_site_url import get_organizer_url
from .get_contact_page_url import get_contact_page
from .get_contact_information import extract_contact_info, fill_missing_fields, search_missing_fields
from .email_validation import email_confidence


# will run on its own thread
def process_event(event, location):
    key = event.get("title")

    try:
        url = get_organizer_url(f"{key},{location}")
    except Exception as e:
        print(f"Failed to get organizer URL for '{key}': {e}")
        url = None

    if not url:
        return {
            "title": key,
            "date": event.get("date", {}).get("when"),
            "address": ", ".join(event.get("address", [])),
            "url": None,
            "contact_page": None,
            "email": None,
        }

    try:
        contact_page_url = get_contact_page(url)
    except Exception as e:
        print(f"Failed to get contact page for '{key}': {e}")
        contact_page_url = [None, None, None]

    try:
        if contact_page_url[1]:  # only call LLM if we got homepage HTML
            contact_information = extract_contact_info(key, contact_page_url[1], contact_page_url[2])
            contact_information = fill_missing_fields(key, location, contact_information)
            contact_information = search_missing_fields(key, location, contact_information)
        else:
            contact_information = [None, None, None]
    except Exception as e:
        print(f"Failed to extract contact info for '{key}': {e}")
        contact_information = [None, None, None]
    address = ", ".join(event.get("address", []))
    return {
        "title": key,
        "date": event.get("date", {}).get("when"),
        "address": ", ".join(event.get("address", [])),
        "url": url,
        "contact_page": contact_page_url[0],
        "email": contact_information[0],
        #"email_confidence": email_confidence(contact_information[0], key, url, address),
        #"phone": contact_information[1],
        #"mailing_address": contact_information[2],
    }
