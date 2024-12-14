import requests
import json
from typing import Dict, List, Optional

def scrape_book_details(book_data: List[Dict[str, str]]) -> List[Optional[Dict]]:
    """
    Scrapes book details from senscritique.com for multiple books.

    Args:
        book_data: A list of dictionaries, where each dictionary contains the 'id' and 'name' (slug) of a book.

    Returns:
        A list of dictionaries, where each dictionary contains the details of a book.
        Returns None for a book if there was an error during scraping.
    """

    base_url = "https://www.senscritique.com/_next/data/NZC4gJK0x7_I2hUZze_-h/fr/universe/"  # Replace with the correct build ID if it changes
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'dnt': '1',
        'referer': 'https://www.senscritique.com',  # You might need to adjust this based on the book
        'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-nextjs-data': '1',
    }

    results = []
    for book in book_data:
        book_id = book['id']
        book_name = book['name']
        url = f"{base_url}{book_name}/{book_id}/details.json?universe=book&slug={book_name}&id={book_id}"
        try:
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            data = response.json()
            book_details = data.get("pageProps", {}).get("__APOLLO_STATE__", {}).get(f"Product:{book_id}")

            if book_details:
                results.append(book_details)
            else:
                print(f"Warning: Could not find book details for ID: {book_id}, Name: {book_name}")
                results.append(None)

        except requests.exceptions.RequestException as e:
            print(f"Error scraping book ID: {book_id}, Name: {book_name}: {e}")
            results.append(None)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for book ID: {book_id}, Name: {book_name}: {e}")
            results.append(None)

    return results

# Example Usage
books_to_scrape = [
    {"id": "103735624", "name": "le_guide_nature_les_oiseaux"},
    {"id": "93871982", "name":"l_impossible_retour"},
    {"id": "97899293", "name": "jacaranda"}
    # Add more books here...
]

scraped_data = scrape_book_details(books_to_scrape)

# Print or process the scraped data
for i, book_details in enumerate(scraped_data):
    if book_details:
        print(f"----- Book {i+1} -----")
        print(f"Title: {book_details.get('title')}")
        print(f"Synopsis: {book_details.get('synopsis')}")
        print(f"Authors: {[author.get('name') for author in book_details.get('authors', [])]}")
        # ... extract other fields as needed ...
    else:
        print(f"----- Book {i+1} -----")
        print("Failed to scrape book details.")
