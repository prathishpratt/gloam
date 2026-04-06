#!/usr/bin/env python3
"""
Gloam Cloner — Save interesting blog posts to your Gloam collection.

Usage:
    python cloner.py "https://magazine.sebastianraschka.com/p/..."
    python cloner.py "https://medium.com/..." --tags "ml,transformers" --author "Jane Doe"
    python cloner.py "https://..." --draft
"""

import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import typer
import yaml
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from slugify import slugify

# Adjust paths relative to this script
SCRIPT_DIR = Path(__file__).parent
POSTS_DIR = SCRIPT_DIR / ".." / "src" / "content" / "posts"
IMAGES_DIR = SCRIPT_DIR / ".." / "public" / "images" / "posts"

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
    """Detect source site from URL."""
    hostname = urlparse(url).hostname or ""
    if "substack.com" in hostname or "magazine." in hostname:
        return "Substack"
    if "medium.com" in hostname or "towardsdatascience.com" in hostname or "towards" in hostname:
        return "Medium"
    return "Other"


def get_extractor(url: str):
    """Return the appropriate extractor for a URL."""
    from extractors.substack import SubstackExtractor
    from extractors.medium import MediumExtractor
    from extractors.generic import GenericExtractor

    site = detect_source_site(url)
    if site == "Substack":
        return SubstackExtractor(url)
    if site == "Medium":
        return MediumExtractor(url)
    return GenericExtractor(url)


@app.command()
def clone(
    url: str = typer.Argument(..., help="URL of the blog post to clone"),
    tags: str = typer.Option("", "--tags", "-t", help="Comma-separated tags"),
    author: str = typer.Option("", "--author", "-a", help="Override author name"),
    draft: bool = typer.Option(False, "--draft", "-d", help="Save as draft"),
    skip_images: bool = typer.Option(False, "--skip-images", help="Skip downloading images"),
):
    console.print(Panel.fit("[bold teal]Gloam Cloner[/bold teal]", border_style="teal"))
    console.print(f"  URL: [link]{url}[/link]\n")

    # 1. Extract content
    console.print("[bold]Step 1:[/bold] Extracting content...")
    extractor = get_extractor(url)
    try:
        extracted = extractor.extract()
    except Exception as e:
        console.print(f"[red]Error during extraction:[/red] {e}")
        raise typer.Exit(1)

    # 2. Convert to markdown
    console.print("[bold]Step 2:[/bold] Converting to Markdown...")
    from processors.md_converter import convert_html_to_markdown
    markdown = convert_html_to_markdown(extracted.main_html)

    if len(markdown.split()) < 100:
        console.print("[yellow]Warning:[/yellow] Extracted content seems very short. The page may require JavaScript or be paywalled.")
        if not Confirm.ask("Continue anyway?"):
            raise typer.Exit(0)

    # 3. Gather metadata (prompt for missing fields)
    console.print("[bold]Step 3:[/bold] Gathering metadata...\n")

    title = Prompt.ask("Title", default=extracted.title)
    detected_author = author or extracted.author or ""
    final_author = Prompt.ask("Author", default=detected_author) if not author else author

    detected_site = detect_source_site(url)
    source_site_choices = ", ".join(f"{i+1}={s}" for i, s in enumerate(SOURCE_SITES))
    console.print(f"  Source site options: {source_site_choices}")
    site_default = detected_site
    source_site_input = Prompt.ask("Source site", default=site_default, choices=SOURCE_SITES, show_choices=False)

    description_default = extracted.description or ""
    description = Prompt.ask("Description (1-2 sentences, optional)", default=description_default)

    tags_default = tags or ""
    tags_input = Prompt.ask("Tags (comma-separated)", default=tags_default)
    tag_list = [t.strip().lower() for t in tags_input.split(",") if t.strip()]

    # Slug from title
    slug = slugify(title, max_length=60)
    date_saved = date.today().isoformat()
    date_published = extracted.publish_date.isoformat() if extracted.publish_date else None

    # 4. Handle images
    images_dir = IMAGES_DIR / slug
    cover_image = None

    if not skip_images:
        console.print(f"\n[bold]Step 4:[/bold] Downloading images...")
        from processors.image_handler import download_and_save_images, get_cover_image

        if extracted.cover_image_url:
            cover_image = get_cover_image(extracted.cover_image_url, slug, images_dir)

        markdown = download_and_save_images(markdown, slug, images_dir)
    else:
        console.print("[bold]Step 4:[/bold] Skipping images.")

    # 5. Render MDX file
    console.print(f"\n[bold]Step 5:[/bold] Writing MDX file...")

    env = Environment(loader=FileSystemLoader(SCRIPT_DIR / "templates"))
    template = env.get_template("frontmatter.yaml.j2")
    frontmatter = template.render(
        title=title,
        description=description if description else None,
        source_url=url,
        source_site=source_site_input,
        original_author=final_author,
        date_saved=date_saved,
        date_published=date_published,
        tags=tag_list,
        cover_image=cover_image,
        draft=draft,
    )

    mdx_content = f"{frontmatter}\n\n{markdown}\n"

    filename = f"{date_saved}--{slug}.mdx"
    output_path = POSTS_DIR / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(mdx_content, encoding="utf-8")

    console.print(f"\n[bold green]Done![/bold green]")
    console.print(f"  Saved: [bold]src/content/posts/{filename}[/bold]")
    if cover_image:
        console.print(f"  Cover: {cover_image}")
    console.print(f"\n  Next:")
    console.print(f"    [dim]cd ..[/dim]")
    console.print(f"    [dim]npm run dev[/dim]  — preview at localhost:4321")
    console.print(f"    [dim]git add . && git commit -m 'add: {title}'[/dim]")


if __name__ == "__main__":
    app()
