from itertools import cycle
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manages a rotating list of proxies."""
    
    def __init__(self, proxy_file: str):
        self.proxies = self._load_proxies(proxy_file)
        self.proxy_cycle = cycle(self.proxies)
        self.working_proxies = set(self.proxies)
        self.failed_proxies = set()
        logger.info(f"Loaded {len(self.proxies)} proxies")

    def _load_proxies(self, proxy_file: str) -> List[str]:
        """Load proxies from file."""
        try:
            with open(proxy_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error(f"Proxy file {proxy_file} not found")
            return []

    def get_next_proxy(self) -> Optional[str]:
        """Get next working proxy."""
        if not self.working_proxies:
            self._reset_proxies()
            
        for _ in range(len(self.proxies)):
            proxy = next(self.proxy_cycle)
            if proxy in self.working_proxies:
                return proxy
        return None

    def mark_proxy_failed(self, proxy: str) -> None:
        """Mark a proxy as failed."""
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)
            self.failed_proxies.add(proxy)
            logger.warning(f"Marked proxy as failed: {proxy}")

    def _reset_proxies(self) -> None:
        """Reset all proxies to working state."""
        self.working_proxies = set(self.proxies)
        self.failed_proxies.clear()
        logger.info("Reset all proxies to working state")