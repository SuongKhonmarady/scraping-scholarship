"""
Check for duplicate scholarships in the scraped data
This script helps identify and remove duplicate scholarships from CSV files
"""
import csv
import os
import pandas as pd
from difflib import SequenceMatcher
import argparse
from datetime import datetime
import re

def similarity_score(a, b):
    """Calculate string similarity between two strings"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b).ratio()

def clean_title(title):
    """Clean and standardize scholarship titles for better comparison"""
    if not title:
        return ""
    
    # Convert to lowercase
    title = title.lower()
    
    # Remove year patterns like 2025/26, 2025-26, etc.
    title = re.sub(r'20\d{2}[-/]2?\d', '', title)
    title = re.sub(r'20\d{2}', '', title)
    
    # Remove common phrases that don't distinguish scholarships
    phrases_to_remove = [
        'fully funded', 'apply now', 'scholarship', 'scholarships', 
        'in', 'at', 'for', 'the', 'funded', 'full', 'free'
    ]
    
    for phrase in phrases_to_remove:
        title = title.replace(phrase, '')
    
    # Remove extra whitespace and parentheses content
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'\([^)]*\)', '', title)
    
    return title.strip()

def find_duplicates(csv_files, output_dir, similarity_threshold=0.85):
    """
    Find duplicate scholarships across multiple CSV files based on title similarity
    and other matching criteria.
    
    Args:
        csv_files: List of CSV files to check
        output_dir: Directory to store cleaned results
        similarity_threshold: Threshold for title similarity (0-1), higher means more strict matching
    
    Returns:
        DataFrame with all scholarships, with duplicates marked
    """
    print(f"Checking for duplicates across {len(csv_files)} files...")
    
    # Load all data into one dataframe
    all_data = []
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            # Add source file information
            df['source_file'] = os.path.basename(file_path)
            all_data.append(df)
            print(f"Loaded {len(df)} scholarships from {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    if not all_data:
        print("No data was loaded. Exiting.")
        return None
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Total scholarships loaded: {len(combined_df)}")
    
    # Add cleaned titles for comparison
    combined_df['cleaned_title'] = combined_df['Title'].apply(clean_title)
    
    # Initialize columns for duplicate detection
    combined_df['is_duplicate'] = False
    combined_df['duplicate_group'] = None
    
    # Find duplicates
    duplicate_count = 0
    duplicate_groups = 0
    
    # First group by exact cleaned_title matches
    title_groups = combined_df.groupby('cleaned_title')
    for title, group in title_groups:
        if len(group) > 1 and title:  # More than one scholarship with same cleaned title
            duplicate_groups += 1
            for idx in group.index:
                combined_df.loc[idx, 'is_duplicate'] = True
                combined_df.loc[idx, 'duplicate_group'] = f"group_{duplicate_groups}"
            duplicate_count += len(group) - 1
            
    # Then check for similar titles using similarity score
    # (This is more computationally expensive, but catches more duplicates)
    remaining_df = combined_df[~combined_df['is_duplicate']]
    
    for i, row in remaining_df.iterrows():
        if row['is_duplicate']:  # Skip if already marked as duplicate
            continue
            
        title1 = row['cleaned_title']
        if not title1:  # Skip empty titles
            continue
            
        similar_found = False
        
        # Compare with all other non-duplicate scholarships
        for j, compare_row in remaining_df.iterrows():
            if i == j or compare_row['is_duplicate']:
                continue
                
            title2 = compare_row['cleaned_title']
            if not title2:
                continue
                
            # Check similarity
            if similarity_score(title1, title2) > similarity_threshold:
                # Additional verification: check if deadlines or host universities match
                deadline_match = False
                university_match = False
                
                if row['Deadline'] and compare_row['Deadline'] and row['Deadline'] == compare_row['Deadline']:
                    deadline_match = True
                    
                if row['Host University'] and compare_row['Host University'] and similarity_score(row['Host University'], compare_row['Host University']) > 0.7:
                    university_match = True
                
                # Mark as duplicate if deadline or university also matches
                if deadline_match or university_match:
                    duplicate_groups += 1
                    combined_df.loc[i, 'is_duplicate'] = True
                    combined_df.loc[j, 'is_duplicate'] = True
                    combined_df.loc[i, 'duplicate_group'] = f"group_{duplicate_groups}"
                    combined_df.loc[j, 'duplicate_group'] = f"group_{duplicate_groups}"
                    duplicate_count += 1
                    similar_found = True
                    break
        
        if similar_found:
            # Skip remaining comparisons for this scholarship
            continue
    
    print(f"Found {duplicate_count} duplicates in {duplicate_groups} groups")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save the full dataframe with duplicate information
    duplicates_file = os.path.join(output_dir, f"duplicates_analysis_{timestamp}.csv")
    combined_df.to_csv(duplicates_file, index=False, encoding='utf-8')
    print(f"Full analysis saved to {duplicates_file}")
    
    # Create filtered dataset with just one instance of each scholarship
    filtered_df = pd.DataFrame()
    
    # Keep all non-duplicated scholarships
    non_duplicates = combined_df[~combined_df['is_duplicate']]
    filtered_df = pd.concat([filtered_df, non_duplicates], ignore_index=True)
    
    # For duplicates, keep just one from each group
    seen_groups = set()
    for _, row in combined_df[combined_df['is_duplicate']].iterrows():
        group = row['duplicate_group']
        if group and group not in seen_groups:
            filtered_df = pd.concat([filtered_df, pd.DataFrame([row])], ignore_index=True)
            seen_groups.add(group)
    
    # Sort by region and title
    filtered_df = filtered_df.sort_values(['Region', 'Title'])
    
    # Remove analysis columns before saving
    filtered_df = filtered_df.drop(columns=['cleaned_title', 'is_duplicate', 'duplicate_group'])
    
    cleaned_file = os.path.join(output_dir, f"scholarships_deduplicated_{timestamp}.csv")
    filtered_df.to_csv(cleaned_file, index=False, encoding='utf-8')
    print(f"Deduplicated data saved to {cleaned_file}")
    print(f"Removed {len(combined_df) - len(filtered_df)} duplicates")
    
    return combined_df

def analyze_file(file_path, output_dir='scholarship_data'):
    """Analyze a single CSV file for duplicate scholarships"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Run duplicate detection
    find_duplicates([file_path], output_dir)

def analyze_directory(dir_path, output_dir=None):
    """Analyze all CSV files in a directory for duplicate scholarships"""
    if not os.path.exists(dir_path):
        print(f"Directory not found: {dir_path}")
        return
        
    # Use the same directory for output if not specified
    if output_dir is None:
        output_dir = dir_path
        
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all CSV files in the directory
    csv_files = [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith('.csv')]
    
    if not csv_files:
        print(f"No CSV files found in {dir_path}")
        return
        
    # Run duplicate detection
    find_duplicates(csv_files, output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for duplicate scholarships in CSV files")
    parser.add_argument("--file", help="Path to a specific CSV file to analyze")
    parser.add_argument("--dir", help="Path to directory containing CSV files")
    parser.add_argument("--output", help="Output directory for results")
    parser.add_argument("--threshold", type=float, default=0.85, 
                        help="Similarity threshold (0-1) for duplicate detection")
    
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        # Default: analyze the scholarship_data directory
        print("No file or directory specified. Using default scholarship_data directory.")
        analyze_directory("scholarship_data")
    elif args.file:
        analyze_file(args.file, args.output or "scholarship_data")
    elif args.dir:
        analyze_directory(args.dir, args.output)
