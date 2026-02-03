"""
Analytics Tweets Endpoint - Fetches user's tweets with engagement metrics
"""
import os
import json
import base64
import requests
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from http.cookies import SimpleCookie
from cryptography.fernet import Fernet


def get_cookie(cookie_header, name):
    """Extract a cookie value from the Cookie header."""
    if not cookie_header:
        return None
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    if name in cookie:
        return cookie[name].value
    return None


def decrypt_token(encrypted_token, key):
    """Decrypt a token."""
    try:
        cipher = Fernet(key.encode() if isinstance(key, str) else key)
        return cipher.decrypt(encrypted_token.encode()).decode()
    except Exception:
        try:
            return base64.b64decode(encrypted_token).decode()
        except Exception:
            return None


def refresh_access_token(refresh_token, client_id, client_secret):
    """Refresh the access token using refresh token."""
    token_url = "https://api.twitter.com/2/oauth2/token"

    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
    }

    auth = None
    if client_secret:
        auth = (client_id, client_secret)

    response = requests.post(
        token_url,
        data=token_data,
        auth=auth,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    if response.status_code == 200:
        return response.json()
    return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        max_results = params.get('max_results', ['20'])[0]

        # Get encryption key and tokens
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        client_id = os.environ.get('X_CLIENT_ID')
        client_secret = os.environ.get('X_CLIENT_SECRET')

        cookie_header = self.headers.get('Cookie', '')
        encrypted_access = get_cookie(cookie_header, 'x_access_token')
        encrypted_refresh = get_cookie(cookie_header, 'x_refresh_token')

        if not encrypted_access:
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not authenticated'}).encode())
            return

        # Decrypt access token
        if encryption_key:
            access_token = decrypt_token(encrypted_access, encryption_key)
        else:
            # No encryption key set - tokens are base64 encoded
            try:
                access_token = base64.b64decode(encrypted_access).decode()
            except Exception:
                access_token = None

        if not access_token:
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid token'}).encode())
            return

        # First get user ID
        user_response = requests.get(
            "https://api.twitter.com/2/users/me",
            headers={'Authorization': f'Bearer {access_token}'}
        )

        if user_response.status_code == 401 and encrypted_refresh:
            # Token expired, try to refresh
            refresh_token = decrypt_token(encrypted_refresh, encryption_key)
            if refresh_token:
                new_tokens = refresh_access_token(refresh_token, client_id, client_secret)
                if new_tokens:
                    access_token = new_tokens.get('access_token')
                    user_response = requests.get(
                        "https://api.twitter.com/2/users/me",
                        headers={'Authorization': f'Bearer {access_token}'}
                    )

        if user_response.status_code != 200:
            self.send_response(user_response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Failed to get user info'}).encode())
            return

        user_id = user_response.json().get('data', {}).get('id')

        # Fetch user's tweets with metrics
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        tweets_params = {
            'max_results': min(int(max_results), 100),
            'tweet.fields': 'public_metrics,created_at,text',
            'exclude': 'retweets,replies'
        }

        tweets_response = requests.get(
            tweets_url,
            headers={'Authorization': f'Bearer {access_token}'},
            params=tweets_params
        )

        if tweets_response.status_code != 200:
            self.send_response(tweets_response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_data = tweets_response.json()
            self.wfile.write(json.dumps({'error': 'Failed to fetch tweets', 'details': error_data}).encode())
            return

        tweets_data = tweets_response.json()
        tweets = tweets_data.get('data', [])

        # Process and sort by engagement
        processed_tweets = []
        for tweet in tweets:
            metrics = tweet.get('public_metrics', {})
            engagement = (
                metrics.get('like_count', 0) +
                metrics.get('retweet_count', 0) * 2 +
                metrics.get('reply_count', 0) +
                metrics.get('quote_count', 0) * 2
            )

            processed_tweets.append({
                'id': tweet.get('id'),
                'text': tweet.get('text'),
                'created_at': tweet.get('created_at'),
                'metrics': metrics,
                'engagement_score': engagement
            })

        # Sort by engagement score
        processed_tweets.sort(key=lambda x: x['engagement_score'], reverse=True)

        # Calculate summary stats
        total_likes = sum(t['metrics'].get('like_count', 0) for t in processed_tweets)
        total_retweets = sum(t['metrics'].get('retweet_count', 0) for t in processed_tweets)
        total_replies = sum(t['metrics'].get('reply_count', 0) for t in processed_tweets)

        result = {
            'tweets': processed_tweets,
            'summary': {
                'total_tweets': len(processed_tweets),
                'total_likes': total_likes,
                'total_retweets': total_retweets,
                'total_replies': total_replies,
                'avg_likes': total_likes / len(processed_tweets) if processed_tweets else 0,
                'avg_retweets': total_retweets / len(processed_tweets) if processed_tweets else 0
            }
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
