#!/usr/bin/env python
"""
Test script to verify that all imports work correctly
"""
import sys
import os
import traceback
import importlib

# Print current working directory and system path
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Test importing from modules
def test_import(module_name, import_statement):
    print(f"\nTesting import: {import_statement}")
    try:
        exec(import_statement)
        print(f"✅ Successfully imported {module_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to import {module_name}: {str(e)}")
        traceback.print_exc()
        return False

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test all our imports
imports = [
    ("main module", "from main.scrap_main import main"),
    ("scrapers package", "from scrapers import scrape_scholarships_corner, scrape_opportunities_corners"),
    ("duplicate_utils package", "from duplicate_utils import DuplicateChecker"),
    ("main.scrap_main direct", "from main.scrap_main import main as scrap_main"),
    ("scrapers direct", "from scrapers.scrape_scholarships_corner import scrape_scholarships_corner"),
    ("duplicate_checker direct", "from duplicate_utils.duplicate_checker import DuplicateChecker"),
]

success_count = 0
for module_name, import_statement in imports:
    if test_import(module_name, import_statement):
        success_count += 1

print(f"\n==== Import test results: {success_count}/{len(imports)} successful ====")

if __name__ == "__main__":
    print("\nIf all imports are successful, the project structure is correct!")
