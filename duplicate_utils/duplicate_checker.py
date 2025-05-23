"""
Helper module to detect and handle duplicate scholarships during the scraping process
This can be integrated into the main workflow to prevent duplicates
"""
from difflib import SequenceMatcher
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

class DuplicateChecker:
    """Class to check for duplicate scholarships during scraping"""
    
    def __init__(self, similarity_threshold=0.85):
        """
        Initialize the duplicate checker
        
        Args:
            similarity_threshold: Threshold for title similarity (0-1)
        """
        self.scholarships = []
        self.similarity_threshold = similarity_threshold
        self.duplicate_count = 0
    
    def is_duplicate(self, scholarship):
        """
        Check if a scholarship is a duplicate of previously seen scholarships
        
        Args:
            scholarship: Dictionary containing scholarship information
            
        Returns:
            bool: True if it's a duplicate, False otherwise
        """
        # Clean the title for better comparison
        title = clean_title(scholarship.get('Title', ''))
        
        if not title:
            return False
        
        # First check for exact title matches
        for existing in self.scholarships:
            existing_title = clean_title(existing.get('Title', ''))
            if title == existing_title:
                self.duplicate_count += 1
                return True
        
        # Then check for similar titles with additional criteria
        for existing in self.scholarships:
            existing_title = clean_title(existing.get('Title', ''))
            
            # Skip if titles aren't similar enough
            if similarity_score(title, existing_title) < self.similarity_threshold:
                continue
                
            # Additional verification to confirm it's truly a duplicate
            # Check if deadlines match
            if scholarship.get('Deadline') and existing.get('Deadline'):
                if scholarship['Deadline'] == existing['Deadline']:
                    self.duplicate_count += 1
                    return True
            
            # Check if host universities match
            if scholarship.get('Host University') and existing.get('Host University'):
                uni_similarity = similarity_score(
                    scholarship['Host University'], 
                    existing['Host University']
                )
                if uni_similarity > 0.7:  # 70% similarity threshold for university names
                    self.duplicate_count += 1
                    return True
            
            # Check if host countries and deadlines are both similar enough
            if (scholarship.get('Host Country') and existing.get('Host Country') and
                scholarship.get('Deadline') and existing.get('Deadline')):
                
                country_similarity = similarity_score(
                    scholarship['Host Country'], 
                    existing['Host Country']
                )
                
                deadline_similarity = similarity_score(
                    scholarship['Deadline'], 
                    existing['Deadline']
                )
                
                if country_similarity > 0.8 and deadline_similarity > 0.6:
                    self.duplicate_count += 1
                    return True
        
        return False
    
    def add_scholarship(self, scholarship):
        """
        Add a scholarship to the tracked list
        
        Args:
            scholarship: Dictionary containing scholarship information
            
        Returns:
            bool: True if it was added (not a duplicate), False if it was a duplicate
        """
        if self.is_duplicate(scholarship):
            return False
        
        self.scholarships.append(scholarship)
        return True
    
    def get_stats(self):
        """Get statistics about tracked scholarships"""
        return {
            "total_processed": len(self.scholarships) + self.duplicate_count,
            "duplicates_found": self.duplicate_count,
            "unique_scholarships": len(self.scholarships)
        }

# Example of how to use this in a script
if __name__ == "__main__":
    # Example usage
    checker = DuplicateChecker()
    
    scholarship1 = {
        "Title": "DAAD Scholarship in Germany 2025 (Fully Funded)",
        "Deadline": "March 15, 2025",
        "Host Country": "Germany",
        "Host University": "Berlin University"
    }
    
    scholarship2 = {
        "Title": "Fully Funded DAAD Germany Scholarship (Apply Now)",
        "Deadline": "March 15, 2025",
        "Host Country": "Germany",
        "Host University": "Berlin University"
    }
    
    scholarship3 = {
        "Title": "Erasmus Mundus Scholarship 2025 in France",
        "Deadline": "May 30, 2025",
        "Host Country": "France",
        "Host University": "Sorbonne University"
    }
    
    print(f"Adding scholarship1: {'Added' if checker.add_scholarship(scholarship1) else 'Duplicate'}")
    print(f"Adding scholarship2: {'Added' if checker.add_scholarship(scholarship2) else 'Duplicate'}")
    print(f"Adding scholarship3: {'Added' if checker.add_scholarship(scholarship3) else 'Duplicate'}")
    
    print("Stats:", checker.get_stats())
