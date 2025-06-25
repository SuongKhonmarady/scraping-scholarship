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
import sys
import re
import traceback
from urllib.parse import urljoin

def generate_slug(title):
    """
    Generate SEO-friendly slug from scholarship title.
    Removes years, marketing words, and creates URL-friendly format.
    """
    if not title or title.strip() == "":
        return ""
    
    # Marketing and promotional words to remove
    marketing_words = [
        'apply now', 'fully funded', 'full funding', 'free', 'no fee', 'deadline',
        'hurry up', 'limited time', 'don\'t miss', 'opportunity', 'chance',
        'amazing', 'exclusive', 'special', 'urgent', 'last call', 'final',
        'best', 'top', 'premium', 'guaranteed', 'easy', 'quick', 'fast'
    ]
    
    # Convert to lowercase
    slug = title.lower()
    
    # Remove years and year ranges (2020-2030 range)
    # Handle formats like: 2025, 2024/25, 2025-26, 2024/2025, etc.
    slug = re.sub(r'\b20[2-3][0-9](?:[/-](?:20)?[2-3][0-9])?\b', '', slug)
    
    # Remove marketing words
    for word in marketing_words:
        slug = re.sub(r'\b' + re.escape(word) + r'\b', '', slug)
    
    # Remove common scholarship-related words that add no SEO value
    common_words = ['scholarship', 'program', 'opportunity', 'application']
    # Keep 'scholarship' if it's the main focus, remove others
    for word in ['program', 'opportunity', 'application']:
        slug = re.sub(r'\b' + re.escape(word) + r'\b', '', slug)
    
    # Remove special characters and punctuation except hyphens and spaces
    slug = re.sub(r'[^\w\s-]', '', slug)
    
    # Replace multiple spaces/hyphens with single hyphen
    slug = re.sub(r'[\s-]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Limit length to 100 characters (SEO best practice)
    if len(slug) > 100:
        # Try to cut at word boundary
        truncated = slug[:100]
        last_hyphen = truncated.rfind('-')
        if last_hyphen > 50:  # If we can find a reasonable break point
            slug = truncated[:last_hyphen]
        else:
            slug = truncated
    
    # Ensure slug is not empty
    if not slug:
        slug = "scholarship"
    
    return slug

# Try to import utility functions
try:
    from utils.file_utils import (
        generate_timestamped_filename,
        ensure_file_can_be_created,
        validate_csv_file
    )
except ImportError:
    # Define simplified versions if the utils module is not available
    def generate_timestamped_filename(base_filename):
        """Generate a filename with timestamp."""
        base_name, extension = os.path.splitext(base_filename)
        timestamp = int(time.time())
        return f"{base_name}-{timestamp}{extension}"
        
    def ensure_file_can_be_created(file_path, create_unique=True, overwrite=False):
        """Ensure a file can be created at the specified path."""
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            return file_path
        if overwrite:
            try:
                os.remove(file_path)
                return file_path
            except:
                pass
        if create_unique:
            return generate_timestamped_filename(file_path)
        return None
        
    def validate_csv_file(csv_file_path):
        """Validate that a CSV file exists and has content."""
        if not os.path.exists(csv_file_path):
            return False
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                return len(f.read()) > 0
        except:
            return False

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
    
    # Setup CSV with better file handling
    base_csv_filename = f"scholarships-{region_name.lower().replace(' ', '-')}.csv"
    
    # Get a safe filename that won't conflict with existing files
    csv_filename = ensure_file_can_be_created(
        base_csv_filename, 
        create_unique=True,
        overwrite=False
    )
    
    if csv_filename is None:
        print(f"❌ Could not create a suitable filename for {region_name} data")
        return None
        
    print(f"Will save data to: {csv_filename}")
    
    # Create the CSV file with better error handling
    csv_file = None
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(csv_filename)), exist_ok=True)
        
        csv_file = open(csv_filename, mode="w", newline="", encoding="utf-8")
        csv_writer = csv.DictWriter(csv_file, fieldnames=[
            "Title", "Slug", "Description", "Link", "Official Link", "Image", "Deadline", "Eligibility",
            "Host Country", "Host University", "Program Duration", "Degree Offered", "Region", "Post_at"
        ])
        csv_writer.writeheader()
    except Exception as e:
        print(f"❌ Error creating CSV file {csv_filename}: {str(e)}")
        traceback.print_exc()
        
        # Clean up if file was partially created
        if csv_file and not csv_file.closed:
            csv_file.close()
        
        if os.path.exists(csv_filename):
            try:
                os.remove(csv_filename)
                print(f"Removed incomplete file {csv_filename}")
            except:
                pass
                
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
        # Load page
        driver.get(url)
        time.sleep(5)  # Increased wait time for page loading
        
        # Get links from the page
        post_links = []
        
        # Function to extract links from current page
        def extract_links_from_page():
            elements = driver.find_elements(By.CSS_SELECTOR, "article h2 a, .post-title a, .entry-title a, .post-box .title a")
            return [elem.get_attribute("href") for elem in elements]
        
        # Extract links from first page
        page_links = extract_links_from_page()
        post_links.extend(page_links)
        
        # Try to handle pagination (up to 3 pages)
        if len(page_links) > 0:
            # Try to navigate to next pages (up to 3 additional pages)
            for page_num in range(2, 4):
                try:
                    next_page_url = f"{url}page/{page_num}/"
                    print(f"Checking pagination: {next_page_url}")
                    driver.get(next_page_url)
                    time.sleep(5)
                    
                    # Extract links from this page
                    additional_links = extract_links_from_page()
                    if additional_links:
                        post_links.extend(additional_links)
                        print(f"Added {len(additional_links)} links from page {page_num}")
                    else:
                        break  # No more pages with links
                except Exception as e:
                    print(f"Failed to load page {page_num}: {str(e)}")
                    break
        
        # Filter out duplicates and ensure valid URLs
        post_links = list(dict.fromkeys([link for link in post_links if link and link.startswith("http")]))
        
        print(f"Found {len(post_links)} posts to scrape for {region_name}")
        
        # Process each scholarship post
        for index, link in enumerate(post_links):
            try:
                print(f"Processing {index+1}/{len(post_links)}: {link}")
                driver.get(link)
                time.sleep(3)
                
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                
                # Extract title
                title = ""
                title_element = soup.select_one("h1.entry-title, .post-title h1, article h1")
                if title_element:
                    title = title_element.get_text(strip=True)
                else:
                    print(f"No title found for {link}, using link as title")
                    title = link
                
                # Generate slug from title
                slug = generate_slug(title)
                
                # Extract content div
                content_div = soup.select_one("div.entry-content, article .post-content, .content-inner")
                
                # Extract description and other fields
                description = extract_description(content_div) if content_div else ""
                
                # Other fields
                deadline = extract_section(soup, ["deadline", "closing date", "application deadline"])
                eligibility = extract_section(soup, ["eligibility", "who can apply", "requirements"])
                host_country = extract_section(soup, ["host country", "destination", "country"])
                host_university = extract_section(soup, ["university", "institution", "school"])
                program_duration = extract_section(soup, ["duration", "period", "length"])
                degree_offered = extract_section(soup, ["degree", "level of study", "program"])
                post_at = time.strftime("%Y-%m-%d")  # Today's date
                
                # Try to find official link
                official_link = ""
                for a in content_div.find_all("a") if content_div else []:
                    href = a.get("href", "")
                    text = a.get_text(strip=True).lower()
                    if href and href.startswith("http") and ("apply" in text or "official" in text or "website" in text):
                        official_link = href
                        break
                
                # Try to find an image
                image_url = ""
                # Function to check if an image URL is valid
                def is_valid_image(url):
                    return url and url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))
                
                # First try to find a featured image
                article = soup.select_one("article")
                if article:
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
                
                # Generate SEO-friendly slug from title
                slug = generate_slug(title)
                
                # Save
                csv_writer.writerow({
                    "Title": title,
                    "Slug": slug,
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
    
    except Exception as e:
        print(f"Unexpected error in scrape_scholarships_corner: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Make sure to close the file safely
        if 'csv_file' in locals() and csv_file and not csv_file.closed:
            try:
                csv_file.close()
                print(f"Closed CSV file: {csv_filename}")
            except Exception as e:
                print(f"Error closing file {csv_filename}: {e}")
        
        # Validate the created file
        if 'csv_filename' in locals() and os.path.exists(csv_filename):
            if validate_csv_file(csv_filename):
                print(f"✅ Validated CSV file: {csv_filename}")
            else:
                print(f"⚠️ Warning: CSV file {csv_filename} may be invalid or empty")
                
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
