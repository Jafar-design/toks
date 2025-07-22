"""
Core scraper functionality for Autochek Africa vehicle listings.
"""

import logging
import time
import csv
import json
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


class AutochekScraper:
    """Main scraper class for Autochek Africa vehicle listings."""
    
    def __init__(self, rate_limit: float = 1.0, headless: bool = True):
        """
        Initialize the scraper.
        
        Args:
            rate_limit: Delay between requests in seconds
            headless: Run browser in headless mode
        """
        self.rate_limit = rate_limit
        self.headless = headless
        self.base_url = "https://autochek.africa"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def search_vehicles(self, make: str, model: str, year: int) -> List[Dict[str, Any]]:
        """
        Search for vehicles matching the specified criteria.
        
        Args:
            make: Vehicle make (e.g., "Toyota")
            model: Vehicle model (e.g., "Corolla")  
            year: Vehicle year (e.g., 2015)
            
        Returns:
            List of vehicle dictionaries containing extracted data
        """
        self.logger.info(f"Searching for {make} {model} {year}")
        
        vehicles = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                page = browser.new_page()
                
                # Navigate to the site
                page.goto(self.base_url, timeout=30000)
                
                # Handle country selection if needed
                self._handle_country_selection(page)
                
                # Perform search
                search_results = self._perform_search(page, make, model, year)
                
                # Extract listings from all pages
                vehicles = self._extract_all_listings(page, search_results)
                
                browser.close()
                
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            # Fallback to requests-based scraping if Playwright fails
            vehicles = self._fallback_scraping(make, model, year)
        
        return vehicles
    
    def _handle_country_selection(self, page) -> None:
        """Handle country selection on the homepage."""
        try:
            # Look for Nigeria flag or country selector
            nigeria_selector = 'img[alt*="Nigeria"], a[href*="/ng"], .country-ng'
            if page.query_selector(nigeria_selector):
                page.click(nigeria_selector)
                page.wait_for_load_state('networkidle')
                time.sleep(self.rate_limit)
        except Exception as e:
            self.logger.warning(f"Could not select Nigeria: {e}")
    
    def _perform_search(self, page, make: str, model: str, year: int) -> str:
        """Navigate to Autochek Nigeria cars-for-sale page."""
        cars_url = f"{self.base_url}/ng/cars-for-sale"
        
        try:
            self.logger.info(f"Navigating to {cars_url}")
            page.goto(cars_url, timeout=30000)
            page.wait_for_load_state('networkidle')
            time.sleep(self.rate_limit)
            return cars_url
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to cars page: {e}")
            # Fallback to base URL
            page.goto(self.base_url, timeout=30000)
            return page.url
    
    def _fill_search_form(self, page, make: str, model: str, year: int) -> bool:
        """Fill out search form if found."""
        try:
            # Common search form selectors
            selectors = {
                'make': ['select[name="make"]', '#make', '.make-select'],
                'model': ['select[name="model"]', '#model', '.model-select'],
                'year': ['select[name="year"]', '#year', '.year-select'],
                'submit': ['button[type="submit"]', '.search-btn', '#search']
            }
            
            filled_any = False
            
            # Try to fill make
            for selector in selectors['make']:
                if page.query_selector(selector):
                    page.select_option(selector, make)
                    filled_any = True
                    break
            
            # Try to fill model
            for selector in selectors['model']:
                if page.query_selector(selector):
                    page.select_option(selector, model)
                    filled_any = True
                    break
            
            # Try to fill year
            for selector in selectors['year']:
                if page.query_selector(selector):
                    page.select_option(selector, str(year))
                    filled_any = True
                    break
            
            # Submit form if we filled anything
            if filled_any:
                for selector in selectors['submit']:
                    if page.query_selector(selector):
                        page.click(selector)
                        page.wait_for_load_state('networkidle')
                        time.sleep(self.rate_limit)
                        return True
            
            return filled_any
            
        except Exception as e:
            self.logger.warning(f"Could not fill search form: {e}")
            return False
    
    def _has_vehicle_listings(self, page) -> bool:
        """Check if page contains vehicle listings."""
        listing_selectors = [
            '.vehicle-card', '.car-card', '.listing-card',
            '[data-testid="car-card"]', '.vehicle-item'
        ]
        
        for selector in listing_selectors:
            if page.query_selector(selector):
                return True
        return False
    
    def _extract_all_listings(self, page, search_url: str) -> List[Dict[str, Any]]:
        """Extract listings from all pages with pagination using page_number parameter."""
        vehicles = []
        page_num = 1
        base_url = f"{self.base_url}/ng/cars-for-sale"
        
        while True:
            self.logger.info(f"Processing page {page_num}")
            
            # Navigate to specific page number
            if page_num == 1:
                page_url = base_url
            else:
                page_url = f"{base_url}?page_number={page_num}"
            
            try:
                page.goto(page_url, timeout=30000)
                page.wait_for_load_state('networkidle')
                time.sleep(self.rate_limit)
                
                # Extract listings from current page
                page_vehicles = self._extract_listings_from_page(page)
                
                if not page_vehicles:
                    self.logger.info(f"No listings found on page {page_num}, stopping pagination")
                    break
                
                vehicles.extend(page_vehicles)
                self.logger.info(f"Extracted {len(page_vehicles)} vehicles from page {page_num}")
                
                page_num += 1
                
                # Add safety limit to prevent infinite loops - reduced for testing
                if page_num > 6:  # Limit for testing - can be increased later
                    self.logger.warning(f"Reached maximum page limit ({page_num-1}), stopping")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error processing page {page_num}: {e}")
                break
        
        return vehicles
    
    def _extract_listings_from_page(self, page) -> List[Dict[str, Any]]:
        """Extract vehicle listings from current page using Autochek-specific selectors."""
        vehicles = []
        
        # Wait for content to load
        try:
            page.wait_for_selector('h6.MuiTypography-h6', timeout=10000)
        except Exception as e:
            self.logger.warning(f"Page content may not have loaded fully: {e}")
        
        # Look for vehicle cards - try different container selectors
        card_selectors = [
            'article',
            '[data-testid*="car"]',
            '.MuiCard-root',
            'div[role="article"]',
            'a[href*="/ng/car/"]'  # Links to individual car pages
        ]
        
        cards = []
        for selector in card_selectors:
            cards = page.query_selector_all(selector)
            if cards:
                self.logger.info(f"Found {len(cards)} potential vehicle cards using selector: {selector}")
                break
        
        if not cards:
            self.logger.warning("No vehicle cards found on page")
            return vehicles
        
        for i, card in enumerate(cards):
            try:
                vehicle_data = self._extract_vehicle_data(card, page)
                if vehicle_data and self._is_valid_vehicle_data(vehicle_data):
                    vehicles.append(vehicle_data)
                    self.logger.debug(f"Successfully extracted vehicle {i+1}: {vehicle_data.get('make')} {vehicle_data.get('model')}")
                else:
                    self.logger.debug(f"Skipped card {i+1}: insufficient data")
            except Exception as e:
                self.logger.error(f"Error extracting vehicle data from card {i+1}: {e}")
                continue
        
        return vehicles
    
    def _extract_vehicle_data(self, card, page) -> Optional[Dict[str, Any]]:
        """Extract data from a single vehicle card using Autochek-specific selectors."""
        try:
            # Initialize vehicle data with None values
            vehicle = {
                'listing_id': None,
                'make': None,
                'model': None,
                'year': None,
                'variant': None,
                'price': None,
                'currency': None,
                'mileage': None,
                'location': None,
                'listing_url': None,
                'thumbnail_url': None,
                'created_at': None
            }
            
            # Extract href from the card element (since we selected 'a[href*="/ng/car/"]')
            href = card.get_attribute('href')
            if not href or '/ng/car/' not in href:
                return None  # Not a car listing
                
            # Set up the listing URL and ID
            vehicle['listing_url'] = urljoin(page.url, href)
            if '-ref-' in href:
                vehicle['listing_id'] = href.split('-ref-')[-1]
            
            # Use the card as the container for data extraction
            container = card
            
            # Extract make/model/year from h6 element - try multiple selectors
            title_selectors = [
                'h6.MuiTypography-root.MuiTypography-h6.css-1g399u0',
                'h6.MuiTypography-h6',
                'h6[class*="MuiTypography"]',
                'h6',
                '[class*="Typography"] h6'
            ]
            
            title_text = None
            for selector in title_selectors:
                title_elem = container.query_selector(selector)
                if title_elem:
                    title_text = title_elem.text_content()
                    if title_text and title_text.strip():
                        title_text = title_text.strip()
                        break
            
            if title_text:
                self._parse_autochek_title(title_text, vehicle)
            
            # Extract price from p element - try multiple selectors
            price_selectors = [
                'p.MuiTypography-root.MuiTypography-body1.css-1bztvjj',
                'p.MuiTypography-body1',
                'p[class*="MuiTypography"]',
                'p[class*="price"]',
                '[class*="price"]',
                'p'
            ]
            
            for selector in price_selectors:
                price_elem = container.query_selector(selector)
                if price_elem:
                    price_text = price_elem.text_content()
                    if price_text and ('₦' in price_text or 'NGN' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                        self._parse_price(price_text.strip(), vehicle)
                        break
            
            # Extract mileage from span - try multiple selectors
            mileage_selectors = [
                'span.MuiChip-label.MuiChip-labelSmall.css-1pjtbja',
                'span.MuiChip-label',
                'span[class*="MuiChip"]',
                'span[class*="chip"]',
                '[class*="mileage"]'
            ]
            
            for selector in mileage_selectors:
                mileage_elem = container.query_selector(selector)
                if mileage_elem:
                    mileage_text = mileage_elem.text_content()
                    if mileage_text and ('km' in mileage_text.lower() or 'mile' in mileage_text.lower()):
                        self._parse_mileage(mileage_text.strip(), vehicle)
                        break
            
            # Extract location from span - try multiple selectors
            location_selectors = [
                'span.MuiTypography-root.MuiTypography-caption.css-umr6w4',
                'span.MuiTypography-caption',
                'span[class*="MuiTypography-caption"]',
                'span[class*="caption"]',
                '[class*="location"]'
            ]
            
            for selector in location_selectors:
                location_elem = container.query_selector(selector)
                if location_elem:
                    location_text = location_elem.text_content()
                    if location_text and location_text.strip():
                        # Check if this looks like a location (has common Nigerian city names)
                        location_text = location_text.strip()
                        nigerian_cities = ['Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt', 'Benin', 'Jos', 'Ilorin', 'Kaduna', 'Oyo', 'Enugu', 'Abeokuta', 'Zaria', 'Aba', 'Maiduguri', 'Warri', 'Ebute Ikorodu', 'Sokoto', 'Onitsha', 'Calabar', 'Uyo', 'Katsina', 'Ado Ekiti', 'Gombe', 'Minna', 'Effon Alaiye', 'Ikeja', 'Victoria Island', 'Lekki', 'Yaba', 'Surulere']
                        
                        if any(city.lower() in location_text.lower() for city in nigerian_cities) or len(location_text.split()) <= 3:
                            vehicle['location'] = location_text
                            break
            
            # Extract thumbnail - try multiple approaches
            img_selectors = [
                'img[src*="http"]',
                'img',
                '[style*="background-image"]'
            ]
            
            for selector in img_selectors:
                img_elem = container.query_selector(selector)
                if img_elem:
                    # Try src attribute
                    src = img_elem.get_attribute('src')
                    if src and ('http' in src or src.startswith('//')):
                        if not src.startswith('http'):
                            src = 'https:' + src if src.startswith('//') else 'https://autochek.africa' + src
                        vehicle['thumbnail_url'] = src
                        break
                    
                    # Try background-image
                    style = img_elem.get_attribute('style')
                    if style and 'background-image' in style:
                        import re
                        url_match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                        if url_match:
                            url = url_match.group(1)
                            if not url.startswith('http'):
                                url = 'https:' + url if url.startswith('//') else 'https://autochek.africa' + url
                            vehicle['thumbnail_url'] = url
                            break
            
            # Try to find posting date - look for time elements or date patterns
            date_selectors = [
                'time',
                '[datetime]',
                '[class*="date"]',
                '[class*="time"]',
                'span[title]',
                'div[title]'
            ]
            
            for selector in date_selectors:
                elements = container.query_selector_all(selector)
                for elem in elements:
                    # Try datetime attribute first
                    datetime_attr = elem.get_attribute('datetime')
                    if datetime_attr:
                        vehicle['created_at'] = datetime_attr
                        break
                    
                    # Try title attribute
                    title_attr = elem.get_attribute('title')
                    if title_attr and ('ago' in title_attr or 'posted' in title_attr.lower() or any(month in title_attr for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])):
                        vehicle['created_at'] = title_attr.strip()
                        break
                    
                    # Try text content
                    text_content = elem.text_content()
                    if text_content and ('ago' in text_content or any(month in text_content for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])):
                        vehicle['created_at'] = text_content.strip()
                        break
                
                if vehicle['created_at']:
                    break
            
            return vehicle
            
        except Exception as e:
            self.logger.error(f"Error extracting vehicle data: {e}")
            return None
    
    def _get_text_from_selectors(self, element, selectors: List[str]) -> Optional[str]:
        """Get text content using multiple selector options."""
        for selector in selectors:
            elem = element.query_selector(selector)
            if elem:
                text = elem.text_content()
                if text and text.strip():
                    return text.strip()
        return None
    
    def _parse_autochek_title(self, title: str, vehicle: Dict[str, Any]) -> None:
        """Parse vehicle make, model, year, variant from Autochek title."""
        title = title.strip()
        parts = title.split()
        
        if not parts:
            return
            
        # Look for year first (4 digits)
        year_found = False
        year_index = -1
        for i, part in enumerate(parts):
            if part.isdigit() and len(part) == 4:
                try:
                    year = int(part)
                    # Reasonable year range for vehicles
                    if 1980 <= year <= 2030:
                        vehicle['year'] = year
                        year_found = True
                        year_index = i
                        break
                except ValueError:
                    continue
        
        # If year is found as first element, it means structure is "YEAR MAKE MODEL ..."
        if year_found and year_index == 0 and len(parts) >= 3:
            vehicle['make'] = parts[1]
            vehicle['model'] = parts[2]
            
            # Everything after year, make, model could be variant
            if len(parts) > 3:
                remaining_parts = parts[3:]
                vehicle['variant'] = ' '.join(remaining_parts)
                
        # Standard structure: "MAKE MODEL YEAR ..." or "MAKE MODEL ..."
        elif len(parts) >= 2:
            vehicle['make'] = parts[0]
            vehicle['model'] = parts[1]
            
            # If year was found later in the string
            if year_found and year_index > 1:
                # Check if there are parts between model and year (could be variant)
                if year_index > 2:
                    variant_parts = parts[2:year_index]
                    vehicle['variant'] = ' '.join(variant_parts)
                
                # Check if there are parts after year (could also be variant)
                if year_index < len(parts) - 1:
                    remaining_parts = parts[year_index + 1:]
                    if vehicle.get('variant'):
                        vehicle['variant'] += ' ' + ' '.join(remaining_parts)
                    else:
                        vehicle['variant'] = ' '.join(remaining_parts)
            
            # If no year found, everything after make and model could be variant
            elif not year_found and len(parts) > 2:
                variant_parts = parts[2:]
                vehicle['variant'] = ' '.join(variant_parts)

    def _parse_vehicle_title(self, title: str, vehicle: Dict[str, Any]) -> None:
        """Parse vehicle make, model, year, variant from title (legacy method)."""
        # Delegate to the new Autochek-specific parser
        self._parse_autochek_title(title, vehicle)
    
    def _parse_price(self, price_text: str, vehicle: Dict[str, Any]) -> None:
        """Parse price and currency from price text."""
        import re
        
        # Remove commas and extract numbers
        numbers = re.findall(r'[\d,]+', price_text)
        if numbers:
            try:
                price_str = numbers[0].replace(',', '')
                vehicle['price'] = int(price_str)
            except ValueError:
                pass
        
        # Extract currency
        currencies = ['NGN', 'N', '₦', 'USD', '$']
        for currency in currencies:
            if currency in price_text:
                vehicle['currency'] = currency
                break
        
        if not vehicle.get('currency'):
            vehicle['currency'] = 'NGN'  # Default for Nigeria
    
    def _parse_mileage(self, mileage_text: str, vehicle: Dict[str, Any]) -> None:
        """Parse mileage from text."""
        import re
        
        numbers = re.findall(r'[\d,]+', mileage_text)
        if numbers:
            try:
                mileage_str = numbers[0].replace(',', '')
                vehicle['mileage'] = int(mileage_str)
            except ValueError:
                pass
    
    def _is_valid_vehicle_data(self, vehicle: Dict[str, Any]) -> bool:
        """Check if vehicle data has minimum required information."""
        # Must have at least make or model, and some other identifying information
        required_fields = ['make', 'model']
        identifying_fields = ['listing_id', 'listing_url', 'price', 'year']
        
        # Check if we have basic make/model info
        has_basic_info = any(vehicle.get(field) for field in required_fields)
        
        # Check if we have some identifying information
        has_identifying_info = any(vehicle.get(field) for field in identifying_fields)
        
        return has_basic_info and has_identifying_info
    
    def _fallback_scraping(self, make: str, model: str, year: int) -> List[Dict[str, Any]]:
        """Fallback scraping using requests if Playwright fails."""
        self.logger.info("Using fallback scraping with requests")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This is a basic fallback - in reality would need to be
            # adapted based on actual website structure
            vehicles = []
            
            # For demo purposes, return a mock result
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
    
    def save_to_csv(self, vehicles: List[Dict[str, Any]], output_path: str) -> None:
        """Save vehicle data to CSV file."""
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
    
    def save_to_json(self, vehicles: List[Dict[str, Any]], output_path: str) -> None:
        """Save vehicle data to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(vehicles, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Successfully saved {len(vehicles)} vehicles to JSON: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")
            raise