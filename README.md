# Scholarship Data Scraper

A tool for scraping scholarship data from multiple websites, with duplicate detection and data cleaning.

## Project Structure

```
scholarship-scraper/
│
├── run_scraper.py               # Main entry point for running the scraper
├── scrap_main.py                # Legacy entry point (use run_scraper.py instead)
├── verify_csv_files.py          # Tool for checking and repairing CSV files
│
├── main/                        # Main package containing core functionality
│   ├── __init__.py
│   ├── scrap_main.py            # Core scraping logic and workflow
│   └── scrapData.py             # Legacy support file
│
├── scrapers/                    # Website-specific scraper implementations
│   ├── __init__.py
│   ├── scrape_scholarships_corner.py    # ScholarshipsCorner.website scraper
│   └── scrape_opportunities_corners.py  # OpportunitiesCorners.com scraper
│
├── duplicate_utils/             # Utilities for duplicate detection
│   ├── __init__.py
│   ├── duplicate_checker.py     # Core duplicate detection logic
│   ├── check_duplicates.py      # Advanced duplicate checking script
│   └── check_duplicates_simple.py # Simple duplicate checking script
│
├── utils/                       # General utility functions
│   ├── __init__.py
│   └── file_utils.py            # File handling utilities
│
├── scholarship_data/            # Output directory for scraped data
│   ├── all_scholarships.csv     # Combined dataset including duplicates
│   ├── unique_scholarships.csv  # Dataset with duplicates removed
│   └── scholarships-*.csv       # Individual scrapes by region
│
└── test_*.py                    # Test scripts for verifying functionality
```

## Usage

### Basic Usage

To run the scraper:

```bash
python run_scraper.py
```

### Dry Run

To see what would be scraped without performing actual scraping:

```bash
python run_scraper.py --dry-run
```

### CSV Verification and Repair

To verify and repair any corrupted CSV files:

```bash
python verify_csv_files.py
```

You can also specify a directory to scan:

```bash
python verify_csv_files.py --dir=scholarship_data
```

### Configuration

Edit `main/scrap_main.py` to change which regions and websites are scraped.

## Data Extracted

For each scholarship, the following data is extracted:
- Title
- Link
- Description
- Deadline
- Host Country
- Host University
- Program Duration

## Duplicate Detection

The system uses advanced text similarity algorithms to detect and remove duplicate scholarships across different sources. The duplicate detection can be configured by adjusting the similarity threshold in the code.

## File Handling

The system includes several features to ensure robust file handling:

1. **Automatic File Backup**: When overwriting existing files, the system creates backups with timestamps.
2. **Unique Filename Generation**: When output files already exist, the system generates unique filenames with timestamps.
3. **CSV Validation**: All generated CSV files are validated to ensure they contain proper data.
4. **Error Recovery**: If any errors occur during file operations, the system attempts to recover and continue processing.
5. **CSV Repair Tool**: The `verify_csv_files.py` script can scan and attempt to repair corrupted CSV files.

## Development

### Testing

Run the import test to verify that all modules can be imported correctly:

```bash
python test_imports.py
```

Run the integration test to verify the system works as expected:

```bash
python test_integration.py
```
