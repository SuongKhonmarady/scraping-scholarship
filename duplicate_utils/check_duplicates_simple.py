"""
Standalone script to check for duplicates in scholarship data
"""
import os
import sys
import argparse
from .duplicate_checker import DuplicateChecker
import csv
import pandas as pd

def check_duplicates_in_file(input_file, output_dir=None):
    """Check for duplicates in a single CSV file"""
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return
    
    # Set default output directory if not provided
    if not output_dir:
        output_dir = os.path.dirname(input_file) or "."
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize the duplicate checker
    checker = DuplicateChecker()
    
    # Load the CSV file
    try:
        with open(input_file, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            
            # Keep track of rows for output
            all_rows = []
            unique_rows = []
            duplicate_rows = []
            
            # Process each scholarship
            for row in reader:
                all_rows.append(row)
                
                # Check if it's a duplicate
                if checker.add_scholarship(row):
                    unique_rows.append(row)
                else:
                    duplicate_rows.append(row)
    
    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return
    
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Write unique scholarships to a new file
    unique_file = os.path.join(output_dir, f"{base_name}_unique.csv")
    with open(unique_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in unique_rows:
            writer.writerow(row)
    
    # Write duplicate scholarships to a separate file
    if duplicate_rows:
        duplicate_file = os.path.join(output_dir, f"{base_name}_duplicates.csv")
        with open(duplicate_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in duplicate_rows:
                writer.writerow(row)
    
    # Get statistics
    stats = checker.get_stats()
    
    print(f"\n🔍 Duplicate check completed for {input_file}")
    print(f"📊 Statistics:")
    print(f"   - Total scholarships: {stats['total_processed']}")
    print(f"   - Duplicates found: {stats['duplicates_found']}")
    print(f"   - Unique scholarships: {stats['unique_scholarships']}")
    print(f"📂 Results saved to:")
    print(f"   - {unique_file} (Unique scholarships)")
    if duplicate_rows:
        print(f"   - {duplicate_file} (Duplicate scholarships)")

def main():
    """Main function to parse arguments and run the script"""
    parser = argparse.ArgumentParser(description="Check for duplicate scholarships in CSV files")
    parser.add_argument("input", help="Path to CSV file containing scholarship data")
    parser.add_argument("--output", help="Output directory for results (default: same as input)")
    
    args = parser.parse_args()
    
    check_duplicates_in_file(args.input, args.output)

if __name__ == "__main__":
    main()
