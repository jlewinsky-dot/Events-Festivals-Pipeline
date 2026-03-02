# Events & Festivals Pipeline

A lead generation pipeline that discovers outdoor festivals, fairs, and events near target service areas, then extracts event organizer contact information (email, phone, mailing address) into per-company CSV files.

## Architecture

```
locations.py (company → cities)
       │
       ▼
get_serp.py (Google Events search per city)
       │
       ▼
outdoor.py (filter: is it an outdoor event?)
       │
       ▼
organizer_site_url.py (Google Search → organizer website)
       │
       ▼
get_contact_page_url.py (Playwright → scrape homepage & contact page)
       │
       ▼
get_contact_information.py (GPT-4.1 → extract email/phone/address)
       │  ├─ fill_missing_fields (SerpAPI + GPT-4.1 for gaps)
       │  └─ search_missing_fields (GPT-4o web search as last resort)
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

This will loop through each company in `serpAPI/locations.py`, search for outdoor events in their service areas, and output a CSV per company (e.g. `a_clean_portoco_events.csv`).

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
| `phone` | Organizer phone number |
| `mailing_address` | Organizer postal/mailing address |

## Project Structure

```
├── main.py                          # Pipeline orchestrator
├── requirements.txt                 # Python dependencies
├── .env                             # API keys (not tracked)
├── .gitignore
└── serpAPI/
    ├── __init__.py
    ├── locations.py                 # Company → city mappings
    ├── outdoor.py                   # Event keyword filtering
    ├── get_serp.py                  # SerpAPI Google Events search
    ├── organizer_site_url.py        # Find organizer website via Google Search
    ├── get_contact_page_url.py      # Scrape homepage & contact page with Playwright
    └── get_contact_information.py   # Extract contact info with GPT-4.1
```

## APIs & Services

- **[SerpAPI](https://serpapi.com/)** — Google Events and Google Search
- **[OpenAI](https://openai.com/)** — GPT-4.1 and GPT-4o-search-preview for contact extraction
- **[Playwright](https://playwright.dev/)** — Headless browser for scraping organizer websites
