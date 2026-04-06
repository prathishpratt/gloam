import httpx
from bs4 import BeautifulSoup
from .generic import GenericExtractor
from .base import ExtractedContent


class MediumExtractor(GenericExtractor):
    GOOGLEBOT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    }

    def extract(self) -> ExtractedContent:
        # Try with googlebot UA to bypass Medium paywall
        try:
            response = httpx.get(
                self.url,
                headers=self.GOOGLEBOT_HEADERS,
                follow_redirects=True,
                timeout=30
            )

            import trafilatura
            result = trafilatura.extract(
                response.text,
                output_format='html',
                include_images=True,
                include_links=True,
                favor_precision=True,
                with_metadata=True,
            )
            metadata = trafilatura.extract_metadata(response.text)

            # Try to get article section
            soup = BeautifulSoup(response.text, 'lxml')
            article = soup.find('article')
            main_html = str(article) if article else (result or response.text)

            from datetime import datetime
            publish_date = None
            if metadata and metadata.date:
                try:
                    publish_date = datetime.fromisoformat(metadata.date[:10]).date()
                except Exception:
                    pass

            og_image = soup.find('meta', property='og:image')
            cover_url = og_image['content'] if og_image and og_image.get('content') else None

            from .base import ExtractedContent
            return ExtractedContent(
                title=(metadata.title if metadata else None) or "Untitled",
                author=metadata.author if metadata else None,
                publish_date=publish_date,
                main_html=main_html,
                cover_image_url=cover_url,
                description=metadata.description if metadata else None,
            )
        except Exception:
            return super().extract()
