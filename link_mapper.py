#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SEO Cluster Crawler - Link Mapper
--------------------------------
Maps internal link relationships between pages on a website.
Creates source→target link mappings and handles backlink analysis.
"""

class LinkMapper:
    """
    A class to map internal link relationships between pages on a website.
    """
    
    def __init__(self, nav_detector=None):
        """
        Initialize the link mapper.
        
        Args:
            nav_detector (NavigationLinkDetector, optional): Navigation link detector for filtering
        """
        # Dictionary mapping source URLs to list of target URLs
        self.outgoing_links = {}
        
        # Dictionary mapping target URLs to list of source URLs (backlinks)
        self.backlinks = {}
        
        # Count of total links mapped
        self.total_links_mapped = 0
        
        # Store filtered (non-navigation) versions of the maps
        self.filtered_outgoing_links = {}
        self.filtered_backlinks = {}
        
        # Navigation link detector
        self.nav_detector = nav_detector
    
    def add_link(self, source_url, target_url):
        """
        Add a link relationship to both outgoing and backlink maps.
        
        Args:
            source_url (str): The URL of the page containing the link
            target_url (str): The URL being linked to
        """
        # Add to outgoing links
        if source_url not in self.outgoing_links:
            self.outgoing_links[source_url] = []
        
        # Only add if not already present (avoid duplicates)
        if target_url not in self.outgoing_links[source_url]:
            self.outgoing_links[source_url].append(target_url)
            self.total_links_mapped += 1
        
        # Add to backlinks
        if target_url not in self.backlinks:
            self.backlinks[target_url] = []
        
        # Only add if not already present (avoid duplicates)
        if source_url not in self.backlinks[target_url]:
            self.backlinks[target_url].append(source_url)
    
    def add_page_links(self, source_url, target_urls):
        """
        Add all outgoing links for a page.
        
        Args:
            source_url (str): The URL of the page containing the links
            target_urls (list): A list of URLs linked to from the source page
        """
        for target_url in target_urls:
            self.add_link(source_url, target_url)
        
        # If we have a navigation detector, register these links for global link detection
        if self.nav_detector:
            self.nav_detector.add_page_links(source_url, target_urls)
    
    def get_outgoing_links(self, url, filter_global=False):
        """
        Get all outgoing links for a specific URL.
        
        Args:
            url (str): The URL to get outgoing links for
            filter_global (bool): Whether to filter out global/navigation links
            
        Returns:
            list: List of URLs that the specified page links to
        """
        links = self.outgoing_links.get(url, [])
        
        if filter_global and self.nav_detector:
            return self.nav_detector.filter_global_links(links)
        
        return links
    
    def get_backlinks(self, url, filter_global=False):
        """
        Get all backlinks for a specific URL.
        
        Args:
            url (str): The URL to get backlinks for
            filter_global (bool): Whether to filter out global/navigation links
            
        Returns:
            list: List of URLs that link to the specified page
        """
        links = self.backlinks.get(url, [])
        
        if filter_global and self.nav_detector:
            return self.nav_detector.filter_global_links(links)
        
        return links
    
    def get_backlink_count(self, url, filter_global=False):
        """
        Get the number of backlinks for a specific URL.
        
        Args:
            url (str): The URL to get backlink count for
            filter_global (bool): Whether to filter out global/navigation links
            
        Returns:
            int: Number of pages linking to the specified URL
        """
        return len(self.get_backlinks(url, filter_global))
    
    def apply_global_link_filtering(self):
        """
        Apply global link filtering to create filtered link maps.
        Must be called after the navigation detector has identified global links.
        """
        if not self.nav_detector:
            return
        
        # Create filtered outgoing links
        self.filtered_outgoing_links = {}
        for source, targets in self.outgoing_links.items():
            filtered_targets = self.nav_detector.filter_global_links(targets)
            if filtered_targets:
                self.filtered_outgoing_links[source] = filtered_targets
        
        # Create filtered backlinks
        self.filtered_backlinks = {}
        for target, sources in self.backlinks.items():
            filtered_sources = self.nav_detector.filter_global_links(sources)
            if filtered_sources:
                self.filtered_backlinks[target] = filtered_sources
    
    def get_link_data(self, include_filtered=True):
        """
        Get the complete link mapping data.
        
        Args:
            include_filtered (bool): Whether to include filtered (non-navigation) link maps
            
        Returns:
            dict: Dictionary containing outgoing links, backlinks, and stats
        """
        # Gather link statistics for summary
        most_linked_pages = sorted(
            self.backlinks.keys(),
            key=lambda url: len(self.backlinks[url]),
            reverse=True
        )[:10]  # Top 10 most linked pages
        
        most_linking_pages = sorted(
            self.outgoing_links.keys(),
            key=lambda url: len(self.outgoing_links[url]),
            reverse=True
        )[:10]  # Top 10 pages with most outgoing links
        
        # Create link stats dictionary
        link_stats = {
            'total_links_mapped': self.total_links_mapped,
            'pages_with_outgoing_links': len(self.outgoing_links),
            'pages_with_backlinks': len(self.backlinks),
            'most_linked_pages': [
                {
                    'url': url,
                    'backlink_count': len(self.backlinks[url])
                }
                for url in most_linked_pages
            ],
            'most_linking_pages': [
                {
                    'url': url,
                    'outgoing_link_count': len(self.outgoing_links[url])
                }
                for url in most_linking_pages
            ]
        }
        
        # Complete link data
        link_data = {
            'outgoing_links': self.outgoing_links,
            'backlinks': self.backlinks,
            'link_stats': link_stats
        }
        
        # Include filtered link data if requested and available
        if include_filtered and self.nav_detector and self.nav_detector.global_links:
            # Add global link information
            link_data['global_links'] = self.nav_detector.get_global_link_stats()
            
            # Add filtered link maps
            link_data['filtered_outgoing_links'] = self.filtered_outgoing_links
            link_data['filtered_backlinks'] = self.filtered_backlinks
            
            # Add filtered statistics
            filtered_most_linked = sorted(
                self.filtered_backlinks.keys(),
                key=lambda url: len(self.filtered_backlinks[url]),
                reverse=True
            )[:10] if self.filtered_backlinks else []
            
            link_data['filtered_link_stats'] = {
                'pages_with_filtered_outgoing_links': len(self.filtered_outgoing_links),
                'pages_with_filtered_backlinks': len(self.filtered_backlinks),
                'most_linked_pages_filtered': [
                    {
                        'url': url,
                        'backlink_count': len(self.filtered_backlinks[url])
                    }
                    for url in filtered_most_linked
                ]
            }
        
        return link_data