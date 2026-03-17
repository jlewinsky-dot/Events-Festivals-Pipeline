import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.cost_tracker import tracker

logger = logging.getLogger(__name__)

load_dotenv()
client = OpenAI()

SYSTEM_PROMPT = (
    "You are a filter for a portable restroom rental company. "
    "Given a numbered list of events, decide which ones are likely outdoor events "
    "that could need portable restroom (porta potty) rentals.\n\n"

    "SAY YES to: outdoor festivals, fairs (county fairs, state fairs, renaissance faires), "
    "rodeos (the rodeo event itself, NOT individual performers playing at a rodeo), "
    "parades, block parties, street festivals, food/beer/wine festivals, "
    "outdoor concerts and music festivals (multi-artist), car shows, truck shows, air shows, "
    "fireworks, outdoor sporting tournaments, "
    "races (5K, 10K, marathon, half marathon, triathlon, mud run, color run, trail run, fun run), "
    "charity walks/runs, fundraiser walks/runs, "
    "large community events, crawfish boils, BBQ competitions, "
    "hot air balloon festivals, monster truck rallies, motorcycle rallies, circus events, "
    "and any gathering that is likely held outdoors or in a temporary venue without permanent restrooms.\n\n"

    "SAY NO to:\n"
    "- Individual singer/band/artist names as the event title — these are performer listings, NOT the event itself. "
    "Examples: 'Gunnar Latham', 'Cameron Hobbs', 'Diamond Dixie', 'Parker Ryan', 'Flatland Cavalry', "
    "'Shane Smith and The Saints', 'Tanya Tucker', 'William Clark Green', 'Katrina Cain', 'Trevor Underwood', "
    "'Vanessa Carlton', 'Niko Moon', 'Luke Bryan', 'Post Malone', 'Bartly Live', 'Honey Made', "
    "'Billy King & the Bad Bad Bad', 'Cam Allen', 'Timothy Howls', 'Marcy Grace', 'Meghan Marie'. "
    "If the title looks like a person's name or band name, it is a NO even if the venue is a rodeo or festival.\n"
    "- Concerts/shows at permanent venues (amphitheaters, arenas, music halls, bars, clubs, wineries, breweries)\n"
    "- Hikes, nature walks, bird walks, wildflower walks, forest bathing, lantern hikes\n"
    "- Farmers markets (weekly recurring markets, not one-time festivals)\n"
    "- Small workshops, classes, camps (gardening, cooking, yoga, dance, Jr. Ranger)\n"
    "- Book fairs, yarn fests, health fairs, career fairs, job fairs, science fairs, expos\n"
    "- Conferences, seminars, webinars, networking events, galas, banquets, luncheons\n"
    "- Events at permanent indoor venues (theaters, convention centers, hotels, restaurants, "
    "bars, libraries, museums)\n"
    "- Motorsport/racing events at permanent tracks or speedways (Formula 1, MotoGP, NASCAR, Le Mans, "
    "MotoAmerica, IndyCar) — these venues like Circuit of the Americas, racetracks, speedways "
    "have their own permanent restrooms\n"
    "- Butterfly/insect/nature education programs or festivals\n"
    "- Movie nights, outdoor movie screenings\n"
    "- Garage sales, estate sales, campouts\n"
    "- Golf tournaments, golf championships, PGA events, golf qualifiers — golf courses have restrooms\n"
    "- Artisan markets, makers markets, night markets, craft markets — these are small vendor events at existing venues\n"
    "- Puppy yoga, goat yoga, outdoor yoga events — too small\n"
    "- Kite days, kite festivals (small community events at parks with restrooms)\n"
    "- Generic ticket listings where the title is just 'Any One Day Ticket' or similar — not an actual event\n\n"

    "CRITICAL RULES:\n"
    "- If the event title is a person's name, band name, or artist name, say NO — even if the venue is 'Rodeo Austin' "
    "or another festival. These are individual performer listings, not the event itself.\n"
    "- If the venue is an amphitheater, arena, music hall, winery, or brewery, say NO.\n"
    "- If the venue is a racetrack, speedway, or 'Circuit of the Americas', say NO — permanent facilities.\n"
    "- 'Farmers market' in the title = NO unless it's clearly a one-time festival.\n"
    "- When in doubt, say YES. Only filter out things that are clearly irrelevant or clearly indoors.\n\n"

    "Return a JSON object with one key: \"relevant\" — an array of the event numbers (integers) that pass."
)


def build_event_list(event_pairs):
    lines = []
    for i, (event, location) in enumerate(event_pairs):
        title = event.get("title", "")
        address = ", ".join(event.get("address", []))
        lines.append(f"{i+1}. {title} | {address} | Market: {location}")
    return "\n".join(lines)


def _filter_batch(batch, batch_num, total_batches):
    logger.info(f"Relevance filter: batch {batch_num}/{total_batches} ({len(batch)} events)")
    event_list = build_event_list(batch)

    response = client.chat.completions.create(
        model="gpt-5",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": event_list},
        ],
    )
    tracker.track_openai("gpt-5", response.usage)

    try:
        result = json.loads(response.choices[0].message.content)
        relevant_nums = set(result.get("relevant", []))
        return [batch[n - 1] for n in relevant_nums if 1 <= n <= len(batch)]
    except (json.JSONDecodeError, IndexError, TypeError) as e:
        logger.error(f"Failed to parse relevance response: {e}")
        return batch


def filter_relevant_events(event_pairs, batch_size=200):
    if not event_pairs:
        return []

    batches = [event_pairs[i:i + batch_size] for i in range(0, len(event_pairs), batch_size)]
    total_batches = len(batches)
    relevant = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_filter_batch, batch, i + 1, total_batches): i
            for i, batch in enumerate(batches)
        }

        for future in as_completed(futures):
            try:
                relevant.extend(future.result())
            except Exception as e:
                logger.error(f"Batch failed: {e}")

    logger.info(f"Relevance filter done: {len(relevant)} relevant / {len(event_pairs)} total")
    return relevant