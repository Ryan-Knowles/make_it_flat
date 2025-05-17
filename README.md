# Documentation Scraper

A flexible documentation scraping tool that converts online documentation to a standardized Markdown format, optimized for various documentation systems including Webdoc.

## Overview

This tool:

- Fetches documentation pages from a URL
- Detects documentation type (Webdoc, etc.)
- Extracts main content and navigation links
- Converts HTML content to Markdown
- Saves in a standardized format with timestamps
- Creates files in a proper directory structure

## Project Structure

```
make_it_flat/
├── data/                      # Output directory for scraped docs
│   └── <domain_name>/         # Subdirectories organized by domain
│       └── api_YYYY_MM_DD.md  # Output files with timestamps
├── fetch/                     # Main source code
│   ├── extractors/            # Content extraction modules
│   │   ├── __init__.py        # Extractor selection logic
│   │   └── webdoc.py          # Webdoc-specific extractor
│   ├── main.py                # Main script
│   ├── requirements.txt       # Dependencies
│   └── .python-version        # Python version specification
└── .cursor/                   # Cursor editor settings
    └── rules/                 # Custom rules for Cursor
        └── scraped-doc-format.mdc  # Documentation format rules
```

## Setup

1. **Requirements**

   - Python 3.12.2 or later
   - Virtual environment (`uv` recommended)

2. **Installation**

```bash
# Create and activate virtual environment
cd fetch
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

## Usage

Run the script with a URL to start scraping:

```bash
python main.py -u https://example.com/docs
```

### Command Line Options

- `-u, --url` (required): URL to fetch content from
- `-d, --delay`: Delay in seconds between requests (default: 1.0)
- `-m, --max-pages`: Maximum number of pages to scrape (default: all)

### Example

```bash
# Scrape first 10 pages with 2 second delay
python main.py -u https://pixijs.download/release/docs/index.html -d 2 -m 10
```

## Output Format

The scraped content is saved in a standardized format:

```
----
Created: YYYY-MM-DD:HH:MM:SS
Extractor: webdoc
----
https://example.com/docs/page
----
Content in Markdown format
----
https://example.com/docs/next-page
----
Content of next page
----
```

Output files are saved to the `/data/<domain_name>/` directory with filenames in the format `api_YYYY_MM_DD.md`.

## Extending

To add support for a new documentation format:

1. Create a new extractor module in `fetch/extractors/`
2. Implement detection, content extraction, and link extraction functions
3. Register the extractor in `fetch/extractors/__init__.py`
