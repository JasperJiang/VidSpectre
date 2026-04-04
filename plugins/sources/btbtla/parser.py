import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
from plugins.interfaces import MediaItem, MediaType, UpdateInfo

BASE_URL = "https://www.btbtla.com"

class BtbtlaParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })

    def search(self, keyword: str) -> List[MediaItem]:
        """Search for media"""
        url = f"{BASE_URL}/search/{keyword}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return self._parse_search_results(response.text)
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def _parse_search_results(self, html: str) -> List[MediaItem]:
        """Parse search results"""
        items = []
        soup = BeautifulSoup(html, "lxml")

        # Find media items - btbtla uses .module-item class
        for item in soup.select(".module-item"):
            try:
                # Title link is in .module-item-title
                title_elem = item.select_one(".module-item-title, .module-item-title a")
                if not title_elem:
                    title_elem = item.select_one("a[href^='/detail/']")
                if not title_elem:
                    continue

                name = title_elem.get_text(strip=True)
                if not name:
                    title_elem = item.select_one("a[href^='/detail/']")
                    if title_elem:
                        name = title_elem.get("title", "") or title_elem.get_text(strip=True)

                detail_url = title_elem.get("href", "") if title_elem else ""
                if not detail_url:
                    # Try to get href from the link inside module-item-title
                    link = item.select_one("a[href^='/detail/']")
                    if link:
                        detail_url = link.get("href", "")

                if not detail_url:
                    continue

                # Extract media ID from URL
                media_id = self._extract_media_id(detail_url)
                if not media_id:
                    continue

                # Get cover image
                img_elem = item.select_one("img")
                cover_url = img_elem.get("src") if img_elem else None
                if cover_url and cover_url.startswith("//"):
                    cover_url = "https:" + cover_url

                # Determine media type from URL or page content
                media_type = MediaType.TV
                if "/movie/" in detail_url or "/Mv/" in detail_url:
                    media_type = MediaType.MOVIE

                items.append(MediaItem(
                    media_id=media_id,
                    name=name,
                    media_type=media_type,
                    cover_url=cover_url,
                    detail_url=detail_url
                ))
            except Exception as e:
                continue

        return items

    def _extract_media_id(self, url: str) -> Optional[str]:
        """Extract media ID from URL"""
        if not url:
            return None
        # Extract ID from URL pattern like /detail/12345 or /movie/12345
        parts = url.strip("/").split("/")
        if parts:
            return parts[-1]
        return None

    def get_updates(self, media_id: str) -> Optional[UpdateInfo]:
        """Get update info for media"""
        # Strip .html suffix if present to get pure ID
        clean_id = media_id.replace(".html", "") if media_id else media_id
        url = f"{BASE_URL}/detail/{clean_id}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return self._parse_detail_page(response.text, media_id)
        except Exception as e:
            print(f"Get updates error: {e}")
            return None

    def _parse_detail_page(self, html: str, media_id: str) -> Optional[UpdateInfo]:
        """Parse detail page"""
        soup = BeautifulSoup(html, "lxml")

        # Get latest episode/title
        latest_episode = ""
        episode_elem = soup.select_one(".latest-episode, .episode, .update-title")
        if episode_elem:
            latest_episode = episode_elem.get_text(strip=True)

        # Get update time
        update_time = None
        time_elem = soup.select_one(".time, .date, time")
        if time_elem:
            update_time = time_elem.get_text(strip=True)

        # Get download links
        download_links = []
        for link_elem in soup.select(".download-link, .magnet-link, a[href^='magnet:']"):
            href = link_elem.get("href", "")
            if href.startswith("magnet:") or href.endswith(".torrent"):
                download_links.append({
                    "type": "magnet" if href.startswith("magnet") else "torrent",
                    "url": href,
                    "title": link_elem.get_text(strip=True)
                })

        return UpdateInfo(
            media_id=media_id,
            latest_episode=latest_episode,
            update_time=update_time,
            download_links=download_links
        )

    def get_download_links(self, media_id: str) -> List[Dict]:
        """Get download links"""
        update_info = self.get_updates(media_id)
        return update_info.download_links if update_info else []

    def get_episode_links(self, media_id: str) -> Dict[str, List[Dict]]:
        """Get all episode download links grouped by episode number from detail page"""
        if not media_id:
            return {}

        url = f"{BASE_URL}/detail/{media_id}"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return self._parse_episodes_from_detail(response.text)
        except Exception as e:
            print(f"Get episode links error: {e}")
            return {}

    def _parse_episodes_from_detail(self, html: str) -> Dict[str, List[Dict]]:
        """Parse detail page to get episode links grouped by episode number"""
        soup = BeautifulSoup(html, "lxml")
        episodes = {}

        # Find all links to tdown pages - they contain the download info
        # Structure: link to /tdown/xxxxx.html with title text inside
        for link_elem in soup.select("a[href^='/tdown/']"):
            href = link_elem.get("href", "")
            if not href or not href.endswith(".html"):
                continue

            # Get title from the text content of the link
            title = link_elem.get_text(strip=True)
            # Skip links with no title or very short titles (these are usually auxiliary links)
            if not title or len(title) < 5:
                continue

            # Extract episode number from title like "[第64集]" or "[第53-55集]"
            ep_num = self._extract_episode_number(title)
            if ep_num == 0:
                ep_num = 1  # Default to 1 for movies or single episodes

            # Build full URL
            full_url = BASE_URL + href if href.startswith("/") else href

            # Determine resource type
            res_type = "torrent" if href.endswith(".torrent") else "magnet"

            if str(ep_num) not in episodes:
                episodes[str(ep_num)] = []

            episodes[str(ep_num)].append({
                "title": title,
                "url": full_url,
                "type": res_type
            })

        return episodes

    def _extract_episode_number(self, title: str) -> int:
        """Extract episode number from title like '第1集' or '第01集' or '[61]'"""
        import re
        # Pattern 1: "第xx集" - most reliable
        match = re.search(r'第(\d+)集', title)
        if match:
            return int(match.group(1))

        # Pattern 2: extract all bracketed numbers like [61] and find the episode
        # Episode numbers are typically 1-999, years are 1990-2030
        bracket_numbers = re.findall(r'\[(\d+)\]', title)
        for num_str in reversed(bracket_numbers):  # Try from end, usually episode comes after year
            num = int(num_str)
            if 1 <= num <= 999:  # Likely an episode number
                return num

        # Pattern 3: no brackets found, try to find any reasonable episode number (1-999)
        # Skip 4+ digit numbers as they're likely years
        all_numbers = re.findall(r'\d+', title)
        for num_str in all_numbers:
            num = int(num_str)
            if 1 <= num <= 999:
                return num

        return 0

    def get_magnet_link(self, tdown_url: str) -> Optional[str]:
        """Get magnet link from a tdown page"""
        try:
            response = self.session.get(tdown_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            # Find magnet link
            magnet_elem = soup.select_one("a[href^='magnet:']")
            if magnet_elem:
                return magnet_elem.get("href")
            return None
        except Exception as e:
            print(f"Get magnet link error: {e}")
            return None
