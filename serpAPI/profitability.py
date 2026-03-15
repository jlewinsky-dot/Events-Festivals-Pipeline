import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from .cost_tracker import tracker

logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI()


def classify_profitability(event_title, location):
    response = client.chat.completions.create(
        model="gpt-4o-search-preview",
        web_search_options={},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are classifying events by profitability potential for a portable sanitation rental company "
                    "(porta potties, roll-off dumpsters, restroom trailers). "
                    "Consider the event's estimated attendance, whether it's outdoor, duration, and overall popularity. "
                    "Return ONLY a JSON object with one key: profitability. "
                    "Value must be one of: high, medium, low. "
                    "No markdown, no explanation, just the JSON object."
                ),
            },
            {
                "role": "user",
                "content": f"Event: {event_title}, Location: {location}",
            },
        ],
    )
    tracker.track_openai("gpt-4o-search-preview", response.usage)

    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(text)
        return result.get("profitability")
    except json.JSONDecodeError:
        logger.error(f"Failed to parse profitability response for '{event_title}'")
        return None