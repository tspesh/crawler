#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEO Cluster Crawler - Navigation Link Detector
--------------------------------------------
Detects and filters navigation/global links that appear across multiple pages.
"""

class NavigationLinkDetector:
    """
    A class to detect and filter navigation/global links that appear across multiple pages.
    """
    
    def __init__(self, threshold=0.8):
        """
        Initialize the navigation link detector.
        
        Args:
            threshold (float): Threshold percentage (0.0-1.0) for considering a link as global/navigation
                               Default is 0.8 (80% of pages)
        """
        self.threshold = threshold
        self.link_occurrences = {}  # Dictionary to track which pages contain each link
        self.total_pages = 0
        self.global_links = set()  # Set of links identified as global/navigation
    
    def add_page_links(self, page_url, links):
        """
        Register the links found on a page.
        
        Args:
            page_url (str): URL of the current page
            links (list): List of links found on the page
        """
        self.total_pages += 1
        
        # Track each link's occurrence
        for link in links:
            if link not in self.link_occurrences:
                self.link_occurrences[link] = set()
            
            self.link_occurrences[link].add(page_url)
    
    def detect_global_links(self):
        """
        Detect global/navigation links based on occurrence threshold.
        
        Returns:
            set: Set of URLs identified as global/navigation links
        """
        if self.total_pages == 0:
            return set()
        
        threshold_count = self.total_pages * self.threshold
        
        # Identify links that appear in more than the threshold percentage of pages
        self.global_links = {
            link for link, sources in self.link_occurrences.items()
            if len(sources) >= threshold_count
        }
        
        return self.global_links
    
    def is_global_link(self, url):
        """
        Check if a URL is identified as a global/navigation link.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if the URL is a global/navigation link
        """
        return url in self.global_links
    
    def filter_global_links(self, links):
        """
        Filter out global/navigation links from a list of links.
        
        Args:
            links (list): List of links
            
        Returns:
            list: Filtered list without global/navigation links
        """
        return [link for link in links if link not in self.global_links]
    
    def get_global_link_stats(self):
        """
        Get statistics about detected global/navigation links.
        
        Returns:
            dict: Dictionary of statistics
        """
        stats = {
            'total_pages_analyzed': self.total_pages,
            'detection_threshold': f"{self.threshold:.0%}",
            'detection_threshold_count': int(self.total_pages * self.threshold),
            'global_links_detected': len(self.global_links),
            'global_links': list(self.global_links)
        }
        
        # Add occurrence counts for each global link
        if self.global_links:
            stats['global_link_occurrences'] = {
                link: len(self.link_occurrences[link])
                for link in self.global_links
            }
        
        return stats