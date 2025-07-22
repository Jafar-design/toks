#!/usr/bin/env python3
"""
Test script to generate CSV output using mock data
"""

import json
from scrape_autochek import AutochekScraper

def test_csv_generation():
    """Test CSV generation with mock data."""
    scraper = AutochekScraper()
    
    # Create mock vehicle data
    vehicles = [
        {
            'listing_id': 'test-001',
            'make': 'Toyota',
            'model': 'Corolla',
            'year': 2015,
            'variant': 'LE',
            'price': 5500000,
            'currency': 'NGN',
            'mileage': 85000,
            'location': 'Lagos',
            'listing_url': 'https://autochek.africa/cars/test-001',
            'thumbnail_url': 'https://autochek.africa/images/test-001.jpg',
            'created_at': '2024-01-15T10:30:00Z'
        },
        {
            'listing_id': 'test-002',
            'make': 'Toyota',
            'model': 'Corolla',
            'year': 2015,
            'variant': 'S',
            'price': 4800000,
            'currency': 'NGN',
            'mileage': 125000,
            'location': 'Abuja',
            'listing_url': 'https://autochek.africa/cars/test-002',
            'thumbnail_url': 'https://autochek.africa/images/test-002.jpg',
            'created_at': '2024-01-12T14:20:00Z'
        }
    ]
    
    # Test CSV export
    csv_file = 'test_automated.csv'
    scraper.save_to_csv(vehicles, csv_file)
    print(f"Generated CSV file: {csv_file}")
    
    # Test JSON export
    json_file = 'test_automated.json'
    scraper.save_to_json(vehicles, json_file)
    print(f"Generated JSON file: {json_file}")
    
    # Verify files were created
    import os
    if os.path.exists(csv_file):
        print(f"✓ CSV file created successfully")
        with open(csv_file, 'r') as f:
            print("CSV content preview:")
            for i, line in enumerate(f):
                print(f"  {line.strip()}")
                if i >= 2:  # Show first 3 lines
                    break
    
    if os.path.exists(json_file):
        print(f"✓ JSON file created successfully")
        with open(json_file, 'r') as f:
            data = json.load(f)
            print(f"JSON contains {len(data)} vehicles")

if __name__ == '__main__':
    test_csv_generation()