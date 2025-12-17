"""
HN2Kindle - Main orchestrator

Fetches top Hacker News posts, extracts content, converts to EPUB,
and sends to configured Kindle email addresses.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars are set directly

from fetch_hn import fetch_top_posts
from content_extractor import extract_content
from convert_epub import create_epub
from send_kindle import send_to_kindle


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch top Hacker News posts and send as EPUB to Kindle"
    )
    parser.add_argument(
        "--skip-send", 
        action="store_true",
        help="Skip sending to Kindle (useful for testing)"
    )
    parser.add_argument(
        "--keep-epub",
        action="store_true", 
        help="Keep the generated EPUB file instead of deleting it"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=None,
        help="Number of top posts to fetch (overrides TOP_POSTS_COUNT env var)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output path for EPUB file"
    )
    return parser.parse_args()


def main():
    """Main entry point for HN2Kindle."""
    args = parse_args()
    
    print("=" * 60)
    print("HN2Kindle - Daily Hacker News Digest")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Fetch top HN posts
    # Priority for count: 1) CLI arg, 2) env var, 3) default (10)
    if args.count is not None:
        post_count = args.count
    elif os.getenv("TOP_POSTS_COUNT"):
        post_count = int(os.getenv("TOP_POSTS_COUNT"))
    else:
        post_count = 10
    
    print(f"\n[1/4] Fetching top {post_count} Hacker News posts...")
    posts = fetch_top_posts(count=post_count)
    
    if not posts:
        print("ERROR: No posts fetched from Hacker News")
        sys.exit(1)
    
    print(f"Successfully fetched {len(posts)} posts")
    
    # Step 2: Extract content from each post
    print("\n[2/4] Extracting content from articles...")
    enriched_posts = []
    
    for i, post in enumerate(posts, 1):
        print(f"  [{i}/{len(posts)}] {post['title'][:50]}...")
        
        extracted = extract_content(post["url"])
        
        # Skip posts where content extraction failed
        if not extracted.success or not extracted.content.strip():
            print(f"    Skipped: {extracted.error or 'No content'}")
            continue
        
        enriched_posts.append({
            "title": post["title"],  # HN title
            "author": extracted.author or post["author"],
            "url": post["url"],
            "content": extracted.content,
            "score": post["score"],
            "comment_count": post["comment_count"],
        })
    
    print(f"Successfully extracted {len(enriched_posts)} posts")
    
    # Step 3: Convert to EPUB
    print("\n[3/4] Creating EPUB file...")
    today = datetime.now().strftime("%Y-%m-%d")
    
    if args.output:
        epub_path = Path(args.output).absolute()
    else:
        epub_filename = f"hn_daily_{today}.epub"
        epub_path = Path(epub_filename).absolute()
    
    create_epub(enriched_posts, str(epub_path))
    print(f"Created: {epub_path}")
    
    # Step 4: Send to Kindle (unless skipped)
    if args.skip_send:
        print("\n[4/4] Skipping send to Kindle (--skip-send flag)")
    else:
        print("\n[4/4] Sending to Kindle...")
        try:
            success = send_to_kindle(str(epub_path))
            if success:
                print("Successfully sent to Kindle!")
            else:
                print("Failed to send to Kindle")
                sys.exit(1)
        except ValueError as e:
            print(f"Configuration error: {e}")
            print("Please ensure GMAIL_ADDRESS, GMAIL_APP_PASSWORD, and KINDLE_EMAILS are set")
            sys.exit(1)
    
    # Cleanup (unless --keep-epub flag is set)
    if not args.keep_epub and not args.skip_send:
        if epub_path.exists():
            epub_path.unlink()
            print(f"Cleaned up: {epub_path.name}")
    elif args.keep_epub:
        print(f"EPUB kept at: {epub_path}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
