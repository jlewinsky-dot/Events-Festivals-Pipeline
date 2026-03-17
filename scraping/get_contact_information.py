import logging
from openai import OpenAI
from dotenv import load_dotenv
import serpapi
import os
import json
from playwright.sync_api import sync_playwright
from .get_contact_page_url import clean_html
from config.cost_tracker import tracker

logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI()


def extract_contact_info(event_title:str, home_html:str, contact_html=None, about_html=None, organizer_url=None) -> list:
    content = f"HOMEPAGE:\n{home_html}"
    if contact_html:
        content += f"\n\nCONTACT PAGE:\n{contact_html}"
    if about_html:
        content += f"\n\nABOUT PAGE:\n{about_html}"

    url_hint = f" The organizer's website is {organizer_url}." if organizer_url else ""

    response = client.chat.completions.create(
        model="gpt-5",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are extracting contact information for the event organizer of '{event_title}'.{url_hint} "
                    "Return a JSON object with these keys: email, phone, mailing_address, sells_food, sells_alcohol, sells_vip, estimated_attendees, attendees_source in this exact order. "
                    "Only return info that belongs to the event organizer, NOT the venue or ticketing platform. "
                    "email must be a valid email address belonging to the event organizer, not the venue, not a ticketing platform, not a person's name. "
                    "If multiple emails are present, prefer the one whose domain matches the organizer's website. "
                    "mailing_address must be a postal or mailing address explicitly labeled as such, not an event venue address. "
                    "sells_food: true if the event sells or serves food (food vendors, food trucks, food included with ticket, etc). "
                    "Do NOT say true just because food is mentioned — phrases like 'no outside food allowed' or 'food not permitted' do not count. "
                    "sells_alcohol: true if the event sells or serves alcohol (beer, wine, cocktails, drink tickets, beer garden, etc). "
                    "Do NOT say true just because alcohol is mentioned — phrases like 'no alcohol allowed' or 'alcohol-free event' do not count. "
                    "sells_vip: true if the event sells VIP tickets, VIP passes, or VIP packages. "
                    "sells_food, sells_alcohol, sells_vip must be boolean true, false, or null — not strings. "
                    "estimated_attendees: the number of attendees expected or reported for this event. "
                    "If the website explicitly mentions an attendance figure, use that number. "
                    "If not, make your best estimate based on the event type, size, and any context available — estimating is allowed and expected for this field. "
                    "estimated_attendees must be a plain integer with no commas, ranges, or text — e.g. 5000 not '5,000' or 'around 5000'. Always return a number, never null. "
                    "attendees_source: 'website' if the figure was explicitly stated on the page, 'estimated' if you guessed. "
                    "For all other fields, only return info you can clearly see on the page. Do not guess or make anything up. "
                    "Use null for any field you cannot find (except estimated_attendees which should always have a value)."
                ),
            },
            {
                "role": "user",
                "content": content,
            },
        ],
    )
    tracker.track_openai("gpt-5", response.usage)

    result = json.loads(response.choices[0].message.content)
    email = result.get("email")
    if email and "[email protected]" in email.lower():
        email = None
    return [email, result.get("phone"), result.get("mailing_address"), result.get("sells_food"), result.get("sells_alcohol"), result.get("sells_vip"), result.get("estimated_attendees"), result.get("attendees_source")]

def fill_missing_fields(event_title, location, contact_info):
    # Only run if email is still missing (phone/mailing_address not used in output right now)
    if contact_info[0] is not None:
        return contact_info
    fields = ["email", "phone", "mailing_address"]

    # Search Google for contact information
    query = f"{event_title} {location} contact information"
    results = serpapi.GoogleSearch({
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_KEY"),
    }).get_dict()
    tracker.track_serpapi()

    # Grab titles and snippets from top results
    search_text = []
    for r in results.get("organic_results", [])[:5]:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        search_text.append(f"{title}\n{snippet}")

    if not search_text:
        return contact_info

    # Ask GPT to extract all missing fields from search results
    response = client.chat.completions.create(
        model="gpt-5",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    f"Extract contact information for the event organizer of '{event_title}' from the search results below. "
                    "Return a JSON object with these keys: email, phone, mailing_address. "
                    "Only return info that belongs to the event organizer, NOT the venue or ticketing platform. "
                    "email must be a valid email address, not a person's name. "
                    "mailing_address must be a postal or mailing address, not an event venue address. "
                    "Only return info you can clearly see. "
                    "Do not guess or make anything up. "
                    "Use null if you cannot find it."
                ),
            },
            {
                "role": "user",
                "content": "\n\n".join(search_text),
            },
        ],
    )
    tracker.track_openai("gpt-5", response.usage)

    result = json.loads(response.choices[0].message.content)

    # Only fill fields that are still null
    for i, field in enumerate(fields):
        if contact_info[i] is None:
            contact_info[i] = result.get(field)

    return contact_info

def search_missing_fields(event_title, location, contact_info):
    # Last resort: have GPT search the web — only if email is still missing
    if contact_info[0] is not None:
        return contact_info
    fields = ["email", "phone", "mailing_address"]
    missing = ["email"]  # only searching for email right now

    response = client.chat.completions.create(
        model="gpt-5-search-api",
        web_search_options={},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are extracting contact information for event organizers. "
                    "Return ONLY a JSON object with these keys: email, phone, mailing_address. "
                    "Only return info that belongs to the event organizer, NOT the venue or ticketing platform. "
                    "email must be a valid email address, not a person's name. "
                    "mailing_address must be a postal or mailing address, not an event venue address. "
                    "Do not guess or make anything up. "
                    "Use null for any field you cannot find. "
                    "No markdown, no explanation, just the JSON object."
                ),
            },
            {
                "role": "user",
                "content": f"Find the {', '.join(missing)} for the organizer of '{event_title}' in {location}.",
            },
        ],
    )
    tracker.track_openai("gpt-5-search-api", response.usage)

    # Parse JSON from response (no structured output support)
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(text)
        for i, field in enumerate(fields):
            if contact_info[i] is None:
                contact_info[i] = result.get(field)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse search response for '{event_title}'")

    return contact_info