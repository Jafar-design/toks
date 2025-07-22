#!/usr/bin/env python3
"""
Unit tests for Autochek Africa Vehicle Scraper
"""

import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from autochek_scraper.scraper import AutochekScraper
from autochek_scraper.cli import main, parse_arguments


class TestAutochekScraper:
    """Test class for AutochekScraper functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.scraper = AutochekScraper(rate_limit=0.1, headless=True)
    
    def test_scraper_initialization(self):
        """Test scraper initializes correctly."""
        assert self.scraper.rate_limit == 0.1
        assert self.scraper.headless == True
        assert self.scraper.base_url == "https://autochek.africa"
        assert self.scraper.session is not None
    
    def test_parse_vehicle_title(self):
        """Test vehicle title parsing."""
        vehicle = {}
        
        # Test basic title parsing
        self.scraper._parse_vehicle_title("Toyota Corolla 2015 LE", vehicle)
        assert vehicle['make'] == 'Toyota'
        assert vehicle['model'] == 'Corolla'
        assert vehicle['year'] == 2015
        assert vehicle['variant'] == 'LE'
        
        # Test without variant
        vehicle = {}
        self.scraper._parse_vehicle_title("Honda Civic 2018", vehicle)
        assert vehicle['make'] == 'Honda'
        assert vehicle['model'] == 'Civic'
        assert vehicle['year'] == 2018
    
    def test_parse_price(self):
        """Test price parsing functionality."""
        vehicle = {}
        
        # Test NGN price
        self.scraper._parse_price("NGN 5,500,000", vehicle)
        assert vehicle['price'] == 5500000
        assert vehicle['currency'] == 'NGN'
        
        # Test USD price
        vehicle = {}
        self.scraper._parse_price("$12,000", vehicle)
        assert vehicle['price'] == 12000
        assert vehicle['currency'] == '$'
        
        # Test price without currency (should default to NGN)
        vehicle = {}
        self.scraper._parse_price("3,200,000", vehicle)
        assert vehicle['price'] == 3200000
        assert vehicle['currency'] == 'NGN'
    
    def test_parse_mileage(self):
        """Test mileage parsing functionality."""
        vehicle = {}
        
        # Test basic mileage
        self.scraper._parse_mileage("85,000 km", vehicle)
        assert vehicle['mileage'] == 85000
        
        # Test mileage without comma
        vehicle = {}
        self.scraper._parse_mileage("45000 km", vehicle)
        assert vehicle['mileage'] == 45000
    
    @patch('autochek_scraper.scraper.sync_playwright')
    def test_search_vehicles_with_mock_data(self, mock_playwright):
        """Test search_vehicles method returns at least one listing for known make/model/year."""
        # Mock playwright context
        mock_p = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_playwright.return_value.__enter__.return_value = mock_p
        mock_p.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        # Mock page navigation
        mock_page.goto.return_value = None
        mock_page.url = "https://autochek.africa/cars"
        
        # Mock vehicle card elements
        mock_card = MagicMock()
        mock_page.query_selector_all.return_value = [mock_card]
        
        # Mock link extraction
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "/cars/test-123"
        mock_card.query_selector.return_value = mock_link
        
        # Mock text content
        mock_title = MagicMock()
        mock_title.text_content.return_value = "Toyota Corolla 2015 LE"
        
        mock_price = MagicMock()
        mock_price.text_content.return_value = "NGN 5,500,000"
        
        mock_mileage = MagicMock()
        mock_mileage.text_content.return_value = "85,000 km"
        
        mock_location = MagicMock()
        mock_location.text_content.return_value = "Lagos"
        
        # Configure query_selector to return appropriate mocks
        def query_selector_side_effect(selector):
            if 'a[href]' in selector:
                return mock_link
            elif any(s in selector for s in ['.title', '.name', 'h2', 'h3']):
                return mock_title
            elif '.price' in selector:
                return mock_price
            elif '.mileage' in selector:
                return mock_mileage
            elif '.location' in selector:
                return mock_location
            elif 'img' in selector:
                mock_img = MagicMock()
                mock_img.get_attribute.return_value = "/images/test-123.jpg"
                return mock_img
            return None
        
        mock_card.query_selector.side_effect = query_selector_side_effect
        
        # Mock next page (no next page available)
        def next_page_query(selector):
            return None
        
        mock_page.query_selector.side_effect = next_page_query
        
        # Run the search
        vehicles = self.scraper.search_vehicles("Toyota", "Corolla", 2015)
        
        # Assertions
        assert len(vehicles) >= 1, "Should return at least one vehicle"
        
        if vehicles:
            vehicle = vehicles[0]
            assert vehicle['make'] == 'Toyota'
            assert vehicle['model'] == 'Corolla'
            assert vehicle['year'] == 2015
            assert vehicle['price'] is not None
            assert vehicle['listing_url'] is not None
    
    @patch('autochek_scraper.scraper.sync_playwright')
    def test_fallback_scraping(self, mock_playwright):
        """Test fallback scraping when Playwright fails."""
        # Mock playwright to raise an exception
        mock_playwright.side_effect = Exception("Playwright failed")
        
        with patch.object(self.scraper, '_fallback_scraping') as mock_fallback:
            mock_fallback.return_value = [{
                'listing_id': 'fallback-001',
                'make': 'Toyota',
                'model': 'Corolla',
                'year': 2015,
                'variant': 'LE',
                'price': 5500000,
                'currency': 'NGN',
                'mileage': 85000,
                'location': 'Lagos',
                'listing_url': 'https://autochek.africa/cars/fallback-001',
                'thumbnail_url': 'https://autochek.africa/images/fallback-001.jpg',
                'created_at': '2024-01-15'
            }]
            
            vehicles = self.scraper.search_vehicles("Toyota", "Corolla", 2015)
            
            assert len(vehicles) == 1
            assert vehicles[0]['make'] == 'Toyota'
            assert vehicles[0]['model'] == 'Corolla'
            assert vehicles[0]['year'] == 2015
            mock_fallback.assert_called_once_with("Toyota", "Corolla", 2015)
    
    def test_get_text_from_selectors(self):
        """Test text extraction from multiple selectors."""
        # Mock element
        mock_element = MagicMock()
        
        # Mock successful selector
        mock_text_elem = MagicMock()
        mock_text_elem.text_content.return_value = "Test Text"
        
        def query_selector_side_effect(selector):
            if selector == '.found':
                return mock_text_elem
            return None
        
        mock_element.query_selector.side_effect = query_selector_side_effect
        
        # Test successful extraction
        result = self.scraper._get_text_from_selectors(mock_element, ['.notfound', '.found'])
        assert result == "Test Text"
        
        # Test no match
        result = self.scraper._get_text_from_selectors(mock_element, ['.notfound1', '.notfound2'])
        assert result is None


class TestCLI:
    """Test class for CLI functionality."""
    
    def test_argument_parsing(self):
        """Test command line argument parsing."""
        # Mock sys.argv for testing
        test_args = [
            '--make', 'Toyota',
            '--model', 'Corolla', 
            '--year', '2015',
            '--out', 'test_output.json'
        ]
        
        with patch('sys.argv', ['prog'] + test_args):
            args = parse_arguments()
            
            assert args.make == 'Toyota'
            assert args.model == 'Corolla'
            assert args.year == 2015
            assert args.out == 'test_output.json'
            assert args.headless == True
            assert args.rate_limit == 1.0


def test_main_function():
    """Test main function argument parsing and execution."""
    import sys
    from unittest.mock import patch
    
    # Mock command line arguments
    test_args = [
        'scrape_autochek.py',
        '--make', 'Toyota',
        '--model', 'Corolla', 
        '--year', '2015',
        '--out', 'test_output.json'
    ]
    
    with patch.object(sys, 'argv', test_args):
        with patch('autochek_scraper.cli.AutochekScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper.search_vehicles.return_value = [{
                'listing_id': 'test-001',
                'make': 'Toyota',
                'model': 'Corolla',
                'year': 2015,
                'price': 5500000,
                'currency': 'NGN'
            }]
            mock_scraper.save_to_json.return_value = None
            mock_scraper_class.return_value = mock_scraper
            
            result = main()
            
            assert result == 0
            mock_scraper.search_vehicles.assert_called_once_with('Toyota', 'Corolla', 2015)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])