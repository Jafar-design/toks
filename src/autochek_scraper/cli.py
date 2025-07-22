"""
Command-line interface for the Autochek Africa vehicle scraper.
"""

import argparse
import logging
import sys
from .scraper import AutochekScraper


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Scrape vehicle listings from Autochek Africa',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # JSON output
  %(prog)s --make "Toyota" --model "Corolla" --year 2015 --out results.json
  
  # CSV output
  %(prog)s --make "Toyota" --model "Corolla" --year 2015 --out results.csv
  
  # Both formats
  %(prog)s --make "Honda" --model "Civic" --year 2018 --out results.json --csv results.csv
        """
    )
    
    # Required arguments
    parser.add_argument('--make', required=True, 
                       help='Vehicle make (e.g., Toyota)')
    parser.add_argument('--model', required=True, 
                       help='Vehicle model (e.g., Corolla)')
    parser.add_argument('--year', required=True, type=int, 
                       help='Vehicle year (e.g., 2015)')
    parser.add_argument('--out', required=True, 
                       help='Output file path (.json or .csv)')
    
    # Optional arguments
    parser.add_argument('--csv', 
                       help='Output CSV file path (alternative to --out)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: true)')
    parser.add_argument('--no-headless', action='store_false', dest='headless',
                       help='Run browser with GUI visible')
    parser.add_argument('--rate-limit', type=float, default=1.0,
                       help='Rate limit between requests in seconds (default: 1.0)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level (default: INFO)')
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for the scraper."""
    try:
        args = parse_arguments()
        
        # Setup logging
        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting Autochek scraper for {args.make} {args.model} {args.year}")
        
        # Initialize scraper
        scraper = AutochekScraper(rate_limit=args.rate_limit, headless=args.headless)
        
        # Perform search
        vehicles = scraper.search_vehicles(args.make, args.model, args.year)
        
        if not vehicles:
            logger.warning("No vehicles found matching the criteria")
        
        # Save results
        saved_files = []
        
        # Determine output format from file extension or --csv flag
        if args.csv:
            scraper.save_to_csv(vehicles, args.csv)
            saved_files.append(f"CSV: {args.csv}")
            
        if args.out.lower().endswith('.csv'):
            scraper.save_to_csv(vehicles, args.out)
            saved_files.append(f"CSV: {args.out}")
        else:
            scraper.save_to_json(vehicles, args.out)
            saved_files.append(f"JSON: {args.out}")
        
        # Print summary
        print(f"\n✅ Successfully scraped {len(vehicles)} vehicles")
        for file_info in saved_files:
            print(f"📁 Results saved to {file_info}")
        
        if vehicles:
            print(f"\n📋 Sample result:")
            sample = vehicles[0]
            for key, value in list(sample.items())[:5]:  # Show first 5 fields
                print(f"  {key}: {value}")
            if len(sample) > 5:
                print("  ...")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        return 130
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.getLogger(__name__).error(f"Unhandled error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())