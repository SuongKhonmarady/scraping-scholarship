"""
Utility functions for file operations
"""
import os
import datetime
import time
import shutil
import csv
import pandas as pd

def generate_timestamped_filename(base_filename):
    """
    Generate a filename with timestamp to avoid conflicts.
    
    Args:
        base_filename: The original filename
    
    Returns:
        A new filename with timestamp inserted before extension
    """
    # Extract base name and extension
    base_name, extension = os.path.splitext(base_filename)
    
    # Generate a timestamp in a readable format
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create new filename
    return f"{base_name}-{timestamp}{extension}"

def ensure_file_can_be_created(file_path, create_unique=True, overwrite=False):
    """
    Ensure that a file can be created at the specified path.
    
    Args:
        file_path: Path where the file should be created
        create_unique: If True and file exists, create a unique path with timestamp
        overwrite: If True and file exists, delete the existing file
        
    Returns:
        The file path (possibly modified with timestamp) where the file can be created
    """
    if not os.path.exists(file_path):
        # Make sure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        return file_path
        
    if overwrite:
        try:
            os.remove(file_path)
            return file_path
        except Exception as e:
            print(f"⚠️ Could not overwrite {file_path}: {e}")
            # Fall back to creating unique filename
            
    if create_unique:
        return generate_timestamped_filename(file_path)
    
    # If we can't create a file, return None
    return None

def validate_csv_file(csv_file_path):
    """
    Validate that a CSV file exists and is readable.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        True if file is valid, False otherwise
    """
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file {csv_file_path} does not exist")
        return False
        
    try:
        # Attempt to read the file with pandas which is more robust
        df = pd.read_csv(csv_file_path)
        if len(df) == 0:
            print(f"⚠️ CSV file {csv_file_path} is empty (header only)")
            return False
        return True
    except Exception as e:
        print(f"❌ CSV file {csv_file_path} is not valid: {str(e)}")
        return False

def create_backup(file_path):
    """
    Create a backup of a file with timestamp.
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        Path to the backup file or None if backup failed
    """
    if not os.path.exists(file_path):
        return None
        
    try:
        backup_path = generate_timestamped_filename(f"{file_path}.bak")
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup of {file_path}: {str(e)}")
        return None

def verify_and_repair_csv(csv_file_path):
    """
    Verify a CSV file for integrity and attempt to repair it if needed.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        Tuple of (is_valid, fixed_file_path) 
        - is_valid: True if file was valid or was fixed, False otherwise
        - fixed_file_path: Path to the fixed file if repairs were made, original path if already valid, None if couldn't fix
    """
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file {csv_file_path} does not exist")
        return (False, None)
        
    try:
        # First try reading with pandas
        df = pd.read_csv(csv_file_path)
        if len(df) > 0:
            return (True, csv_file_path)  # File is valid
        else:
            print(f"⚠️ CSV file {csv_file_path} is empty (header only)")
            return (False, None)
    except Exception as e:
        print(f"⚠️ CSV file {csv_file_path} has issues: {str(e)}")
        print(f"Attempting to repair {csv_file_path}...")
        
        try:
            # Create a backup of the corrupted file
            backup_path = create_backup(csv_file_path)
            if not backup_path:
                print(f"❌ Could not create backup of corrupted file")
                return (False, None)
                
            # Try to read the file with more lenient settings
            with open(csv_file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                
            # Try to fix common issues:
            # 1. Remove any null bytes
            content = content.replace('\0', '')
            
            # 2. Ensure the file ends with a newline
            if not content.endswith('\n'):
                content += '\n'
                
            # 3. Remove any corrupted lines (lines with wrong number of fields)
            lines = content.split('\n')
            if len(lines) > 1:
                header = lines[0]
                expected_commas = header.count(',')
                
                # Keep only lines with the right number of fields
                valid_lines = [header]
                for i in range(1, len(lines)):
                    if lines[i] and lines[i].count(',') == expected_commas:
                        valid_lines.append(lines[i])
                    elif lines[i]:
                        print(f"Removing corrupted line {i+1}: {lines[i][:50]}...")
                
                # Write the fixed content
                fixed_path = csv_file_path + ".fixed"
                with open(fixed_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(valid_lines))
                    
                # Verify the fixed file
                try:
                    df = pd.read_csv(fixed_path)
                    
                    # Replace the original with the fixed version
                    os.remove(csv_file_path)
                    os.rename(fixed_path, csv_file_path)
                    print(f"✅ Successfully repaired {csv_file_path}")
                    return (True, csv_file_path)
                except:
                    print(f"❌ Could not repair {csv_file_path}")
                    return (False, None)
            else:
                print(f"❌ File has too few lines to repair")
                return (False, None)
        except Exception as repair_error:
            print(f"❌ Error during repair: {str(repair_error)}")
            return (False, None)
