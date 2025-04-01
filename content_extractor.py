#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEO Cluster Crawler - Content Extractor
--------------------------------------
Extracts and cleans the main text content from web pages for semantic analysis.
Attempts to remove navigation, footers, and other non-content elements.
"""

from bs4 import BeautifulSoup
import re

class ContentExtractor:
    """
    A class to extract and clean the main text content from web pages.
    """
    
    def __init__(self, content_limit=None):
        """
        Initialize the content extractor.
        
        Args:
            content_limit (int, optional): Maximum number of characters to extract
                                         (None means no limit)
        """
        self.content_limit = content_limit
        
        # Common class and ID patterns for non-content elements
        self.non_content_patterns = [
            re.compile(r'(nav|navigation|menu|header|footer|sidebar|comment|widget|ad|banner|cookie)'),
            re.compile(r'(social|share|related|popular|tag|category|subscribe|newsletter)')
        ]
    
    def extract_content(self, html_content, url):
        """
        Extract and clean the main text content from HTML.
        
        Args:
            html_content (str): HTML content of the webpage
            url (str): URL of the webpage (for reference)
            
        Returns:
            dict: Dictionary containing extracted content information
        """
        if not html_content:
            return {
                'url': url,
                'error': 'No HTML content to extract from',
                'content': '',
                'content_length': 0,
                'word_count': 0
            }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'noscript', 'svg', 'iframe']):
            element.decompose()
        
        # Remove likely non-content elements based on common patterns
        for element in soup.find_all(class_=self.is_non_content_class):
            element.decompose()
        
        for element in soup.find_all(id=self.is_non_content_id):
            element.decompose()
        
        # Handle common navigation elements by tag
        for nav in soup.find_all(['nav', 'header', 'footer', 'aside']):
            nav.decompose()
        
        # Extract the remaining text from the body
        body = soup.body
        if not body:
            body = soup
        
        # Get the text content
        content = ''
        
        # Try to focus on main content area first if it exists
        main_content = body.find(['main', 'article']) or body.find('div', id='content') or body
        
        # Extract text and normalize whitespace
        content = self._extract_and_clean_text(main_content)
        
        # Apply content limit if specified
        if self.content_limit and len(content) > self.content_limit:
            content = content[:self.content_limit]
        
        # Calculate word count
        word_count = len(content.split())
        
        return {
            'url': url,
            'content': content,
            'content_length': len(content),
            'word_count': word_count,
            'truncated': self.content_limit is not None and len(content) >= self.content_limit
        }
    
    def is_non_content_class(self, class_attr):
        """
        Check if a class attribute likely belongs to a non-content element.
        
        Args:
            class_attr (str): Class attribute to check
            
        Returns:
            bool: True if it matches non-content patterns
        """
        if not class_attr:
            return False
        
        if isinstance(class_attr, list):
            class_str = ' '.join(class_attr)
        else:
            class_str = class_attr
            
        return any(pattern.search(class_str.lower()) for pattern in self.non_content_patterns)
    
    def is_non_content_id(self, id_attr):
        """
        Check if an ID attribute likely belongs to a non-content element.
        
        Args:
            id_attr (str): ID attribute to check
            
        Returns:
            bool: True if it matches non-content patterns
        """
        if not id_attr:
            return False
            
        return any(pattern.search(str(id_attr).lower()) for pattern in self.non_content_patterns)
    
    def _extract_and_clean_text(self, element):
        """
        Extract and clean text from a BeautifulSoup element.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            str: Cleaned text content
        """
        if not element:
            return ''
        
        # Get all text
        text = element.get_text(separator=' ', strip=True)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Add paragraph breaks
        for p in element.find_all('p'):
            p_text = p.get_text(strip=True)
            if p_text:
                text = text.replace(p_text, p_text + '\n\n')
        
        text = text.strip()
        
        return text