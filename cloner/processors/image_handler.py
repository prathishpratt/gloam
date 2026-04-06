import httpx
from pathlib import Path
from PIL import Image
import io
import re
from rich.console import Console

console = Console()


def download_and_save_images(markdown: str, slug: str, output_dir: Path) -> str:
    """Download all images in markdown, save as WebP, rewrite paths."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all image references: ![alt](url)
    pattern = r'!\[([^\]]*)\]\((https?://[^\)]+)\)'

    def replace_image(match: re.Match) -> str:
        alt = match.group(1)
        url = match.group(2)

        # Generate filename from URL
        url_path = url.split('?')[0]  # Remove query params
        original_name = url_path.split('/')[-1]
        stem = Path(original_name).stem[:40] or 'image'
        filename = f"{stem}.webp"
        local_path = output_dir / filename
        web_path = f"/images/posts/{slug}/{filename}"

        if local_path.exists():
            return f"![{alt}]({web_path})"

        try:
            response = httpx.get(url, follow_redirects=True, timeout=20)
            response.raise_for_status()

            img = Image.open(io.BytesIO(response.content))
            # Convert to RGB if necessary (e.g., RGBA PNG)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(local_path, 'WEBP', quality=85, method=4)
            console.print(f"  [green]↓[/green] Downloaded: {filename}")
            return f"![{alt}]({web_path})"

        except Exception as e:
            console.print(f"  [yellow]⚠[/yellow] Failed to download image: {url[:60]}... ({e})")
            return match.group(0)  # Keep original on failure

    return re.sub(pattern, replace_image, markdown)


def get_cover_image(cover_url: str, slug: str, output_dir: Path) -> str | None:
    """Download and save the cover image, return web path."""
    if not cover_url:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    local_path = output_dir / "cover.webp"
    web_path = f"/images/posts/{slug}/cover.webp"

    if local_path.exists():
        return web_path

    try:
        response = httpx.get(cover_url, follow_redirects=True, timeout=20)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(local_path, 'WEBP', quality=85)
        return web_path
    except Exception as e:
        console.print(f"  [yellow]⚠[/yellow] Cover image failed: {e}")
        return None
