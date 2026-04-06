from markdownify import markdownify as md
import re


def convert_html_to_markdown(html: str) -> str:
    """Convert HTML to clean Markdown."""
    result = md(
        html,
        heading_style="ATX",
        bullets="-",
        strip=["script", "style", "iframe", "nav", "footer", "aside", "button"],
        convert_links=True,
        wrap=False,
    )

    # Clean up excessive blank lines
    result = re.sub(r'\n{3,}', '\n\n', result)

    # Fix image alt text
    result = re.sub(r'!\[\s*\]', '![image]', result)

    return result.strip()
