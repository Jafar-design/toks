"""
Autochek Africa Vehicle Scraper

A proof-of-concept scraper for gathering vehicle advertisements
from Autochek Africa for specific make, model, and year combinations.
"""

from .scraper import AutochekScraper
from .cli import main

__version__ = "1.0.0"
__author__ = "Tokunbo.io Engineering"

__all__ = ["AutochekScraper", "main"]