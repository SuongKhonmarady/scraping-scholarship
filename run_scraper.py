#!/usr/bin/env python
"""
Run script for the scholarship scraper
This provides a clean entry point to run the scraper
"""
import os
import sys
import argparse

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import the actual main function
from main.scrap_main import main

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scholarship scraping tool")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be scraped without actually scraping")
    args = parser.parse_args()

    # Run the main function with the appropriate arguments
    print(f"Starting scholarship scraper (dry run: {args.dry_run})")
    try:
        main(dry_run=args.dry_run)
        print("Scraping completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
