#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEO Cluster Crawler - Metadata Extractor
---------------------------------------
Extracts SEO-relevant metadata from web pages including titles, meta descriptions,
canonical tags, OpenGraph tags, Twitter Card tags, and H1 headings.
"""

from bs4 import BeautifulSoup

class MetadataExtractor:
    """
    A class to extract SEO-relevant metadata from web pages.
    """
    
    def __init__(self):
        """Initialize the metadata extractor."""
        pass
    
    def extract_metadata(self, html_content, url):
        """
        Extract metadata from HTML content.
        
        Args:
            html_content (str): HTML content of the webpage
            url (str): URL of the webpage (for reference and fallbacks)
            
        Returns:
            dict: Dictionary containing extracted metadata
        """
        if not html_content:
            return {
                'url': url,
                'error': 'No HTML content to extract metadata from'
            }
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize metadata dictionary
        metadata = {
            'url': url,
            'title': {
                'content': None,
                'length': 0
            },
            'meta_description': {
                'content': None,
                'length': 0
            },
            'canonical': None,
            'h1': {
                'content': None,
                'count': 0
            },
            'open_graph': {},
            'twitter_card': {}
        }
        
        # Extract title
        title_tag = soup.title
        if title_tag and title_tag.string:
            title_text = title_tag.string.strip()
            metadata['title']['content'] = title_text
            metadata['title']['length'] = len(title_text)
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc_text = meta_desc['content'].strip()
            metadata['meta_description']['content'] = desc_text
            metadata['meta_description']['length'] = len(desc_text)
        
        # Extract canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            metadata['canonical'] = canonical['href'].strip()
        
        # Extract H1 headings
        h1_tags = soup.find_all('h1')
        metadata['h1']['count'] = len(h1_tags)
        if h1_tags and h1_tags[0].get_text():
            # Extract first H1
            metadata['h1']['content'] = h1_tags[0].get_text().strip()
        
        # Extract OpenGraph tags
        og_tags = soup.find_all('meta', property=lambda p: p and p.startswith('og:'))
        for tag in og_tags:
            if tag.get('property') and tag.get('content'):
                prop = tag['property'].replace('og:', '')  # Remove 'og:' prefix
                metadata['open_graph'][prop] = tag['content'].strip()
        
        # Extract Twitter Card tags
        twitter_tags = []
        # Find Twitter tags with name attribute
        twitter_tags.extend(soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}))
        # Find Twitter tags with property attribute
        twitter_tags.extend(soup.find_all('meta', attrs={'property': lambda x: x and x.startswith('twitter:')}))
        
        for tag in twitter_tags:
            prop_attr = tag.get('name') or tag.get('property')
            if prop_attr and tag.get('content'):
                prop = prop_attr.replace('twitter:', '')  # Remove 'twitter:' prefix
                metadata['twitter_card'][prop] = tag['content'].strip()
        
        # Extract additional useful SEO metadata
        robots = soup.find('meta', attrs={'name': 'robots'})
        if robots and robots.get('content'):
            metadata['robots'] = robots['content'].strip()
        
        # Check for hreflang tags
        hreflang_tags = soup.find_all('link', attrs={'rel': 'alternate', 'hreflang': True})
        if hreflang_tags:
            metadata['hreflang'] = []
            for tag in hreflang_tags:
                if tag.get('href') and tag.get('hreflang'):
                    metadata['hreflang'].append({
                        'href': tag['href'].strip(),
                        'hreflang': tag['hreflang'].strip()
                    })
        
        return metadata