#!/usr/bin/env python3
"""
Gloam Cloner — Save interesting blog posts to your Gloam collection.

Uses 'monolith' to capture a self-contained HTML snapshot of the original page
(preserving the exact look and feel), then saves metadata as an MDX file.

Requirements:
  - monolith CLI: brew install monolith
  - Python deps: pip install -r requirements.txt

Usage:
    python cloner.py "https://magazine.sebastianraschka.com/p/..."
    python cloner.py "https://medium.com/..." --tags "ml,transformers" --author "Jane Doe"
    python cloner.py "https://..." --draft
    python cloner.py "https://..." --no-snapshot   # metadata only, no HTML snapshot
"""

import shutil
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import typer
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from slugify import slugify

SCRIPT_DIR = Path(__file__).parent
POSTS_DIR  = SCRIPT_DIR / ".." / "src" / "content" / "posts"
SAVED_DIR  = SCRIPT_DIR / ".." / "public" / "saved"

app = typer.Typer(add_completion=False)
console = Console()

SOURCE_SITES = [
    "Substack",
    "Medium",
    "Personal Blog",
    "WordPress",
    "Course Page",
    "Other",
]


def detect_source_site(url: str) -> str:
    host = urlparse(url).hostname or ""
    if "substack.com" in host or host.startswith("magazine."):
        return "Substack"
    if "medium.com" in host or "towardsdatascience.com" in host:
        return "Medium"
    if "wordpress.com" in host or "wp-content" in url:
        return "WordPress"
    return "Other"


def fetch_metadata(url: str) -> dict:
    """Use trafilatura to extract title, author, date, description."""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            import httpx
            r = httpx.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }, follow_redirects=True, timeout=30)
            downloaded = r.text
        metadata = trafilatura.extract_metadata(downloaded)
        if metadata:
            pub_date = None
            if metadata.date:
                try:
                    from datetime import datetime
                    pub_date = datetime.fromisoformat(metadata.date[:10]).date()
                except Exception:
                    pass
            return {
                "title": metadata.title or "Untitled",
                "author": metadata.author,
                "date": pub_date,
                "description": metadata.description,
            }
    except Exception as e:
        console.print(f"  [yellow]Metadata extraction failed:[/yellow] {e}")
    return {"title": "Untitled", "author": None, "date": None, "description": None}


def save_snapshot(url: str, output_path: Path) -> bool:
    """Run monolith to save a self-contained HTML snapshot of the page.

    --no-js:     skip JS bundles (not needed for reading, keeps file small)
    --no-images: images remain as external URLs (loads from original CDN)
    --no-fonts:  fonts remain as external URLs
    Result: ~1-3 MB HTML with all CSS inlined, original images/fonts load from CDN.
    """
    monolith = shutil.which("monolith")
    if not monolith:
        console.print("[yellow]Warning:[/yellow] 'monolith' not found. Install: brew install monolith")
        console.print("  Skipping snapshot.")
        return False

    SAVED_DIR.mkdir(parents=True, exist_ok=True)
    console.print("  Running monolith (10-30 seconds)...")

    result = subprocess.run(
        [monolith, url, "--no-js", "--no-images", "--no-fonts", "--silent", "-o", str(output_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if output_path.exists() and output_path.stat().st_size > 1000:
        size_kb = output_path.stat().st_size // 1024
        console.print(f"  [green]✓[/green] Snapshot saved ({size_kb} KB)")
        return True

    console.print(f"[red]✗[/red] Snapshot failed.")
    if result.stderr:
        console.print(f"  Error: {result.stderr[:300]}")
    return False


@app.command()
def clone(
    url: str = typer.Argument(..., help="URL of the blog post to clone"),
    tags: str = typer.Option("", "--tags", "-t", help="Comma-separated tags"),
    author: str = typer.Option("", "--author", "-a", help="Override author name"),
    draft: bool = typer.Option(False, "--draft", "-d", help="Save as draft"),
    no_snapshot: bool = typer.Option(False, "--no-snapshot", help="Skip HTML snapshot, metadata only"),
):
    console.print(Panel.fit("[bold cyan]Gloam Cloner[/bold cyan]", border_style="cyan"))
    console.print(f"  URL: {url}\n")

    # Step 1: Fetch metadata
    console.print("[bold]Step 1:[/bold] Fetching metadata...")
    meta = fetch_metadata(url)

    # Step 2: Prompt for missing metadata
    console.print("[bold]Step 2:[/bold] Confirm metadata\n")

    title = Prompt.ask("  Title", default=meta["title"])
    final_author = author if author else Prompt.ask("  Author", default=meta["author"] or "")
    source_site = Prompt.ask(
        f"  Source site",
        default=detect_source_site(url),
        choices=SOURCE_SITES,
        show_choices=False,
    )
    description = Prompt.ask("  Description (optional)", default=meta["description"] or "")
    tags_input = Prompt.ask("  Tags (comma-separated)", default=tags or "")
    tag_list = [t.strip().lower() for t in tags_input.split(",") if t.strip()]

    # Derive slug and dates
    slug = slugify(title, max_length=60)
    date_saved_str = date.today().isoformat()
    date_published_str = meta["date"].isoformat() if meta["date"] else None
    file_stem = f"{date_saved_str}--{slug}"

    # Step 3: Save HTML snapshot via monolith
    snapshot_saved = False
    if not no_snapshot:
        console.print(f"\n[bold]Step 3:[/bold] Saving HTML snapshot...")
        snapshot_saved = save_snapshot(url, SAVED_DIR / f"{file_stem}.html")
    else:
        console.print("\n[bold]Step 3:[/bold] Skipping snapshot (--no-snapshot).")

    # Step 4: Write MDX metadata file
    console.print(f"\n[bold]Step 4:[/bold] Writing MDX metadata file...")

    env = Environment(loader=FileSystemLoader(SCRIPT_DIR / "templates"))
    frontmatter = env.get_template("frontmatter.yaml.j2").render(
        title=title,
        description=description if description else None,
        source_url=url,
        source_site=source_site,
        original_author=final_author,
        date_saved=date_saved_str,
        date_published=date_published_str,
        tags=tag_list,
        cover_image=None,
        draft=draft,
    )

    # MDX body is intentionally minimal — reading happens via the iframe snapshot
    mdx_body = f"> Originally published by **{final_author}** on [{source_site}]({url})."

    output_path = POSTS_DIR / f"{file_stem}.mdx"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"{frontmatter}\n\n{mdx_body}\n", encoding="utf-8")

    # Summary
    console.print(f"\n[bold green]✓ Done![/bold green]")
    console.print(f"  MDX:  src/content/posts/{file_stem}.mdx")
    if snapshot_saved:
        console.print(f"  HTML: public/saved/{file_stem}.html")
    console.print(f"\n  Preview:  cd ..  &&  npm run dev")
    console.print(f"  Publish:  git add .  &&  git commit -m 'add: {title}'  &&  git push")


if __name__ == "__main__":
    app()
