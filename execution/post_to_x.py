"""
Post to X (Twitter) with image attachment using OAuth 1.0a
"""

import os
import sys
import json
import base64
from pathlib import Path
from datetime import date

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
import tweepy

# Load environment variables
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# X API credentials
API_KEY = os.getenv("X_API_KEY")
API_SECRET = os.getenv("X_API_SECRET")
ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")


def get_x_client():
    """Create and return authenticated X API client."""
    # OAuth 1.0a authentication for posting
    auth = tweepy.OAuth1UserHandler(
        API_KEY,
        API_SECRET,
        ACCESS_TOKEN,
        ACCESS_TOKEN_SECRET
    )

    # API v1.1 for media upload
    api_v1 = tweepy.API(auth)

    # API v2 for posting tweets
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET
    )

    return client, api_v1


def post_with_image(text: str, image_path: str) -> dict:
    """Post a tweet with an image attachment."""
    try:
        client, api_v1 = get_x_client()

        # Upload image using v1.1 API
        print(f"Uploading image: {image_path}")
        media = api_v1.media_upload(filename=image_path)
        print(f"Image uploaded, media_id: {media.media_id}")

        # Post tweet with media using v2 API
        print(f"Posting tweet...")
        response = client.create_tweet(
            text=text,
            media_ids=[media.media_id]
        )

        tweet_id = response.data['id']
        tweet_url = f"https://twitter.com/KRAM_btc/status/{tweet_id}"

        print(f"Successfully posted!")
        print(f"Tweet URL: {tweet_url}")

        return {
            "success": True,
            "tweet_id": tweet_id,
            "tweet_url": tweet_url
        }

    except tweepy.TweepyException as e:
        print(f"Error posting to X: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def post_text_only(text: str) -> dict:
    """Post a tweet without an image."""
    try:
        client, _ = get_x_client()

        print(f"Posting tweet...")
        response = client.create_tweet(text=text)

        tweet_id = response.data['id']
        tweet_url = f"https://twitter.com/KRAM_btc/status/{tweet_id}"

        print(f"Successfully posted!")
        print(f"Tweet URL: {tweet_url}")

        return {
            "success": True,
            "tweet_id": tweet_id,
            "tweet_url": tweet_url
        }

    except tweepy.TweepyException as e:
        print(f"Error posting to X: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def post_from_daily_content(post_index: int = 0, target_date: str = None):
    """Post content from the daily content JSON file."""
    if target_date is None:
        target_date = date.today().isoformat()

    content_file = BASE_DIR / ".tmp" / "daily_content" / f"{target_date}.json"

    if not content_file.exists():
        print(f"No content found for {target_date}")
        print(f"Run: python execution/generate_content.py")
        return None

    with open(content_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    posts = data.get('posts', [])
    if post_index >= len(posts):
        print(f"Post index {post_index} out of range (only {len(posts)} posts)")
        return None

    post = posts[post_index]
    text = post['post_text']
    image_path = post.get('image_path')

    print(f"Post text: {text}")

    if image_path:
        full_image_path = BASE_DIR / image_path
        if full_image_path.exists():
            return post_with_image(text, str(full_image_path))
        else:
            print(f"Image not found: {full_image_path}")
            print("Posting without image...")
            return post_text_only(text)
    else:
        print("No image for this post, posting text only...")
        return post_text_only(text)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Post to X (Twitter)")
    parser.add_argument("--text", type=str, help="Text to post")
    parser.add_argument("--image", type=str, help="Path to image file")
    parser.add_argument("--date", type=str, help="Date of content to post (YYYY-MM-DD)")
    parser.add_argument("--index", type=int, default=0, help="Post index from daily content")
    parser.add_argument("--test", action="store_true", help="Test API connection")

    args = parser.parse_args()

    if args.test:
        # Test API connection
        print("Testing X API connection...")
        try:
            client, api_v1 = get_x_client()
            me = client.get_me()
            print(f"Connected as: @{me.data.username}")
            print("API connection successful!")
            return 0
        except Exception as e:
            print(f"API connection failed: {e}")
            return 1

    if args.text:
        # Post custom text
        if args.image:
            result = post_with_image(args.text, args.image)
        else:
            result = post_text_only(args.text)
    else:
        # Post from daily content
        result = post_from_daily_content(args.index, args.date)

    if result and result.get('success'):
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
