import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from config.cost_tracker import tracker

logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = (
    "You are classifying events by profitability potential for a portable sanitation rental company "
    "(porta potties, roll-off dumpsters, restroom trailers). "
    "Consider the event's estimated attendance, whether it's outdoor, duration, and overall popularity. "
    "Given a numbered list of events, return a JSON object with one key: 'profitability' — "
    "an object mapping each event number (as a string) to one of: 'high', 'medium', 'low'. "
    "Example: {\"profitability\": {\"1\": \"high\", \"2\": \"low\", \"3\": \"medium\"}}"
)


def _build_event_list(events):
    lines = []
    for i, event in enumerate(events):
        title = event.get("title", "")
        address = event.get("address", "")
        lines.append(f"{i+1}. {title} | {address}")
    return "\n".join(lines)


def _classify_batch(batch, batch_num, total_batches):
    logger.info(f"Profitability batch {batch_num}/{total_batches} ({len(batch)} events)")
    event_list = _build_event_list(batch)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": event_list},
        ],
    )
    tracker.track_openai("gpt-4.1-mini", response.usage)

    try:
        result = json.loads(response.choices[0].message.content)
        profitability_map = result.get("profitability", {})
        for i, event in enumerate(batch):
            event["profitability"] = profitability_map.get(str(i + 1), "medium")
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse profitability batch {batch_num}: {e}")
        for event in batch:
            event["profitability"] = None

    return batch


def classify_profitability_batch(events, batch_size=50):
    """Classify profitability for all events in batches."""
    if not events:
        return events

    batches = [events[i:i + batch_size] for i in range(0, len(events), batch_size)]
    total_batches = len(batches)

    for i, batch in enumerate(batches):
        _classify_batch(batch, i + 1, total_batches)

    logger.info(f"Profitability classification done for {len(events)} events")
    return events