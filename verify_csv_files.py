#!/usr/bin/env python
"""
CSV Verification and Repair Tool

This script checks all CSV files in the current directory and subdirectories
for integrity issues and attempts to repair any corrupted files.

Usage:
    python verify_csv_files.py [--dir=<directory>]

Options:
    --dir=<directory>   Directory to scan for CSV files (default: current directory)
"""

import os
import argparse
import glob
import sys

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.file_utils import verify_and_repair_csv
except ImportError:
    print("❌ Could not import the file_utils module")
    print("Make sure this script is run from the main project directory")
    sys.exit(1)

def verify_csv_files(directory="."):
    """
    Scan a directory for CSV files and verify/repair them
    
    Args:
        directory: Directory to scan for CSV files
    """
    print(f"Scanning directory: {directory}")
    
    # Find all CSV files in the directory and subdirectories
    csv_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    
    print(f"Found {len(csv_files)} CSV files to check")
    
    valid_count = 0
    repaired_count = 0
    failed_count = 0
    
    for csv_file in csv_files:
        print(f"\nChecking {csv_file}...")
        is_valid, fixed_path = verify_and_repair_csv(csv_file)
        
        if is_valid and fixed_path == csv_file:
            print(f"✅ {csv_file} is valid")
            valid_count += 1
        elif is_valid:
            print(f"✅ {csv_file} has been repaired")
            repaired_count += 1
        else:
            print(f"❌ {csv_file} could not be verified or repaired")
            failed_count += 1
    
    print("\n=== CSV File Verification Summary ===")
    print(f"Total files checked: {len(csv_files)}")
    print(f"Valid files: {valid_count}")
    print(f"Repaired files: {repaired_count}")
    print(f"Failed files: {failed_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify and repair CSV files")
    parser.add_argument("--dir", default=".", help="Directory to scan (default: current directory)")
    args = parser.parse_args()
    
    verify_csv_files(args.dir)
