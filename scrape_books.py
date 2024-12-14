"""
Enhanced book scraper using Next.js API for both collection and detail data.

This script performs the following actions:
1. Reads book URLs from a text file
2. Fetches detailed information for each book using Next.js API
3. Saves the collected book data into a JSON file with periodic checkpoints
"""

import json
import asyncio
import aiohttp
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from tqdm.asyncio import tqdm
from config import NUM_WORKERS, DELAY_TIME, BOOKS_URLS_PATH, BOOKS_DATA_PATH, APIConfig
from proxy_manager import ProxyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
CHECKPOINT_INTERVAL = 1000  # Save every 1000 books
CHECKPOINT_DIR = Path("checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)
BOOKS_PER_FILE = 10000
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def save_checkpoint(results: List[Dict], checkpoint_num: int) -> None:
    """Save intermediate results to a checkpoint file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_file = CHECKPOINT_DIR / f"checkpoint_{checkpoint_num}_{timestamp}.json"
    try:
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"Checkpoint {checkpoint_num} saved: {checkpoint_file}")
    except Exception as e:
        logger.error(f"Failed to save checkpoint {checkpoint_num}: {e}")

def load_latest_checkpoint() -> tuple[List[Dict], set]:
    """Load the most recent checkpoint if it exists."""
    try:
        checkpoint_files = sorted(CHECKPOINT_DIR.glob("checkpoint_*.json"))
        if not checkpoint_files:
            return [], set()

        latest_checkpoint = checkpoint_files[-1]
        with open(latest_checkpoint, 'r', encoding='utf-8') as f:
            results = json.load(f)
        processed_ids = {str(book.get('id')) for book in results}
        logger.info(f"Loaded checkpoint: {latest_checkpoint}")
        return results, processed_ids
    except Exception as e:
        logger.error(f"Failed to load checkpoint: {e}")
        return [], set()

def extract_book_info_from_url(url: str) -> Dict[str, str]:
    """Extract both ID and name from a SensCritique URL."""
    try:
        parts = url.strip().split('/')
        book_id = parts[-1]
        book_name = parts[-2]
        return {"id": book_id, "name": book_name}
    except (IndexError, ValueError) as e:
        logger.error(f"Error extracting info from URL {url}: {e}")
        return None

def read_book_urls(filename: str) -> List[Dict[str, str]]:
    """Read book URLs from a file and extract their IDs and names."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = f.readlines()
        results = [info for url in urls if (info := extract_book_info_from_url(url)) is not None]
        logger.info(f"Successfully read {len(results)} valid book URLs")
        return results
    except FileNotFoundError:
        logger.error(f"Error: File {filename} not found")
        return []

async def fetch_book_details(
    session: aiohttp.ClientSession,
    book_id: int,
    book_name: str,
    config: APIConfig,
    semaphore: asyncio.Semaphore,
    proxy_manager: ProxyManager,
    retry_count: int = 3
) -> Dict:
    """Fetch book details using Next.js API with retries and proxy rotation."""
    for attempt in range(retry_count):
        proxy = proxy_manager.get_next_proxy()
        if not proxy:
            logger.error("No working proxies available")
            return None

        async with semaphore:
            try:
                await asyncio.sleep(DELAY_TIME)
                
                url = f"{config.BASE_URL}{book_name}/{book_id}/details.json?universe=book&slug={book_name}&id={book_id}"
                headers = dict(config.HEADERS)
                headers['x-nextjs-data'] = '1'
                
                async with session.get(url, headers=headers, proxy=f"http://{proxy}") as response:
                    if response.status == 200:
                        data = await response.json()
                        book_details = data.get("pageProps", {}).get("__APOLLO_STATE__", {}).get(f"Product:{book_id}")
                        
                        if book_details:
                            # Extract only relevant fields and clean the data
                            cleaned_details = {
                                "id": book_details.get("id"),
                                "title": book_details.get("title"),
                                "subtitle": book_details.get("subtitle"),
                                "rating": book_details.get("rating"),
                                "year": book_details.get("yearOfProduction"),
                                "french_release_date": book_details.get("frenchReleaseDate"),
                                "original_language": book_details.get("originalLanguage"),
                                "synopsis": book_details.get("synopsis"),
                                "isbn": book_details.get("isbn", []),
                                "cover_image": book_details.get("medias({\"backdropSize\":\"1200\"})").get("picture"),
                                "stats": {
                                    "rating_count": book_details.get("stats", {}).get("ratingCount", 0),
                                    "review_count": book_details.get("stats", {}).get("reviewCount", 0),
                                    "wish_count": book_details.get("stats", {}).get("wishCount", 0)
                                },
                                "authors": [
                                    {
                                        "name": author.get("name"),
                                        "id": author.get("person_id"),
                                        "url": author.get("url")
                                    }
                                    for author in book_details.get("authors", []) if author
                                ],
                                "publishers": [
                                    {
                                        "name": publisher.get("name"),
                                        "id": publisher.get("person_id"),
                                        "url": publisher.get("url")
                                    }
                                    for publisher in book_details.get("publishers", []) if publisher
                                ]
                            }
                            
                            # Remove None values
                            cleaned_details = {k: v for k, v in cleaned_details.items() if v is not None}
                            return cleaned_details
                        
                        logger.warning(f"No product data found for book ID {book_id}")
                        return None
                    
                    logger.warning(f"HTTP {response.status} for book ID {book_id} using proxy {proxy}")
                    proxy_manager.mark_proxy_failed(proxy)
                    if attempt < retry_count - 1:
                        await asyncio.sleep(DELAY_TIME * (attempt + 1))
                    
            except Exception as e:
                logger.error(f"Error fetching book {book_id} with proxy {proxy}: {str(e)}")
                proxy_manager.mark_proxy_failed(proxy)
                if attempt < retry_count - 1:
                    await asyncio.sleep(DELAY_TIME * (attempt + 1))
                
    return None

def save_split_results(results: List[Dict], base_filename: str) -> None:
    """Save results split into multiple files of BOOKS_PER_FILE books each."""
    try:
        for i in range(0, len(results), BOOKS_PER_FILE):
            chunk = results[i:i + BOOKS_PER_FILE]
            file_number = i // BOOKS_PER_FILE + 1
            output_file = OUTPUT_DIR / f"{base_filename}_{file_number}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(chunk)} books to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save split results: {e}")

async def main():
    """Main execution function."""
    config = APIConfig()
    proxy_manager = ProxyManager("proxies/http_proxies.txt")
    logger.info("Starting book scraping process")

    # Load the latest checkpoint if it exists
    existing_results, processed_ids = load_latest_checkpoint()
    
    # Read books from the URL file
    books = read_book_urls(BOOKS_URLS_PATH)[:1000]
    
    if not books:
        logger.error("No valid books found in the input file")
        return

    # Filter out already processed books
    books_to_process = [book for book in books if book['id'] not in processed_ids]
    logger.info(f"Processing {len(books_to_process)} new books")

    results = list(existing_results)
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(NUM_WORKERS)
        tasks = [
            fetch_book_details(
                session, 
                int(book['id']), 
                book['name'], 
                config, 
                semaphore,
                proxy_manager
            )
            for book in books_to_process
        ]
        
        # Fixed progress tracking
        for i, task in enumerate(tqdm.as_completed(tasks, total=len(tasks))):
            result = await task
            if result:
                results.append(result)
                
                # Save checkpoint every CHECKPOINT_INTERVAL books
                if (i + 1) % CHECKPOINT_INTERVAL == 0:
                    checkpoint_num = (i + 1) // CHECKPOINT_INTERVAL
                    save_checkpoint(results, checkpoint_num)

        logger.info(f"Successfully fetched {len(results)} out of {len(books)} books")
        if results:
            try:
                # Save in split files
                timestamp = datetime.now().strftime("%Y%m%d")
                base_filename = f"books_{timestamp}"
                save_split_results(results, base_filename)
                
                # Also save a metadata file with information about the split
                metadata = {
                    "total_books": len(results),
                    "files_count": (len(results) + BOOKS_PER_FILE - 1) // BOOKS_PER_FILE,
                    "books_per_file": BOOKS_PER_FILE,
                    "date_created": timestamp
                }
                with open(OUTPUT_DIR / f"{base_filename}_metadata.json", 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Results split and saved in {OUTPUT_DIR} directory")
            except Exception as e:
                logger.error(f"Failed to save final results: {e}")

if __name__ == "__main__":
    asyncio.run(main())
