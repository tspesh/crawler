#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEO Cluster Crawler
-----------------
Crawls a website for SEO analysis, extracts metadata and content,
and outputs structured data for content cluster analysis.

Enhanced with more refined control over crawling:
- Can prompt user for URL if none provided
- Can crawl directly from a sitemap URL without recursive crawling
"""

import argparse
import json
import time
import requests
import os
import sys
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque

# Fix imports by adding the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Now import our modules
try:
    from metadata_extractor import MetadataExtractor
    from content_extractor import ContentExtractor
    from link_mapper import LinkMapper
    from navigation_link_detector import NavigationLinkDetector
    from json_formatter import JSONFormatter
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Make sure all required .py files are in the directory: {current_dir}")
    print("Required files: metadata_extractor.py, content_extractor.py, link_mapper.py, navigation_link_detector.py, json_formatter.py")
    sys.exit(1)

class SEOClusterCrawler:
    """
    A class to crawl a website for SEO analysis, extract metadata and content,
    and output structured data for content cluster analysis.
    """
    
    def __init__(self, start_url, max_pages=100, delay=0.5, content_limit=None, nav_threshold=0.8):
        """
        Initialize the crawler with a starting URL and constraints.
        
        Args:
            start_url (str): The URL to start crawling from
            max_pages (int): Maximum number of pages to crawl
            delay (float): Delay between requests in seconds
            content_limit (int, optional): Maximum number of characters to extract for content
            nav_threshold (float): Threshold for global link detection (0.0-1.0)
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.delay = delay
        
        # Extract the base domain and root URL
        parsed_url = urlparse(start_url)
        self.base_domain = parsed_url.netloc
        
        # Store the domain without www. prefix for consistent comparison
        self.normalized_domain = self.base_domain.replace('www.', '')
        
        # Store the root URL for constructing sitemap URLs
        self.root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Initialize data structures
        self.visited = set()  # Track visited URLs
        self.queue = deque()  # Queue of URLs to visit
        self.pages_data = []  # Store data about each page
        
        # XML namespaces used in sitemaps
        self.ns = {
            'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'xhtml': 'http://www.w3.org/1999/xhtml'
        }
        
        # Initialize extractors
        self.metadata_extractor = MetadataExtractor()
        self.content_extractor = ContentExtractor(content_limit=content_limit)
        
        # Initialize navigation link detector
        self.nav_detector = NavigationLinkDetector(threshold=nav_threshold)
        
        # Initialize link mapper with navigation detector
        self.link_mapper = LinkMapper(nav_detector=self.nav_detector)
        
    def is_same_domain(self, url):
        """
        Check if a URL belongs to the same domain as the crawled site,
        accounting for www vs non-www variants.
        
        Args:
            url (str): The URL to check
            
        Returns:
            bool: True if the URL is from the same domain
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Compare normalized domains (without www)
        normalized_domain = domain.replace('www.', '')
        return normalized_domain == self.normalized_domain
    
    def fetch_page(self, url):
        """
        Fetches content from a specified URL.
        
        Args:
            url (str): The URL to fetch content from
            
        Returns:
            tuple: (content, status_code) or (None, None) if failed
        """
        try:
            headers = {
                'User-Agent': 'SEO-Cluster-Crawler/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            return response.text, response.status_code
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {url}")
            print(f"Error details: {e}")
            return None, None
    
    def check_sitemap(self):
        """
        Checks if sitemap.xml exists and processes it if found.
        
        Returns:
            bool: True if sitemap was found and processed, False otherwise
        """
        sitemap_url = f"{self.root_url}/sitemap.xml"
        print(f"Checking for sitemap at: {sitemap_url}")
        
        sitemap_content, status_code = self.fetch_page(sitemap_url)
        
        if sitemap_content and status_code == 200:
            try:
                # Parse the sitemap XML
                urls = self.parse_sitemap(sitemap_content)
                
                if urls:
                    print(f"Found {len(urls)} URLs in sitemap.xml")
                    # Add sitemap URLs to queue
                    for url in urls:
                        if url not in self.visited:
                            self.queue.append(url)
                    return True
                else:
                    print("Sitemap found but contains no valid URLs")
                    return False
            except Exception as e:
                print(f"Error parsing sitemap: {e}")
                return False
        
        print("No sitemap.xml found, falling back to recursive crawling")
        return False
    
    def parse_sitemap(self, content):
        """
        Parses sitemap XML content to extract URLs.
        
        Args:
            content (str): XML content of the sitemap
            
        Returns:
            list: List of URLs found in the sitemap
        """
        urls = []
        
        try:
            # Parse XML
            root = ET.fromstring(content)
            
            # Check if this is a sitemap index (contains other sitemaps)
            sitemap_tags = root.findall('.//sm:sitemap', self.ns)
            if sitemap_tags:
                print("Found a sitemap index with multiple sitemaps")
                # Process each linked sitemap
                for sitemap_tag in sitemap_tags:
                    loc_tag = sitemap_tag.find('sm:loc', self.ns)
                    if loc_tag is not None and loc_tag.text:
                        nested_sitemap_url = loc_tag.text
                        print(f"Processing nested sitemap: {nested_sitemap_url}")
                        nested_content, _ = self.fetch_page(nested_sitemap_url)
                        if nested_content:
                            nested_urls = self.parse_sitemap(nested_content)
                            urls.extend(nested_urls)
                            time.sleep(self.delay)  # Add delay between requests
            else:
                # Regular sitemap with URLs
                url_tags = root.findall('.//sm:url', self.ns)
                for url_tag in url_tags:
                    loc_tag = url_tag.find('sm:loc', self.ns)
                    if loc_tag is not None and loc_tag.text:
                        url = loc_tag.text
                        parsed_url = urlparse(url)
                        # Check for domain match using our helper method
                        if self.is_same_domain(url):
                            urls.append(url)
        except ET.ParseError as e:
            print(f"XML parsing error: {e}")
        
        return urls
    
    def extract_internal_links(self, html, base_url):
        """
        Extracts all internal links from the HTML content.
        
        Args:
            html (str): HTML content to parse
            base_url (str): The base URL to determine internal links
            
        Returns:
            list: List of internal links found
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        internal_links = []
        
        # Find all anchor tags
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip empty links, javascript, mailto, tel links, and anchors
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue
            
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            # Filter out external links and ensure scheme is http/https
            if self.is_same_domain(full_url) and parsed_url.scheme in ('http', 'https'):
                # Remove fragments from URLs
                clean_url = parsed_url._replace(fragment='').geturl()
                
                internal_links.append(clean_url)
        
        return internal_links
    
    def crawl(self):
        """
        Crawl the website using sitemap if available or recursive crawling.
        Extract metadata and content for SEO analysis.
        
        Returns:
            dict: Crawling results including visited pages and their data
        """
        # First check for sitemap if queue is empty (not skipped via --no-sitemap)
        sitemap_found = False
        if not self.queue:
            sitemap_found = self.check_sitemap()
        
        # If no sitemap or sitemap processing failed, start with the homepage
        if not sitemap_found:
            self.queue.append(self.start_url)
        
        page_count = 0
        
        while self.queue and page_count < self.max_pages:
            # Get the next URL from the queue
            current_url = self.queue.popleft()
            
            # Skip if already visited
            if current_url in self.visited:
                continue
            
            # Add to visited set
            self.visited.add(current_url)
            
            print(f"Crawling {page_count + 1}/{self.max_pages}: {current_url}")
            
            # Fetch the page
            html_content, status_code = self.fetch_page(current_url)
            
            if html_content and status_code == 200:
                # Extract metadata
                metadata = self.metadata_extractor.extract_metadata(html_content, current_url)
                
                # Extract content
                content_data = self.content_extractor.extract_content(html_content, current_url)
                
                # Extract internal links
                internal_links = self.extract_internal_links(html_content, current_url)
                
                # Add links to the link mapper
                self.link_mapper.add_page_links(current_url, internal_links)
                
                # Store page data
                page_data = {
                    'url': current_url,
                    'status_code': status_code,
                    'title': metadata['title']['content'],
                    'metadata': metadata,
                    'content': content_data,
                    'internal_links_count': len(internal_links),
                    'internal_links': internal_links,
                    'backlinks_count': self.link_mapper.get_backlink_count(current_url)
                }
                
                self.pages_data.append(page_data)
                
                # Add new links to the queue
                for link in internal_links:
                    if link not in self.visited:
                        self.queue.append(link)
                
                page_count += 1
                
                # Add delay to be nice to the server
                time.sleep(self.delay)
            elif status_code:
                # Store error data
                self.pages_data.append({
                    'url': current_url,
                    'status_code': status_code,
                    'error': f"Failed to fetch content (Status code: {status_code})"
                })
                
                page_count += 1
        
        # After crawling all pages, detect global links
        print("Analyzing link structure and detecting navigation links...")
        global_links = self.nav_detector.detect_global_links()
        print(f"Detected {len(global_links)} global/navigation links")
        
        # Apply global link filtering to link mapper
        self.link_mapper.apply_global_link_filtering()
        
        # Update page data with filtered backlink counts
        for page_data in self.pages_data:
            if 'url' in page_data and 'status_code' in page_data and page_data['status_code'] == 200:
                url = page_data['url']
                page_data['filtered_internal_links'] = self.link_mapper.get_outgoing_links(url, filter_global=True)
                page_data['filtered_internal_links_count'] = len(page_data['filtered_internal_links'])
                page_data['filtered_backlinks_count'] = self.link_mapper.get_backlink_count(url, filter_global=True)
                
                # Mark global links in internal_links list
                if 'internal_links' in page_data:
                    page_data['nav_links'] = [
                        link for link in page_data['internal_links'] 
                        if self.nav_detector.is_global_link(link)
                    ]
                    page_data['nav_links_count'] = len(page_data['nav_links'])
        
        # Get complete link data from the link mapper
        link_data = self.link_mapper.get_link_data()
        
        # Prepare results
        results = {
            'start_url': self.start_url,
            'base_domain': self.base_domain,
            'sitemap_used': sitemap_found,
            'pages_crawled': len(self.pages_data),
            'max_pages': self.max_pages,
            'nav_threshold': self.nav_detector.threshold,
            'nav_links_detected': len(self.nav_detector.global_links),
            'pages': self.pages_data,
            'link_structure': link_data
        }
        
        return results

    def crawl_from_sitemap(self, sitemap_url):
        """
        Crawl only the URLs from a specified sitemap, without recursive crawling.
        
        Args:
            sitemap_url (str): URL of the sitemap to crawl
            
        Returns:
            dict: Crawling results including visited pages and their data
        """
        print(f"Fetching sitemap from: {sitemap_url}")
        sitemap_content, status_code = self.fetch_page(sitemap_url)
        
        if not sitemap_content or status_code != 200:
            print(f"Error: Could not fetch sitemap from {sitemap_url} (Status code: {status_code})")
            return {
                'start_url': self.start_url,
                'base_domain': self.base_domain,
                'sitemap_used': True,
                'pages_crawled': 0,
                'max_pages': self.max_pages,
                'nav_threshold': self.nav_detector.threshold,
                'nav_links_detected': 0,
                'pages': [],
                'link_structure': {'outgoing_links': {}, 'backlinks': {}, 'link_stats': {'total_links_mapped': 0}}
            }
        
        try:
            # Parse the sitemap XML
            urls = self.parse_sitemap(sitemap_content)
            
            if not urls:
                print("Error: No URLs found in the sitemap")
                return {
                    'start_url': self.start_url,
                    'base_domain': self.base_domain,
                    'sitemap_used': True,
                    'pages_crawled': 0,
                    'max_pages': self.max_pages,
                    'nav_threshold': self.nav_detector.threshold,
                    'nav_links_detected': 0,
                    'pages': [],
                    'link_structure': {'outgoing_links': {}, 'backlinks': {}, 'link_stats': {'total_links_mapped': 0}}
                }
            
            print(f"Found {len(urls)} URLs in sitemap")
            
            # Limit to max_pages if needed
            if len(urls) > self.max_pages:
                print(f"Limiting to {self.max_pages} pages")
                urls = urls[:self.max_pages]
            
            page_count = 0
            
            # Crawl each URL from the sitemap
            for url in urls:
                print(f"Crawling {page_count + 1}/{len(urls)}: {url}")
                
                # Add to visited set
                self.visited.add(url)
                
                # Fetch the page
                html_content, status_code = self.fetch_page(url)
                
                if html_content and status_code == 200:
                    # Extract metadata
                    metadata = self.metadata_extractor.extract_metadata(html_content, url)
                    
                    # Extract content
                    content_data = self.content_extractor.extract_content(html_content, url)
                    
                    # Extract internal links (we still gather link data, even if we don't follow them)
                    internal_links = self.extract_internal_links(html_content, url)
                    
                    # Add links to the link mapper
                    self.link_mapper.add_page_links(url, internal_links)
                    
                    # Store page data
                    page_data = {
                        'url': url,
                        'status_code': status_code,
                        'title': metadata['title']['content'],
                        'metadata': metadata,
                        'content': content_data,
                        'internal_links_count': len(internal_links),
                        'internal_links': internal_links,
                        'backlinks_count': self.link_mapper.get_backlink_count(url),
                        'from_sitemap': True
                    }
                    
                    self.pages_data.append(page_data)
                    
                    page_count += 1
                    
                    # Add delay to be nice to the server
                    time.sleep(self.delay)
                elif status_code:
                    # Store error data
                    self.pages_data.append({
                        'url': url,
                        'status_code': status_code,
                        'error': f"Failed to fetch content (Status code: {status_code})",
                        'from_sitemap': True
                    })
                    
                    page_count += 1
            
            # After crawling all pages, detect global links
            print("Analyzing link structure and detecting navigation links...")
            global_links = self.nav_detector.detect_global_links()
            print(f"Detected {len(global_links)} global/navigation links")
            
            # Apply global link filtering to link mapper
            self.link_mapper.apply_global_link_filtering()
            
            # Update page data with filtered backlink counts
            for page_data in self.pages_data:
                if 'url' in page_data and 'status_code' in page_data and page_data['status_code'] == 200:
                    url = page_data['url']
                    page_data['filtered_internal_links'] = self.link_mapper.get_outgoing_links(url, filter_global=True)
                    page_data['filtered_internal_links_count'] = len(page_data['filtered_internal_links'])
                    page_data['filtered_backlinks_count'] = self.link_mapper.get_backlink_count(url, filter_global=True)
                    
                    # Mark global links in internal_links list
                    if 'internal_links' in page_data:
                        page_data['nav_links'] = [
                            link for link in page_data['internal_links'] 
                            if self.nav_detector.is_global_link(link)
                        ]
                        page_data['nav_links_count'] = len(page_data['nav_links'])
            
            # Get complete link data from the link mapper
            link_data = self.link_mapper.get_link_data()
            
            # Prepare results
            results = {
                'start_url': self.start_url,
                'sitemap_url': sitemap_url,
                'base_domain': self.base_domain,
                'sitemap_used': True,
                'sitemap_only': True,
                'pages_crawled': len(self.pages_data),
                'max_pages': self.max_pages,
                'nav_threshold': self.nav_detector.threshold,
                'nav_links_detected': len(self.nav_detector.global_links),
                'pages': self.pages_data,
                'link_structure': link_data
            }
            
            return results
            
        except Exception as e:
            print(f"Error processing sitemap: {e}")
            return {
                'start_url': self.start_url,
                'sitemap_url': sitemap_url,
                'base_domain': self.base_domain,
                'sitemap_used': True,
                'sitemap_only': True,
                'error': str(e),
                'pages_crawled': 0,
                'max_pages': self.max_pages,
                'nav_threshold': self.nav_detector.threshold,
                'nav_links_detected': 0,
                'pages': [],
                'link_structure': {'outgoing_links': {}, 'backlinks': {}, 'link_stats': {'total_links_mapped': 0}}
            }

def main():
    parser = argparse.ArgumentParser(description='SEO Cluster Crawler - Extract metadata and content from websites')
    # Make URL optional by using nargs='?'
    parser.add_argument('url', nargs='?', help='Starting URL to crawl (e.g., https://example.com). If not provided, you will be prompted.')
    parser.add_argument('--max-pages', '-m', type=int, default=100,
                      help='Maximum number of pages to crawl (default: 100)')
    parser.add_argument('--delay', '-d', type=float, default=0.5,
                      help='Delay between requests in seconds (default: 0.5)')
    parser.add_argument('--no-sitemap', action='store_true',
                      help='Skip sitemap.xml check and use recursive crawling only')
    parser.add_argument('--content-limit', '-c', type=int, default=None,
                      help='Limit content extraction to specified number of characters (default: no limit)')
    parser.add_argument('--output', '-o', default='seo_crawler_results.json',
                      help='Output JSON file (default: seo_crawler_results.json)')
    parser.add_argument('--links-only', action='store_true',
                      help='Only output link structure data (smaller file size)')
    parser.add_argument('--nav-threshold', '-t', type=float, default=0.8,
                      help='Threshold for global/navigation link detection (0.0-1.0, default: 0.8)')
    parser.add_argument('--format-json', '-f', action='store_true',
                      help='Format output as clean JSON optimized for LLM processing')
    parser.add_argument('--individual-files', '-i', action='store_true',
                      help='Output individual JSON files for each page (creates a directory)')
    parser.add_argument('--no-link-structure', '-n', action='store_true',
                      help='Exclude the link structure data from JSON output (smaller file size)')
    
    args = parser.parse_args()
    
    # Get starting URL
    url = args.url
    sitemap_url = None
    sitemap_only_mode = False
    
    if not url:
        # No URL provided via command line, prompt the user
        print("\nSEO Cluster Crawler - Choose crawling mode:")
        print("1. Website crawl (starts from homepage, looks for sitemap.xml)")
        print("2. Sitemap-only crawl (crawls URLs from a specific sitemap without recursive crawling)")
        
        mode = input("\nSelect mode (1 or 2): ").strip()
        
        if mode == '2':
            # Sitemap-only mode
            sitemap_url = input("\nEnter sitemap URL (e.g., https://example.com/sitemap.xml): ").strip()
            
            if not sitemap_url:
                print("Error: No sitemap URL provided. Exiting.")
                return
                
            # Validate sitemap URL
            parsed_url = urlparse(sitemap_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                print("Error: Invalid sitemap URL format. Please use format: https://example.com/sitemap.xml")
                return
                
            # For sitemap-only mode, we'll use the domain from the sitemap URL
            # as our starting point for domain matching purposes
            url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            sitemap_only_mode = True
        else:
            # Normal website crawl mode
            url = input("\nEnter website URL to crawl (e.g., https://example.com): ").strip()
            
            if not url:
                print("Error: No URL provided. Exiting.")
                return
    
    # Validate URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        print("Error: Invalid URL format. Please use format: https://example.com")
        return
    
    # Validate nav threshold
    if args.nav_threshold < 0 or args.nav_threshold > 1:
        print("Error: Navigation threshold must be between 0.0 and 1.0")
        return
    
    # Create the crawler
    crawler = SEOClusterCrawler(
        url, 
        args.max_pages, 
        args.delay, 
        args.content_limit,
        nav_threshold=args.nav_threshold
    )
    
    # Run the appropriate crawl mode
    if sitemap_only_mode:
        print(f"\nStarting sitemap-only crawl from: {sitemap_url}")
        results = crawler.crawl_from_sitemap(sitemap_url)
    else:
        print(f"\nStarting website crawl from: {url}")
        
        # Skip sitemap check if specified
        if args.no_sitemap:
            crawler.queue.append(url)
            print("Skipping sitemap.xml check as requested")
        
        results = crawler.crawl()
    
    # Create links-only version if requested
    if args.links_only:
        # Create a slimmed down version with just the link data
        link_results = {
            'start_url': results['start_url'],
            'base_domain': results['base_domain'],
            'pages_crawled': results['pages_crawled'],
            'nav_threshold': results['nav_threshold'],
            'nav_links_detected': results['nav_links_detected'],
            'link_structure': results['link_structure']
        }
        
        # Include sitemap info if available
        if 'sitemap_url' in results:
            link_results['sitemap_url'] = results['sitemap_url']
            link_results['sitemap_only'] = results.get('sitemap_only', False)
            
        output_data = link_results
    else:
        output_data = results
        
    # Remove link structure if requested to reduce file size
    if args.no_link_structure and 'link_structure' in output_data:
        del output_data['link_structure']
    
    # Format JSON for LLM processing if requested
    if args.format_json:
        formatter = JSONFormatter(include_filtered_links=True)
        
        if args.individual_files:
            # Create output directory from the output file name
            output_dir = os.path.splitext(args.output)[0] + '_pages'
            file_count = formatter.save_individual_json_files(output_data, output_dir)
            print(f"Created {file_count} individual JSON files in directory: {output_dir}")
        else:
            # Save as a single consolidated file
            formatter.save_consolidated_json(output_data, args.output)
            print(f"Formatted JSON saved to: {args.output}")
    else:
        # Save the standard results
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        print(f"Results saved to: {args.output}")
    
    print(f"\nCrawling complete!")
    
    # Show appropriate summary based on crawl mode
    if sitemap_only_mode:
        print(f"Sitemap URL: {sitemap_url}")
        print(f"Pages crawled from sitemap: {results['pages_crawled']}")
    else:
        print(f"Starting URL: {url}")
        print(f"Sitemap used: {results['sitemap_used']}")
        print(f"Pages crawled: {results['pages_crawled']}")
        
    print(f"Total links mapped: {results['link_structure']['link_stats']['total_links_mapped']}")
    print(f"Navigation links detected: {results['nav_links_detected']}")

if __name__ == "__main__":
    main()