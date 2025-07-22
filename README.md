# Autochek Africa Vehicle Scraper

A functional command-line scraper that extracts real vehicle listings from Autochek Africa. Successfully tested and verified to work with the live website.

## ⚠️ Current Status

**✅ Working Features:**
- Real data extraction from Autochek.africa
- Listing ID, URL, make, model, year, and variant extraction
- Pagination handling (currently limited to 2 pages for testing)
- Proper Playwright integration with Autochek's dynamic content

**🔧 Known Limitations:**
- Price, location, mileage, and thumbnail extraction need HTML selector updates
- Currently extracts all vehicles, not filtered by search criteria (Autochek shows all available inventory)
- Page limit set to 2 for testing (can be increased by modifying `page_num > 2` in scraper.py line 203)

## Project Structure

```
autochek-scraper/
├── src/autochek_scraper/          # Core package
│   ├── __init__.py               # Package initialization  
│   ├── scraper.py                # Main scraping logic
│   └── cli.py                    # Command-line interface
├── tests/                        # Test suite
│   ├── __init__.py
│   └── test_scraper.py           # Unit tests
├── examples/                     # Sample outputs
│   ├── sample_toyota_corolla_2015.json
│   └── sample_toyota_corolla_2015.csv
├── scripts/                      # Utility scripts
│   ├── validate_scraper.py       # Comprehensive validation
│   └── test_csv_generation.py    # CSV generation test
├── config/                       # Configuration files
│   └── .env.example             # Environment template
├── docs/                         # Documentation
│   └── CODE_EXPLANATION.md      # Detailed code walkthrough
├── scrape_autochek.py           # Main entry point
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container configuration
└── README.md                     # Project documentation
```

## Features

- **Modular Architecture**: Clean separation of concerns with organized codebase
- **Multiple Search Strategies**: Form-based, URL parameter, and fallback approaches
- **Comprehensive Data Extraction**: All required fields with intelligent parsing
- **Pagination Handling**: Automatic traversal of all result pages  
- **Dual Output Formats**: Both JSON and CSV export options
- **Robust Error Handling**: Graceful fallbacks and detailed logging
- **Rate Limiting**: Respectful scraping with configurable delays
- **Browser Automation**: Playwright with requests fallback
- **Comprehensive Testing**: Unit tests and validation suite

## Installation

### Local Installation

1. Clone this repository
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

**Note:** Due to system-managed Python environments on some systems, using a virtual environment is required.

### Docker Installation

1. Build the Docker image:
   ```bash
   docker build -t autochek-scraper .
   ```

2. Verify the build:
   ```bash
   docker run --rm autochek-scraper --help
   ```

## Usage

### Local Usage

**Important:** Activate your virtual environment first:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### JSON Output
```bash
python3 scrape_autochek.py --make "Toyota" --model "Corolla" --year 2015 --out corolla_2015.json
```

#### CSV Output
```bash
python3 scrape_autochek.py --make "Toyota" --model "Corolla" --year 2015 --out corolla_2015.csv
```

#### Both Formats
```bash
python3 scrape_autochek.py --make "Toyota" --model "Corolla" --year 2015 --out results.json --csv corolla_2015.csv
```

**Note:** The scraper currently extracts all available vehicles from Autochek, not just those matching your search criteria. This is due to how Autochek's website displays inventory.

### Docker Usage

#### Basic Docker Usage
```bash
# JSON output (save to current directory)
docker run --rm -v $(pwd):/app/output autochek-scraper \
  --make "Toyota" --model "Corolla" --year 2015 --out /app/output/results.json

# CSV output
docker run --rm -v $(pwd):/app/output autochek-scraper \
  --make "Honda" --model "Civic" --year 2018 --out /app/output/results.csv

# Both formats with custom rate limiting
docker run --rm -v $(pwd):/app/output autochek-scraper \
  --make "Nissan" --model "Sentra" --year 2020 \
  --out /app/output/results.json --csv /app/output/results.csv --rate-limit 2.0
```

#### Advanced Docker Options
```bash
# Run with visible browser (useful for debugging)
docker run --rm -v $(pwd):/app/output \
  -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
  autochek-scraper --make "Toyota" --model "Camry" --year 2019 \
  --out /app/output/results.json --no-headless

# Run with custom logging level
docker run --rm -v $(pwd):/app/output autochek-scraper \
  --make "Ford" --model "Focus" --year 2017 --out /app/output/results.json \
  --log-level DEBUG
```

#### Docker Compose (Optional)

Create `docker-compose.yml` for easier management:
```yaml
version: '3.8'
services:
  autochek-scraper:
    build: .
    volumes:
      - ./output:/app/output
    environment:
      - PYTHONUNBUFFERED=1
    command: >
      --make "Toyota" 
      --model "Corolla" 
      --year 2015 
      --out /app/output/results.json
```

Then run with:
```bash
docker-compose up --build
```

### Docker Notes

#### Volume Mounting
- **Required**: Mount output directory with `-v $(pwd):/app/output` to save results to host
- **Optional**: Mount config directory with `-v $(pwd)/config:/app/config` for custom settings

#### Environment Variables
```bash
# Set via Docker run
docker run --rm -e PYTHONUNBUFFERED=1 -e LOG_LEVEL=DEBUG \
  -v $(pwd):/app/output autochek-scraper --make "Toyota" --model "Corolla" --year 2015 \
  --out /app/output/results.json

# Or create .env file and use --env-file
echo "PYTHONUNBUFFERED=1" > .env
echo "LOG_LEVEL=DEBUG" >> .env
docker run --rm --env-file .env -v $(pwd):/app/output autochek-scraper \
  --make "Honda" --model "Accord" --year 2020 --out /app/output/results.json
```

#### Troubleshooting Docker

**Common Issues:**
- **Permission errors**: Ensure output directory is writable
- **No output files**: Check volume mount paths (`/app/output` in container)
- **Browser issues**: Use `--no-headless` for debugging, add display forwarding on Linux

**Debug Mode:**
```bash
# Run with interactive shell for debugging
docker run -it --rm -v $(pwd):/app/output autochek-scraper bash

# Check logs with verbose output
docker run --rm -v $(pwd):/app/output autochek-scraper \
  --make "Toyota" --model "Corolla" --year 2015 --out /app/output/results.json \
  --log-level DEBUG
```

### Arguments

- `--make`: Vehicle make (required, e.g., "Toyota")
- `--model`: Vehicle model (required, e.g., "Corolla") 
- `--year`: Vehicle year (required, e.g., 2015)
- `--out`: Output file path (required, .json or .csv)
- `--csv`: Alternative CSV output file path (optional)
- `--headless`: Run browser in headless mode (default: true)
- `--rate-limit`: Rate limit between requests in seconds (default: 1.0)

## Sample Output

### Current Real Output (Working)
```json
[
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
]
```

### Expected Full Output (After Selector Updates)
```json
[
  {
    "listing_id": "12345",
    "make": "Toyota",
    "model": "Corolla",
    "year": 2015,
    "variant": "LE",
    "price": 5500000,
    "currency": "NGN",
    "mileage": 85000,
    "location": "Lagos",
    "listing_url": "https://autochek.africa/ng/car/Toyota-Corolla-ref-12345",
    "thumbnail_url": "https://autochek.africa/images/12345.jpg",
    "created_at": "2024-01-15"
  }
]
```

## 🔧 Required Updates for Complete Data Extraction

To extract the remaining fields (price, location, mileage, thumbnails), the following updates are needed:

### 1. Price Extraction
**Current Issue:** `price` and `currency` fields return `null`
**Required:** Update CSS selectors in `_extract_vehicle_data()` method (lines 323-338 in scraper.py)
```python
# Current selectors may need updating:
price_selectors = [
    'p.MuiTypography-root.MuiTypography-body1.css-1bztvjj',
    # Add more specific selectors based on actual HTML
]
```

### 2. Location Extraction  
**Current Issue:** `location` field returns `null`
**Required:** Update location selectors (lines 358-377 in scraper.py)
```python
# Nigerian cities detection is working, but selectors need updating
location_selectors = [
    'span.MuiTypography-root.MuiTypography-caption.css-umr6w4',
    # Add more specific selectors
]
```

### 3. Mileage Extraction
**Current Issue:** `mileage` field returns `null`  
**Required:** Update mileage selectors (lines 341-355 in scraper.py)

### 4. Thumbnail Images
**Current Issue:** `thumbnail_url` field returns `null`
**Required:** Update image selectors (lines 380-407 in scraper.py)

### 5. Increase Page Limit
**Current:** Limited to 2 pages for testing
**Update:** Change line 203 in scraper.py:
```python
if page_num > 10:  # Increase from 2 to desired limit
```

## Documentation

For detailed technical information:

- **[Code Explanation](docs/CODE_EXPLANATION.md)**: Comprehensive step-by-step walkthrough of the implementation
- **[Sample Outputs](examples/)**: JSON and CSV examples for Toyota Corolla 2015
- **[Configuration](config/.env.example)**: Environment setup template

## Architecture

The scraper uses a modular architecture with:

- **`scraper.py`**: Core scraping logic with Playwright automation
- **`cli.py`**: Command-line interface and argument parsing
- **`test_scraper.py`**: Comprehensive unit test coverage
- **`validate_scraper.py`**: Automated validation and quality checks

Key design principles:
- **Separation of Concerns**: Clear module boundaries
- **Error Resilience**: Multiple fallback mechanisms
- **Testability**: Mockable components and dependency injection
- **Configurability**: Flexible settings via CLI and environment

## Limitations

- Website structure may change requiring scraper updates
- Rate limiting applied to respect website resources  
- Some fields may be null if not available on listings
- Currently optimized for Nigerian market
- Search filtering not implemented (extracts all available vehicles)
- Price, location, mileage, and thumbnail extraction need selector updates

## Missing Features (Stretch Goals)

The following stretch goals from the original requirements are documented but not yet implemented:

### 1. HTTP 5xx Auto-Retry
- **Status:** Implementation guide available in `docs/MISSING_FEATURES_IMPLEMENTATION.md`
- **What's Needed:** Exponential backoff retry logic for server errors
- **Estimated Effort:** 2-3 hours

### 2. Database Storage Options
- **Status:** Implementation guide available in `docs/MISSING_FEATURES_IMPLEMENTATION.md`  
- **What's Needed:** `--store sqlite` and `--store ddb` command-line options
- **Estimated Effort:** 4-6 hours
- **Dependencies:** `boto3` for DynamoDB, `sqlalchemy` for database abstraction

See `docs/MISSING_FEATURES_IMPLEMENTATION.md` for complete step-by-step implementation guides.

## Testing

### Quick Functionality Test
Test that the scraper is working with real data:
```bash
source venv/bin/activate
python3 scrape_autochek.py --make "Toyota" --model "Corolla" --year 2015 --out test.json --log-level INFO
```

Expected result: Should extract 40+ vehicles with valid listing IDs, URLs, make/model/year data.

### Unit Tests
Run unit tests with:
```bash
pytest test_scraper.py -v
```

### Comprehensive Validation
Run complete validation suite:
```bash
python scripts/validate_scraper.py
```

This validates:
- Project structure and file organization
- Dependencies and package imports
- Python syntax for all modules
- Unit test execution
- Data validation and output formats
- Command-line interface functionality
- Network error handling and fallbacks

## Recent Updates (Latest)

**✅ Fixed Major Issues (January 2025):**
- Fixed Playwright ElementHandle API usage errors
- Updated title parsing to handle Autochek's "YEAR MAKE MODEL" format
- Verified real data extraction from live Autochek website
- Successfully extracts listing IDs, URLs, make/model/year, and variants
- Added comprehensive installation instructions for virtual environments

**🔄 Next Steps for Full Functionality:**
1. Update HTML selectors for price/location/mileage extraction
2. Implement search filtering to match user criteria
3. Add missing stretch goals (HTTP retry, database storage)
4. Increase pagination limit for production use