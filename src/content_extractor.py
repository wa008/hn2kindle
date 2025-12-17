"""
Extract main content from article URLs.

Uses trafilatura with fallback to newspaper3k for content extraction.
"""

import requests
import sys
from typing import Optional
from dataclasses import dataclass


@dataclass
class ExtractedContent:
    """Container for extracted article content."""
    title: str
    author: str
    content: str
    url: str
    success: bool = True
    error: Optional[str] = None


def extract_with_trafilatura(url: str, html: str) -> Optional[ExtractedContent]:
    """Try to extract content using trafilatura."""
    try:
        import trafilatura
        
        # Use HTML output to preserve headings (h2, h3, etc.)
        result = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            include_images=False,
            output_format="html",  # Preserve heading structure
        )
        
        if result:
            metadata = trafilatura.extract_metadata(html)
            title = metadata.title if metadata and metadata.title else ""
            author = metadata.author if metadata and metadata.author else ""
            
            return ExtractedContent(title=title, author=author, content=result, url=url)
    except ImportError:
        print("trafilatura not installed, skipping...")
    except Exception as e:
        print(f"trafilatura extraction failed: {e}")
    
    return None


def extract_with_newspaper(url: str, html: str) -> Optional[ExtractedContent]:
    """Try to extract content using newspaper3k."""
    try:
        from newspaper import Article
        
        article = Article(url)
        article.download(input_html=html)
        article.parse()
        
        if article.text:
            return ExtractedContent(
                title=article.title or "",
                author=", ".join(article.authors) if article.authors else "",
                content=article.text,
                url=url,
            )
    except ImportError:
        print("newspaper3k not installed, skipping...")
    except Exception as e:
        print(f"newspaper extraction failed: {e}")
    
    return None


def extract_content(url: str, timeout: int = 15) -> ExtractedContent:
    """
    Extract main content from an article URL.
    
    Args:
        url: The URL to extract content from
        timeout: Request timeout in seconds
        
    Returns:
        ExtractedContent with the extracted data or error information
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        html = response.text
    except requests.RequestException as e:
        return ExtractedContent(
            title="", author="", content="", url=url,
            success=False, error=f"Failed to fetch URL: {e}",
        )
    
    # Try trafilatura first
    result = extract_with_trafilatura(url, html)
    if result and result.content:
        return result
    
    # Fall back to newspaper3k
    result = extract_with_newspaper(url, html)
    if result and result.content:
        return result
    
    # Both extractors failed
    return ExtractedContent(
        title="", author="",
        content="[Content could not be extracted from this page]",
        url=url, success=False, error="All extraction methods failed",
    )


if __name__ == "__main__":
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    print(f"Testing: {test_url}")
    result = extract_content(test_url)
    print(f"Title: {result.title}")
    print(f"Author: {result.author}")
    print(f"Content: {len(result.content)} chars")
    print(f"Success: {result.success}")
