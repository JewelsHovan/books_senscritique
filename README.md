# SensCritique Book Scraper

A Python-based scraper for collecting book information from SensCritique using their Next.js API. This project includes tools for extracting book URLs from sitemaps and fetching detailed book information.

## Features

- Extract book URLs from XML sitemaps
- Asynchronous book data collection
- Proxy rotation support
- Checkpoint system for data persistence
- Configurable number of workers and delay times
- Detailed logging system
- Split output files for better data management

## Prerequisites

- Python 3.8+
- Required Python packages (see requirements.txt)
- HTTP proxies list (optional but recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JewelsHovan/books_senscritique
cd senscritique-book-scraper
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Project Structure

```
├── collect_books.py     # Sitemap URL extractor
├── config.py           # Configuration settings
├── proxy_manager.py    # Proxy rotation handler
├── scrape_books.py     # Main scraping script
├── output/            # Directory for scraped data
├── checkpoints/       # Directory for saving progress
└── proxies/          # Directory for proxy lists
```

## Usage

### 1. Collecting Book URLs

First, collect the book URLs from the sitemap:

```bash
python collect_books.py
```

This will:
- Parse the sitemap XML file
- Extract book URLs
- Save them to `output/book_urls.txt`

### 2. Scraping Book Details

After collecting URLs, run the main scraper:

```bash
python scrape_books.py
```

This will:
- Read URLs from `output/book_urls.txt`
- Fetch detailed information for each book
- Save results in JSON format in the `output` directory
- Create checkpoints in the `checkpoints` directory

## Configuration

You can modify the following settings in `config.py`:

- `NUM_WORKERS`: Number of concurrent workers (default: 10)
- `DELAY_TIME`: Delay between requests in seconds (default: 1)
- `BOOKS_URLS_PATH`: Path to the file containing book URLs
- `BOOKS_DATA_PATH`: Path for saving scraped data

## Proxy Setup

1. Create a file `proxies/http_proxies.txt`
2. Add your HTTP proxies, one per line in the format:
```
ip:port
username:password@ip:port
```

## Output Format

The scraped data is saved in JSON files with the following structure:

```json
{
  "id": "book_id",
  "title": "Book Title",
  "subtitle": "Book Subtitle",
  "rating": "Average Rating",
  "year": "Publication Year",
  "french_release_date": "French Release Date",
  "original_language": "Original Language",
  "synopsis": "Book Synopsis",
  "isbn": ["ISBN Numbers"],
  "cover_image": "Cover Image URL",
  "stats": {
    "rating_count": "Number of Ratings",
    "review_count": "Number of Reviews",
    "wish_count": "Number of Wishlist Additions"
  },
  "authors": [...],
  "publishers": [...]
}
```

## Error Handling

- The scraper includes comprehensive error logging
- Failed requests are automatically retried
- Progress is saved regularly through checkpoints
- Proxy rotation helps avoid rate limiting

## Limitations

- Respect SensCritique's robots.txt and terms of service
- Use appropriate delays between requests
- Consider using proxies to avoid IP blocks


## Contributing

Contributions to this project are welcome! Please feel free to submit pull requests or open issues to suggest improvements or report bugs.
