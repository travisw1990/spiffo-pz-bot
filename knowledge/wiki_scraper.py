"""Wiki scraper for Project Zomboid wiki"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import re


class WikiScraper:
    """Scrapes and processes Project Zomboid wiki content"""

    BASE_URL = "https://pzwiki.net"

    def __init__(self, delay: float = 1.0):
        """
        Initialize wiki scraper

        Args:
            delay: Delay between requests (seconds) to be respectful
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })

    def get_all_pages(self) -> List[str]:
        """
        Get list of all wiki page URLs

        Returns:
            List of page URLs
        """
        print("Fetching list of all wiki pages...")

        # Start with main category pages and common pages
        seed_pages = [
            "/wiki/Main_Page",
            "/wiki/Gameplay",
            "/wiki/Items",
            "/wiki/Mechanics",
            "/wiki/Skills",
            "/wiki/Moodles",
            "/wiki/Survival",
            "/wiki/Crafting",
            "/wiki/Farming",
            "/wiki/Fishing",
            "/wiki/Trapping",
            "/wiki/Cooking",
            "/wiki/Carpentry",
            "/wiki/Electrical",
            "/wiki/Metalworking",
            "/wiki/First_Aid",
            "/wiki/Combat",
            "/wiki/Zombies",
            "/wiki/Vehicles",
            "/wiki/Weather",
            "/wiki/Multiplayer",
            "/wiki/Sandbox",
            "/wiki/Game_Modes",
        ]

        discovered_pages = set(seed_pages)
        pages_to_crawl = list(seed_pages)
        crawled_pages = set()

        # Crawl pages and discover links (limited crawl)
        max_pages = 200  # Limit to prevent excessive crawling

        while pages_to_crawl and len(discovered_pages) < max_pages:
            page = pages_to_crawl.pop(0)

            if page in crawled_pages:
                continue

            crawled_pages.add(page)

            try:
                # Find links on this page
                links = self._extract_links(page)

                for link in links:
                    if link not in discovered_pages and link.startswith("/wiki/"):
                        discovered_pages.add(link)
                        if len(discovered_pages) < max_pages:
                            pages_to_crawl.append(link)

                print(f"Discovered {len(discovered_pages)} pages so far...")
                time.sleep(self.delay)

            except Exception as e:
                print(f"Error crawling {page}: {e}")
                continue

        return list(discovered_pages)

    def _extract_links(self, page_path: str) -> List[str]:
        """Extract wiki links from a page"""
        url = f"{self.BASE_URL}{page_path}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all links in the main content
            content = soup.find('div', {'id': 'content'})
            if not content:
                return []

            links = []
            for link in content.find_all('a', href=True):
                href = link['href']
                if href.startswith('/wiki/') and ':' not in href:  # Skip special pages
                    links.append(href)

            return links

        except Exception as e:
            print(f"Error extracting links from {page_path}: {e}")
            return []

    def scrape_page(self, page_path: str) -> Optional[Dict[str, str]]:
        """
        Scrape a single wiki page

        Args:
            page_path: Path to wiki page (e.g., "/wiki/Zombies")

        Returns:
            Dict with 'title', 'url', and 'content', or None if failed
        """
        url = f"{self.BASE_URL}{page_path}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title = soup.find('h1', {'id': 'firstHeading'})
            title_text = title.get_text().strip() if title else page_path.split('/')[-1]

            # Extract main content
            content_div = soup.find('div', {'id': 'mw-content-text'})

            if not content_div:
                return None

            # Remove unwanted elements
            for element in content_div.find_all(['script', 'style', 'nav', 'footer', 'table']):
                element.decompose()

            # Get text content
            text = content_div.get_text()

            # Clean up text
            text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove excessive newlines
            text = re.sub(r'[ \t]+', ' ', text)  # Normalize spaces
            text = text.strip()

            return {
                'title': title_text,
                'url': url,
                'content': text
            }

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    def scrape_all(self, page_paths: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        Scrape multiple wiki pages

        Args:
            page_paths: List of page paths to scrape, or None to discover and scrape all

        Returns:
            List of page data dictionaries
        """
        if page_paths is None:
            page_paths = self.get_all_pages()

        pages_data = []
        total = len(page_paths)

        print(f"\nScraping {total} wiki pages...")

        for i, path in enumerate(page_paths, 1):
            print(f"[{i}/{total}] Scraping {path}...")

            page_data = self.scrape_page(path)

            if page_data:
                pages_data.append(page_data)

            time.sleep(self.delay)

        print(f"\nSuccessfully scraped {len(pages_data)} pages")
        return pages_data

    def search_wiki_live(self, query: str) -> Optional[str]:
        """
        Search PZ wiki and return the most relevant page content

        Args:
            query: Search query

        Returns:
            Content of most relevant page, or None if not found
        """
        # Use wiki search
        search_url = f"{self.BASE_URL}/w/index.php"
        params = {
            'search': query,
            'title': 'Special:Search'
        }

        try:
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Check if redirected to a page (exact match)
            if '/wiki/' in response.url and '/Special:' not in response.url:
                # Redirected to exact page
                content_div = soup.find('div', {'id': 'mw-content-text'})
                if content_div:
                    # Get title
                    title = soup.find('h1', {'id': 'firstHeading'})
                    title_text = title.get_text().strip() if title else "Unknown"

                    # Remove unwanted elements
                    for element in content_div.find_all(['script', 'style', 'nav', 'footer', 'table']):
                        element.decompose()

                    text = content_div.get_text()
                    text = re.sub(r'\n\s*\n', '\n\n', text)
                    text = re.sub(r'[ \t]+', ' ', text)

                    return f"# {title_text}\n\n{text.strip()}"

            # Otherwise, get first search result
            results = soup.find('ul', {'class': 'mw-search-results'})
            if results:
                first_result = results.find('a', href=True)
                if first_result:
                    page_path = first_result['href']
                    page_data = self.scrape_page(page_path)
                    if page_data:
                        return f"# {page_data['title']}\n\n{page_data['content']}"

            return None

        except Exception as e:
            print(f"Error searching wiki: {e}")
            return None
