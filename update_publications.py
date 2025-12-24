#!/usr/bin/env python3
"""
Script to fetch publications from Google Scholar and update README.md

This script attempts to automatically fetch publications from Google Scholar.
If automatic fetching fails due to rate limiting or blocking, publications
can be manually maintained in a publications.json file.
"""

import json
import os
import re
import sys
from typing import List, Dict

# Configuration constants
DEFAULT_SCHOLAR_ID = 'icZ4Gd0AAAAJ'  # Parsa Hejabi's Google Scholar ID
SERP_API_KEY_ENV = 'SERP_API_KEY'


def fetch_publications_serpapi(scholar_id: str) -> List[Dict]:
    """
    Fetch publications from Google Scholar using SerpAPI.
    
    SerpAPI provides a reliable API with built-in proxy rotation and anti-CAPTCHA handling.
    """
    try:
        from serpapi import GoogleSearch
        
        # Get API key from environment
        api_key = os.environ.get(SERP_API_KEY_ENV, '').strip()
        
        if not api_key:
            print(f"Warning: {SERP_API_KEY_ENV} environment variable is not set.", file=sys.stderr)
            print("SerpAPI requires an API key to function. Please set the environment variable.", file=sys.stderr)
            return []
        
        print(f"Fetching publications for author ID: {scholar_id} using SerpAPI...")
        
        # Set up SerpAPI parameters
        params = {
            "engine": "google_scholar_author",
            "author_id": scholar_id,
            "api_key": api_key
        }
        
        # Make the API request
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Extract articles from results
        articles = results.get("articles", [])
        print(f"Found {len(articles)} publications from SerpAPI")
        
        publications = []
        for article in articles:
            # Extract publication details
            title = article.get('title', 'Unknown Title')
            authors = article.get('authors', 'Unknown Authors')
            year = article.get('year', 'N/A')
            
            # Get citations count
            cited_by = article.get('cited_by', {})
            citations = cited_by.get('value', 0) if isinstance(cited_by, dict) else 0
            
            # Get publication URL
            url = article.get('link', '')
            
            # Extract venue/publication info if available
            venue = article.get('publication', 'N/A')
            
            publications.append({
                'title': title,
                'authors': authors,
                'year': str(year),
                'venue': venue,
                'citations': citations,
                'url': url
            })
        
        # Sort by year (descending) and then by citations
        publications.sort(key=lambda x: (-(int(x['year']) if x['year'] != 'N/A' and str(x['year']).isdigit() else 0), -x['citations']))
        
        # Save to cache file
        if publications:
            save_publications_cache(publications)
        
        return publications
    except ImportError as e:
        print(f"Error: SerpAPI library not installed. Please install it with: pip install google-search-results", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error fetching publications from SerpAPI: {e}", file=sys.stderr)
        return []


def load_publications_cache() -> List[Dict]:
    """Load publications from cache file."""
    cache_file = 'publications.json'
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                publications = json.load(f)
                print(f"Loaded {len(publications)} publications from cache file")
                return publications
        except Exception as e:
            print(f"Error loading cache file: {e}", file=sys.stderr)
    return []


def save_publications_cache(publications: List[Dict]):
    """Save publications to cache file."""
    cache_file = 'publications.json'
    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(publications, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(publications)} publications to cache file")
    except Exception as e:
        print(f"Error saving cache file: {e}", file=sys.stderr)


def format_publications_markdown(publications: List[Dict], scholar_id: str = None) -> str:
    """Format publications as markdown list."""
    if not publications:
        return "*No publications found. Please update publications.json manually or wait for automatic update.*\n"
    
    # Add note with link to Google Scholar profile if scholar_id is provided
    markdown = ""
    if scholar_id:
        scholar_url = f"https://scholar.google.com/citations?user={scholar_id}&hl=en"
        markdown = f"*Publications are automatically updated weekly from my [Google Scholar profile]({scholar_url}).*\n\n"
    
    for i, pub in enumerate(publications, 1):
        title = pub['title']
        if pub.get('url'):
            title = f"[{title}]({pub['url']})"
        
        markdown += f"{i}. **{title}**\n"
        markdown += f"   - Authors: {pub['authors']}\n"
        markdown += f"   - Year: {pub['year']}"
        if pub.get('venue') and pub['venue'] != 'N/A':
            markdown += f" | Venue: {pub['venue']}"
        markdown += f"\n   - Citations: {pub['citations']}\n\n"
    
    return markdown


def update_readme(publications_md: str) -> bool:
    """Update README.md with publications section."""
    readme_path = 'README.md'
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {readme_path} not found", file=sys.stderr)
        return False
    
    # Define the publications section markers
    start_marker = "<!-- PUBLICATIONS_START -->"
    end_marker = "<!-- PUBLICATIONS_END -->"
    
    # Create the new publications section
    new_section = f"{start_marker}\n## 📚 Publications\n\n{publications_md}{end_marker}"
    
    # Check if markers already exist
    if start_marker in content and end_marker in content:
        # Replace existing section
        pattern = f"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
        new_content = re.sub(pattern, new_section, content, flags=re.DOTALL)
    else:
        # Append to end of file
        if not content.endswith('\n'):
            content += '\n'
        new_content = content + '\n' + new_section + '\n'
    
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully updated {readme_path}")
        return True
    except Exception as e:
        print(f"Error writing to {readme_path}: {e}", file=sys.stderr)
        return False


def main():
    """Main function."""
    # Get Google Scholar ID from environment variable or use default
    scholar_id = os.environ.get('SCHOLAR_ID', DEFAULT_SCHOLAR_ID)
    
    # Try to fetch from Google Scholar via SerpAPI
    print("Attempting to fetch publications from Google Scholar using SerpAPI...")
    publications = fetch_publications_serpapi(scholar_id)
    
    # If fetching failed, try to load from cache
    if not publications:
        print("\nAutomatic fetching failed. Checking for cached publications...")
        publications = load_publications_cache()
    
    if not publications:
        print("\nNo publications available. The README will be updated with a placeholder.")
        print("To manually add publications, create a publications.json file with the following format:")
        print("""
[
  {
    "title": "Your Paper Title",
    "authors": "Author1, Author2, Author3",
    "year": "2024",
    "venue": "Conference/Journal Name",
    "citations": 10,
    "url": "https://link-to-paper.com"
  }
]
""")
    else:
        print(f"\nUsing {len(publications)} publications")
    
    print("\nFormatting publications as markdown...")
    publications_md = format_publications_markdown(publications, scholar_id)
    
    print("Updating README.md...")
    success = update_readme(publications_md)
    
    if success:
        print("\n✓ Done!")
        return 0
    else:
        print("\n✗ Failed to update README.md", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
