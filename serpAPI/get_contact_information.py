from openai import OpenAI
from dotenv import load_dotenv
import serpapi
import os
import json
from playwright.sync_api import sync_playwright
from .get_contact_page_url import clean_html

load_dotenv()
client = OpenAI()


def extract_contact_info(event_title:str, home_html:str, contact_html=None) -> list:
    content = f"HOMEPAGE:\n{home_html}"
    if contact_html:
        content += f"\n\nCONTACT PAGE:\n{contact_html}"

    response = client.chat.completions.create(
        model="gpt-4.1",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are extracting contact information for the event organizer of '{event_title}'. "
                    "Return a JSON object with these keys: email, phone, mailing_address in this exact order. "
                    "Only return info that belongs to the event organizer, NOT the venue or ticketing platform. "
                    "email must be a valid email address, not a person's name. "
                    "mailing_address must be a postal or mailing address explicitly labeled as such, not an event venue address. "
                    "Only return info you can clearly see on the page. "
                    "Do not guess or make anything up. "
                    "Use null for any field you cannot find."
                ),
            },
            {
                "role": "user",
                "content": content,
            },
        ],
    )

    result = json.loads(response.choices[0].message.content)
    return [result.get("email"), result.get("phone"), result.get("mailing_address")]

def fill_missing_fields(event_title, location, contact_info):
    # If all fields already filled, skip
    fields = ["email", "phone", "mailing_address"]
    if all(v is not None for v in contact_info):
        return contact_info

    # Search Google for contact information
    query = f"{event_title} {location} contact information"
    results = serpapi.GoogleSearch({
        "engine": "google",
        "q": query,
        "api_key": os.getenv("SERPAPI_KEY"),
    }).get_dict()

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
        model="gpt-4.1",
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

    result = json.loads(response.choices[0].message.content)

    # Only fill fields that are still null
    for i, field in enumerate(fields):
        if contact_info[i] is None:
            contact_info[i] = result.get(field)

    return contact_info

def search_missing_fields(event_title, location, contact_info):
    # Last resort: have GPT search the web for any still-missing fields
    fields = ["email", "phone", "mailing_address"]
    if all(v is not None for v in contact_info):
        return contact_info

    # Build a string of what's still missing
    missing = [fields[i] for i in range(3) if contact_info[i] is None]

    response = client.chat.completions.create(
        model="gpt-4o-search-preview",
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

    # Parse JSON from response (no structured output support)
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(text)
        for i, field in enumerate(fields):
            if contact_info[i] is None:
                contact_info[i] = result.get(field)
    except json.JSONDecodeError:
        print(f"Failed to parse search response for '{event_title}'")

    return contact_info