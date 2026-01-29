"""
Analyze X Posts - Parse analytics CSV and identify top performers

Usage: python analyze_posts.py

Outputs:
- .tmp/post_analysis.json - Full analysis with style profile
- .tmp/top_posts.json - Top 50 posts for content generation
"""

import csv
import json
import html
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
TMP_DIR = BASE_DIR / ".tmp"


def load_posts():
    """Load posts from CSV file."""
    csv_files = list(DATA_DIR.glob("account_analytics_content_*.csv"))
    if not csv_files:
        raise FileNotFoundError("No analytics CSV found in data/")

    posts = []
    csv_file = csv_files[0]

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean HTML entities
            text = html.unescape(row['Post text'])

            post = {
                'id': row['Post id'],
                'date': row['Date'],
                'text': text,
                'link': row['Post Link'],
                'impressions': int(row['Impressions']),
                'likes': int(row['Likes']),
                'engagements': int(row['Engagements']),
                'bookmarks': int(row['Bookmarks']),
                'shares': int(row['Shares']),
                'new_follows': int(row['New follows']),
                'replies': int(row['Replies']),
                'reposts': int(row['Reposts']),
                'profile_visits': int(row['Profile visits']),
                'detail_expands': int(row['Detail Expands']),
                'url_clicks': int(row['URL Clicks']),
            }
            posts.append(post)

    return posts


def calculate_engagement_score(post):
    """Calculate weighted engagement score."""
    return (
        post['likes'] * 2 +
        post['reposts'] * 3 +
        post['replies'] +
        post['bookmarks'] * 2 +
        post['impressions'] * 0.001 +
        post['new_follows'] * 5
    )


def is_low_effort_reply(text):
    """Check if post is a low-effort reply (just @mention + short text)."""
    # Starts with @username and is short
    if text.startswith('@') and len(text) < 60:
        # Check if it's mostly just mentions and GM/GN/emoji
        stripped = re.sub(r'@\w+\s*', '', text).strip()
        if len(stripped) < 30:
            return True
    return False


def is_gm_post(text):
    """Check if post is a GM/GN community post."""
    lower = text.lower()
    gm_indicators = ['gm ', 'gm!', 'gmgm', 'gn ', 'gn!', 'good morning', 'good night', 'happy sunday', 'happy thanksgiving']
    return any(ind in lower for ind in gm_indicators) or lower.strip() in ['gm', 'gn']


def is_commentary(text):
    """Check if post is commentary on news/other content."""
    # Usually starts with @mention and has opinion
    return text.startswith('@') and len(text) > 60


def is_original_thought(text):
    """Check if post is original thought/content (not a reply)."""
    return not text.startswith('@')


def extract_hashtags(text):
    """Extract hashtags from text."""
    return re.findall(r'#\w+', text)


def extract_emojis(text):
    """Extract emojis from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.findall(text)


def analyze_posts(posts):
    """Analyze all posts and build style profile."""

    # Filter out deleted posts (0 impressions)
    active_posts = [p for p in posts if p['impressions'] > 0]

    # Calculate engagement scores
    for post in active_posts:
        post['engagement_score'] = calculate_engagement_score(post)
        post['is_low_effort_reply'] = is_low_effort_reply(post['text'])
        post['is_gm_post'] = is_gm_post(post['text'])
        post['is_commentary'] = is_commentary(post['text'])
        post['is_original'] = is_original_thought(post['text'])
        post['hashtags'] = extract_hashtags(post['text'])
        post['emojis'] = extract_emojis(post['text'])

    # Separate post types
    gm_posts = [p for p in active_posts if p['is_gm_post']]
    commentary_posts = [p for p in active_posts if p['is_commentary'] and not p['is_gm_post']]
    original_posts = [p for p in active_posts if p['is_original'] and not p['is_gm_post']]

    # Sort by engagement
    sorted_posts = sorted(active_posts, key=lambda x: x['engagement_score'], reverse=True)

    # Top 50 ORIGINAL posts only (not replies - doesn't start with @)
    original_only = [p for p in sorted_posts if p['is_original']]
    top_posts = original_only[:50]

    # Top performers by category
    top_gm = sorted(gm_posts, key=lambda x: x['engagement_score'], reverse=True)[:10]
    top_commentary = sorted(commentary_posts, key=lambda x: x['engagement_score'], reverse=True)[:20]
    top_original = sorted(original_posts, key=lambda x: x['engagement_score'], reverse=True)[:20]

    # Aggregate stats
    all_hashtags = []
    all_emojis = []
    post_lengths = []

    for p in active_posts:
        all_hashtags.extend(p['hashtags'])
        all_emojis.extend(p['emojis'])
        post_lengths.append(len(p['text']))

    hashtag_freq = Counter(all_hashtags).most_common(20)
    emoji_freq = Counter(all_emojis).most_common(20)

    # Style profile
    style_profile = {
        'total_posts': len(active_posts),
        'gm_posts_count': len(gm_posts),
        'commentary_count': len(commentary_posts),
        'original_count': len(original_posts),
        'avg_post_length': sum(post_lengths) / len(post_lengths) if post_lengths else 0,
        'median_post_length': sorted(post_lengths)[len(post_lengths)//2] if post_lengths else 0,
        'top_hashtags': hashtag_freq,
        'top_emojis': emoji_freq,
        'avg_likes': sum(p['likes'] for p in active_posts) / len(active_posts),
        'avg_impressions': sum(p['impressions'] for p in active_posts) / len(active_posts),
        'avg_engagement_score': sum(p['engagement_score'] for p in active_posts) / len(active_posts),
    }

    # Extract common phrases from top performers
    top_texts = [p['text'] for p in top_posts[:30]]

    return {
        'style_profile': style_profile,
        'top_posts': top_posts,
        'top_gm_posts': top_gm,
        'top_commentary': top_commentary,
        'top_original': top_original,
        'sample_high_performers': top_texts,
    }


def main():
    print("Loading posts...")
    posts = load_posts()
    print(f"Loaded {len(posts)} posts")

    print("Analyzing posts...")
    analysis = analyze_posts(posts)

    # Ensure tmp dir exists
    TMP_DIR.mkdir(exist_ok=True)

    # Save full analysis
    with open(TMP_DIR / "post_analysis.json", 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"Saved analysis to .tmp/post_analysis.json")

    # Save top posts separately (cleaner for content generation)
    top_posts_clean = [{
        'text': p['text'],
        'likes': p['likes'],
        'impressions': p['impressions'],
        'engagement_score': p['engagement_score'],
        'type': 'gm' if p['is_gm_post'] else 'commentary' if p['is_commentary'] else 'original'
    } for p in analysis['top_posts']]

    with open(TMP_DIR / "top_posts.json", 'w', encoding='utf-8') as f:
        json.dump(top_posts_clean, f, indent=2, ensure_ascii=False)
    print(f"Saved top posts to .tmp/top_posts.json")

    # Print summary
    sp = analysis['style_profile']
    print("\n" + "="*50)
    print("STYLE PROFILE SUMMARY")
    print("="*50)
    print(f"Total posts analyzed: {sp['total_posts']}")
    print(f"GM/Community posts: {sp['gm_posts_count']}")
    print(f"Commentary posts: {sp['commentary_count']}")
    print(f"Original content: {sp['original_count']}")
    print(f"Avg post length: {sp['avg_post_length']:.0f} chars")
    print(f"Avg likes: {sp['avg_likes']:.1f}")
    print(f"Avg impressions: {sp['avg_impressions']:.0f}")
    print(f"\nTop emojis: {[e[0] for e in sp['top_emojis'][:5]]}")

    print("\n" + "="*50)
    print("TOP 10 POSTS BY ENGAGEMENT")
    print("="*50)
    for i, p in enumerate(analysis['top_posts'][:10], 1):
        text_preview = p['text'][:80] + "..." if len(p['text']) > 80 else p['text']
        print(f"\n{i}. Score: {p['engagement_score']:.0f} | Likes: {p['likes']} | Impressions: {p['impressions']:,}")
        print(f"   {text_preview}")


if __name__ == "__main__":
    main()
