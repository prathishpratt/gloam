import httpx
from bs4 import BeautifulSoup
from .generic import GenericExtractor
from .base import ExtractedContent


class SubstackExtractor(GenericExtractor):
    def extract(self) -> ExtractedContent:
        # First get generic extraction
        result = super().extract()

        # Try to get a better body by targeting Substack-specific selectors
        try:
            headers = {**self.HEADERS}
            response = httpx.get(self.url, headers=headers, follow_redirects=True, timeout=30)
            soup = BeautifulSoup(response.text, 'lxml')

            # Substack article content selectors
            content_div = (
                soup.find('div', class_='available-content') or
                soup.find('div', class_='post-content') or
                soup.find('div', {'data-component-name': 'PostBodyViewer'})
            )

            if content_div:
                result.main_html = str(content_div)

            # Get cover image from og:image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                result.cover_image_url = og_image['content']

        except Exception:
            pass  # Fall back to generic extraction

        return result
