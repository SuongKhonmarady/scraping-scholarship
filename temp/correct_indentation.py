"""
Temporary file for scrape_scholarships_corner.py with proper indentation
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv
import os
from urllib.parse import urljoin

def scrape_scholarships_corner(url, region_name, driver=None):
    """Scrape scholarships from ScholarshipsCorner.website."""
    print(f"\n=== Scraping {region_name} scholarships from ScholarshipsCorner ===")
    
    # Setup CSV
    csv_filename = f"scholarships-{region_name.lower().replace(' ', '-')}.csv"
    
    # Check if file already exists and handle accordingly
    if os.path.exists(csv_filename):
        print(f"File {csv_filename} already exists. Creating with unique name...")
        base_name = os.path.splitext(csv_filename)[0]
        timestamp = int(time.time())
        csv_filename = f"{base_name}-{timestamp}.csv"
        
    # Create the CSV file
    try:
        csv_file = open(csv_filename, mode="w", newline="", encoding="utf-8")
        csv_writer = csv.DictWriter(csv_file, fieldnames=[
            "Title", "Description", "Link", "Official Link", "Image", "Deadline", "Eligibility",
            "Host Country", "Host University", "Program Duration", "Degree Offered", "Region", "Post_at"
        ])
        csv_writer.writeheader()
    except Exception as e:
        print(f"Error creating CSV file {csv_filename}: {str(e)}")
        # If we can't create the file, return None to signal failure
        return None
    
    # If no driver is provided, create one
    local_driver = False
    if driver is None:
        local_driver = True
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        # Process each scholarship post
        for index, link in enumerate(post_links):
            try:
                # Process the scholarship post
                # ...existing code...
                
                # Save
                csv_writer.writerow({
                    "Title": title,
                    "Description": description,
                    "Link": link,
                    "Official Link": official_link,
                    "Image": image_url,
                    "Deadline": deadline,
                    "Eligibility": eligibility,
                    "Host Country": host_country,
                    "Host University": host_university,
                    "Program Duration": program_duration,
                    "Degree Offered": degree_offered,
                    "Region": region_name,
                    "Post_at": post_at
                })
                
                print(f"✅ {region_name} - Saved {index+1}/{len(post_links)}: {title[:50]}...")
            
            except Exception as e:
                print(f"❌ Error processing post {index+1} in {region_name} region: {str(e)}")
                # Log the error for debugging
                with open(f"error_log_{region_name}.txt", "a", encoding="utf-8") as error_log:
                    error_log.write(f"Error on {link}: {str(e)}\n")
                continue
        
        # Return the filename after all processing
        return csv_filename
    
    except Exception as e:
        print(f"Unexpected error in scrape_scholarships_corner: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Make sure to close the file safely
        if 'csv_file' in locals() and csv_file and not csv_file.closed:
            csv_file.close()
            print(f"Closed CSV file: {csv_filename}")
        
        # Close the driver if we created it locally
        if local_driver and driver:
            driver.quit()
