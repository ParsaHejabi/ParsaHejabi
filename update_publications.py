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
import time
from typing import List, Dict


def fetch_publications_scholarly(scholar_id: str) -> List[Dict]:
    """
    Fetch publications from Google Scholar using the scholarly library.
    
    Note: This may fail due to Google Scholar's rate limiting or blocking.
    """
    try:
        from scholarly import scholarly, ProxyGenerator
        
        # Try to set up a proxy generator to avoid rate limiting
        try:
            pg = ProxyGenerator()
            success = pg.ScraperAPI(os.environ.get('SCRAPER_API_KEY', ''))
            if not success:
                # Try free proxies as fallback
                success = pg.FreeProxies()
            if success:
                scholarly.use_proxy(pg)
                print("Using proxy to access Google Scholar...")
        except Exception as proxy_error:
            print(f"Note: Could not set up proxy: {proxy_error}", file=sys.stderr)
            print("Attempting direct connection...", file=sys.stderr)
        
        # Add a small delay to be respectful to Google's servers
        time.sleep(2)
        
        # Search for author by ID
        print(f"Searching for author with ID: {scholar_id}")
        author = scholarly.search_author_id(scholar_id)
        
        # Fill in author details including publications
        print("Fetching author details and publications...")
        author = scholarly.fill(author, sections=['publications'])
        
        publications = []
        pub_list = author.get('publications', [])
        print(f"Found {len(pub_list)} publications")
        
        for i, pub in enumerate(pub_list):
            try:
                print(f"Processing publication {i+1}/{len(pub_list)}...")
                # Fill in publication details
                pub_details = scholarly.fill(pub)
                
                title = pub_details.get('bib', {}).get('title', 'Unknown Title')
                authors = pub_details.get('bib', {}).get('author', 'Unknown Authors')
                year = pub_details.get('bib', {}).get('pub_year', 'N/A')
                venue = pub_details.get('bib', {}).get('venue', 'N/A')
                citations = pub_details.get('num_citations', 0)
                
                # Get publication URL if available
                pub_url = pub_details.get('pub_url', '')
                eprint_url = pub_details.get('eprint_url', '')
                url = pub_url or eprint_url
                
                publications.append({
                    'title': title,
                    'authors': authors,
                    'year': year,
                    'venue': venue,
                    'citations': citations,
                    'url': url
                })
                
                # Be respectful with rate limiting
                time.sleep(1)
            except Exception as pub_error:
                print(f"Error processing publication {i+1}: {pub_error}", file=sys.stderr)
                continue
        
        # Sort by year (descending) and then by citations
        publications.sort(key=lambda x: (-(int(x['year']) if x['year'] != 'N/A' else 0), -x['citations']))
        
        # Save to cache file
        if publications:
            save_publications_cache(publications)
        
        return publications
    except Exception as e:
        print(f"Error fetching publications from Google Scholar: {e}", file=sys.stderr)
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


def format_publications_markdown(publications: List[Dict]) -> str:
    """Format publications as markdown list."""
    if not publications:
        return "*No publications found. Please update publications.json manually or wait for automatic update.*\n"
    
    markdown = ""
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
    # Google Scholar ID for Parsa Hejabi
    scholar_id = 'icZ4Gd0AAAAJ'
    
    # Try to fetch from Google Scholar
    print("Attempting to fetch publications from Google Scholar...")
    publications = fetch_publications_scholarly(scholar_id)
    
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
    publications_md = format_publications_markdown(publications)
    
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
