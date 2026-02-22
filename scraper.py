"""
SteamUnlocked Scraper - Core scraping logic
"""
import re
import time
import random
from typing import List, Optional
from urllib.parse import urljoin, urlparse, parse_qs, quote

import requests
from bs4 import BeautifulSoup

from models import Game, GameDetails, SystemRequirements, DownloadInfo, CATEGORIES


class SteamUnlockedScraper:
    """Scraper for SteamUnlocked website"""

    BASE_URL = "https://steamunlocked.org"

    # User agents to rotate
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    def __init__(self, request_delay: float = 1.0):
        """
        Initialize the scraper

        Args:
            request_delay: Delay between requests in seconds (default: 1.0)
        """
        self.request_delay = request_delay
        self.session = requests.Session()
        self.last_request_time = 0

    def _get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.USER_AGENTS)

    def _make_request(self, url: str, timeout: int = 30) -> requests.Response:
        """
        Make an HTTP request with rate limiting and headers

        Args:
            url: URL to request
            timeout: Request timeout in seconds

        Returns:
            Response object
        """
        # Rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_delay:
            time.sleep(self.request_delay - time_since_last_request)

        headers = {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            # "Accept-Encoding": "gzip, deflate",  # Removed to avoid compression issues
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        try:
            response = self.session.get(url, headers=headers, timeout=timeout)
            self.last_request_time = time.time()
            return response
        except requests.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def search_games(self, query: str, max_results: int = 20) -> List[Game]:
        """
        Search for games on SteamUnlocked

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of Game objects
        """
        # URL encode the query (spaces become +)
        search_url = f"{self.BASE_URL}/?s={quote(query, safe='')}"

        response = self._make_request(search_url)
        soup = BeautifulSoup(response.text, "html.parser")  # Use html.parser for better compatibility

        games = []

        # SteamUnlocked uses div class="cover-item category" for search results
        cover_items = soup.find_all("div", class_="cover-item category")

        for item in cover_items[:max_results]:
            try:
                # Extract title and link from cover-item-title > a > h1
                title_div = item.find("div", class_="cover-item-title")
                if not title_div:
                    continue

                link = title_div.find("a")
                if not link:
                    continue

                url = link.get("href", "")
                title_tag = link.find("h1")
                title = title_tag.get_text(strip=True) if title_tag else link.get_text(strip=True)

                # Extract thumbnail from cover-item-image > a > img
                img_div = item.find("div", class_="cover-item-image")
                thumbnail = None
                if img_div:
                    img_tag = img_div.find("img")
                    if img_tag:
                        thumbnail = img_tag.get("src") or img_tag.get("data-src")

                games.append(Game(
                    title=title,
                    url=url,
                    thumbnail=thumbnail,
                    release_date=None
                ))
            except Exception as e:
                print(f"Error parsing game result: {e}")
                continue

        return games

    def get_game_details(self, game_url: str) -> Optional[GameDetails]:
        """
        Get detailed information about a game

        Args:
            game_url: URL of the game page

        Returns:
            GameDetails object or None
        """
        response = self._make_request(game_url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title_tag = soup.find("h1") or soup.find("h2", class_="post-title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Extract thumbnail
        img_tag = soup.find("img", class_=re.compile(r"featured|thumb", re.I))
        thumbnail = img_tag.get("src") or img_tag.get("data-src") if img_tag else None

        # Extract description
        content_div = soup.find("div", class_=re.compile(r"entry|content|post-content", re.I))
        description = ""
        if content_div:
            # Get text content, excluding download section
            description = content_div.get_text(strip=True)

        # Extract screenshots
        screenshots = []
        screenshot_imgs = soup.find_all("img", class_=re.compile(r"screenshot|gallery", re.I))
        for img in screenshot_imgs:
            src = img.get("src") or img.get("data-src")
            if src:
                screenshots.append(src)

        # Extract system requirements
        sys_req_div = soup.find("div", class_=re.compile(r"system.*req", re.I))
        system_requirements = None
        if sys_req_div:
            system_requirements = self._parse_system_requirements(sys_req_div)

        # Extract download link section
        download_info = self._extract_download_link(soup, title)

        # Extract genre/categories
        genre_tags = soup.find_all("a", rel=re.compile(r"category", re.I))
        genres = [tag.get_text(strip=True) for tag in genre_tags]

        # Extract metadata
        developer = None
        publisher = None
        release_date_full = None

        meta_items = soup.find_all("div", class_=re.compile(r"meta|info", re.I))
        for item in meta_items:
            text = item.get_text(strip=True).lower()
            if "developer" in text or "dev" in text:
                developer = item.get_text(strip=True).replace("Developer:", "").strip()
            elif "publisher" in text or "pub" in text:
                publisher = item.get_text(strip=True).replace("Publisher:", "").strip()
            elif "release" in text or "published" in text:
                release_date_full = item.get_text(strip=True).replace("Release Date:", "").strip()

        return GameDetails(
            title=title,
            url=game_url,
            thumbnail=thumbnail,
            description=description,
            screenshots=screenshots,
            system_requirements=system_requirements,
            download_page_url=download_info.download_url if download_info else None,
            file_size=download_info.file_size if download_info else None,
            genre=genres,
            developer=developer,
            publisher=publisher,
            release_date_full=release_date_full
        )

    def _parse_system_requirements(self, sys_req_div) -> Optional[SystemRequirements]:
        """Parse system requirements from HTML"""
        reqs = SystemRequirements()

        # Look for list items or divs containing requirement info
        items = sys_req_div.find_all(["li", "div", "p", "span"])

        for item in items:
            text = item.get_text(strip=True).lower()
            if "os:" in text or "operating system" in text:
                reqs.os = item.get_text(strip=True).split(":", 1)[-1].strip()
            elif "processor:" in text or "cpu:" in text:
                reqs.processor = item.get_text(strip=True).split(":", 1)[-1].strip()
            elif "memory:" in text or "ram:" in text:
                reqs.memory = item.get_text(strip=True).split(":", 1)[-1].strip()
            elif "graphics:" in text or "gpu:" in text or "video:" in text:
                reqs.graphics = item.get_text(strip=True).split(":", 1)[-1].strip()
            elif "storage:" in text or "disk:" in text:
                reqs.storage = item.get_text(strip=True).split(":", 1)[-1].strip()

        # Return None if no requirements found
        if any([reqs.os, reqs.processor, reqs.memory, reqs.graphics, reqs.storage]):
            return reqs
        return None

    def _extract_download_link(self, soup: BeautifulSoup, game_title: str) -> Optional[DownloadInfo]:
        """
        Extract download link from game page

        The download section typically contains text like:
        "Download {game_name} for PC using the link below."

        Args:
            soup: BeautifulSoup object of the game page
            game_title: Title of the game

        Returns:
            DownloadInfo object or None
        """
        # Method 1: Look for download button with class "btn-download"
        download_btn = soup.find("a", class_="btn-download")
        if download_btn:
            url = download_btn.get("href")
            if url and url.startswith("http"):
                # Look for file size near the download button
                file_size = None
                parent = download_btn.find_parent("div") or download_btn.find_parent("p")
                if parent:
                    size_match = re.search(r"(\d+(?:\.\d+)?)\s*(GB|MB)", parent.get_text(), re.I)
                    if size_match:
                        file_size = f"{size_match.group(1)} {size_match.group(2)}"

                return DownloadInfo(
                    file_host=self._identify_file_host(url),
                    download_url=url,
                    file_size=file_size
                )

        # Method 2: Look for any link with uploadhaven.com/download/ using regex
        download_btn = soup.find("a", href=re.compile(r"uploadhaven\.com/download/"))
        if download_btn:
            url = download_btn.get("href")
            # Look for file size
            file_size = None
            parent = download_btn.find_parent("div")
            if parent:
                size_match = re.search(r"(\d+(?:\.\d+)?)\s*(GB|MB)", parent.get_text(), re.I)
                if size_match:
                    file_size = f"{size_match.group(1)} {size_match.group(2)}"

            return DownloadInfo(
                file_host="UploadHaven",
                download_url=url,
                file_size=file_size
            )

        # Method 3: Look for download section with specific text pattern
        download_pattern = re.compile(r"download.*for pc using the link below", re.I)

        # Search for paragraphs or divs containing download instructions
        for element in soup.find_all(["p", "div", "span"]):
            text = element.get_text(strip=True)
            if download_pattern.search(text):
                # Found the download section, now find the link
                link = element.find("a", href=True)
                if link:
                    url = link.get("href")
                    # Determine file host from URL
                    file_host = self._identify_file_host(url)

                    # Extract file size if mentioned nearby
                    size_text = element.get_text()
                    size_match = re.search(r"(\d+(?:\.\d+)?)\s*(GB|MB)", size_text, re.I)
                    file_size = f"{size_match.group(1)} {size_match.group(2)}" if size_match else None

                    return DownloadInfo(
                        file_host=file_host,
                        download_url=url,
                        file_size=file_size
                    )

        # Method 4: Fallback - look for any link with known file hosts
        for btn in soup.find_all("a", href=True):
            url = btn.get("href")
            if url and ("uploadhaven.com/download/" in url or "megaup.net/" in url or "pixeldrain.com/" in url):
                return DownloadInfo(
                    file_host=self._identify_file_host(url),
                    download_url=url
                )

        return None

    def _identify_file_host(self, url: str) -> str:
        """Identify the file hosting service from URL"""
        domain = urlparse(url).netloc.lower()

        if "uploadhaven" in domain:
            return "UploadHaven"
        elif "megaup" in domain:
            return "MegaUp"
        elif "pixeldrain" in domain:
            return "PixelDrain"
        elif "rapidgator" in domain:
            return "RapidGator"
        elif "nitroflare" in domain:
            return "NitroFlare"
        elif "uploaded" in domain:
            return "Uploaded"
        else:
            return "Unknown"

    def get_games_by_category(self, category: str, page: int = 1) -> List[Game]:
        """
        Get games from a specific category

        Args:
            category: Category slug (e.g., "action", "rpg")
            page: Page number (default: 1)

        Returns:
            List of Game objects
        """
        # Use /category/ instead of /categories/
        category_url = f"{self.BASE_URL}/category/{category.lower()}/"
        if page > 1:
            category_url += f"page/{page}/"

        response = self._make_request(category_url)
        soup = BeautifulSoup(response.text, "html.parser")

        games = []

        # Same structure as search: div class="cover-item category"
        cover_items = soup.find_all("div", class_="cover-item category")

        for item in cover_items:
            try:
                # Extract title and link from cover-item-title > a > h1
                title_div = item.find("div", class_="cover-item-title")
                if not title_div:
                    continue

                link = title_div.find("a")
                if not link:
                    continue

                url = link.get("href", "")
                title_tag = link.find("h1")
                title = title_tag.get_text(strip=True) if title_tag else link.get_text(strip=True)

                # Extract thumbnail from cover-item-image > a > img
                img_div = item.find("div", class_="cover-item-image")
                thumbnail = None
                if img_div:
                    img_tag = img_div.find("img")
                    if img_tag:
                        thumbnail = img_tag.get("src") or img_tag.get("data-src")

                games.append(Game(
                    title=title,
                    url=url,
                    thumbnail=thumbnail
                ))
            except Exception as e:
                print(f"Error parsing category game: {e}")
                continue

        return games

    def get_games_a_z(self, letter: Optional[str] = None, page: int = 1) -> List[Game]:
        """
        Get games from A-Z listing

        Args:
            letter: Letter to filter by (A-Z), or None for all
            page: Page number (default: 1)

        Returns:
            List of Game objects
        """
        url = f"{self.BASE_URL}/all-games/"

        if letter:
            # Add letter filter
            url += f"?letter={letter.lower()}"
        if page > 1:
            separator = "&" if letter else "?"
            url += f"{separator}page={page}"

        response = self._make_request(url)
        soup = BeautifulSoup(response.text, "html.parser")

        print(f"[DEBUG] A-Z URL: {url}")
        print(f"[DEBUG] Response length: {len(response.text)}")

        games = []

        # A-Z page uses div class="su-pop-item" structure
        pop_items = soup.find_all("div", class_="su-pop-item")
        print(f"[DEBUG] Found {len(pop_items)} pop items")

        for item in pop_items[:100]:  # Limit to 100 games
            try:
                # Find the info div which contains the link
                info_div = item.find("div", class_="info")
                if not info_div:
                    continue

                link = info_div.find("a")
                if not link:
                    continue

                url = link.get("href", "")
                title = link.get_text(strip=True)

                # Extract thumbnail from img div
                img_div = item.find("div", class_="img")
                thumbnail = None
                if img_div:
                    img_tag = img_div.find("img")
                    if img_tag:
                        # Try data-wpfc-original-src first (lazy loaded), then src
                        thumbnail = img_tag.get("data-wpfc-original-src") or img_tag.get("src")

                games.append(Game(
                    title=title,
                    url=url,
                    thumbnail=thumbnail
                ))
            except Exception as e:
                print(f"Error parsing A-Z game: {e}")
                continue

        return games

    def get_all_categories(self) -> List[dict]:
        """
        Get list of all available categories

        Returns:
            List of category dictionaries
        """
        categories = []
        for category in CATEGORIES:
            slug = category.lower().replace(" ", "-")
            categories.append({
                "name": category,
                "slug": slug,
                "url": f"{self.BASE_URL}/categories/{slug}/"
            })
        return categories
