# Events & Festivals Pipeline

Finds outdoor festivals, fairs, and events near a set of service areas, then scrapes each event organizer's website for contact info and writes one CSV report per site.

Built for lead generation in the portable sanitation industry, but the site coordinates and search queries are configurable, so it works for any business that sells to outdoor event organizers.

## How it works

1. `config/locations.py` defines each site as a list of lat/long coordinates with a search radius.
2. `discovery/get_cities.py` turns those coordinates into nearby city names (GeoDB API), with a prompt to add cities manually.
3. `discovery/get_serp.py` searches Google Events (SerpAPI) for each city across ~50 event queries, and `discovery/ticketmaster.py` pulls more from the Ticketmaster Discovery API.
4. `discovery/relevance.py` runs a GPT filter to keep only outdoor events that would actually need temporary facilities.
5. `analysis/processing.py` handles each event: find the organizer's site (`scraping/organizer_site_url.py`), scrape the homepage, contact, and about pages with Playwright (`scraping/get_pages.py`), then extract email, phone, and event details with GPT (`scraping/get_contact_information.py`), falling back to search when fields are missing.
6. `analysis/dedup_on_emails.py` drops duplicate organizers, `analysis/profitability.py` classifies each event high/medium/low, and `analysis/date_normalizer.py` cleans up date formats.
7. `output/report_writer.py` writes a CSV per site with the events table, a cost summary, and cities that returned no results.

`config/cost_tracker.py` tracks OpenAI and SerpAPI spend across the run and logs a summary per site.

## Setup

```bash
git clone <repo-url>
cd Events-Festivals-Pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Copy the example config files and fill in real values:

```bash
cp .env.example .env
cp config/locations.example.py config/locations.py
```

`.env` needs keys for SerpAPI, OpenAI, GeoDB (RapidAPI), and Ticketmaster. `config/locations.py` needs your site coordinates and yard cities. Both files are gitignored.

## Usage

```bash
python main.py
```

For each site it prints progress as it searches, asks if you want to manually add cities, and writes `<site_name>_events.csv` in the project root. Columns include event title, date, address, organizer URL and contact page, email, phone, whether the event sells food/alcohol/VIP, estimated attendance, and a profitability rating.

A full run costs real money (OpenAI + SerpAPI). The cost summary at the end of each site shows what was spent.
