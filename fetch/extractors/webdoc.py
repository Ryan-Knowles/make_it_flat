"""
Extractor functions for Webdoc documentation.
"""
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def is_webdoc_generated(soup):
    """
    Check if the HTML was generated by Webdoc.
    
    Args:
        soup: BeautifulSoup object of the HTML page
        
    Returns:
        bool: True if the page was generated by Webdoc, False otherwise
    """
    # Look for the Webdoc link in footer
    webdoc_links = soup.find_all('a', href=lambda href: href and 'webdoc-js/webdoc' in href)
    if webdoc_links:
        for link in webdoc_links:
            # Check if the link text contains "Webdoc"
            if 'Webdoc' in link.text:
                # Check if it's in a footer context with "Documentation generated by"
                footer_div = link.find_parent('div')
                if footer_div and "Documentation generated by" in footer_div.text:
                    return True
                    
    # Alternative detection if footer isn't found
    footer = soup.find('footer', {'class': 'content-size'})
    if footer and 'Webdoc' in footer.text and 'Documentation generated by' in footer.text:
        return True
        
    return False

def extract_navigation_links(soup):
    """
    Extract navigation links from a Webdoc documentation page.
    
    Args:
        soup: BeautifulSoup object of the HTML page
        
    Returns:
        list: List of navigation link URLs
    """
    links = []
    
    # Try to find navigation section - adjust selectors based on actual structure
    navigation = soup.find('nav') or soup.find('div', {'class': 'navigation'})
    if navigation:
        for link in navigation.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith('#') and not href.startswith('javascript:'):
                links.append(href)
    
    # If no dedicated navigation, look for links in sidebar or menu
    if not links:
        sidebar = soup.find('div', {'class': ['sidebar', 'menu', 'side-nav']})
        if sidebar:
            for link in sidebar.find_all('a', href=True):
                href = link.get('href')
                if href and not href.startswith('#') and not href.startswith('javascript:'):
                    links.append(href)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
            
    return unique_links

def extract_main_content(soup) -> str:
    """
    Extract the main content from a Webdoc documentation page.
    
    Args:
        soup: BeautifulSoup object of the HTML page
        
    Returns:
        str: Main content as text
    """
    # Try different selectors that might contain the main content
    main_selectors = [
        'div.main',
    ]
    
    main_content = None
    for selector in main_selectors:
        tag, *classes = selector.split('.')
        if classes:
            main_content = soup.find(tag, {'class': classes})
        else:
            main_content = soup.find(tag)
            
        if main_content:
            break
    
    # If none of the specific selectors worked, try more generic approach
    if not main_content:
        # Exclude header, footer, nav, sidebar elements
        body = soup.find('body')
        if body:
            for header in body.find_all(['header', 'footer', 'nav']):
                header.decompose()
            for sidebar in body.find_all(class_=lambda c: c and ('sidebar' in c or 'menu' in c or 'nav' in c)):
                sidebar.decompose()
            main_content = body
    
    if main_content:
        # Process content to clean it up
        for script in main_content.find_all('script'):
            script.decompose()
        for style in main_content.find_all('style'):
            style.decompose()
        for footer in main_content.find_all('footer'):
            footer.decompose()
            
        # Convert to text
        return str(main_content).strip()
    
    # Fallback to body text if nothing else works
    return str(soup).strip()