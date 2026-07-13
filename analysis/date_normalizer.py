import json

from dotenv import load_dotenv
from openai import OpenAI

from config.cost_tracker import tracker


load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = (
    "Normalize event dates accurately. Return JSON only in this shape: "
    "{\"results\":[{\"index\":0,\"date\":\"...\"}]}. "
    "Output ONLY the day(s), never include times of day, weekdays, or time zones. "
    "If the original date is a range that spans multiple days, preserve BOTH the start and end dates "
    "as a range (e.g. 'May 15 – May 17' or 'Dec 28, 2026 – Jan 2, 2027'). "
    "If the original date is a range but only covers a single day (start and end are the same day), output just that single day. "
    "If the original date does NOT include a year, do NOT add one. "
    "If the original date includes a year, preserve it. "
    "Translate non-English month names to English (e.g. 'abr' → 'Apr', 'sept' → 'Sep'). "
    "Use the format 'Mon DD' for single days and 'Mon DD – Mon DD' for ranges, with year appended only if present in the original. "
    "If uncertain, keep the original date text."
)


def _normalize_batch(rows):
    response = client.chat.completions.create(
        model="gpt-5",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"rows": rows}, ensure_ascii=False)},
        ],
    )
    tracker.track_openai("gpt-5", response.usage)
    result = json.loads(response.choices[0].message.content)
    return {
        item.get("index"): item.get("date")
        for item in result.get("results", [])
        if isinstance(item, dict)
    }


def normalize_event_dates(events):
    if not events:
        return events

    rows = [
        {
            "index": i,
            "title": event.get("title", ""),
            "city_state": event.get("city_state", ""),
            "date": event.get("date", ""),
        }
        for i, event in enumerate(events)
    ]

    try:
        updates = {}
        batch_size = 10
        for start in range(0, len(rows), batch_size):
            updates.update(_normalize_batch(rows[start:start + batch_size]))
    except Exception:
        return events

    for i, event in enumerate(events):
        value = updates.get(i)
        if isinstance(value, str) and value.strip():
            event["date"] = value.strip()

    return events