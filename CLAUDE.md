# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RSS feed aggregator that generates and manages 19 RSS feeds from AI/tech blogs and communities. Feeds are organized into two OPML files: `blog_rss.xml` (16 blog sources) and `post_rss.xml` (3 forum/community sources). The system is configuration-driven and automatically generates OPML files by category.

## Common Commands

```bash
# Run all RSS generators
python run_all.py

# Run individual script
python script/anthropic_engineering_rss.py

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for scraping scripts)
playwright install

# Dry run - show what would execute
python run_all.py --dry-run

# Stop on first error
python run_all.py --stop-on-error

# Skip OPML generation
python run_all.py --no-opml

# Use custom config
python run_all.py --config my-config.yaml
```

## Architecture

### Configuration System

All RSS sources are defined in `config.yaml`:

```yaml
options:
  output_dir: rss
  script_dir: script
  opml:
    enabled: true
    base_url: https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss
    outputs:
      - name: blog_rss.xml
        title: Blog RSS Subscriptions
        categories: [blog]
      - name: post_rss.xml
        title: Post/Forum RSS Subscriptions
        categories: [post]

scripts:
  - name: Source Name
    file: script_filename.py
    output: output_filename.xml
    title: Display Title
    category: blog  # or 'post'
    enabled: true
```

**Key concepts:**
- `category`: Determines which OPML file includes the feed
- `enabled`: Toggle individual sources on/off
- `opml.outputs`: Generate multiple OPML files by category
- `base_url`: Automatically converts GitHub blob URLs to raw URLs

### Script Patterns

Three script patterns are used depending on the source:

**1. External RSS Importer** (Most common for sources with existing RSS)

Use `ExternalRSSImporter` class from `tldr_tech_rss.py` as template:

```python
class ExternalRSSImporter:
    def __init__(self, rss_url, output_file, feed_title, feed_link, feed_description):
        self.rss_url = rss_url
        self.output_file = output_file
        self.feed_title = feed_title
        self.feed_link = feed_link
        self.feed_description = feed_description

    def fetch_and_reformat(self):
        # Fetches external RSS, parses with ElementTree
        # Reformats using feedgen
        # Saves to rss/{output_file}
```

Example sources: TLDR Tech, DeepLearning.AI, Ben's Bites, TechCrunch AI, Ars Technica AI, etc.

**2. Web Scraping Scripts** (For websites without RSS feeds)

Use `anthropic_engineering_rss.py` or `claude_blog_rss.py` as template:

```python
import asyncio
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

class SourceRSSGenerator:
    async def fetch_posts(self):
        # Use BeautifulSoup to parse HTML
        # Extract articles, titles, dates, descriptions

    def generate_rss(self, articles_data):
        # Create FeedGenerator instance
        # Add entries with article data
```

Example sources: Anthropic Engineering, Cursor Blog, Claude Blog

**3. Reddit/Atom Feeds** (Extended importer for Reddit/Atom format)

Use `reddit_artificial_rss.py` as template:

```python
class ExternalRSSImporter:
    def parse_atom_entry(self, entry):
        # Handle Atom feed entries
        # Extract content, links, dates

    def fetch_and_reformat(self):
        # Handle both RSS and Atom formats
```

Example sources: Reddit r/artificial, Reddit r/ClaudeAI, Reddit r/OpenAI

### Main Execution Flow

`run_all.py` orchestrates everything:

1. **Load config** from YAML/JSON (default: `config.yaml`)
2. **Run scripts** as async subprocesses in sequence
   - Each script generates one RSS file in `rss/` directory
   - Failed scripts don't stop others (unless `stop_on_error: true`)
3. **Generate OPML** files by category
   - Reads `category` field from each script config
   - Includes only successful feeds in OPML
   - Uses `base_url` + `output` for feed URLs
4. **Print summary** with success/failure counts

### Adding New RSS Sources

1. **Create script** in `script/` directory using appropriate pattern
2. **Add to `config.yaml`** under `scripts:` section:
   ```yaml
   - name: Your Source
     file: your_source_rss.py
     output: your_source_rss.xml
     title: Your Source Title
     category: blog  # or create new category
     enabled: true
   ```
3. **Test locally:**
   ```bash
   python script/your_source_rss.py
   python run_all.py
   ```
4. **Verify output:**
   - Check `rss/your_source_rss.xml` exists and is valid
   - Check appropriate OPML file includes your feed

5. **To add new category:**
   - Add new OPML output under `opml.outputs` in `config.yaml`
   - Set `categories: [your_category]`
   - Add new RSS sources with `category: your_category`

## Important Implementation Details

### OPML Generation

- OPML files are generated automatically by `run_all.py`
- Each OPML output corresponds to a `categories` filter
- Failed scripts are excluded from OPML
- Static feeds can be added via `static_feeds` array in config
- GitHub URLs are auto-converted to raw URLs for reliability

### Error Handling

- Default: `stop_on_error: false` - continues on failures
- Failed scripts show "✗ FAIL" in summary but don't block others
- Individual scripts handle their own errors gracefully
- Scripts with `enabled: false` are skipped

### Date Handling

- Always use `datetime.now(timezone.utc)` for current dates
- Parse dates with `dateutil.parser` for flexibility
- Include timezone info: `parsed_date.replace(tzinfo=timezone.utc)`
- Format: RFC 2822 (handled by feedgen)

### File Organization

```
script/              # Individual RSS generator scripts
  ├── *_rss.py      # Script files
rss/                # Generated RSS feeds
  ├── *_rss.xml    # Output files
config.yaml         # Main configuration
run_all.py          # Main orchestrator
blog_rss.xml        # OPML: blog category feeds
post_rss.xml        # OPML: post category feeds
```

### Dependencies

- `feedgen` - RSS feed generation
- `requests` - HTTP client
- `beautifulsoup4` - HTML parsing (scraping scripts)
- `python-dateutil` - Date parsing
- `playwright` - Browser automation (some scraping scripts)
- `pyyaml` - YAML config parsing

### Automation

- GitHub Actions workflow: `.github/workflows/generate-rss.yml`
- Runs: Hourly via cron (`0 * * * *`) and on push to main
- Auto-commits and pushes generated RSS feeds
- Uses personal access token for authentication

## Working Guidelines

### Documentation Policy

**IMPORTANT: Do NOT write summary documents unless the user explicitly requests them.**

- Only create documentation files (README, SUMMARY, REPORT, etc.) when the user specifically asks
- Focus on completing the actual work rather than writing about it
- If documentation is needed, ask the user first

### Code Push Policy

**IMPORTANT: Do NOT push code unless the user explicitly requests it.**

- Always test changes locally before considering a push
- After making changes, wait for user confirmation before pushing
- Only push when user explicitly says "推送代码" or "push the code"
- This prevents pushing untested or broken code to the repository

### Testing Before Pushing

Before any push (when requested):
1. Run `python run_all.py` to verify all feeds work
2. Check that new RSS files are valid
3. Verify OPML files are updated correctly
4. Commit with descriptive message including Co-Authored-By

## Key Constraints

- All RSS feeds must be written to `rss/` directory
- Output filenames must match `output` field in config
- Each script generates exactly one RSS file
- Categories must match an OPML output's `categories` array
- Use absolute URLs in RSS feeds (no relative links)
