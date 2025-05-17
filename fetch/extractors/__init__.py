"""
Extractors package for handling different documentation formats.
"""
from typing import Callable, Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

# Import all available extractors
from .webdoc import (
    is_webdoc_generated, 
    extract_main_content as webdoc_extract_main_content,
    extract_navigation_links as webdoc_extract_navigation_links
)

# Type definitions for extractor functions
ContentExtractorFunc = Callable[[BeautifulSoup], str]
LinkExtractorFunc = Callable[[BeautifulSoup], List[str]]
DetectorFunc = Callable[[BeautifulSoup], bool]

# Registry of available extractors
EXTRACTORS = {
    "webdoc": {
        "detector": is_webdoc_generated,
        "content_extractor": webdoc_extract_main_content,
        "link_extractor": webdoc_extract_navigation_links,
    }
    # Add more extractors here as they become available
}

def detect_doc_type(soup: BeautifulSoup) -> Optional[str]:
    """
    Detect the type of documentation from the soup.
    
    Args:
        soup: BeautifulSoup object of the HTML page
        
    Returns:
        str: The detected documentation type or None if unknown
    """
    for doc_type, funcs in EXTRACTORS.items():
        if funcs["detector"](soup):
            return doc_type
    return None

def get_extractors(soup: BeautifulSoup) -> Tuple[ContentExtractorFunc, LinkExtractorFunc]:
    """
    Get the appropriate content and link extractors based on document type.
    
    Args:
        soup: BeautifulSoup object of the HTML page
        
    Returns:
        tuple: (content_extractor, link_extractor) functions
    """
    doc_type = detect_doc_type(soup)
    
    if doc_type and doc_type in EXTRACTORS:
        return (
            EXTRACTORS[doc_type]["content_extractor"],
            EXTRACTORS[doc_type]["link_extractor"]
        )
    
    # Default to generic extractors if we can't determine type
    # For now, just use webdoc extractors as fallback
    return (
        EXTRACTORS["webdoc"]["content_extractor"],
        EXTRACTORS[doc_type or "webdoc"]["link_extractor"]
    )

# Function to check if documentation is of a supported type
def is_supported_doc_type(soup: BeautifulSoup) -> bool:
    """Check if the given soup is a supported documentation type."""
    return detect_doc_type(soup) is not None

__all__ = [
    'detect_doc_type', 
    'get_extractors',
    'is_supported_doc_type',
    'is_webdoc_generated',
    'extract_main_content',
    'extract_navigation_links'
]