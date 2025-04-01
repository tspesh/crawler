#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEO Cluster Crawler - JSON Formatter
----------------------------------
Formats crawler results into clean JSON structures for LLM analysis.
"""

import json
import os
from datetime import datetime

class JSONFormatter:
    """
    A class to format crawler results into clean JSON structures
    optimized for LLM analysis.
    """
    
    def __init__(self, include_filtered_links=True):
        """
        Initialize the JSON formatter.
        
        Args:
            include_filtered_links (bool): Whether to include filtered (non-navigation) links
        """
        self.include_filtered_links = include_filtered_links
    
    def format_page(self, page_data):
        """
        Format a single page's data into a clean JSON structure.
        
        Args:
            page_data (dict): The raw page data from the crawler
            
        Returns:
            dict: Formatted page data
        """
        # Skip pages with errors
        if 'error' in page_data:
            return {
                'url': page_data.get('url', ''),
                'status_code': page_data.get('status_code', 0),
                'error': page_data.get('error', 'Unknown error'),
                'crawled_successfully': False
            }
        
        # Extract metadata from the nested structure
        metadata = page_data.get('metadata', {})
        
        # Extract content data
        content_data = page_data.get('content', {})
        
        # Build the formatted page object
        formatted_page = {
            'url': page_data.get('url', ''),
            'status_code': page_data.get('status_code', 0),
            'crawled_successfully': True,
            'title': metadata.get('title', {}).get('content', ''),
            'title_length': metadata.get('title', {}).get('length', 0),
            'meta_description': metadata.get('meta_description', {}).get('content', ''),
            'meta_description_length': metadata.get('meta_description', {}).get('length', 0),
            'canonical': metadata.get('canonical', ''),
            'h1': metadata.get('h1', {}).get('content', ''),
            'h1_count': metadata.get('h1', {}).get('count', 0),
            'og_tags': metadata.get('open_graph', {}),
            'twitter_tags': metadata.get('twitter_card', {}),
            'robots': metadata.get('robots', ''),
            'content': content_data.get('content', ''),
            'content_length': content_data.get('content_length', 0),
            'word_count': content_data.get('word_count', 0),
            'internal_links_out': page_data.get('internal_links', []),
            'internal_links_count': page_data.get('internal_links_count', 0),
            'backlinks_count': page_data.get('backlinks_count', 0)
        }
        
        # Include hreflang if present
        if 'hreflang' in metadata:
            formatted_page['hreflang'] = metadata['hreflang']
        
        # Include filtered link data if available and requested
        if self.include_filtered_links:
            if 'nav_links' in page_data:
                formatted_page['nav_links'] = page_data['nav_links']
                formatted_page['nav_links_count'] = page_data.get('nav_links_count', 0)
            
            if 'filtered_internal_links' in page_data:
                formatted_page['filtered_internal_links'] = page_data['filtered_internal_links']
                formatted_page['filtered_internal_links_count'] = page_data.get('filtered_internal_links_count', 0)
            
            if 'filtered_backlinks_count' in page_data:
                formatted_page['filtered_backlinks_count'] = page_data['filtered_backlinks_count']
        
        return formatted_page
    
    def format_crawler_results(self, crawler_results):
        """
        Format the entire crawler results into a clean JSON structure.
        
        Args:
            crawler_results (dict): The raw crawler results
            
        Returns:
            dict: Formatted crawler results
        """
        # Extract pages data
        pages_data = crawler_results.get('pages', [])
        
        # Format each page
        formatted_pages = [self.format_page(page) for page in pages_data]
        
        # Build the formatted results object
        formatted_results = {
            'metadata': {
                'start_url': crawler_results.get('start_url', ''),
                'base_domain': crawler_results.get('base_domain', ''),
                'sitemap_used': crawler_results.get('sitemap_used', False),
                'pages_crawled': crawler_results.get('pages_crawled', 0),
                'max_pages': crawler_results.get('max_pages', 0),
                'crawler_version': '1.0',
                'crawl_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'pages': formatted_pages
        }
        
        # Include navigation link detection info if available
        if 'nav_threshold' in crawler_results:
            formatted_results['metadata']['nav_threshold'] = crawler_results['nav_threshold']
            formatted_results['metadata']['nav_links_detected'] = crawler_results.get('nav_links_detected', 0)
        
        return formatted_results
    
    def save_consolidated_json(self, crawler_results, output_file):
        """
        Save the entire crawler results as a single consolidated JSON file.
        
        Args:
            crawler_results (dict): The raw crawler results
            output_file (str): Path to the output JSON file
            
        Returns:
            str: Path to the saved file
        """
        formatted_results = self.format_crawler_results(crawler_results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_results, f, indent=2)
        
        return output_file
    
    def save_individual_json_files(self, crawler_results, output_dir):
        """
        Save each page's data as an individual JSON file in a directory.
        
        Args:
            crawler_results (dict): The raw crawler results
            output_dir (str): Directory to save the individual JSON files
            
        Returns:
            int: Number of files created
        """
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract pages data
        pages_data = crawler_results.get('pages', [])
        
        # Format and save each page
        file_count = 0
        
        for page_data in pages_data:
            formatted_page = self.format_page(page_data)
            
            # Skip pages with errors
            if not formatted_page.get('crawled_successfully', False):
                continue
            
            # Create a safe filename from the URL
            url = formatted_page['url']
            page_name = url.replace('://', '_').replace('/', '_').replace('?', '_').replace('&', '_')
            
            # Ensure filename isn't too long
            if len(page_name) > 200:
                page_name = page_name[:200]
            
            # Save the page data
            file_path = os.path.join(output_dir, f"{page_name}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(formatted_page, f, indent=2)
            
            file_count += 1
        
        # Save a metadata file with information about the crawl
        metadata = {
            'start_url': crawler_results.get('start_url', ''),
            'base_domain': crawler_results.get('base_domain', ''),
            'sitemap_used': crawler_results.get('sitemap_used', False),
            'pages_crawled': crawler_results.get('pages_crawled', 0),
            'max_pages': crawler_results.get('max_pages', 0),
            'crawler_version': '1.0',
            'crawl_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'files_created': file_count
        }
        
        # Include navigation link detection info if available
        if 'nav_threshold' in crawler_results:
            metadata['nav_threshold'] = crawler_results['nav_threshold']
            metadata['nav_links_detected'] = crawler_results.get('nav_links_detected', 0)
        
        metadata_file = os.path.join(output_dir, "_metadata.json")
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return file_count
