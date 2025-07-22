# Autochek Africa Vehicle Scraper

A functional command-line scraper that extracts real vehicle listings from Autochek Africa. Successfully tested and verified to work with the live website.

## Status

**✅ Working:** Listing IDs, URLs, make/model/year, variants, pagination, HTTP 5xx retry logic  
**🔧 Needs Updates:** Price, location, mileage, thumbnail extraction (CSS selectors)

## Installation

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
# Basic usage
python3 scrape_autochek.py --make "Toyota" --model "Corolla" --year 2015 --out results.json

# With retry configuration
python3 scrape_autochek.py --make "Honda" --model "Civic" --year 2018 --out results.csv --max-retries 5

# CSV output
python3 scrape_autochek.py --make "Ford" --model "Focus" --year 2020 --out results.csv
```

## Sample Output

```json
{
  "listing_id": "BAZ8UQt5b",
  "make": "Toyota",
  "model": "corolla", 
  "year": 2020,
  "variant": null,
  "price": null,
  "currency": null,
  "mileage": null,
  "location": null,
  "listing_url": "https://autochek.africa/ng/car/Toyota-corolla-ref-BAZ8UQt5b",
  "thumbnail_url": null,
  "created_at": null
}
```

## Features

- **HTTP 5xx Auto-Retry**: Exponential backoff on server errors
- **Real Data Extraction**: Working with live Autochek.africa
- **Pagination**: Automatic page traversal (currently limited to 6 pages)
- **Rate Limiting**: Respectful scraping delays
- **Multiple Formats**: JSON and CSV output

## Arguments

- `--make`, `--model`, `--year`: Vehicle criteria (required)
- `--out`: Output file path (required)
- `--max-retries`: HTTP retry attempts (default: 3)
- `--rate-limit`: Delay between requests (default: 1.0s)
- `--log-level`: Logging verbosity (default: INFO)

## Known Limitations

- Extracts all available vehicles (not filtered by search criteria)  
- Price/location/mileage fields need CSS selector updates
- Page limit set to 6 for testing (configurable in scraper.py:203)

## Quick Test

```bash
source venv/bin/activate
python3 scrape_autochek.py --make "Toyota" --model "Corolla" --year 2015 --out test.json
```

Expected: 40+ vehicles with valid listing data.