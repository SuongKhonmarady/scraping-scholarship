"""
Specialized scraper for ScholarshipsCorner.website
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

def extract_section(soup, keywords):
    """Extract text that comes after a heading containing any of the keywords."""
    for tag in soup.find_all(["h2", "h3", "strong", "b"]):
        if any(word in tag.get_text(strip=True).lower() for word in keywords):
            content = []
            next_tag = tag.find_next_sibling()
            while next_tag and next_tag.name in ["p", "ul"]:
                content.append(next_tag.get_text(strip=True))
                next_tag = next_tag.find_next_sibling()
            return "\n".join(content)
    return ""

def extract_description(content_div):
    """Extracts main description before any of the key headings."""
    description = []
    for tag in content_div.find_all(recursive=False):
        if tag.name in ["h2", "h3", "strong", "b"]:
            break  # Stop at the first heading
        if tag.name in ["p", "ul"]:
            description.append(tag.get_text(strip=True))
    return "\n".join(description)

def scrape_scholarships_corner(url, region_name, driver=None):
    """Scrape scholarships from ScholarshipsCorner.website."""
    print(f"\n=== Scraping {region_name} scholarships from ScholarshipsCorner ===")
    
    # Setup CSV
    csv_filename = f"scholarships-{region_name.lower().replace(' ', '-')}.csv"
    csv_file = open(csv_filename, mode="w", newline="", encoding="utf-8")
    csv_writer = csv.DictWriter(csv_file, fieldnames=[
        "Title", "Description", "Link", "Official Link", "Image", "Deadline", "Eligibility",
        "Host Country", "Host University", "Program Duration", "Degree Offered", "Region", "Post_at"
    ])
    csv_writer.writeheader()
    
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
        # Load page
        driver.get(url)
        time.sleep(5)  # Increased wait time for page loading
        
        # Get links from the page
        elements = driver.find_elements(By.CSS_SELECTOR, "h2.entry-title a")
        post_links = [elem.get_attribute("href") for elem in elements]
        
        # Remove duplicate links
        post_links = list(dict.fromkeys(post_links))
        print(f"Found {len(post_links)} posts in {region_name} from ScholarshipsCorner website.")
        
        # Loop through each post
        for index, link in enumerate(post_links):
            try:
                driver.get(link)
                time.sleep(3)  # Increased wait time
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # Title
                title_element = soup.find("h1", class_="entry-title")
                if not title_element:
                    # Try generic h1 as fallback
                    title_element = soup.find("h1")
                    if not title_element:
                        print(f"⚠️ No title found for post {index+1}. Skipping...")
                        continue
                    
                title = title_element.text.strip()
                
                # Content area
                content_div = soup.find("div", class_="entry-content")
                if not content_div:
                    # Try article content as fallback
                    content_div = soup.find("article") or soup.find("div", class_="post")
                    if not content_div:
                        print(f"⚠️ No content found for post: {title}. Skipping...")
                        continue
                
                # Official Link
                official_link = ""
                for a in content_div.find_all("a"):
                    if not a.text:
                        continue
                    if "official" in a.text.lower() or "apply" in a.text.lower():
                        official_link = a.get("href")
                        break
                
                # Extract sections using standard methods for ScholarshipsCorner
                deadline = extract_section(content_div, ["deadline", "last date", "closing date"])
                description = extract_description(content_div)
                eligibility = extract_section(content_div, ["eligibility", "who can apply", "eligible"])
                host_country = extract_section(content_div, ["host country", "study in", "country"])
                host_university = extract_section(content_div, ["host university", "offered by", "university"])
                program_duration = extract_section(content_div, ["program duration", "duration"])
                degree_offered = extract_section(content_div, ["degree", "degree offered", "field of study", "what you will study"])
                
                # Extract post date
                post_at = ""
                post_at_element = (
                    soup.select_one(".entry-date.published") or 
                    soup.select_one(".post-date") or 
                    soup.select_one(".date") or
                    soup.select_one("time")
                )
                if post_at_element:
                    post_at = post_at_element.get_text(strip=True)
                
                # Featured Image
                image_url = ""
                # Helper function to check if image URL is an ad or valid scholarship image
                def is_valid_image(url):
                    # Skip ad-related images
                    ad_domains = ['ezodn.com', 'ezcdn.com', 'doubleclick.net', 'google.com']
                    if any(domain in url.lower() for domain in ad_domains):
                        return False
                    
                    # Look for scholarship-related images
                    scholarship_indicators = ['wp-content/uploads', 'scholarship', 'study', 'university', 'education']
                    return any(indicator in url.lower() for indicator in scholarship_indicators)
                
                # First try to get the featured image from article header
                article = soup.find('article')
                if article:
                    # Look for featured image div first
                    featured_div = article.find('div', class_='post-thumbnail') or article.find('div', class_='featured-image')
                    if featured_div:
                        img_tag = featured_div.find('img')
                        if img_tag and img_tag.get('src'):
                            raw_src = img_tag['src'].split('?')[0]
                            full_url = urljoin(link, raw_src)
                            if is_valid_image(full_url):
                                image_url = full_url
                    
                    # If no featured image found, try other images in the article
                    if not image_url:
                        for img in article.find_all('img'):
                            if img.get('src'):
                                raw_src = img['src'].split('?')[0]
                                full_url = urljoin(link, raw_src)
                                if is_valid_image(full_url):
                                    image_url = full_url
                                    break
                
                # If still no image found, look in content div
                if not image_url and content_div:
                    for img_tag in content_div.find_all('img'):
                        if img_tag and img_tag.get('src'):
                            raw_src = img_tag['src'].split('?')[0]
                            full_url = urljoin(link, raw_src)
                            if is_valid_image(full_url):
                                image_url = full_url
                                break
                
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
        
        return csv_filename
    
    finally:
        csv_file.close()
        # Close the driver if we created it locally
        if local_driver and driver:
            driver.quit()

# Main script execution example
if __name__ == "__main__":
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    # Example usage
    url = "https://scholarshipscorner.website/scholarships-in-europe/"
    region_name = "Europe-ScholarshipsCorner"
    
    try:
        csv_filename = scrape_scholarships_corner(url, region_name, driver)
        print(f"Scraping completed. Results saved to {csv_filename}")
    finally:
        driver.quit()
