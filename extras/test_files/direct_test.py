"""
Simple test script to directly invoke the main function
"""
import sys
import os

# Add the current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

print(f"Current directory: {current_dir}")
print(f"Path: {sys.path}")

# Import the main.scrap_main module directly
sys.path.append(os.path.join(current_dir, "main"))
from main.scrap_main import main

# Run with dry_run=True
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test script for scholarship scraper")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry run mode", default=True)
    args = parser.parse_args()
    
    try:
        print("Running main with dry_run=True...")
        main(dry_run=args.dry_run)
        print("Done!")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
