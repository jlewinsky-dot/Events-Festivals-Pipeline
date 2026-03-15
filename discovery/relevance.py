import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from config.cost_tracker import tracker

logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = (
    "You are a filter for a portable restroom rental company. "
    "Given a numbered list of events, decide which events "
    "would plausibly need portable restroom (porta potty) rentals.\n\n"

    "SAY YES to: outdoor festivals, fairs (county fairs, state fairs, renaissance faires), "
    "races (5k, 10k, marathon, triathlon, mud run, color run), "
    "parades, rodeos, block parties, street festivals, food/beer/wine festivals, "
    "outdoor concerts and music festivals, car shows, truck shows, air shows, "
    "fireworks, outdoor sporting tournaments, charity walks/runs, "
    "large community events, crawfish boils, BBQ competitions, "
    "and any large gathering that is likely held outdoors "
    "or in a temporary venue without permanent restrooms.\n\n"

    "SAY NO to:\n"
    "- Hikes, nature walks, bird walks, wildflower walks, forest bathing, lantern hikes, moon hikes\n"
    "- Farmers markets (weekly recurring markets, not one-time festivals)\n"
    "- Small workshops, classes, camps (gardening workshops, succulent workshops, Jr. Ranger camps)\n"
    "- Indoor concerts at permanent venues (amphitheaters, music halls, arenas, bars, clubs)\n"
    "- Book fairs, yarn fests, health fairs, career fairs, job fairs, science fairs, expos\n"
    "- Conferences, seminars, webinars, networking events, galas, banquets, luncheons\n"
    "- Events at permanent indoor venues with their own restrooms "
    "(theaters, convention centers, hotels, restaurants, bars, libraries, museums)\n"
    "- Yoga, dance classes, recitals, lectures\n"
    "- Pop-up food vendor events at established markets (these are at permanent market buildings)\n"
    "- Small nonprofit meetings, school events with under ~100 expected attendees\n\n"

    "HINTS:\n"
    "- If the venue is a nature park/sanctuary and the event is a hike or nature program, say NO.\n"
    "- If the event title contains 'farmers market' and it looks like a regular weekly market, say NO. "
    "But a one-time festival AT a farmers market venue is fine.\n"
    "- If the venue is an amphitheater, arena, or music hall, the venue has restrooms — say NO.\n"
    "- Fundraiser walks/runs are YES (they set up on trails/roads with no facilities).\n"
    "- When in doubt, say YES. Only filter out things that are clearly irrelevant.\n\n"

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