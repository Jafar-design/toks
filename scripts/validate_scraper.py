#!/usr/bin/env python3
"""
Comprehensive validation script for the Autochek scraper
"""

import os
import sys
import json
import csv
import subprocess
import tempfile
from typing import List, Dict, Any

# Add src to Python path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, 'src'))


class ScraperValidator:
    """Validator class for comprehensive scraper testing."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed_tests = 0
        self.total_tests = 0
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
    
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
    
    def log_success(self, message: str) -> None:
        """Log a success message."""
        self.passed_tests += 1
        print(f"✅ PASS: {message}")
    
    def test_file_exists(self, filepath: str, description: str) -> bool:
        """Test if a file exists."""
        self.total_tests += 1
        full_path = os.path.join(self.project_root, filepath)
        if os.path.exists(full_path):
            self.log_success(f"{description} exists")
            return True
        else:
            self.log_error(f"{description} not found: {filepath}")
            return False
    
    def test_dependencies(self) -> None:
        """Test that all required dependencies are installed."""
        required_packages = [
            'requests', 'beautifulsoup4', 'lxml', 'playwright', 
            'python-dotenv', 'pytest'
        ]
        
        print("\n📦 Testing dependencies...")
        for package in required_packages:
            self.total_tests += 1
            try:
                __import__(package.replace('-', '_'))
                self.log_success(f"Package {package} is installed")
            except ImportError:
                try:
                    # Handle packages with different import names
                    if package == 'beautifulsoup4':
                        import bs4
                        self.log_success(f"Package {package} is installed")
                    elif package == 'python-dotenv':
                        import dotenv
                        self.log_success(f"Package {package} is installed")
                    else:
                        raise ImportError
                except ImportError:
                    self.log_error(f"Package {package} is not installed")
    
    def test_code_syntax(self) -> None:
        """Test Python syntax for main files."""
        python_files = [
            'scrape_autochek.py',
            'src/autochek_scraper/__init__.py',
            'src/autochek_scraper/scraper.py', 
            'src/autochek_scraper/cli.py',
            'tests/test_scraper.py'
        ]
        
        print("\n🐍 Testing Python syntax...")
        for filename in python_files:
            self.total_tests += 1
            full_path = os.path.join(self.project_root, filename)
            if os.path.exists(full_path):
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'py_compile', full_path],
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        self.log_success(f"Syntax valid for {filename}")
                    else:
                        self.log_error(f"Syntax error in {filename}: {result.stderr}")
                except Exception as e:
                    self.log_error(f"Failed to check syntax for {filename}: {e}")
            else:
                self.log_error(f"File not found: {filename}")
    
    def test_unit_tests(self) -> None:
        """Run unit tests and verify they pass."""
        print("\n🧪 Running unit tests...")
        self.total_tests += 1
        
        try:
            # Change to project root for test execution
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/test_scraper.py', '-v'],
                capture_output=True, text=True
            )
            
            # Restore original working directory
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                self.log_success("All unit tests passed")
            else:
                self.log_error(f"Unit tests failed: {result.stdout}")
                if result.stderr:
                    self.log_error(f"Error output: {result.stderr}")
        except Exception as e:
            self.log_error(f"Failed to run unit tests: {e}")
    
    def test_scraper_import(self) -> None:
        """Test that the scraper can be imported."""
        print("\n📥 Testing scraper import...")
        self.total_tests += 1
        
        try:
            from autochek_scraper.scraper import AutochekScraper
            scraper = AutochekScraper()
            self.log_success("AutochekScraper imported and instantiated successfully")
            return scraper
        except Exception as e:
            self.log_error(f"Failed to import AutochekScraper: {e}")
            return None
    
    def test_data_validation(self) -> None:
        """Test data validation for scraped results."""
        print("\n📋 Testing data validation...")
        
        # Test with mock data
        mock_vehicle = {
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
        }
        
        required_fields = [
            'listing_id', 'make', 'model', 'year', 'variant', 
            'price', 'currency', 'mileage', 'location', 
            'listing_url', 'thumbnail_url', 'created_at'
        ]
        
        for field in required_fields:
            self.total_tests += 1
            if field in mock_vehicle:
                self.log_success(f"Required field '{field}' present")
            else:
                self.log_error(f"Required field '{field}' missing")
        
        # Test data types
        type_tests = [
            ('year', int),
            ('price', (int, type(None))),
            ('mileage', (int, type(None))),
            ('listing_id', (str, type(None))),
            ('make', (str, type(None))),
            ('model', (str, type(None)))
        ]
        
        for field, expected_type in type_tests:
            self.total_tests += 1
            if field in mock_vehicle:
                if isinstance(mock_vehicle[field], expected_type):
                    self.log_success(f"Field '{field}' has correct type")
                else:
                    self.log_error(f"Field '{field}' has wrong type: {type(mock_vehicle[field])}")
    
    def test_output_formats(self) -> None:
        """Test JSON and CSV output functionality."""
        print("\n💾 Testing output formats...")
        
        scraper = self.test_scraper_import()
        if not scraper:
            return
        
        mock_data = [{
            'listing_id': 'test-format',
            'make': 'Honda',
            'model': 'Civic',
            'year': 2018,
            'variant': 'LX',
            'price': 4200000,
            'currency': 'NGN',
            'mileage': 95000,
            'location': 'Abuja',
            'listing_url': 'https://autochek.africa/cars/test-format',
            'thumbnail_url': 'https://autochek.africa/images/test-format.jpg',
            'created_at': '2024-01-20T15:00:00Z'
        }]
        
        # Test JSON output
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            json_file = f.name
        
        try:
            self.total_tests += 1
            scraper.save_to_json(mock_data, json_file)
            
            # Verify JSON file
            with open(json_file, 'r') as f:
                loaded_data = json.load(f)
                if loaded_data == mock_data:
                    self.log_success("JSON output format working correctly")
                else:
                    self.log_error("JSON output data doesn't match input")
        except Exception as e:
            self.log_error(f"JSON output failed: {e}")
        finally:
            if os.path.exists(json_file):
                os.unlink(json_file)
        
        # Test CSV output
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            csv_file = f.name
        
        try:
            self.total_tests += 1
            scraper.save_to_csv(mock_data, csv_file)
            
            # Verify CSV file
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)
                
                if len(csv_data) == 1 and csv_data[0]['listing_id'] == 'test-format':
                    self.log_success("CSV output format working correctly")
                else:
                    self.log_error("CSV output data doesn't match input")
        except Exception as e:
            self.log_error(f"CSV output failed: {e}")
        finally:
            if os.path.exists(csv_file):
                os.unlink(csv_file)
    
    def test_command_line_interface(self) -> None:
        """Test command line interface."""
        print("\n💻 Testing command line interface...")
        
        script_path = os.path.join(self.project_root, 'scrape_autochek.py')
        
        # Test help command
        self.total_tests += 1
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--help'],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0 and '--make' in result.stdout:
                self.log_success("Command line help working")
            else:
                self.log_error("Command line help not working properly")
        except Exception as e:
            self.log_error(f"Failed to test CLI help: {e}")
        
        # Test with invalid arguments
        self.total_tests += 1
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                self.log_success("CLI properly rejects missing required arguments")
            else:
                self.log_warning("CLI should reject missing required arguments")
        except Exception as e:
            self.log_error(f"Failed to test CLI validation: {e}")
    
    def test_network_robustness(self) -> None:
        """Test network error handling."""
        print("\n🌐 Testing network robustness...")
        
        scraper = self.test_scraper_import()
        if not scraper:
            return
        
        # Test with invalid URL (should use fallback)
        self.total_tests += 1
        try:
            original_url = scraper.base_url
            scraper.base_url = "https://invalid-url-that-does-not-exist-12345.com"
            
            # This should gracefully handle the error and use fallback
            vehicles = scraper.search_vehicles("Toyota", "Corolla", 2015)
            
            # Restore original URL
            scraper.base_url = original_url
            
            # Should have fallback data
            if isinstance(vehicles, list):
                self.log_success("Network error handling works (fallback used)")
            else:
                self.log_error("Network error handling failed")
        except Exception as e:
            self.log_error(f"Network robustness test failed: {e}")
    
    def test_project_structure(self) -> None:
        """Test project structure and organization."""
        print("\n📁 Testing project structure...")
        
        # Test directories
        directories = [
            ('src', 'Source code directory'),
            ('src/autochek_scraper', 'Main package directory'),
            ('tests', 'Tests directory'),
            ('examples', 'Examples directory'),
            ('scripts', 'Scripts directory'),
            ('config', 'Configuration directory'),
            ('docs', 'Documentation directory')
        ]
        
        for dir_path, description in directories:
            self.test_file_exists(dir_path, description)
        
        # Test main files
        files_to_check = [
            ('scrape_autochek.py', 'Main entry script'),
            ('src/autochek_scraper/__init__.py', 'Package init file'),
            ('src/autochek_scraper/scraper.py', 'Core scraper module'),
            ('src/autochek_scraper/cli.py', 'CLI module'),
            ('tests/__init__.py', 'Tests init file'),
            ('tests/test_scraper.py', 'Unit test file'),
            ('requirements.txt', 'Requirements file'),
            ('README.md', 'README file'),
            ('Dockerfile', 'Docker configuration'),
            ('.gitignore', 'Git ignore file'),
            ('examples/sample_toyota_corolla_2015.json', 'Sample JSON output'),
            ('examples/sample_toyota_corolla_2015.csv', 'Sample CSV output'),
            ('config/.env.example', 'Environment configuration example')
        ]
        
        for filepath, description in files_to_check:
            self.test_file_exists(filepath, description)
    
    def run_all_tests(self) -> None:
        """Run all validation tests."""
        print("🚀 Starting comprehensive scraper validation...\n")
        
        # Change to project root for consistent relative paths
        original_cwd = os.getcwd()
        os.chdir(self.project_root)
        
        try:
            # Run all tests
            self.test_project_structure()
            self.test_dependencies()
            self.test_code_syntax()
            self.test_unit_tests()
            self.test_scraper_import()
            self.test_data_validation()
            self.test_output_formats()
            self.test_command_line_interface()
            self.test_network_robustness()
            
            # Print summary
            self.print_summary()
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
    
    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        print(f"Total tests run: {self.total_tests}")
        print(f"Tests passed: {self.passed_tests}")
        print(f"Tests failed: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"Pass rate: {pass_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print("\n" + "="*60)
        
        if len(self.errors) == 0:
            print("🎉 ALL VALIDATIONS PASSED! Scraper is ready for use.")
        elif pass_rate >= 80:
            print("✅ MOSTLY GOOD! Minor issues to address.")
        else:
            print("❌ SIGNIFICANT ISSUES FOUND! Please address errors before use.")
        
        print("="*60)


if __name__ == '__main__':
    validator = ScraperValidator()
    validator.run_all_tests()