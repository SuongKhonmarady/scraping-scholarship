from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import csv
import os
import re
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

def get_website_type(url):
    """Determine the type of website based on URL."""
    if "scholarshipscorner.website" in url.lower():
        return "scholarships_corner"
    elif "opportunitiescorners.com" in url.lower():
        return "opportunities_corners"
    else:
        return "unknown"

def extract_deadline_opportunities_corners(content_div, soup, title):
    """
    Special function to extract deadline from opportunitiescorners.com pages.
    This simplified version focuses on common patterns seen in the website.
    """
    # Default deadline value
    deadline = ""
    
    # First check for elements with strong text containing "Deadline"
    for strong in content_div.find_all(['strong', 'b']):
        text = strong.get_text(strip=True)
        if "Deadline" in text or "deadline" in text:
            parent = strong.parent
            if parent:
                return parent.get_text(strip=True)
    
    # Next, check for paragraphs containing deadline keyword
    for p in content_div.find_all(['p', 'li']):
        text = p.get_text(strip=True)
        if "Deadline" in text or "deadline" in text:
            return "Deadline: " + text.split("eadline", 1)[1].strip(": ")
    
    # Check if any heading contains deadline
    for h in content_div.find_all(['h2', 'h3', 'h4']):
        text = h.get_text(strip=True)
        if "Deadline" in text or "deadline" in text:
            return text
    
    # If we get here, use a simple approach - just look for "Deadline" in text
    content_text = content_div.get_text(strip=True)
    if "Deadline" in content_text or "deadline" in content_text:
        # Split text around the word "deadline" and take what comes after
        parts = content_text.split("eadline", 1)
        if len(parts) > 1:
            # Get 50 characters after "deadline" to capture the date
            deadline_part = parts[1].strip(": ").split(".")[0]
            if len(deadline_part) > 50:
                deadline_part = deadline_part[:50] + "..."
            return "Deadline: " + deadline_part
    
    return "Deadline not specified"# Look for a date pattern in the title and content
    import re
    title_lower = title.lower() if title else ""
    
    # Check for date mentions in the title (like "2025/26" or "2025")
    year_pattern = re.compile(r'20\d{2}(?:/\d{2})?')
    year_match = year_pattern.search(title_lower)
    
    # Common date formats in OpportunitiesCorners content
    content_text = content_div.get_text().lower() if content_div else ""
    
    # Define date patterns to search for
    date_patterns = [
        r'deadline.*?(\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december),?\s+20\d{2})',
        r'deadline.*?(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec),?\s+20\d{2})',
        r'application\s+deadline.*?(\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december),?\s+20\d{2})',
        r'applications\s+close.*?(\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december),?\s+20\d{2})'
    ]
    
    for pattern in date_patterns:
        deadline_match = re.search(pattern, content_text, re.IGNORECASE)
        if deadline_match:
            return "Deadline: " + deadline_match.group(1)
    
    # Look for simple month mentions followed by a date
    month_date_pattern = r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december),?\s+20\d{2})'
    deadline_match = re.search(month_date_pattern, content_text, re.IGNORECASE)
    if deadline_match:
        # If found in text near deadline words
        context = content_text[max(0, deadline_match.start() - 50):min(len(content_text), deadline_match.end() + 50)]
        if "deadline" in context or "application" in context or "apply" in context or "close" in context:
            return "Deadline: " + deadline_match.group(1)
    
    # Look for deadline mentions like "Deadline: Month Day, Year"
    for p in content_div.find_all(['p', 'li', 'h3', 'h4']):
        p_text = p.get_text(strip=True).lower()
        if "deadline" in p_text and any(m in p_text for m in ["january", "february", "march", "april", "may", "june", "july", 
                                                             "august", "september", "october", "november", "december"]):
            return "Deadline: " + p_text.split("deadline")[1].strip(": ")
    
    # As a last fallback, return any date mentioned near the word "deadline"
    for p in content_div.find_all(['p', 'li']):
        p_text = p.get_text(strip=True).lower()
        if "deadline" in p_text:
            return "Deadline: " + p_text
    
    return deadline
    
    # If no deadline in title, try to find it in the content using standard method
    standard_deadline = extract_section(content_div, ["deadline", "last date", "closing date", "application deadline"])
    if standard_deadline:
        return standard_deadline
    
    # Look for deadline in a different format - sometimes it's in a table or list with specific formatting
    # Check for text patterns like "Deadline: May 15, 2025"
    for p_tag in content_div.find_all(['p', 'li']):
        text = p_tag.get_text(strip=True).lower()
        if "deadline" in text or "application close" in text or "closes on" in text or "last date" in text:
            # Look for date patterns in this text
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    return p_tag.get_text(strip=True)
            # If no pattern found but contains deadline keyword, return the whole text
            return p_tag.get_text(strip=True)
    
    # Check for bold or strong tags that might contain deadline info
    for tag in content_div.find_all(['strong', 'b']):
        text = tag.get_text(strip=True).lower()
        if "deadline" in text:
            # Get the parent paragraph
            parent = tag.parent
            if parent:
                parent_text = parent.get_text(strip=True)
                # Look for date patterns in this text
                for pattern in date_patterns:
                    matches = re.findall(pattern, parent_text.lower())
                    if matches:
                        return parent_text
                return parent_text
    
    # As a last resort, search the entire content for date patterns
    content_text = content_div.get_text(strip=True).lower()
    deadline_context = None
    
    # Try to find sentences containing deadlines
    sentences = re.split(r'[.!?]\s+', content_text)
    for sentence in sentences:
        if "deadline" in sentence or "application close" in sentence or "last date" in sentence:
            deadline_context = sentence
            break
    
    if deadline_context:
        # Extract date patterns from the context
        for pattern in date_patterns:
            matches = re.findall(pattern, deadline_context)
            if matches:
                full_match = re.search(pattern, deadline_context)
                if full_match:
                    return "Deadline: " + deadline_context[full_match.start():full_match.end()]
        
        return "Deadline context: " + deadline_context[:100]  # Return truncated context
    
    return deadline

def scrape_scholarships(url, region_name, driver=None):
    """Scrape scholarships for a specific region."""
    print(f"\n=== Scraping {region_name} scholarships ===")
    
    # Setup CSV
    csv_filename = f"scholarships-{region_name.lower().replace(' ', '-')}.csv"
    csv_file = open(csv_filename, mode="w", newline="", encoding="utf-8")
    csv_writer = csv.DictWriter(csv_file, fieldnames=[
        "Title", "Slug", "Description", "Link", "Official Link", "Image", "Deadline", "Eligibility",
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
        # Determine website type
        website_type = get_website_type(url)
        
        # Load page
        driver.get(url)
        time.sleep(5)  # Increased wait time for page loading
        
        # Get links based on website type
        post_links = []
        
        # Function to extract links from current page
        def extract_links_from_page():
            if website_type == "scholarships_corner":
                elements = driver.find_elements(By.CSS_SELECTOR, "h2.entry-title a")
                return [elem.get_attribute("href") for elem in elements]
            elif website_type == "opportunities_corners":
                # Try various selectors that might be used on the site
                elements = driver.find_elements(By.CSS_SELECTOR, "article h2 a, .post-title a, .entry-title a, .post-box .title a")
                return [elem.get_attribute("href") for elem in elements]
            return []
        
        # Extract links from first page
        page_links = extract_links_from_page()
        post_links.extend(page_links)
        
        # For opportunities_corners, try to handle pagination (up to 3 pages)
        if website_type == "opportunities_corners" and len(page_links) > 0:
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
        
        # Remove duplicate links
        post_links = list(dict.fromkeys(post_links))
        print(f"Found {len(post_links)} posts in {region_name} from {website_type} website.")
        
        # Loop through each post
        for index, link in enumerate(post_links):
            try:
                driver.get(link)
                time.sleep(3)  # Increased wait time
                soup = BeautifulSoup(driver.page_source, "html.parser")
                  # Title - try different possible selectors
                title_element = soup.find("h1", class_="entry-title") or soup.find("h1", class_="post-title")
                if not title_element:
                    # Try generic h1 as fallback
                    title_element = soup.find("h1")
                    if not title_element:
                        print(f"⚠️ No title found for post {index+1}. Skipping...")
                        continue
                    
                title = title_element.text.strip()
                
                # Content area - try different possible selectors
                content_div = soup.find("div", class_="entry-content") or soup.find("div", class_="post-content")
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
                
                # Extract sections
                # Enhanced deadline extraction for OpportunitiesCorners
                if website_type == "opportunities_corners":
                    deadline = extract_deadline_opportunities_corners(content_div, soup, title)
                else:
                    deadline = extract_section(content_div, ["deadline", "last date", "closing date"])
                
                description = extract_description(content_div)
                eligibility = extract_section(content_div, ["eligibility", "who can apply", "eligible"])
                host_country = extract_section(content_div, ["host country", "study in", "country"])
                host_university = extract_section(content_div, ["host university", "offered by", "university"])
                program_duration = extract_section(content_div, ["program duration", "duration"])
                degree_offered = extract_section(content_div, ["degree", "degree offered", "field of study", "what you will study"])
                  # Extract post date - try multiple possible selectors for different sites
                post_at = ""
                post_at_element = (
                    soup.select_one(".entry-date.published") or 
                    soup.select_one(".post-date") or 
                    soup.select_one(".date") or
                    soup.select_one("time")
                )
                if post_at_element:
                    post_at = post_at_element.get_text(strip=True)# Featured Image
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
                        if img_tag.get('src'):
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
                    "Host Country": host_country,                    "Host University": host_university,
                    "Program Duration": program_duration,
                    "Degree Offered": degree_offered,
                    "Region": region_name,
                    "Post_at": post_at
                })
                
                print(f"✅ {region_name} - Saved {index+1}/{len(post_links)}: {title[:50]}...")
            
            except Exception as e:
                website_type = get_website_type(link)
                print(f"❌ Error processing post {index+1} in {region_name} region (site: {website_type}): {str(e)}")
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
        

# Test function that can be imported and run
def test_deadline_extraction():
    print("Test deadline extraction function is working!")
    return "Test successful"

# Main script
if __name__ == "__main__":
    # Setup browser
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Define regions and their URLs
    regions = {
        "Africa": "https://scholarshipscorner.website/scholarships-in-africa/",
        "Europe-OpportunitiesCorners": "https://opportunitiescorners.com/category/scholarships-in-europe/",
        "Europe-ScholarshipsCorner": "https://scholarshipscorner.website/scholarships-in-europe/",
        # "Asia": "https://scholarshipscorner.website/scholarships-in-asia/",
        # "Australia": "https://scholarshipscorner.website/scholarships-in-australia/",
        # "Middle East": "https://scholarshipscorner.website/scholarships-in-middle-east/",
        # "North America": "https://scholarshipscorner.website/scholarships-in-north-america/",
        # "South America": "https://scholarshipscorner.website/scholarships-in-south-america/",
        # "USA": "https://scholarshipscorner.website/scholarships-in-usa/"
    }
    
    # Create output directory for all CSVs
    output_dir = "scholarship_data"
    os.makedirs(output_dir, exist_ok=True)
      # Store all CSV filenames
    all_csv_files = []
    
    try:
        # Process each region
        for region_name, url in regions.items():
            csv_filename = scrape_scholarships(url, region_name, driver)
            all_csv_files.append(csv_filename)
        
        # Combine all CSV files into one master file
        with open(os.path.join(output_dir, "all_scholarships.csv"), "w", newline="", encoding="utf-8") as master_file:
            # Get fieldnames from the first CSV file
            with open(all_csv_files[0], "r", encoding="utf-8") as first_file:
                reader = csv.reader(first_file)
                fieldnames = next(reader)  # First row contains headers
            
            # Create writer for master file
            master_writer = csv.DictWriter(master_file, fieldnames=fieldnames)
            master_writer.writeheader()
            
            # Copy data from each region file
            for csv_file in all_csv_files:
                with open(csv_file, "r", encoding="utf-8") as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        master_writer.writerow(row)
                
                # Move region file to output directory
                os.rename(csv_file, os.path.join(output_dir, csv_file))
        
        print(f"\n🎉 All data successfully scraped and combined!")
        print(f"📂 Individual region files and combined data saved in '{output_dir}' folder")
    
    except Exception as e:
        print(f"❌ Error in main process: {str(e)}")
    
    finally:
        driver.quit()