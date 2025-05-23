#!/usr/bin/env python
"""
Test script to verify proper integration of all components
"""
import os
import sys
import traceback

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import components
try:    # Import modules directly
    import main.scrap_main
    
    # Import the scrapers
    from scrapers import scrape_scholarships_corner, scrape_opportunities_corners
    
    # Import duplicate checker
    from duplicate_utils import DuplicateChecker
    
    print("\n✅ All modules imported successfully")
      # Create a mock webdriver for testing
    class MockDriver:
        def __init__(self, service=None, options=None):
            self.current_url = ""
            print("  Mock Chrome driver initialized")
            
        def get(self, url):
            print(f"  Mock driver navigating to: {url}")
            self.current_url = url
            
        def quit(self):
            print("  Mock driver closed")
    
    # Create a mock scraper function for testing
    def mock_scrape_function(url, region_name, driver):
        print(f"  Mock scraping {region_name} from {url}")
        # Create a temporary CSV file for testing
        file_path = f"scholarships-{region_name.lower()}.csv"
        with open(file_path, 'w') as f:
            f.write("Title,Link,Description,Deadline,Host Country,Host University,Program Duration\n")
            f.write(f"Test Scholarship {region_name},http://example.com,Test description,2025-12-31,Test Country,Test University,1 year\n")
        return file_path
    
    # Patch the scraper functions
    import main.scrap_main
    main.scrap_main.scrape_scholarships_corner = mock_scrape_function
    main.scrap_main.scrape_opportunities_corners = mock_scrape_function
    
    # Patch the webdriver
    from unittest.mock import patch
    import selenium.webdriver
    selenium.webdriver.Chrome = MockDriver
      # Run the main function with dry_run=True
    print("\n🧪 Running main function with dry_run=True")
    main.scrap_main.main(dry_run=True)
    
    print("\n✅ Test completed successfully!")
    
except Exception as e:
    print(f"\n❌ Test failed: {str(e)}")
    traceback.print_exc()
