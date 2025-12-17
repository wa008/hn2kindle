"""
Convert extracted content to EPUB format.
"""

from datetime import datetime
from typing import Optional
from ebooklib import epub


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def create_navigation_html(prev_id: Optional[str], next_id: Optional[str]) -> str:
    """Create navigation links for a chapter."""
    links = []
    if prev_id:
        links.append(f'<a href="{prev_id}.xhtml">← Previous</a>')
    links.append('<a href="nav.xhtml">Menu</a>')
    if next_id:
        links.append(f'<a href="{next_id}.xhtml">Next →</a>')
    
    return f'<div style="margin: 20px 0; padding: 10px; border-top: 1px solid #ccc;">{" | ".join(links)}</div>'


def create_chapter_html(title: str, author: str, url: str, content: str,
                        prev_id: Optional[str] = None, next_id: Optional[str] = None) -> str:
    """Create HTML content for a chapter."""
    escaped_title = escape_html(title)
    escaped_author = escape_html(author)
    display_url = escape_html(url[:50] + '...' if len(url) > 50 else url)
    
    # Content is already HTML from trafilatura (preserves headings like h2, h3)
    # If it's plain text (fallback), wrap in paragraphs
    if '<' in content and '>' in content:
        content_html = content  # Already HTML
    else:
        content_html = escape_html(content)
        content_html = content_html.replace('\n\n', '</p><p>').replace('\n', '<br/>')
        content_html = f'<p>{content_html}</p>'
    
    nav_top = create_navigation_html(prev_id, next_id)
    nav_bottom = create_navigation_html(prev_id, next_id)
    
    return f'''<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{escaped_title}</title>
    <style type="text/css">
        body {{ font-family: Georgia, serif; line-height: 1.6; padding: 1em; }}
        h1.chapter-title {{ font-size: 1.8em; font-weight: bold; margin-top: 1em; margin-bottom: 0.5em; color: #333; }}
        h2 {{ font-size: 1.4em; font-weight: bold; margin-top: 1.5em; margin-bottom: 0.5em; color: #444; }}
        h3 {{ font-size: 1.2em; font-weight: bold; margin-top: 1.2em; margin-bottom: 0.4em; color: #555; }}
        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 1em; }}
        .content {{ text-align: justify; }}
        a {{ color: #0066cc; }}
    </style>
</head>
<body>
    {nav_top}
    <h1 class="chapter-title">{escaped_title}</h1>
    <div class="meta">
        <p>By: {escaped_author}</p>
        <p>Source: <a href="{url}">{display_url}</a></p>
    </div>
    <div class="content">
        {content_html}
    </div>
    {nav_bottom}
</body>
</html>'''


def create_epub(posts: list[dict], output_path: str, title: Optional[str] = None) -> str:
    """
    Create an EPUB file from a list of posts.
    
    Args:
        posts: List of dicts with keys: title, author, url, content
        output_path: Path to save the EPUB file
        title: Optional title for the EPUB
        
    Returns:
        Path to the created EPUB file
    """
    today = datetime.now().strftime("%Y-%m-%d")
    book_title = title or f"HN Daily - {today}"
    
    book = epub.EpubBook()
    book.set_identifier(f"hn-daily-{today}")
    book.set_title(book_title)
    book.set_language("en")
    book.add_author("HN2Kindle")
    
    css = epub.EpubItem(
        uid="style", file_name="style/main.css", media_type="text/css",
        content="body { font-family: Georgia, serif; line-height: 1.6; }"
    )
    book.add_item(css)
    
    chapters = []
    for i, post in enumerate(posts):
        chapter_id = f"chapter_{i}"
        prev_id = f"chapter_{i-1}" if i > 0 else None
        next_id = f"chapter_{i+1}" if i < len(posts) - 1 else None
        
        chapter = epub.EpubHtml(
            title=post.get("title", f"Post {i+1}"),
            file_name=f"{chapter_id}.xhtml",
            lang="en"
        )
        
        chapter.content = create_chapter_html(
            title=post.get("title", f"Post {i+1}"),
            author=post.get("author", "Unknown"),
            url=post.get("url", ""),
            content=post.get("content", "No content available"),
            prev_id=prev_id,
            next_id=next_id,
        )
        
        chapter.add_item(css)
        book.add_item(chapter)
        chapters.append(chapter)
    
    book.toc = chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters
    
    epub.write_epub(output_path, book)
    return output_path


if __name__ == "__main__":
    test_posts = [
        {"title": "Test Article", "author": "Author", "url": "https://example.com", "content": "Content here."},
    ]
    print(f"Created: {create_epub(test_posts, 'test_output.epub')}")
