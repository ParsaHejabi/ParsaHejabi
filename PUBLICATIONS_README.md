# Publications Auto-Update System

This directory contains scripts to automatically update the publications list in README.md from Google Scholar.

## Files

- `update_publications.py` - Main script that fetches publications from Google Scholar
- `publications.json` - Cache file for publications (fallback when Scholar is unavailable)
- `requirements.txt` - Python dependencies
- `.github/workflows/update-publications.yml` - GitHub Action that runs weekly

## How It Works

1. **Automatic Updates**: A GitHub Action runs weekly (every Monday) to fetch the latest publications from Google Scholar and update README.md
2. **Manual Trigger**: You can manually trigger the workflow from the Actions tab on GitHub
3. **Fallback**: If Google Scholar blocks the automatic fetch (common due to rate limiting), the script uses `publications.json` as a fallback

## Manual Updates

Since Google Scholar may block automated access, you can manually update publications:

1. Edit `publications.json` with your latest publications
2. Run `python update_publications.py` locally
3. Commit the changes to README.md

### Publication Format

```json
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
```

## Local Testing

To test the script locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the script
python update_publications.py
```

## Troubleshooting

- **Google Scholar blocking**: This is normal. The script will fall back to `publications.json`
- **Workflow fails**: Check the Actions tab for error logs. The workflow may need ScraperAPI credentials to bypass Scholar's rate limits
- **To add ScraperAPI**: Add `SCRAPER_API_KEY` as a repository secret (optional, for better reliability)
