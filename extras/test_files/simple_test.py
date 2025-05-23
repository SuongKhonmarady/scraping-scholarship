#!/usr/bin/env python
"""
Simple script to test importing main function
"""
import sys
import os
import traceback

# Get the directory containing this script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the parent directory to sys.path
sys.path.append(current_dir)

print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

try:
    print("Importing main.scrap_main...")
    import main.scrap_main
    print("Success!")
    
    print("Accessing main function...")
    main_function = main.scrap_main.main
    print(f"Type of main function: {type(main_function)}")
    
    print("\nRunning main function with dry_run=True...")
    main_function(dry_run=True)
    
except Exception as e:
    print(f"Error: {str(e)}")
    traceback.print_exc()
