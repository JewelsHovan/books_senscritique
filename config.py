"""
Configuration for the scraping process.
"""
from dataclasses import dataclass, field
from typing import Dict

NUM_WORKERS = 10

DELAY_TIME = 1

# Data paths
BOOKS_URLS_PATH = 'output/book_urls.txt'
BOOKS_DATA_PATH = 'output/books_data.json'


# API config
@dataclass
class APIConfig:
    """Configuration for Next.js API requests."""
    BASE_URL: str = "https://www.senscritique.com/_next/data/NZC4gJK0x7_I2hUZze_-h/fr/universe/"
    HEADERS: Dict[str, str] = field(default_factory=lambda: {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'dnt': '1',
        'referer': 'https://www.senscritique.com',
        'sec-ch-ua': '"Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })
    
    def __post_init__(self):
        """Validate the configuration after initialization."""
        if not isinstance(self.BASE_URL, str) or not self.BASE_URL.startswith("http"):
            raise ValueError("BASE_URL must be a valid HTTP/HTTPS URL string.")
        if not isinstance(self.HEADERS, dict):
            raise TypeError("HEADERS must be a dictionary.")
        for key, value in self.HEADERS.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("HEADERS keys and values must be strings.")
