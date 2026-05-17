# AI & Tech Blog RSS Feed Aggregator

A comprehensive RSS feed generator that aggregates AI and technology content from leading sources. This project automatically generates RSS feeds for 111 active AI/tech blogs and newsletters (116 configured, 5 currently disabled), making it easy to stay updated with the latest developments.

## 📡 RSS Sources

| Source | Description | Feed |
|--------|-------------|------|
| **Anthropic Engineering** | Official engineering blog from Anthropic | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/anthropic_engineering_rss.xml) |
| **Cursor Blog** | IDE and AI-powered development tools | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/cursor_blog_rss.xml) |
| **Claude Blog** | Official Claude and Anthropic product updates | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/claude_blog_rss.xml) |
| **OpenAI Blog** | Research and product updates from OpenAI | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/openai_blog_rss.xml) |
| **LangChain Blog** | LLM application development framework | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/langchain_blog_rss.xml) |
| **Andrej Karpathy Blog** | Deep learning and AI research insights | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/karpathy_blog_rss.xml) |
| **MarkTechPost** | Machine learning and AI news | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/marktechpost_rss.xml) |
| **Azure Blog** | Cloud computing and AI from Microsoft | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/azure_blog_rss.xml) |
| **TLDR Tech** | Daily tech news summaries | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/tldr_tech_rss.xml) |
| **The Batch | DeepLearning.AI** | The Batch - Weekly AI news | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/deeplearning_batch_rss.xml) |
| **Ben's Bites** | Daily AI news and insights | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/bensbites_rss.xml) |
| **TechCrunch AI** | AI industry news and analysis | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/techcrunch_ai_rss.xml) |
| **TechCrunch AI Tag** | TechCrunch posts tagged with AI | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/techcrunch_ai_tag_rss.xml) |
| **TechCrunch Generative AI** | TechCrunch coverage of generative AI | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/techcrunch_generative_ai_rss.xml) |
| **Wired AI** | Wired's latest AI coverage | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/wired_ai_rss.xml) |
| **The Verge AI** | AI coverage from The Verge | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/verge_ai_rss.xml) |
| **Import AI** | Jack Clark's Import AI newsletter | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/importai_rss.xml) |
| **VentureBeat AI** | AI news from VentureBeat | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/venturebeat_ai_rss.xml) |
| **AI News** | AI industry news and analysis from artificialintelligence-news.com | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/artificial_intelligence_news_rss.xml) |
| **Ars Technica AI** | In-depth AI coverage and analysis | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/arstechnica_ai_rss.xml) |
| **雷峰网 AI** | AI news and articles in Chinese | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/leiphone_ai_rss.xml) |
| **David Heinemeier Hansson** | Web development, design, and technology | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/david_heinemeier_hansson_rss.xml) |
| **Smashing Magazine** | Web Design and Development articles | [RSS](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/rss/smashing_magazine_rss.xml) |

Plus 87 active HN Popular Blogs (curated from Hacker News). For the full list, see `blog_rss.xml` or `config.yaml`.

## 📦 All-in-One OPML Feeds

### Blog Feeds (111 active sources)

Subscribe to all blog sources at once:
```
https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/blog_rss.xml
```

Import this file into your RSS reader to get all feeds in one go.

## ✨ Features

- **Automated Updates**: GitHub Actions run regularly to keep feeds fresh
- **OPML Support**: `blog_rss.xml` includes all blog feeds
- **Multiple Sources**: 111 active RSS feeds (116 configured, 5 disabled)
- **Standard RSS Format**: Compatible with all RSS readers
- **Robust Parsing**: Handles various date formats and content types

## 🚀 Quick Start

### Option 1: Subscribe Directly

Copy any of the RSS feed URLs above and paste them into your favorite RSS reader:
- Feedly
- Inoreader
- NewsBlur
- FreshRSS
- NetNewsWire
- Or any RSS reader of your choice

### Option 2: Use the OPML File

1. Download the OPML file: [blog_rss.xml](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/blog_rss.xml)
2. Import it into your RSS reader
3. All 111 active feeds will be added automatically

### Option 3: Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run all RSS generators
python run_all.py

# Or run individual feeds
python script/anthropic_engineering_rss.py
```

## 📁 Project Structure

```
.
├── config.yaml              # Configuration file for all RSS sources
├── run_all.py              # Script to run all RSS generators
├── blog_rss.xml            # OPML file with all blog feeds
├── script/                 # RSS generator scripts
│   ├── anthropic_engineering_rss.py
│   ├── cursor_rss.py
│   ├── claude_blog_rss.py
│   └── external_rss_importer.py
└── rss/                    # Generated RSS feed files
    ├── anthropic_engineering_rss.xml
    ├── cursor_blog_rss.xml
    └── ... (one per source)
```

## 🔧 Configuration

All RSS sources are configured in `config.yaml`. To add a new source:

1. Create a new script in the `script/` directory
2. Add an entry to `config.yaml` under the `scripts` section
3. Run `python run_all.py` to generate the feed

### Using the RSS Feed Converter Skill

This project includes a built-in skill (`.claude/skills/rss-feed-converter/SKILL.md`) that helps convert any URL to an RSS feed automatically:

- **For existing RSS feeds**: Automatically uses `external_rss_importer.py` to import the feed
- **For web pages without RSS**: Creates a custom scraping script based on templates like `cursor_rss.py`

When using Claude Code to work on this project, simply provide a URL and the skill will:
1. Detect if it's an RSS feed or a web page
2. Generate the appropriate script or configuration
3. Add it to `config.yaml` automatically

### Manual Configuration

Example configuration for existing RSS feeds:
```yaml
scripts:
  - name: Your Source Name
    file: external_rss_importer.py
    output: your_source_rss.xml
    title: Your Source Title
    category: blog
    enabled: true
    rssUrl: https://example.com/feed.xml
```

Example configuration for custom scrapers:
```yaml
scripts:
  - name: Your Source Name
    file: your_source_rss.py
    output: your_source_rss.xml
    title: Your Source Title
    category: blog
    enabled: true
```

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add new RSS sources
- Improve existing parsers
- Fix bugs
- Update documentation

## 📄 License

This project is open source and available under the MIT License.

## 🔗 Links

- **Repository**: [SebastianLavertheDe/blog-rss-feed](https://github.com/SebastianLavertheDe/blog-rss-feed)
- **OPML Feed**: [blog_rss.xml](https://raw.githubusercontent.com/SebastianLavertheDe/blog-rss-feed/main/blog_rss.xml)
