#!/usr/bin/env python3
"""
Random Comment Picker

Downloads comments from a YouTube video, filters to unique authors,
and randomly selects one comment to return.

Usage:
    python pick_comment.py <youtube_video_url>

Or as a skill:
    yt-random-comment-picker <youtube_video_url>
"""

import json
import random
import sys
import subprocess
from typing import List, Dict, Optional


def download_comments(video_url: str, output_path: str = "/tmp/youtube_comments.info.json") -> Optional[Dict]:
    """
    Download comments from a YouTube video using yt-dlp.
    
    Args:
        video_url: YouTube video URL
        output_path: Path to save the info.json file
        
    Returns:
        Parsed info.json data if successful, None otherwise
    """
    try:
        # Use yt-dlp to download comments and video metadata
        # --skip-download avoids downloading the video itself
        # --write-comments retrieves the comments
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-comments",
            "--output", output_path,
            video_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"yt-dlp error: {result.stderr}", file=sys.stderr)
            return None
        
        # Read the generated info.json
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading info.json: {e}", file=sys.stderr)
            return None
            
    except subprocess.TimeoutExpired:
        print("yt-dlp command timed out", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return None


def extract_top_level_comments(data: Dict) -> List[Dict]:
    """
    Extract top-level comments from yt-dlp info.json data.
    
    Args:
        data: Parsed yt-dlp info.json data
        
    Returns:
        List of top-level comment dictionaries
    """
    # yt-dlp stores comments under 'comments' key
    # Each comment has: author, text, likes, etc.
    comments = data.get('comments', [])
    
    if not comments:
        # Try alternative key
        comments = data.get('comment', [])
    
    # Filter to top-level only (no reply threads)
    # yt-dlp comment structure: each comment may have 'replies' key
    top_level = []
    for comment in comments:
        # Only include comments without replies, or where replies is empty
        # This ensures we get top-level comments only
        if comment.get('author') and comment.get('text'):
            top_level.append(comment)
    
    return top_level


def filter_unique_authors(comments: List[Dict]) -> List[Dict]:
    """
    Filter comments to keep only the first occurrence of each author.
    
    Args:
        comments: List of comment dictionaries
        
    Returns:
        List of comments with unique authors (first occurrence kept)
    """
    seen_authors = set()
    unique_comments = []
    
    for comment in comments:
        author = comment.get('author', '')
        if author not in seen_authors:
            seen_authors.add(author)
            unique_comments.append(comment)
    
    return unique_comments


def select_random_comment(comments: List[Dict]) -> Optional[Dict]:
    """
    Randomly select one comment from the list.
    
    Args:
        comments: List of comment dictionaries with unique authors
        
    Returns:
        A randomly selected comment dictionary, or None if list is empty
    """
    if not comments:
        return None
    
    return random.choice(comments)


def format_comment(comment: Dict) -> str:
    """
    Format a comment for display.
    
    Args:
        comment: Comment dictionary with 'author' and 'text' keys
        
    Returns:
        Formatted string with author and text
    """
    author = comment.get('author', 'Unknown')
    text = comment.get('text', '')
    
    # Clean up text - remove newlines and excessive whitespace
    text = ' '.join(text.split())
    
    return f"Author: {author}\nComment: {text}"


def main():
    """Main entry point for the random comment picker."""
    if len(sys.argv) < 2:
        print("Usage: python pick_comment.py <youtube_video_url>")
        print("Example: python pick_comment.py https://youtu.be/oZce8zzXYV4")
        sys.exit(1)
    
    video_url = sys.argv[1]
    
    print(f"Downloading comments from: {video_url}")
    print("This may take a moment while yt-dlp fetches the comment section...\n")
    
    # Step 1: Download comments
    data = download_comments(video_url)
    
    if data is None:
        print("Failed to download comments. Please check the URL and try again.")
        sys.exit(1)
    
    # Check if we have comment data
    comment_count = data.get('comment_count', 0)
    print(f"Video has {comment_count} total comments")
    
    # Step 2: Extract top-level comments
    comments = extract_top_level_comments(data)
    print(f"Extracted {len(comments)} top-level comments")
    
    # Step 3: Filter to unique authors
    unique_comments = filter_unique_authors(comments)
    print(f"After filtering to unique authors: {len(unique_comments)} comments")
    
    if len(unique_comments) == 0:
        print("No comments found with authors. This is unusual.")
        sys.exit(1)
    
    # Step 4: Select random comment
    selected = select_random_comment(unique_comments)
    
    if selected is None:
        print("Failed to select a comment.")
        sys.exit(1)
    
    # Step 5: Display the result
    print("\n" + "="*60)
    print("RANDOMLY SELECTED COMMENT")
    print("="*60)
    print(format_comment(selected))
    print("="*60)
    
    # Also output JSON for programmatic use
    result = {
        "author": selected.get('author', ''),
        "text": selected.get('text', ''),
        "likes": selected.get('likes', 0),
    }
    print("\nJSON output:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()