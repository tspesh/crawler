# SEO Cluster Crawler

A Python-based tool for crawling websites, extracting SEO-relevant data, mapping internal links, and outputting structured datasets for content cluster analysis.

## Features

- Crawls websites using sitemap.xml (when available) or recursive link discovery
- Extracts SEO metadata (title, meta description, canonical, OpenGraph, Twitter Card, H1)
- Extracts clean page content for semantic analysis
- Maps internal linking structure
- Outputs data in structured JSON format for further analysis

## Requirements

- Python 3.6+
- Required packages: requests, beautifulsoup4

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/seo-cluster-crawler.git
cd seo-cluster-crawler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic usage

```bash
python seo_cluster_crawler.py https://example.com
```

### Options

```
usage: seo_cluster_crawler.py [-h] [--max-pages MAX_PAGES] [--delay DELAY] [--no-sitemap]
                           [--content-limit CONTENT_LIMIT] [--output OUTPUT] url

SEO Cluster Crawler - Extract metadata and content from websites

positional arguments:
  url                   Starting URL to crawl (e.g., https://example.com)

optional arguments:
  -h, --help            show this help message and exit
  --max-pages MAX_PAGES, -m MAX_PAGES
                        Maximum number of pages to crawl (default: 100)
  --delay DELAY, -d DELAY
                        Delay between requests in seconds (default: 0.5)
  --no-sitemap          Skip sitemap.xml check and use recursive crawling only
  --content-limit CONTENT_LIMIT, -c CONTENT_LIMIT
                        Limit content extraction to specified number of characters (default: no limit)
  --output OUTPUT, -o OUTPUT
                        Output JSON file (default: seo_crawler_results.json)
```

### Examples

1. Crawl up to 50 pages with a 1-second delay between requests:
```bash
python seo_cluster_crawler.py https://example.com --max-pages 50 --delay 1
```

2. Skip sitemap check and crawl recursively:
```bash
python seo_cluster_crawler.py https://example.com --no-sitemap
```

3. Limit content extraction to 5000 characters per page:
```bash
python seo_cluster_crawler.py https://example.com --content-limit 5000
```

## Output Format

The crawler outputs a JSON file with the following structure:

```json
{
  "start_url": "https://example.com",
  "base_domain": "example.com",
  "sitemap_used": true,
  "pages_crawled": 50,
  "max_pages": 100,
  "pages": [
    {
      "url": "https://example.com/page1",
      "status_code": 200,
      "title": "Page Title",
      "metadata": {
        "title": {
          "content": "Page Title",
          "length": 10
        },
        "meta_description": {
          "content": "Page description...",
          "length": 20
        },
        "canonical": "https://example.com/page1",
        "h1": {
          "content": "Page Heading",
          "count": 1
        },
        "open_graph": {
          "title": "OG Title",
          "description": "OG Description"
        },
        "twitter_card": {
          "title": "Twitter Title",
          "description": "Twitter Description"
        }
      },
      "content": {
        "content": "Extracted page content...",
        "content_length": 500,
        "word_count": 100,
        "truncated": false
      },
      "internal_links_count": 20,
      "internal_links": [
        "https://example.com/page2",
        "https://example.com/page3"
      ]
    }
    // Additional pages...
  ]
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
