"""
Enhanced book scraper using Next.js API for both collection and detail data.

This script performs the following actions:
1. Reads book URLs from a text file
2. Fetches detailed information for each book using Next.js API
3. Saves the collected book data into a JSON file
"""

import json
import asyncio
import aiohttp
from typing import List, Dict, Any
from tqdm.asyncio import tqdm
from config import NUM_WORKERS, DELAY_TIME, BOOKS_URLS_PATH, BOOKS_DATA_PATH, APIConfig 


def extract_book_info_from_url(url: str) -> Dict[str, str]:
    """Extract both ID and name from a SensCritique URL."""
    try:
        parts = url.strip().split('/')
        book_id = parts[-1]
        book_name = parts[-2]
        return {"id": book_id, "name": book_name}
    except (IndexError, ValueError) as e:
        print(f"Error extracting info from URL {url}: {e}")
        return None

def read_book_urls(filename: str) -> List[Dict[str, str]]:
    """Read book URLs from a file and extract their IDs and names."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = f.readlines()
        return [info for url in urls if (info := extract_book_info_from_url(url)) is not None]
    except FileNotFoundError:
        print(f"Error: File {filename} not found")
        return []

async def fetch_book_details(session: aiohttp.ClientSession, 
                           book_id: int,
                           book_name: str,
                           config: APIConfig,
                           semaphore: asyncio.Semaphore) -> Dict:
    """Fetch book details using Next.js API."""
    async with semaphore:
        try:
            await asyncio.sleep(DELAY_TIME)
            
            url = f"{config.BASE_URL}{book_name}/{book_id}/details.json?universe=book&slug={book_name}&id={book_id}"
            headers = dict(config.HEADERS)
            headers['x-nextjs-data'] = '1'
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    book_details = data.get("pageProps", {}).get("__APOLLO_STATE__", {}).get(f"Product:{book_id}")
                    
                    if book_details:
                        return book_details
                    
                    print(f"Error: No product data found for book ID {book_id}")
                    return None
                
                print(f"Error: HTTP {response.status} for book ID {book_id}")
                return None
                
        except Exception as e:
            print(f"Error fetching book {book_id}: {str(e)}")
            return None

async def main():
    """Main execution function."""
    config = APIConfig()

    # Read books from the URL file
    books = read_book_urls(BOOKS_URLS_PATH)
    
    if not books:
        print("No valid books found in the input file")
        return
    
    # for testing
    books = books[:10]

    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(NUM_WORKERS)
        tasks = [
            fetch_book_details(session, int(book['id']), book['name'], config, semaphore)
            for book in books
        ]
        
        results = await tqdm.gather(*tasks, desc="Fetching book details")
        valid_results = [r for r in results if r is not None]

        print(f"\nSuccessfully fetched {len(valid_results)} out of {len(books)} books")
        if valid_results:
            with open(BOOKS_DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(valid_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
