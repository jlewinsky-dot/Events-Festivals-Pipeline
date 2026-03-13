import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from .cost_tracker import tracker

logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = (
    "You are a filter for a portable restroom rental company. "
    "Given a numbered list of events, decide which events "
    "would plausibly need portable restroom (porta potty) rentals.\n\n"

    "SAY YES to: outdoor festivals, fairs, races (5k, marathon, triathlon), "
    "parades, rodeos, block parties, food/beer/wine events, concerts, car shows, "
    "fireworks, sporting tournaments, weddings, church gatherings, community events, "
    "fundraisers, holiday events, and any large gathering that is likely held outdoors "
    "or in a temporary venue without permanent restrooms. When in doubt, say YES.\n\n"

    "SAY NO to: small indoor events (recitals, classes, workshops, lectures, webinars), "
    "events at permanent indoor venues with their own restrooms (theaters, convention centers, "
    "hotels, restaurants, bars, libraries, museums), job/career fairs, "
    "dance classes, choir/orchestra concerts at indoor halls, yoga sessions, "
    "networking events, galas, banquets, resource fairs, benefit fairs at indoor venues, "
    "and anything that is clearly a small or indoor-only gathering.\n\n"

    "Be LENIENT. If there's any reasonable chance the event is outdoor or large enough "
    "to need portable restrooms, say yes. Only filter out things that are obviously irrelevant.\n\n"

    "Return a JSON object with one key: \"relevant\" — an array of the event numbers (integers) that pass."
)

def build_event_list(event_pairs):
    lines = []
    for i, (event, location) in enumerate(event_pairs):
        title = event.get("title", "")
        address = ", ".join(event.get("address", []))
        lines.append(f"{i+1}. {title} | {address} | Market: {location}")
    return "\n".join(lines)


def filter_relevant_events(event_pairs: list[tuple]) -> list[tuple]:
    if not event_pairs:
        return []

    event_list = build_event_list(event_pairs)

    response = client.chat.completions.create(
        model="gpt-4.1",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": event_list},
        ],
    )
    tracker.track_openai("gpt-4.1", response.usage)

    try:
        result = json.loads(response.choices[0].message.content)
        relevant_nums = set(result.get("relevant", []))
        return [event_pairs[n - 1] for n in relevant_nums if 1 <= n <= len(event_pairs)]
    
    except (json.JSONDecodeError, IndexError, TypeError) as e:
        logger.error(f"Failed to parse relevance response: {e}")
        return event_pairs