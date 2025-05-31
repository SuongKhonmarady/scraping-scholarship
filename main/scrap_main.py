"""
Main script to run both scrapers and combine results
Includes duplicate detection and removal
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import csv
import os
import time
import pandas as pd
import shutil
import datetime

# Import the specialized scrapers and utilities
try:
    from scrapers import scrape_scholarships_corner, scrape_opportunities_corners
    from duplicate_utils import DuplicateChecker
    from utils.file_utils import (
        generate_timestamped_filename,
        ensure_file_can_be_created,
        validate_csv_file,
        create_backup
    )
except ImportError:
    # Fallback for direct imports if package imports fail
    from scrapers.scrape_scholarships_corner import scrape_scholarships_corner
    from scrapers.scrape_opportunities_corners import scrape_opportunities_corners
    from duplicate_utils.duplicate_checker import DuplicateChecker
    
    # Define simplified versions if the utils module is not available
    def generate_timestamped_filename(base_filename):
        """Generate a filename with timestamp."""
        base_name, extension = os.path.splitext(base_filename)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
            
    def create_backup(file_path):
        """Create a backup of a file with timestamp."""
        if not os.path.exists(file_path):
            return None
        try:
            backup_path = generate_timestamped_filename(f"{file_path}.bak")
            shutil.copy2(file_path, backup_path)
            return backup_path
        except:
            return None

def safe_file_move(src_file, dest_file, create_backup=True):
    """
    Safely move a file to a destination, handling existing files appropriately.
    
    Args:
        src_file: Source file path
        dest_file: Destination file path
        create_backup: If True, create a backup of existing files instead of overwriting
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        
        # Check if destination file already exists
        if os.path.exists(dest_file):
            if create_backup:
                # Create a backup with timestamp
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{dest_file}.{timestamp}.bak"
                print(f"Creating backup of existing file: {backup_file}")
                shutil.copy2(dest_file, backup_file)
            
            # Remove the existing destination file
            print(f"Removing existing file: {dest_file}")
            os.remove(dest_file)
        
        # Now move the file
        print(f"Moving file: {src_file} -> {dest_file}")
        shutil.move(src_file, dest_file)
        return True
    
    except Exception as e:
        print(f"❌ Error moving file {src_file} to {dest_file}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def combine_csv_files(csv_files, output_dir):
    """Combine multiple CSV files into one master file with duplicate checking."""
    if not csv_files:
        print("No CSV files to combine!")
        return
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize duplicate checker
    duplicate_checker = DuplicateChecker(similarity_threshold=0.85)
    
    # Check if first file exists and is readable
    if not os.path.exists(csv_files[0]):
        print(f"❌ Error: First CSV file {csv_files[0]} does not exist!")
        return
        
    try:
        # Get fieldnames from the first CSV file
        with open(csv_files[0], "r", encoding="utf-8") as first_file:
            reader = csv.reader(first_file)
            fieldnames = next(reader)  # First row contains headers
    except Exception as e:
        print(f"❌ Error reading first CSV file {csv_files[0]}: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Create the output files
    all_file_path = os.path.join(output_dir, "all_scholarships.csv")
    unique_file_path = os.path.join(output_dir, "unique_scholarships.csv")
    
    # Keep track of all rows for later writing
    all_rows = []
    unique_rows = []
    
    # Process each file
    for csv_file in csv_files:
        try:
            if not os.path.exists(csv_file):
                print(f"⚠️ Warning: CSV file {csv_file} does not exist, skipping...")
                continue
                
            with open(csv_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    all_rows.append(row)
                    
                    # Add to unique list if not a duplicate
                    if duplicate_checker.add_scholarship(row):
                        unique_rows.append(row)
                        
            # Move region file to output directory using safe file move
            dest_file = os.path.join(output_dir, os.path.basename(csv_file))
            safe_file_move(csv_file, dest_file, create_backup=True)
        
        except Exception as e:
            print(f"❌ Error processing CSV file {csv_file}: {str(e)}")
            import traceback
            traceback.print_exc()
            # Continue to next file instead of aborting the entire process
            
    # Verify we have data to write
    if not all_rows:
        print("⚠️ Warning: No scholarship data was extracted from CSV files!")
        return
            
    try:
        # Write all scholarships (with duplicates)
        with open(all_file_path, "w", newline="", encoding="utf-8") as all_file:
            writer = csv.DictWriter(all_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_rows:
                writer.writerow(row)
        print(f"✅ Successfully wrote {len(all_rows)} scholarships to {all_file_path}")
    
    except Exception as e:
        print(f"❌ Error writing all scholarships file {all_file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    try:
        # Write unique scholarships (duplicates removed)
        with open(unique_file_path, "w", newline="", encoding="utf-8") as unique_file:
            writer = csv.DictWriter(unique_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in unique_rows:
                writer.writerow(row)
        print(f"✅ Successfully wrote {len(unique_rows)} unique scholarships to {unique_file_path}")
    
    except Exception as e:
        print(f"❌ Error writing unique scholarships file {unique_file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Get statistics from the duplicate checker
    stats = duplicate_checker.get_stats()
    
    print(f"\n🎉 All data successfully scraped and combined!")
    print(f"📊 Statistics:")
    print(f"   - Total scholarships: {stats['total_processed']}")
    print(f"   - Duplicates found: {stats['duplicates_found']}")
    print(f"   - Unique scholarships: {stats['unique_scholarships']}")
    print(f"📂 Files saved in '{output_dir}' folder:")
    print(f"   - all_scholarships.csv: All scholarships including duplicates")
    print(f"   - unique_scholarships.csv: Scholarships with duplicates removed")
    print(f"   - Individual region files also saved in the same folder")

def cleanup_temporary_files(csv_files):
    """
    Clean up any temporary files that might have been created during scraping
    but were not properly processed.
    
    Args:
        csv_files: List of CSV files that were successfully processed
    """
    # Get the directory where csv files are stored
    cwd = os.getcwd()
    
    # Look for any csv files that match our naming pattern but aren't in the list
    for file in os.listdir(cwd):
        if file.startswith('scholarships-') and file.endswith('.csv') and file not in [os.path.basename(f) for f in csv_files]:
            try:
                # Check if it's a valid CSV file
                if validate_csv_file(os.path.join(cwd, file)):
                    print(f"Found unprocessed CSV file: {file}")
                    # Add it to our list to be processed
                    csv_files.append(os.path.join(cwd, file))
                else:
                    # It's an invalid or empty file, clean it up
                    print(f"Cleaning up invalid/empty CSV file: {file}")
                    os.remove(os.path.join(cwd, file))
            except Exception as e:
                print(f"Error checking file {file}: {str(e)}")
                
    return csv_files

def main(dry_run=False):
    # Set up shared browser instance
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Uncomment for headless operation
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Define regions and their URLs
    regions = {
        "Africa": {
            "url": "https://scholarshipscorner.website/scholarships-in-africa/",
            "type": "scholarships_corner"
        },
        "Europe-OpportunitiesCorners": {
            "url": "https://opportunitiescorners.com/category/scholarships-in-europe/",
            "type": "opportunities_corners"
        },
        # "Europe-ScholarshipsCorner": {
        #     "url": "https://scholarshipscorner.website/scholarships-in-europe/",
        #     "type": "scholarships_corner"
        # },
        
        # "Asia": {
        #     "url": "https://scholarshipscorner.website/scholarships-in-asia/",
        #     "type": "scholarships_corner"
        # },
        # "Australia": {
        #     "url": "https://scholarshipscorner.website/scholarships-in-australia/",
        #     "type": "scholarships_corner"
        # },
        # "Australia-OpportunitiesCorners": {
        #     "url": "https://opportunitiescorners.com/category/scholarships-in-australia/",
        #     "type": "opportunities_corners"
        # },
        # "Middle East": {
        #     "url": "https://scholarshipscorner.website/scholarships-in-middle-east/",
        #     "type": "scholarships_corner"
        # },
        # "North America": {
        #     "url": "https://scholarshipscorner.website/scholarships-in-north-america/",
        #     "type": "scholarships_corner"
        # },
        
        # Country-specific scholarships
        # "USA": {
        #     "url": "https://opportunitiescorners.com/category/scholarships-in-usa/",
        #     "type": "opportunities_corners"
        # },
        "UK": {
            "url": "https://opportunitiescorners.com/category/scholarships-in-uk/",
            "type": "opportunities_corners"
        },
        # "Canada": {
        #     "url": "https://opportunitiescorners.com/category/scholarships-in-canada/",
        #     "type": "opportunities_corners"
        # },
        # "Japan": {
        #     "url": "https://opportunitiescorners.com/category/scholarships-in-japan/",
        #     "type": "opportunities_corners"
        # },
        # "China": {
        #     "url": "https://opportunitiescorners.com/category/scholarships-in-china/",
        #     "type": "opportunities_corners"
        # },
        # "South Korea": {
        #     "url": "https://opportunitiescorners.com/category/scholarships-in-south-korea/",
        #     "type": "opportunities_corners"
        # },
        # "Singapore": {
        #     "url": "https://opportunitiescorners.com/category/scholarships-in-singapore/",
        #     "type": "opportunities_corners"
        # },
        # "Germany": {
        #     "url": "https://scholarshipscorner.website/scholarships-in-germany/",
        #     "type": "scholarships_corner"
        # },
        # "Saudi Arabia": {
        #     "url": "https://scholarshipscorner.website/scholarships-in-saudi-arabia/",
        #     "type": "scholarships_corner"
        # },
        # "Turkey": {
        #     "url": "https://scholarshipscorner.website/scholarships-in-turkey/",
        #     "type": "scholarships_corner"
        # }
    }
    
    # If this is a dry run, just print what would be scraped
    if dry_run:
        print("\n=== DRY RUN - No actual scraping will be performed ===")
        for region_name, region_info in regions.items():
            print(f"Would scrape {region_name} from {region_info['url']} using {region_info['type']} scraper")
        driver.quit()
        return
      # Output directory for combined results
    output_dir = "scholarship_data"
    # Store all CSV filenames
    all_csv_files = []
    
    try:
        # Process each region with the appropriate scraper
        for region_name, region_info in regions.items():
            start_time = time.time()
            url = region_info["url"]
            website_type = region_info["type"]
            
            print(f"\n==== Starting to scrape {region_name} ({website_type}) ====")
            try:
                if website_type == "scholarships_corner":
                    csv_filename = scrape_scholarships_corner(url, region_name, driver)
                elif website_type == "opportunities_corners":
                    csv_filename = scrape_opportunities_corners(url, region_name, driver)
                else:
                    print(f"Unknown website type: {website_type}")
                    continue
                    
                # Verify the file was created and properly returned
                if csv_filename is None or not os.path.exists(csv_filename):
                    print(f"⚠️ Warning: CSV file for {region_name} was not created or doesn't exist")
                    continue
                    
            except Exception as e:
                print(f"❌ Error scraping {region_name}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
                
            all_csv_files.append(csv_filename)
            
            elapsed_time = time.time() - start_time
            print(f"Completed {region_name} in {elapsed_time:.1f} seconds")
            
            # Short pause between regions
            time.sleep(2)        # Clean up any temporary files and see if we found additional files
        print("\n==== Checking for any unprocessed CSV files ====")
        all_csv_files = cleanup_temporary_files(all_csv_files)
        
        # Check if we have any CSV files to combine
        if not all_csv_files:
            print("⚠️ No CSV files were created during scraping")
        else:
            try:
                # Validate CSV files before combining
                valid_csv_files = []
                for csv_file in all_csv_files:
                    if os.path.exists(csv_file) and validate_csv_file(csv_file):
                        valid_csv_files.append(csv_file)
                    else:
                        print(f"⚠️ Skipping invalid file: {csv_file}")
                
                # Combine all valid CSV files into a master file
                print(f"\n==== Combining {len(valid_csv_files)} valid CSV files ====")
                combine_csv_files(valid_csv_files, output_dir)
            except Exception as e:
                print(f"❌ Error combining CSV files: {str(e)}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error in main process: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    main()
