# ScholarTrack File Structure & Usage Guide

## File Organization

### 📁 Main Files Structure

```
Srcaping Scholarship/
├── run_scraper.py              # ✅ MAIN ENTRY POINT - Use this to run scraping
├── scrapData.py               # ✅ Updated with slug - Standalone scraper
├── db_upload.py               # ✅ Updated with slug - Database upload script
├── main/
│   ├── scrap_main.py          # ✅ Main orchestrator (called by run_scraper.py)
│   └── scrapData.py           # ✅ Updated with slug - Module version
└── other files...
```

## Which File to Use?

### 🚀 **For Running the Scraper:**
**Use: `run_scraper.py`**
```bash
python run_scraper.py
```

This file:
- Imports from `main/scrap_main.py`
- Provides a clean entry point
- Handles command-line arguments
- Manages error handling

### 🔧 **File Relationships:**

1. **`run_scraper.py`** → calls → **`main/scrap_main.py`**
2. **`main/scrap_main.py`** → uses → **`main/scrapData.py`** (and other modules)
3. **`scrapData.py`** → standalone version (can run independently)

## Slug Implementation Status

### ✅ **Updated Files (WITH slug functionality):**
- `scrapData.py` (standalone version)
- `main/scrapData.py` (module version)  
- `db_upload.py` (database upload)
- `test_slug_generation.py` (testing)

### 📋 **What Each File Does:**

#### `run_scraper.py`
- **Purpose**: Main entry point for the application
- **Usage**: `python run_scraper.py`
- **Function**: Calls the main scraping orchestrator

#### `main/scrap_main.py`
- **Purpose**: Main orchestrator that coordinates all scraping activities
- **Function**: Manages multiple scrapers, duplicate detection, file handling
- **Usage**: Called by `run_scraper.py`

#### `scrapData.py` (root level)
- **Purpose**: Standalone scraper that can run independently
- **Function**: Direct scraping with slug generation
- **Usage**: `python scrapData.py` (if you want to run it directly)

#### `main/scrapData.py`
- **Purpose**: Module version used by the main orchestrator
- **Function**: Same as standalone but designed as a module
- **Usage**: Imported by `main/scrap_main.py`

#### `db_upload.py`
- **Purpose**: Handles uploading scraped data to MySQL database
- **Function**: Reads CSV files, processes data, uploads to database
- **Features**: Slug generation, duplicate detection, data validation

## Recommended Workflow

### 1. **Run Scraping:**
```bash
python run_scraper.py
```

### 2. **Upload to Database:**
```bash
python db_upload.py
```

### 3. **Test Slug Generation:**
```bash
python test_slug_generation.py
```

## Key Features Added

### 🎯 **Slug Generation:**
- Removes marketing words ("apply now", "fully funded", etc.)
- Removes years and year ranges (2024, 2025/26, etc.)
- Creates SEO-friendly URLs
- Ensures uniqueness in database

### 📊 **Example Results:**
```
"Rhodes Scholarship 2025/26 - Apply Now" → "rhodes-scholarship"
"DAAD Scholarship Germany 2024/25" → "daad-scholarship-germany"
"Chevening Scholarships 2025 - Fully Funded" → "chevening-scholarships"
```

## Database Schema

The database now includes:
```sql
CREATE TABLE scholarships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500),
    slug VARCHAR(150),        -- NEW: SEO-friendly URL slug
    description TEXT,
    -- ... other fields ...
    UNIQUE INDEX unique_slug (slug)
);
```

## Usage Tips

1. **Always use `run_scraper.py`** as your main entry point
2. **Both scrapData.py versions are now updated** with slug functionality
3. **Database upload handles both old and new CSV formats** (with/without slug)
4. **Slugs are automatically generated** if missing from CSV files
5. **Uniqueness is guaranteed** through database constraints

This structure ensures consistency while maintaining backward compatibility!
