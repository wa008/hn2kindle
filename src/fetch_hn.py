"""
Fetch yesterday's top stories from Hacker News using Algolia API.
Uses date-based search for stable/fixed content.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional


ALGOLIA_API = "https://hn.algolia.com/api/v1"
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
DEFAULT_TOP_POSTS_COUNT = 10


def get_top_posts_count() -> int:
    """Get the number of top posts to fetch from environment or default."""
    return int(os.getenv("TOP_POSTS_COUNT", DEFAULT_TOP_POSTS_COUNT))


def get_yesterday_timestamps() -> tuple[int, int]:
    """Get Unix timestamps for yesterday (start and end of day)."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today - timedelta(days=1)
    yesterday_end = today - timedelta(seconds=1)
    return int(yesterday_start.timestamp()), int(yesterday_end.timestamp())


def fetch_yesterday_top_stories(count: int) -> list[dict]:
    """
    Fetch top stories from yesterday using Algolia HN API.
    
    Returns stories sorted by points (score) from yesterday.
    """
    start_ts, end_ts = get_yesterday_timestamps()
    
    try:
        # Search for front page stories from yesterday, sorted by points
        params = {
            "tags": "front_page",
            "numericFilters": f"created_at_i>{start_ts},created_at_i<{end_ts}",
            "hitsPerPage": count * 2,  # Get extra in case some don't have URLs
        }
        
        response = requests.get(f"{ALGOLIA_API}/search_by_date", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        stories = []
        for hit in data.get("hits", []):
            url = hit.get("url")
            score = hit.get("points", 0)
            
            # Skip stories without external URLs or with low scores
            if not url or score < 10:
                continue
                
            stories.append({
                "id": int(hit.get("objectID", 0)),
                "title": hit.get("title", "Untitled"),
                "url": url,
                "author": hit.get("author", "Unknown"),
                "score": score,
                "comment_count": hit.get("num_comments", 0),
                "time": hit.get("created_at_i", 0),
            })
            
            if len(stories) >= count:
                break
        
        # Keep default HN front page order (already ranked by HN algorithm)
        return stories[:count]
        
    except requests.RequestException as e:
        print(f"Error fetching from Algolia API: {e}")
        return []


def fetch_top_posts(count: Optional[int] = None) -> list[dict]:
    """
    Fetch the top N stories from yesterday's HN front page.
    
    Args:
        count: Number of posts to fetch. If None, uses TOP_POSTS_COUNT env var or default.
        
    Returns:
        List of story dictionaries with keys: id, title, url, author, score, comment_count, time
    """
    if count is None:
        count = get_top_posts_count()
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Fetching HN front page for: {yesterday}")
    
    # Fetch from Algolia API
    posts = fetch_yesterday_top_stories(count)
    
    if posts:
        for post in posts:
            print(f"Fetched: {post['title'][:60]}...")
        return posts
    
    # Fallback to live top stories if Algolia fails
    print("Algolia API failed, falling back to live top stories")
    try:
        response = requests.get(f"{HN_API_BASE}/topstories.json", timeout=10)
        response.raise_for_status()
        story_ids = response.json()[:count * 2]
        
        posts = []
        for story_id in story_ids:
            if len(posts) >= count:
                break
            try:
                resp = requests.get(f"{HN_API_BASE}/item/{story_id}.json", timeout=10)
                resp.raise_for_status()
                data = resp.json()
                if data and data.get("url"):
                    posts.append({
                        "id": data.get("id"),
                        "title": data.get("title", "Untitled"),
                        "url": data.get("url"),
                        "author": data.get("by", "Unknown"),
                        "score": data.get("score", 0),
                        "comment_count": data.get("descendants", 0),
                        "time": data.get("time", 0),
                    })
                    print(f"Fetched: {data['title'][:60]}...")
            except requests.RequestException:
                continue
        
        return posts
    except requests.RequestException:
        return []


if __name__ == "__main__":
    print("Fetching yesterday's top 3 HN posts...")
    stories = fetch_top_posts(3)
    for i, story in enumerate(stories, 1):
        print(f"\n{i}. {story['title']}")
        print(f"   URL: {story['url']}")
        print(f"   By: {story['author']} | Score: {story['score']} | Comments: {story['comment_count']}")
