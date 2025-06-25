"""
Specialized scraper for OpportunitiesCorners.com
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

def extract_deadline_opportunities_corners(content_div, soup, title):
    """
    Extract deadline information from OpportunitiesCorners.com pages.
    Uses multiple techniques to find the deadline.
    """
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
    
    # Look for date formats like "31st May 2025" or "May 31, 2025"
    date_patterns_2 = [
        r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:january|february|march|april|may|june|july|august|september|october|november|december),?\s+20\d{2})',
        r'((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?,\s+20\d{2})'
    ]
    
    for p in content_div.find_all(['p', 'li', 'strong', 'b']):
        p_text = p.get_text(strip=True)
        for pattern in date_patterns_2:
            match = re.search(pattern, p_text, re.IGNORECASE)
            if match and ("deadline" in p_text.lower() or "application" in p_text.lower() or "closing" in p_text.lower()):
                return "Deadline: " + match.group(1)
    
    # If we get here, use a simple approach - just look for "Deadline" in text
    if "Deadline" in content_text or "deadline" in content_text:
        # Split text around the word "deadline" and take what comes after
        parts = content_text.split("eadline", 1)
        if len(parts) > 1:
            # Get 50 characters after "deadline" to capture the date
            deadline_part = parts[1].strip(": ").split(".")[0]
            if len(deadline_part) > 50:
                deadline_part = deadline_part[:50] + "..."
            return "Deadline: " + deadline_part
    
    return "Deadline not specified"

def extract_description_opportunities_corners(content_div):
    """
    Extract description from OpportunitiesCorners.com pages.
    Returns the first few paragraphs before any headings.
    """
    description_parts = []
    
    # Get the first few paragraphs before any major heading
    for tag in content_div.find_all(['p', 'div']):
        # Skip tags that are likely to be navigation or metadata
        if tag.parent and tag.parent.name in ['nav', 'header', 'footer']:
            continue
            
        # Stop if we hit any heading or strong text that likely indicates a new section
        if tag.find(['h2', 'h3', 'h4', 'strong', 'b']) and len(description_parts) > 0:
            if any(keyword in tag.get_text().lower() for keyword in ['eligibility', 'deadline', 'host', 'country', 'university', 'duration']):
                break
                
        # Add paragraph text if it's not too short and doesn't contain section keywords
        text = tag.get_text(strip=True)
        if len(text) > 30 and not any(keyword in text.lower() for keyword in ['eligibility:', 'deadline:', 'host country:', 'university:', 'duration:']):
            description_parts.append(text)
            
            # If we've collected enough text, stop
            if len(' '.join(description_parts)) > 300:
                break
                
    return '\n'.join(description_parts)

def extract_host_country_opportunities_corners(content_div, title):
    """
    Extract host country information from OpportunitiesCorners.com pages.
    """
    # First check for explicit host country section
    for tag in content_div.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
        if any(country_keyword in tag.get_text().lower() for country_keyword in ['host country', 'country of study', 'country:']):
            next_sibling = tag.find_next_sibling()
            if next_sibling:
                return next_sibling.get_text(strip=True)
            else:
                parent = tag.parent
                if parent:
                    text = parent.get_text(strip=True)
                    if ':' in text:
                        return text.split(':', 1)[1].strip()
    
    # If no explicit section, try to extract from title
    common_countries = ['germany', 'italy', 'france', 'spain', 'uk', 'united kingdom', 'netherlands', 
                       'belgium', 'sweden', 'norway', 'finland', 'denmark', 'switzerland', 'austria', 
                       'ireland', 'poland', 'portugal', 'czech republic', 'greece', 'hungary', 'malta',
                       'turkey', 'romania', 'estonia', 'europe']
                       
    title_lower = title.lower()
    
    # Check if country name is in title with "in" preposition (e.g., "Scholarship in Germany")
    country_match = re.search(r'in\s+([a-zA-Z\s]+)(?:\s+\(|,|\s+20\d{2}|$)', title_lower)
    if country_match:
        potential_country = country_match.group(1).strip()
        if potential_country in common_countries:
            return potential_country.title()
            
    # Direct country mention in title
    for country in common_countries:
        if country in title_lower:
            # Make sure it's not just part of another word
            if re.search(r'\b' + country + r'\b', title_lower):
                return country.title()
    
    # Check content for any country mentions
    content_text = content_div.get_text(strip=True).lower()
    for country in common_countries:
        if f"host country: {country}" in content_text or f"country: {country}" in content_text:
            return country.title()
            
    return ""

def extract_host_university_opportunities_corners(content_div, title):
    """
    Extract host university information from OpportunitiesCorners.com pages.
    """
    # First check for explicit university section
    for tag in content_div.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
        if any(uni_keyword in tag.get_text().lower() for uni_keyword in ['host university', 'university:', 'offered by']):
            next_sibling = tag.find_next_sibling()
            if next_sibling:
                return next_sibling.get_text(strip=True)
            else:
                parent = tag.parent
                if parent:
                    text = parent.get_text(strip=True)
                    if ':' in text:
                        return text.split(':', 1)[1].strip()
    
    # Try to extract university name from title
    
    # Common university keywords
    uni_keywords = ['university', 'college', 'institute', 'school']
    
    # Check if the title starts with a university name
    title_parts = title.split()
    if len(title_parts) >= 2:
        # Look for patterns like "Oxford University Scholarship" or "University of Cambridge Scholarship"
        uni_name = []
        found_uni_keyword = False
        
        for i, part in enumerate(title_parts):
            part_lower = part.lower()
            if part_lower in uni_keywords:
                found_uni_keyword = True
                uni_name.append(part)
            elif found_uni_keyword and part_lower in ['of', 'for', 'and', 'the']:
                uni_name.append(part)
            elif found_uni_keyword and i < 5:  # Limit to first few words after keyword
                uni_name.append(part)
            elif not found_uni_keyword and i < 3 and part_lower not in ['scholarship', 'scholarships', 'fully', 'funded']:
                uni_name.append(part)
            else:
                if found_uni_keyword:
                    break
        
        if found_uni_keyword:
            return " ".join(uni_name)
    
    # Look for university name in content
    content_text = content_div.get_text()
    uni_pattern = re.compile(r'(university\s+of\s+[\w\s]+|[\w\s]+\s+university|[\w\s]+\s+institute\s+of\s+[\w\s]+)', re.IGNORECASE)
    uni_matches = uni_pattern.findall(content_text)
    
    if uni_matches:
        # Return the first match that doesn't contain "apply" or other common words
        for match in uni_matches:
            if "apply" not in match.lower() and "eligible" not in match.lower():
                return match
    
    return ""

def extract_program_duration_opportunities_corners(content_div):
    """
    Extract program duration information from OpportunitiesCorners.com pages.
    """
    # First check for explicit duration section
    for tag in content_div.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
        if any(duration_keyword in tag.get_text().lower() for duration_keyword in ['program duration', 'duration:', 'course duration', 'length of study']):
            next_sibling = tag.find_next_sibling()
            if next_sibling:
                return next_sibling.get_text(strip=True)
            else:
                parent = tag.parent
                if parent:
                    text = parent.get_text(strip=True)
                    if ':' in text:
                        return text.split(':', 1)[1].strip()
    
    # Look for duration patterns in the content
    content_text = content_div.get_text(strip=True).lower()
    
    # Common duration patterns
    duration_patterns = [
        r'program(?:\s+is|\s+will\s+be)?\s+(\d+(?:\.\d+)?)\s+years?',
        r'duration(?:\s+is|\s+will\s+be)?\s+(\d+(?:\.\d+)?)\s+years?',
        r'duration(?:\s+is|\s+will\s+be)?\s+(\d+(?:\.\d+)?)\s+months?',
        r'(\d+(?:\.\d+)?)\s*-?\s*year(?:\s+program|\s+course|\s+degree)',
        r'(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)\s+years?',
        r'bachelor\'s[^.]*?(\d+(?:\.\d+)?)\s+years?',
        r'master\'s[^.]*?(\d+(?:\.\d+)?)\s+years?',
        r'ph\.?d\.?[^.]*?(\d+(?:\.\d+)?)\s+years?'
    ]
    
    for pattern in duration_patterns:
        duration_match = re.search(pattern, content_text)
        if duration_match:
            if len(duration_match.groups()) == 2:  # Range format (e.g., "1 to 2 years")
                return f"{duration_match.group(1)} to {duration_match.group(2)} years"
            else:
                # Check if we need to add "years" or "months"
                captured_value = duration_match.group(1)
                if "year" in pattern:
                    return f"{captured_value} years"
                elif "month" in pattern:
                    return f"{captured_value} months"
                else:
                    return captured_value
    
    # Look for program specific durations
    program_durations = {
        "bachelor": "3-4 years",
        "undergraduate": "3-4 years",
        "master": "1-2 years", 
        "postgraduate": "1-2 years",
        "msc": "1-2 years",
        "ma": "1-2 years",
        "mba": "1-2 years",
        "phd": "3-5 years",
        "doctorate": "3-5 years",
    }
    
    # Check if any of these program types are mentioned
    for program_type, duration in program_durations.items():
        if program_type in content_text:
            return duration
    
    return ""

def extract_degree_offered_opportunities_corners(content_div, title):
    """
    Extract degree offered information from OpportunitiesCorners.com pages.
    """
    # First check for explicit degree section
    for tag in content_div.find_all(['h2', 'h3', 'h4', 'strong', 'b']):
        if any(degree_keyword in tag.get_text().lower() for degree_keyword in ['degree', 'degree offered', 'field of study', 'what you will study']):
            next_sibling = tag.find_next_sibling()
            if next_sibling:
                return next_sibling.get_text(strip=True)
            else:
                parent = tag.parent
                if parent:
                    text = parent.get_text(strip=True)
                    if ':' in text:
                        return text.split(':', 1)[1].strip()
    
    # Look for degree mentions in the title
    title_lower = title.lower()
    degree_keywords = {
        'bachelor': "Bachelor's Degree",
        'undergraduate': "Bachelor's Degree",
        'master': "Master's Degree", 
        'msc': "Master of Science",
        'ma': "Master of Arts",
        'mba': "Master of Business Administration",
        'phd': "PhD/Doctorate",
        'doctorate': "PhD/Doctorate",
    }
    
    for keyword, degree_type in degree_keywords.items():
        if keyword in title_lower:
            return degree_type
            
    # Check for degree program in the content text
    content_text = content_div.get_text(strip=True).lower()
    
    degree_patterns = [
        r'(bachelor(?:\'s)?(?:\s+of\s+[a-z]+)?(?:\s+degree)?)',
        r'(master(?:\'s)?(?:\s+of\s+[a-z]+)?(?:\s+degree)?)',
        r'(ph\.?d\.?|doctorate)(?:\s+degree)?'
    ]
    
    for pattern in degree_patterns:
        degree_match = re.search(pattern, content_text, re.IGNORECASE)
        if degree_match:
            return degree_match.group(0).capitalize()
    
    return ""

def scrape_opportunities_corners(url, region_name, driver=None):
    """Scrape scholarships from OpportunitiesCorners.com."""
    print(f"\n=== Scraping {region_name} scholarships from OpportunitiesCorners ===")
    
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
        
        # Remove duplicate links
        post_links = list(dict.fromkeys(post_links))
        print(f"Found {len(post_links)} posts in {region_name} from OpportunitiesCorners website.")
        
        # Loop through each post
        for index, link in enumerate(post_links):
            try:
                driver.get(link)
                time.sleep(3)  # Increased wait time
                soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # Title
                title_element = soup.find("h1", class_="entry-title") or soup.find("h1", class_="post-title")
                if not title_element:
                    # Try generic h1 as fallback
                    title_element = soup.find("h1")
                    if not title_element:
                        print(f"⚠️ No title found for post {index+1}. Skipping...")
                        continue
                    
                title = title_element.text.strip()
                
                # Content area
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
                
                # Extract sections using specialized methods for OpportunitiesCorners
                deadline = extract_deadline_opportunities_corners(content_div, soup, title)
                description = extract_description_opportunities_corners(content_div)
                eligibility = extract_section(content_div, ["eligibility", "who can apply", "eligible"])
                host_country = extract_host_country_opportunities_corners(content_div, title)
                host_university = extract_host_university_opportunities_corners(content_div, title)
                program_duration = extract_program_duration_opportunities_corners(content_div)
                degree_offered = extract_degree_offered_opportunities_corners(content_div, title)
                
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
                print(f"❌ Error processing post {index+1} in {region_name} region: {str(e)}")                # Log the error for debugging
                with open(f"error_log_{region_name}.txt", "a", encoding="utf-8") as error_log:
                    error_log.write(f"Error on {link}: {str(e)}\n")
                continue
        return csv_filename
    
    except Exception as e:
        print(f"Unexpected error in scrape_opportunities_corners: {str(e)}")
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

# Main script execution example
if __name__ == "__main__":
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    # Example usage
    url = "https://opportunitiescorners.com/category/scholarships-in-europe/"
    region_name = "Europe-OpportunitiesCorners"
    
    try:
        csv_filename = scrape_opportunities_corners(url, region_name, driver)
        print(f"Scraping completed. Results saved to {csv_filename}")
    finally:
        driver.quit()
