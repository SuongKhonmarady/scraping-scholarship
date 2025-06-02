import mysql.connector
import pandas as pd
import numpy as np
from datetime import datetime
import re
import os
import glob
# Load environment variables
from dotenv import load_dotenv

def clean_date(date_str):
    """Convert various date string formats to MySQL date format YYYY-MM-DD"""
    if pd.isna(date_str) or not date_str or date_str.strip() == "":
        return None
        
    # Remove any "Apply Now" or "Official Link" text
    date_str = re.sub(r'Apply Now.*|Official Link.*', '', date_str, flags=re.IGNORECASE)
    
    # Try to extract date patterns
    patterns = [
        # Day Month Year formats
        r'(\d{1,2})(?:st|nd|rd|th)?\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*(\d{4})',
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})',
        
        # Year Month Day formats
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        r'(\d{4})\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*(\d{1,2})',
        
        # Month Year formats (assuming day 1)
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*(\d{4})'
    ]
    
    # Month name to number mapping
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    for pattern in patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                # For standard date formats, try parsing directly
                try:
                    date_obj = datetime.strptime(match.group(0), "%d %B %Y")
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    pass
                
                try:
                    date_obj = datetime.strptime(match.group(0), "%B %d %Y")
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    pass
                
                try:
                    date_obj = datetime.strptime(match.group(0), "%B %d, %Y")
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    pass
                    
                # For Year-Month-Day format
                if re.match(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', match.group(0)):
                    date_parts = re.split(r'[/-]', match.group(0))
                    return f"{date_parts[0]}-{int(date_parts[1]):02d}-{int(date_parts[2]):02d}"
                
                # For "Month Year" format (use 1st day of month)
                month_year_match = re.match(r'(\w+)\s+(\d{4})', match.group(0), re.IGNORECASE)
                if month_year_match:
                    month_name = month_year_match.group(1).lower()
                    year = month_year_match.group(2)
                    if month_name in month_map:
                        return f"{year}-{month_map[month_name]:02d}-01"
                
            except Exception as e:
                print(f"Date parsing error for '{date_str}': {str(e)}")
                
    return None

def create_table(cursor):
    """Create scholarships table if it doesn't exist"""
    # Check if table exists instead of dropping it
    # Removed: drop_table_sql = "DROP TABLE IF EXISTS scholarships;"
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS scholarships (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(500),
        description TEXT,
        link VARCHAR(500),
        official_link VARCHAR(500),
        deadline DATE,
        eligibility TEXT,
        host_country VARCHAR(100),
        host_university VARCHAR(200),
        program_duration VARCHAR(200),
        degree_offered VARCHAR(200),
        region VARCHAR(50),
        post_at DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX (title(255)),
        INDEX (link(255)),
        INDEX (region),
        INDEX (post_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    cursor.execute(create_table_sql)

def scholarship_exists(cursor, title, link):
    """
    Check if a scholarship already exists in the database
    Returns False if not exists, or the row ID if it exists
    """
    # Handle case where link is None or NaN
    if link is None:
        check_sql = """
        SELECT id FROM scholarships 
        WHERE title = %s
        """
        cursor.execute(check_sql, (title,))
    else:
        check_sql = """
        SELECT id FROM scholarships 
        WHERE title = %s OR link = %s
        """
        cursor.execute(check_sql, (title, link))
        
    result = cursor.fetchone()
    if result:
        return result[0]  # Return the id of existing scholarship
    return False

def process_csv_file(cursor, file_path):
    """Process a single CSV file and insert data into database"""
    print(f"\n📄 Processing: {os.path.basename(file_path)}")
    
    # Track statistics for this file
    total_rows = 0
    skipped_rows = 0
    inserted_rows = 0
    error_rows = 0
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Clean and prepare data
        for _, row in df.iterrows():
            total_rows += 1
            
            try:
                # Skip rows with empty titles
                if pd.isna(row['Title']) or row['Title'].strip() == "":
                    print(f"⚠️ Skipped row {total_rows} (no title)")
                    skipped_rows += 1
                    continue
                
                # Check if scholarship already exists
                # Make sure Link exists before using it
                link = row.get('Link')
                link = None if pd.isna(link) else link
                existing_id = scholarship_exists(cursor, row['Title'], link)
                if existing_id:
                    print(f"⏭️ Existing record found (id: {existing_id}): {row['Title'][:50]}...")
                    skipped_rows += 1
                    continue

                # Clean deadline date
                deadline = clean_date(row.get('Deadline', None))
                
                # Skip expired scholarships (those with a deadline in the past)
                today = datetime.today()
                post_at = None
                try:
                    if deadline:
                        deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                        
                        if deadline_date < today:
                            # Skip expired scholarships
                            print(f"📆 Skipping expired scholarship (deadline: {deadline}): {row['Title'][:50]}...")
                            skipped_rows += 1
                            continue
                        else:
                            # Deadline is in the future → post_at = today
                            post_at = today.strftime("%Y-%m-%d")
                            print(f"📆 Upcoming deadline {deadline}. Set post_at to today's date: {post_at}")
                    else:
                        # No deadline specified - include these per requirements
                        post_at = today.strftime("%Y-%m-%d")
                        print(f"📆 No deadline. Default post_at to today: {post_at}")
                except Exception as e:
                    print(f"⚠️ Failed to calculate post_at: {str(e)}")
                    post_at = today.strftime("%Y-%m-%d")

                # Get region from data or from filename
                try:
                    region = row.get('Region', None)
                    if region is None or pd.isna(region):
                        # Extract region from filename
                        filename = os.path.basename(file_path)
                        match = re.search(r'scholarships-(\w+)', filename)
                        if match:
                            region = match.group(1).replace('-', ' ').title()
                        else:
                            region = None  # Ensure region is None not NaN if extraction fails
                    # Ensure NaN is converted to None
                    region = None if pd.isna(region) else region
                except:
                    region = None
                
                # Prepare insert query
                insert_sql = """
                INSERT INTO scholarships (
                    title, description, link, official_link, deadline, 
                    eligibility, host_country, host_university, 
                    program_duration, degree_offered, region, post_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                
                # Handle missing values and pandas NaN values properly
                def safe_get(row, key, default=None):
                    """Get a value from the row, handling NaN cases"""
                    value = row.get(key, default)
                    # Convert pandas NaN to None for MySQL
                    return None if pd.isna(value) else value
                
                # Make absolutely sure all values are properly handled for MySQL
                # Convert any pandas NaN or numpy.nan to None
                title = None if pd.isna(row['Title']) else row['Title']  # Already checked above, but just to be safe
                description = safe_get(row, 'Description')
                link = safe_get(row, 'Link')
                official_link = safe_get(row, 'Official Link')
                eligibility = safe_get(row, 'Eligibility')
                host_country = safe_get(row, 'Host Country')
                host_university = safe_get(row, 'Host University')
                program_duration = safe_get(row, 'Program Duration')
                degree_offered = safe_get(row, 'Degree Offered')
                
                # Create data tuple with all properly sanitized values
                data = (
                    title, 
                    description,
                    link,
                    official_link,
                    deadline,
                    eligibility,
                    host_country, 
                    host_university,
                    program_duration,
                    degree_offered,
                    region,
                    post_at
                )
                
                try:
                    cursor.execute(insert_sql, data)
                    print(f"✅ Inserted: {row['Title'][:50]}...")
                except mysql.connector.Error as err:
                    # Print the error and the data that caused it
                    print(f"❌ MySQL Error: {str(err)}")
                    print(f"❌ Problematic data: {data}")
                    raise
                inserted_rows += 1
                
            except Exception as e:
                print(f"❌ Error processing row {total_rows}: {str(e)}")
                error_rows += 1
        
        return {
            'total': total_rows,
            'skipped': skipped_rows,
            'inserted': inserted_rows,
            'errors': error_rows
        }
        
    except Exception as e:
        print(f"❌ Error processing file {file_path}: {str(e)}")
        return {
            'total': 0,
            'skipped': 0,
            'inserted': 0,
            'errors': 1
        }

def main():
    load_dotenv()
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_DATABASE')
    }

    # Overall statistics
    stats = {
        'total_files': 0,
        'total_rows': 0,
        'total_skipped': 0,
        'total_inserted': 0,
        'total_errors': 0
    }

    try:
        # Connect to MySQL
        print("🔌 Connecting to MySQL database...")
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        print("🏗️ Setting up database table...")
        create_table(cursor)

        # Find all CSV files to process
        data_dir = "scholarship_data"  # Default directory from the scraper
        all_csv_files = []
        
        # First check if the combined file exists
        master_file = os.path.join(data_dir, "all_scholarships.csv")
        if os.path.exists(master_file):
            print(f"📦 Found master data file: {master_file}")
            all_csv_files = [master_file]
        else:
            # Otherwise, get all individual region files
            csv_pattern = os.path.join(data_dir, "*.csv")
            all_csv_files = glob.glob(csv_pattern)
            
            # If no files in the directory, look in current directory
            if not all_csv_files:
                all_csv_files = glob.glob("*.csv")
                
        print(f"🔍 Found {len(all_csv_files)} CSV files to process")
        
        if not all_csv_files:
            print("❌ No CSV files found! Please run the scraper first.")
            return
            
        # Process each file
        for file_path in all_csv_files:
            stats['total_files'] += 1
            file_stats = process_csv_file(cursor, file_path)
            
            # Update overall statistics
            stats['total_rows'] += file_stats['total']
            stats['total_skipped'] += file_stats['skipped']
            stats['total_inserted'] += file_stats['inserted']
            stats['total_errors'] += file_stats['errors']
            
            # Commit after each file to avoid large transactions
            conn.commit()

        # Final statistics
        print(f"\n📊 Upload Summary:")
        print(f"CSV files processed: {stats['total_files']}")
        print(f"Total scholarships records: {stats['total_rows']}")
        print(f"New scholarships inserted: {stats['total_inserted']}")
        print(f"Existing scholarships skipped: {stats['total_skipped']}")
        print(f"Errors encountered: {stats['total_errors']}")
        print("\n🎉 All data has been processed and uploaded to the database!")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
