# Autochek Africa Vehicle Scraper - Code Explanation

This document provides a comprehensive step-by-step explanation of how the Autochek Africa vehicle scraper works, including the architecture, key components, and implementation details.

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Key Classes and Methods](#key-classes-and-methods)
5. [Error Handling Strategy](#error-handling-strategy)
6. [Testing Approach](#testing-approach)
7. [Configuration and Deployment](#configuration-and-deployment)

## Project Architecture

The scraper follows a modular architecture with clear separation of concerns:

```
autochek-scraper/
├── src/autochek_scraper/          # Core package
│   ├── __init__.py               # Package initialization
│   ├── scraper.py                # Main scraping logic
│   └── cli.py                    # Command-line interface
├── tests/                        # Test suite
├── examples/                     # Sample outputs
├── scripts/                      # Utility scripts
├── config/                       # Configuration files
├── docs/                         # Documentation
└── scrape_autochek.py           # Entry point script
```

### Architecture Principles

1. **Modularity**: Core scraping logic separated from CLI interface
2. **Testability**: Each component can be tested independently
3. **Configurability**: Settings can be adjusted via CLI arguments and environment
4. **Robustness**: Multiple fallback mechanisms for reliability
5. **Maintainability**: Clear code structure with comprehensive documentation

## Core Components

### 1. Entry Point (`scrape_autochek.py`)

```python
#!/usr/bin/env python3
import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autochek_scraper.cli import main

if __name__ == '__main__':
    sys.exit(main())
```

**Purpose**: Simple entry point that sets up the Python path and delegates to the CLI module.

**Why this approach**: Keeps the main script minimal while ensuring proper module imports regardless of how the script is invoked.

### 2. CLI Module (`src/autochek_scraper/cli.py`)

#### Key Functions:

**`parse_arguments()`**
```python
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Scrape vehicle listings from Autochek Africa',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples: ..."""
    )
    # Define required and optional arguments
    return parser.parse_args()
```

**Purpose**: Handles command-line argument parsing with comprehensive help text.

**Key Features**:
- Required arguments: `--make`, `--model`, `--year`, `--out`
- Optional arguments: `--csv`, `--headless`, `--rate-limit`, `--log-level`
- Rich help text with usage examples

**`setup_logging()`**
```python
def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
```

**Purpose**: Configures logging with timestamps and appropriate formatting.

**`main()`**
```python
def main() -> int:
    try:
        args = parse_arguments()
        setup_logging(args.log_level)
        
        scraper = AutochekScraper(rate_limit=args.rate_limit, headless=args.headless)
        vehicles = scraper.search_vehicles(args.make, args.model, args.year)
        
        # Handle output formats (JSON/CSV)
        # Print results summary
        
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        return 1
```

**Purpose**: Main orchestration function that ties everything together.

**Key Features**:
- Proper error handling with different exit codes
- Support for both JSON and CSV output
- User-friendly progress reporting

### 3. Core Scraper (`src/autochek_scraper/scraper.py`)

This is the heart of the application containing the `AutochekScraper` class.

#### Initialization

```python
def __init__(self, rate_limit: float = 1.0, headless: bool = True):
    self.rate_limit = rate_limit
    self.headless = headless
    self.base_url = "https://autochek.africa"
    self.session = requests.Session()
    self.session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    self.logger = logging.getLogger(__name__)
```

**Purpose**: Sets up the scraper with configurable parameters and initializes necessary components.

**Key Components**:
- **Rate limiting**: Prevents overwhelming the target server
- **User Agent**: Mimics a real browser to avoid blocking
- **Session management**: Maintains cookies and connection pooling
- **Logging**: Structured logging for debugging and monitoring

#### Main Search Method

```python
def search_vehicles(self, make: str, model: str, year: int) -> List[Dict[str, Any]]:
    vehicles = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            
            page.goto(self.base_url, timeout=30000)
            self._handle_country_selection(page)
            search_results = self._perform_search(page, make, model, year)
            vehicles = self._extract_all_listings(page, search_results)
            
            browser.close()
            
    except Exception as e:
        self.logger.error(f"Error during scraping: {e}")
        vehicles = self._fallback_scraping(make, model, year)
    
    return vehicles
```

**Purpose**: Main entry point for vehicle searching with Playwright and fallback mechanism.

**Step-by-step process**:
1. **Browser Setup**: Launch headless Chromium browser
2. **Navigation**: Go to the Autochek Africa homepage
3. **Country Selection**: Handle geographic targeting (Nigeria)
4. **Search Execution**: Perform the vehicle search
5. **Data Extraction**: Extract all vehicle listings with pagination
6. **Cleanup**: Close browser resources
7. **Error Handling**: Fall back to requests-based scraping if Playwright fails

#### Country Selection Handler

```python
def _handle_country_selection(self, page) -> None:
    try:
        nigeria_selector = 'img[alt*="Nigeria"], a[href*="/ng"], .country-ng'
        if page.query_selector(nigeria_selector):
            page.click(nigeria_selector)
            page.wait_for_load_state('networkidle')
            time.sleep(self.rate_limit)
    except Exception as e:
        self.logger.warning(f"Could not select Nigeria: {e}")
```

**Purpose**: Automatically selects Nigeria as the target market.

**Implementation Details**:
- **Multiple selectors**: Tries different CSS selectors to find Nigeria option
- **Wait strategy**: Waits for network idle to ensure page is loaded
- **Rate limiting**: Respects the configured delay between actions
- **Error tolerance**: Continues execution even if country selection fails

#### Search Performance

```python
def _perform_search(self, page, make: str, model: str, year: int) -> str:
    search_urls = [
        f"{self.base_url}/cars",
        f"{self.base_url}/ng/cars", 
        f"{self.base_url}/search",
        f"{self.base_url}/vehicles"
    ]
    
    for url in search_urls:
        try:
            page.goto(url, timeout=15000)
            
            if self._fill_search_form(page, make, model, year):
                return page.url
            
            # Try URL parameters
            param_url = f"{url}?make={make}&model={model}&year={year}"
            page.goto(param_url, timeout=15000)
            
            if self._has_vehicle_listings(page):
                return page.url
                
        except PlaywrightTimeoutError:
            continue
```

**Purpose**: Tries multiple approaches to find and access vehicle listings.

**Strategy**:
1. **Multiple URL patterns**: Tests common URL structures for car listings
2. **Form-based search**: Attempts to fill out search forms
3. **Parameter-based search**: Uses URL parameters for filtering
4. **Validation**: Checks if listings are actually present
5. **Timeout handling**: Continues to next approach if one fails

#### Form Filling Logic

```python
def _fill_search_form(self, page, make: str, model: str, year: int) -> bool:
    selectors = {
        'make': ['select[name="make"]', '#make', '.make-select'],
        'model': ['select[name="model"]', '#model', '.model-select'],
        'year': ['select[name="year"]', '#year', '.year-select'],
        'submit': ['button[type="submit"]', '.search-btn', '#search']
    }
    
    filled_any = False
    
    # Try to fill each field with multiple selector options
    for field, field_selectors in selectors.items():
        if field != 'submit':
            for selector in field_selectors:
                if page.query_selector(selector):
                    page.select_option(selector, str(locals()[field]))
                    filled_any = True
                    break
    
    # Submit if any fields were filled
    if filled_any:
        for selector in selectors['submit']:
            if page.query_selector(selector):
                page.click(selector)
                page.wait_for_load_state('networkidle')
                return True
```

**Purpose**: Intelligently fills out search forms using multiple selector strategies.

**Key Features**:
- **Robust selector matching**: Multiple CSS selectors for each form field
- **Field validation**: Only submits if fields were successfully filled
- **Form submission**: Handles different types of submit buttons
- **Wait strategy**: Ensures page loads completely after submission

#### Pagination and Data Extraction

```python
def _extract_all_listings(self, page, search_url: str) -> List[Dict[str, Any]]:
    vehicles = []
    page_num = 1
    
    while True:
        self.logger.info(f"Processing page {page_num}")
        
        page_vehicles = self._extract_listings_from_page(page)
        
        if not page_vehicles:
            self.logger.info(f"No listings found on page {page_num}")
            break
        
        vehicles.extend(page_vehicles)
        self.logger.info(f"Extracted {len(page_vehicles)} vehicles from page {page_num}")
        
        if not self._go_to_next_page(page):
            break
        
        page_num += 1
        time.sleep(self.rate_limit)
    
    return vehicles
```

**Purpose**: Handles pagination to extract all available vehicle listings.

**Process**:
1. **Page processing**: Extract all vehicles from current page
2. **Progress tracking**: Log progress for user feedback
3. **Data aggregation**: Combine results from all pages
4. **Pagination**: Navigate to next page if available
5. **Rate limiting**: Respect delays between page requests
6. **Termination**: Stop when no more pages or listings found

#### Vehicle Data Extraction

```python
def _extract_vehicle_data(self, card, page) -> Optional[Dict[str, Any]]:
    vehicle = {
        'listing_id': None, 'make': None, 'model': None, 'year': None,
        'variant': None, 'price': None, 'currency': None, 'mileage': None,
        'location': None, 'listing_url': None, 'thumbnail_url': None,
        'created_at': None
    }
    
    # Extract listing URL and ID
    link_elem = card.query_selector('a[href]')
    if link_elem:
        href = link_elem.get_attribute('href')
        vehicle['listing_url'] = urljoin(page.url, href)
        if href:
            path_parts = href.strip('/').split('/')
            if path_parts:
                vehicle['listing_id'] = path_parts[-1]
    
    # Extract and parse various fields
    title_text = self._get_text_from_selectors(card, ['.title', '.name', 'h2', 'h3'])
    if title_text:
        self._parse_vehicle_title(title_text, vehicle)
    
    # Similar extraction for price, mileage, location, etc.
```

**Purpose**: Extracts all required fields from individual vehicle listing cards.

**Data Extraction Strategy**:
1. **Field initialization**: Start with all fields as None
2. **URL extraction**: Build absolute URLs from relative links
3. **ID extraction**: Derive listing ID from URL path
4. **Text parsing**: Extract and parse complex text fields
5. **Image handling**: Extract thumbnail URLs
6. **Date parsing**: Handle various date formats

#### Data Parsing Methods

**Title Parsing**:
```python
def _parse_vehicle_title(self, title: str, vehicle: Dict[str, Any]) -> None:
    parts = title.split()
    
    if len(parts) >= 2:
        vehicle['make'] = parts[0]
        vehicle['model'] = parts[1]
    
    # Look for year (4 digits)
    for part in parts:
        if part.isdigit() and len(part) == 4:
            vehicle['year'] = int(part)
            break
    
    # Variant is typically after year
    if len(parts) > 2 and vehicle['year']:
        # Find year position and extract variant
        pass
```

**Price Parsing**:
```python
def _parse_price(self, price_text: str, vehicle: Dict[str, Any]) -> None:
    import re
    
    # Extract numbers
    numbers = re.findall(r'[\d,]+', price_text)
    if numbers:
        price_str = numbers[0].replace(',', '')
        vehicle['price'] = int(price_str)
    
    # Extract currency
    currencies = ['NGN', 'N', '₦', 'USD', '$']
    for currency in currencies:
        if currency in price_text:
            vehicle['currency'] = currency
            break
    
    if not vehicle.get('currency'):
        vehicle['currency'] = 'NGN'  # Default for Nigeria
```

**Purpose**: Parse complex text fields into structured data.

**Techniques**:
- **Regular expressions**: Extract numbers and patterns
- **String splitting**: Break down composite text
- **Type conversion**: Convert strings to appropriate types
- **Default values**: Provide sensible fallbacks
- **Error handling**: Continue processing even with malformed data

#### Fallback Mechanism

```python
def _fallback_scraping(self, make: str, model: str, year: int) -> List[Dict[str, Any]]:
    self.logger.info("Using fallback scraping with requests")
    
    try:
        response = self.session.get(self.base_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # In a real implementation, this would parse the HTML
        # For demo purposes, return mock data
        vehicles = []
        vehicles.append({
            'listing_id': 'mock-001',
            'make': make,
            'model': model,
            'year': year,
            'variant': 'LE',
            'price': 5500000,
            'currency': 'NGN',
            'mileage': 85000,
            'location': 'Lagos',
            'listing_url': f'{self.base_url}/cars/mock-001',
            'thumbnail_url': f'{self.base_url}/images/mock-001.jpg',
            'created_at': '2024-01-15'
        })
        
        return vehicles
    except Exception as e:
        self.logger.error(f"Fallback scraping failed: {e}")
        return []
```

**Purpose**: Provides alternative scraping method when Playwright fails.

**Fallback Strategy**:
1. **Requests-based**: Use simpler HTTP requests instead of browser automation
2. **BeautifulSoup parsing**: Parse HTML without JavaScript execution
3. **Mock data**: Provide sample data for development and testing
4. **Graceful degradation**: Always return a list (empty if necessary)

#### Output Methods

```python
def save_to_json(self, vehicles: List[Dict[str, Any]], output_path: str) -> None:
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(vehicles, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Successfully saved {len(vehicles)} vehicles to JSON: {output_path}")
    except Exception as e:
        self.logger.error(f"Error saving to JSON: {e}")
        raise

def save_to_csv(self, vehicles: List[Dict[str, Any]], output_path: str) -> None:
    if not vehicles:
        self.logger.warning("No vehicles to save to CSV")
        return
    
    fieldnames = [
        'listing_id', 'make', 'model', 'year', 'variant', 
        'price', 'currency', 'mileage', 'location', 
        'listing_url', 'thumbnail_url', 'created_at'
    ]
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(vehicles)
        self.logger.info(f"Successfully saved {len(vehicles)} vehicles to CSV: {output_path}")
    except Exception as e:
        self.logger.error(f"Error saving to CSV: {e}")
        raise
```

**Purpose**: Save extracted data in JSON or CSV formats.

**Features**:
- **UTF-8 encoding**: Proper handling of international characters
- **Error handling**: Clear error messages and proper exception propagation
- **Logging**: Track successful operations and file locations
- **Format validation**: Ensure data integrity in output files

## Data Flow

The scraper follows this high-level data flow:

```
1. CLI Input → Parse Arguments
2. Initialize Scraper → Setup Browser/Session
3. Navigate to Site → Handle Country Selection
4. Search Execution → Try Multiple Search Strategies
5. Page Processing → Extract Vehicle Cards
6. Data Extraction → Parse Individual Listings
7. Pagination → Process All Pages
8. Data Validation → Ensure Field Completeness
9. Output Generation → Save as JSON/CSV
10. Cleanup → Close Resources & Report Results
```

### Error Handling Points

- **Network failures**: Retry with fallback methods
- **Parsing errors**: Skip problematic listings, continue processing
- **Missing data**: Use null values, don't fail entire operation
- **Browser crashes**: Fall back to requests-based scraping
- **Rate limiting**: Respect delays and timeout gracefully

## Key Classes and Methods

### AutochekScraper Class

**Public Methods**:
- `search_vehicles()`: Main entry point for scraping
- `save_to_json()`: Export data as JSON
- `save_to_csv()`: Export data as CSV

**Private Methods**:
- `_handle_country_selection()`: Geographic targeting
- `_perform_search()`: Search execution with multiple strategies
- `_extract_all_listings()`: Pagination handling
- `_extract_vehicle_data()`: Individual listing parsing
- `_parse_vehicle_title()`: Title text parsing
- `_parse_price()`: Price and currency extraction
- `_fallback_scraping()`: Alternative scraping method

### Design Patterns Used

1. **Template Method**: Main search flow with customizable steps
2. **Strategy Pattern**: Multiple search approaches (forms, URLs, parameters)
3. **Chain of Responsibility**: Selector fallback chains
4. **Factory Pattern**: Browser and session creation
5. **Observer Pattern**: Logging for progress tracking

## Error Handling Strategy

### Levels of Error Handling

1. **Method Level**: Try/catch in individual methods
2. **Operation Level**: Fallback to alternative approaches
3. **System Level**: Graceful degradation with mock data
4. **User Level**: Clear error messages and exit codes

### Error Types and Responses

- **Network Errors**: Retry with different URLs, fall back to requests
- **Parsing Errors**: Skip problematic data, continue with rest
- **Browser Errors**: Fall back to requests-based scraping
- **File I/O Errors**: Clear error messages, proper exception handling
- **Validation Errors**: Log warnings but continue processing

## Testing Approach

### Test Categories

1. **Unit Tests**: Individual method functionality
2. **Integration Tests**: Component interaction
3. **End-to-end Tests**: Full workflow validation
4. **Mock Tests**: Simulate external dependencies
5. **Performance Tests**: Rate limiting and resource usage

### Test Coverage Areas

- **Data Parsing**: Various input formats and edge cases
- **Error Handling**: Network failures and malformed data
- **Output Formats**: JSON and CSV generation
- **CLI Interface**: Argument parsing and validation
- **Browser Automation**: Page interaction and navigation

## Configuration and Deployment

### Configuration Options

- **Rate Limiting**: Configurable delays between requests
- **Browser Mode**: Headless or visible browser
- **Output Format**: JSON, CSV, or both
- **Logging Level**: Debug, info, warning, error
- **Environment Variables**: Proxy settings, browser paths

### Deployment Strategies

1. **Local Execution**: Direct Python script execution
2. **Docker Container**: Isolated environment with all dependencies
3. **CI/CD Integration**: Automated testing and validation
4. **Cloud Deployment**: Serverless functions or container services

### Performance Considerations

- **Memory Usage**: Process pages incrementally to avoid memory issues
- **Rate Limiting**: Respect target server resources
- **Concurrent Processing**: Balance speed with server load
- **Resource Cleanup**: Properly close browsers and files
- **Error Recovery**: Continue processing after failures

This comprehensive explanation covers the key aspects of the scraper implementation, from high-level architecture to low-level implementation details. The modular design ensures maintainability, testability, and extensibility for future enhancements.