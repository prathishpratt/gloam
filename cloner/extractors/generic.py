import trafilatura
from trafilatura.settings import use_config
from .base import BaseExtractor, ExtractedContent
from datetime import datetime
import httpx
import re


class GenericExtractor(BaseExtractor):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def extract(self) -> ExtractedContent:
        # Try trafilatura's built-in fetch first
        downloaded = trafilatura.fetch_url(self.url)

        # Fallback: httpx with browser headers
        if not downloaded:
            response = httpx.get(self.url, headers=self.HEADERS, follow_redirects=True, timeout=30)
            response.raise_for_status()
            downloaded = response.text

        # Extract with trafilatura
        result = trafilatura.extract(
            downloaded,
            output_format='html',
            include_images=True,
            include_links=True,
            include_tables=True,
            favor_precision=True,
            with_metadata=True,
        )

        # Get metadata separately
        metadata = trafilatura.extract_metadata(downloaded)

        title = (metadata.title if metadata else None) or self._extract_title_from_html(downloaded) or "Untitled"
        author = metadata.author if metadata else None

        publish_date = None
        if metadata and metadata.date:
            try:
                publish_date = datetime.fromisoformat(metadata.date[:10]).date()
            except Exception:
                pass

        # Extract cover image from og:image
        cover_url = None
        if metadata and hasattr(metadata, 'image'):
            cover_url = metadata.image

        return ExtractedContent(
            title=title,
            author=author,
            publish_date=publish_date,
            main_html=result or downloaded,
            cover_image_url=cover_url,
            description=metadata.description if metadata else None,
        )

    def _extract_title_from_html(self, html: str) -> str | None:
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None
