# Events & Festivals Pipeline

A lead generation pipeline that discovers outdoor festivals, fairs, and events near target service areas, then extracts event organizer contact information (email, phone, mailing address) into per-company CSV files.

## Architecture

```
config/locations.py (company → lat/long coordinates)
       │
       ▼
discovery/get_cities.py (GeoDB API → city names from coordinates)
       │
       ▼
discovery/get_serp.py (Google Events search per city)
       │
       ▼
discovery/relevance.py (GPT filter: is it relevant for porta potty rental?)
       │
       ▼
scraping/organizer_site_url.py (Google Search → organizer website)
       │
       ▼
scraping/get_contact_page_url.py (Playwright → scrape homepage & contact page)
       │
       ▼
scraping/get_contact_information.py (GPT-5 → extract email/phone/address)
       │  ├─ fill_missing_fields (SerpAPI + GPT-5 for gaps)
       │  └─ search_missing_fields (GPT-5-search-api as last resort)
       ▼
analysis/profitability.py (GPT → classify event profitability)
       │
       ▼
main.py (write CSV per company)
```

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/jlewinsky-dot/Events-Festivals-Pipeline.git
cd Events-Festivals-Pipeline
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Set up environment variables
Create a `.env` file in the project root:
```
SERPAPI_KEY=your_serpapi_key
OPENAI_API_KEY=your_openai_api_key
```

## Usage

```bash
python main.py
```

This will loop through each company in `config/locations.py`, search for outdoor events in their service areas, and output a CSV per company (e.g. `a_clean_portoco_events.csv`).

## Output

Each CSV contains the following columns:

| Column | Description |
|---|---|
| `title` | Event name |
| `date` | When the event takes place |
| `address` | Event venue address |
| `url` | Organizer's official website |
| `contact_page` | URL of the organizer's contact page |
| `email` | Organizer email address |
| `sells_food` | Whether the event sells/serves food |
| `sells_alcohol` | Whether the event sells/serves alcohol |
| `sells_vip` | Whether the event sells VIP tickets |
| `profitability` | Event profitability potential (high/medium/low) |

## Project Structure

```
├── main.py                                # Pipeline orchestrator
├── requirements.txt                       # Python dependencies
├── .env                                   # API keys (not tracked)
├── .gitignore
├── config/
│   ├── __init__.py
│   ├── locations.py                       # Company → lat/long coordinate mappings
│   └── cost_tracker.py                    # Thread-safe API cost tracking
├── discovery/
│   ├── __init__.py
│   ├── get_cities.py                      # GeoDB API → city names from coordinates
│   ├── get_serp.py                        # SerpAPI Google Events search
│   └── relevance.py                       # GPT relevance filtering
├── scraping/
│   ├── __init__.py
│   ├── organizer_site_url.py              # Find organizer website via Google Search
│   ├── get_contact_page_url.py            # Scrape homepage & contact page with Playwright
│   └── get_contact_information.py         # Extract contact info with GPT-5
├── analysis/
│   ├── __init__.py
│   ├── processing.py                      # Per-event processing orchestrator
│   └── profitability.py                   # GPT profitability classification
└── inactive/
    ├── __init__.py
    ├── outdoor.py                         # Legacy keyword-based event filtering
    └── email_validation.py                # Email confidence scoring (disabled)
```

## APIs & Services

- **[SerpAPI](https://serpapi.com/)** — Google Events and Google Search
- **[OpenAI](https://openai.com/)** — GPT-5 and GPT-5-search-api for contact extraction, relevance filtering, and profitability classification
- **[Playwright](https://playwright.dev/)** — Headless browser for scraping organizer websites
- **[GeoDB Cities API](https://rapidapi.com/wirefreethought/api/geodb-cities)** — City lookup by lat/long coordinates
