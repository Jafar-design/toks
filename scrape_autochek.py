#!/usr/bin/env python3
"""
Entry point script for the Autochek Africa vehicle scraper.

This script provides a command-line interface for scraping vehicle
listings from Autochek Africa based on make, model, and year.
"""

import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autochek_scraper.cli import main

if __name__ == '__main__':
    sys.exit(main())