#!/usr/bin/env python3
import argparse
import requests
import sys
import time
import re
import io
import tempfile
import os
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin
from markitdown import MarkItDown, DocumentConverterResult
from bs4 import BeautifulSoup
from extractors import get_extractors, is_supported_doc_type, detect_doc_type

def fetch_url(url) -> requests.Response:
    """Fetch content from a URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        sys.exit(1)

def format_timestamp() -> str:
    """Return current timestamp in YYYY-MM-DD:hh:mm:ss format."""
    return f"{datetime.now().strftime('%Y-%m-%d:%H:%M:%S')}"

def save_to_file(content, output_file, mode='w'):
    """Save content to the specified output file."""
    try:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, mode, encoding='utf-8') as f:
            f.write(content)
    except IOError as e:
        print(f"Error saving to file: {e}", file=sys.stderr)
        sys.exit(1)

def get_output_path(url, title=None):
    """
    Generate appropriate output path based on URL according to conventions.
    
    Args:
        url: The URL of the scraped content
        title: Optional title to use in filename
        
    Returns:
        str: Path to save the content to
    """
    parsed_url = urlparse(url)
    
    # Extract domain and replace dots with underscores
    domain = parsed_url.netloc.replace('.', '_')
    
    # Generate the filename with current date in YYMMDD format
    current_date = datetime.now().strftime("%Y_%m_%d")
    filename = f"api_{current_date}.md"
    
    # Combine into full path
    output_path = Path('../data') / domain / filename
    
    return output_path

def normalize_url(url):
    """
    Normalize a URL to avoid duplicates by removing trailing slashes and fragments.
    
    Args:
        url: The URL to normalize
        
    Returns:
        str: Normalized URL
    """
    # Parse the URL
    parsed = urlparse(url)
    
    # Reconstruct without fragments
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    # Remove trailing slashes
    while normalized.endswith('/'):
        normalized = normalized[:-1]
        
    # Add query parameters if present
    if parsed.query:
        normalized += f"?{parsed.query}"
        
    return normalized

def scrape_page(url, base_url=None, content_extractor=None):
    """Scrape a page and return its content."""
    if base_url and not url.startswith(('http://', 'https://')):
        # Handle relative URLs using urljoin for proper URL joining
        full_url = urljoin(base_url, url)
    else:
        full_url = url
    
    resp = fetch_url(full_url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Try to get the title
    title_tag = soup.find('title')
    title = title_tag.text if title_tag else None
    
    # Use the provided content extractor or get one based on document type
    if content_extractor is None:
        content_extractor, _ = get_extractors(soup)
    
    # Get the main content as HTML
    html_content = content_extractor(soup)
    html_content = "<html><body>" + html_content + "</body></html>"

    
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(suffix='.html', mode='w', encoding='utf-8', delete=False) as temp_file:
        temp_file_path = temp_file.name
        temp_file.write(html_content)
    
    try:
        # Convert HTML file to markdown using MarkItDown
        md = MarkItDown(enable_plugins=False)
        result: DocumentConverterResult = md.convert_local(temp_file_path)
        markdown_content = result.markdown
        markdown_content = markdown_content.replace("<S>", "\\<S>")
        markdown_content = markdown_content.replace("<s>", "\\<s>")
    except Exception as e:
        print(f"Error converting HTML to markdown: {e}", file=sys.stderr)
        # Fall back to original HTML content if conversion fails
        markdown_content = html_content
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except Exception:
            pass  # Ignore errors during cleanup
    
    return {
        "url": full_url,
        "content": markdown_content,
        "title": title
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch content from a URL and save to a file")
    parser.add_argument("-u", "--url", required=True, help="URL to fetch content from")
    parser.add_argument("-d", "--delay", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument("-m", "--max-pages", type=int, help="Maximum number of pages to scrape")
    
    args = parser.parse_args()
    
    # Track scraped URLs to avoid duplicates
    scraped_urls = set()
    
    # Normalize initial URL
    initial_url = normalize_url(args.url)
    scraped_urls.add(initial_url)
    
    # Get initial page
    print(f"Fetching initial page: {initial_url}")
    resp = fetch_url(initial_url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    doc_type = detect_doc_type(soup)
    if doc_type:
        print(f"Detected documentation type: {doc_type}")
        extractor_type = doc_type
    else:
        print("Unknown documentation type. Using default extractors.")
        extractor_type = "generic"
    
    # Get the appropriate extractors for this document type
    content_extractor, link_extractor = get_extractors(soup)
    
    # Extract navigation links and normalize them
    raw_links = link_extractor(soup)
    
    # Normalize all links to avoid duplicates
    links = []
    for link in raw_links:
        if not link.startswith(('http://', 'https://')):
            full_link = urljoin(initial_url, link)
        else:
            full_link = link
        
        normalized_link = normalize_url(full_link)
        
        # Only add if we haven't seen this URL before
        if normalized_link not in scraped_urls:
            links.append(full_link)
            
    print(f"Found {len(links)} unique navigation links")
    
    # Initialize output file with timestamp and first page
    initial_page = scrape_page(initial_url, content_extractor=content_extractor)
    timestamp = format_timestamp()
    
    # Determine output path based on URL and title
    output_path = get_output_path(initial_url, initial_page.get("title"))
    print(f"Saving documentation to: {output_path}")
    
    content = f"""----

Created: {timestamp}
Extractor: {extractor_type}

----

{initial_page['url']}

----

{initial_page['content']}

----
"""
    save_to_file(content, output_path)
    print(f"[1/{len(links)+1}] Scraped: {initial_url}")
    
    # Process all navigation links
    max_pages = args.max_pages if args.max_pages else len(links)
    for i, link in enumerate(links[:max_pages], 2):
        try:
            # Normalize the URL before scraping
            normalized_link = normalize_url(link)
            
            # Skip if we've already scraped this URL
            if normalized_link in scraped_urls:
                print(f"[{i}/{min(len(links)+1, max_pages+1)}] Skipping already scraped: {link}")
                continue

            # Add delay between requests
            time.sleep(args.delay)
                
            # Mark as scraped
            scraped_urls.add(normalized_link)
            
            page_data = scrape_page(link, initial_url, content_extractor)
            page_content = f"""
{page_data['url']}

----

{page_data['content']}

----
"""
            # Append to the file
            save_to_file(page_content, output_path, mode='a')
            print(f"[{i}/{min(len(links)+1, max_pages+1)}] Scraped: {link}")
        except Exception as e:
            print(f"Error scraping {link}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main() 