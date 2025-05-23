"""
Test script for OpportunitiesCorners extraction functions
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import extraction functions from the opportunities corners script
from scrape_opportunitiescorners import (
    extract_deadline_opportunities_corners,
    extract_description_opportunities_corners,
    extract_host_country_opportunities_corners,
    extract_host_university_opportunities_corners,
    extract_program_duration_opportunities_corners,
    extract_degree_offered_opportunities_corners
)

def test_extraction_functions(url):
    """Test all extraction functions on a specific URL"""
    print(f"\nTesting URL: {url}")
    
    # Setup browser
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Uncomment for headless operation
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # Load page
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Get title
        title_element = soup.find("h1", class_="entry-title") or soup.find("h1", class_="post-title") or soup.find("h1")
        if not title_element:
            print("Could not find title element")
            return
        
        title = title_element.text.strip()
        print(f"Title: {title}")
        
        # Get content
        content_div = soup.find("div", class_="entry-content") or soup.find("div", class_="post-content")
        if not content_div:
            content_div = soup.find("article") or soup.find("div", class_="post")
        
        if not content_div:
            print("Could not find content div")
            return
        
        # Test each extraction function
        print("\n=== EXTRACTION RESULTS ===")
        
        deadline = extract_deadline_opportunities_corners(content_div, soup, title)
        print(f"Deadline: {deadline}")
        
        description = extract_description_opportunities_corners(content_div)
        print(f"Description: {description[:100]}..." if len(description) > 100 else description)
        
        host_country = extract_host_country_opportunities_corners(content_div, title)
        print(f"Host Country: {host_country}")
        
        host_university = extract_host_university_opportunities_corners(content_div, title)
        print(f"Host University: {host_university}")
        
        program_duration = extract_program_duration_opportunities_corners(content_div)
        print(f"Program Duration: {program_duration}")
        
        degree_offered = extract_degree_offered_opportunities_corners(content_div, title)
        print(f"Degree Offered: {degree_offered}")
        
        print("\n=== TEST COMPLETE ===")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test URLs
    test_urls = [
        "https://opportunitiescorners.com/malta-endeavour-scholarship/",
        "https://opportunitiescorners.com/leipzig-university-daad-epos-sept-scholarship/",
        "https://opportunitiescorners.com/eric-bleumink-fellowship/"
    ]
    
    # Run tests
    for url in test_urls:
        test_extraction_functions(url)
        print("\n" + "=" * 50)
