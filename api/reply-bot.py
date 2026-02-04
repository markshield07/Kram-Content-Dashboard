"""
Reply Bot Endpoint - Manages reply bot settings and executes replies to commenters on user's posts.

GET /api/reply-bot
    Returns bot settings and status.

GET /api/reply-bot?action=replies&tweet_id=XXXXX
    Fetches replies/comments on a specific user tweet (requires tweet.read scope).

POST /api/reply-bot?action=reply
    Body: { "tweet_id": "...", "reply_text": "..." }
    Posts a reply to a specific tweet via X API.

POST /api/reply-bot?action=settings
    Body: { settings object }
    Updates bot settings.
"""
import os
import json
import base64
import requests
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from http.cookies import SimpleCookie
from cryptography.fernet import Fernet


# Default bot settings
DEFAULT_SETTINGS = {
    'enabled': False,
    'gm_enabled': True,
    'gm_templates': [
        'GM {NAME}',
        'Morning {NAME}',
        'Gmgm {NAME}',
        'GM',
        'Gm'
    ],
    'verified_only': True,
    'reply_speed': '1min',
    'max_replies_per_post': 10,
    'enabled_post_ids': [],
    'stats': {
        'bot_replies_sent': 0
    }
}


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


def get_access_token(headers, encryption_key, client_id, client_secret):
    """Extract and decrypt the access token from cookies, refreshing if needed.
    Returns (access_token, error_response) - if error_response is set, access_token is None."""
    cookie_header = headers.get('Cookie', '')
    encrypted_access = get_cookie(cookie_header, 'x_access_token')
    encrypted_refresh = get_cookie(cookie_header, 'x_refresh_token')

    if not encrypted_access:
        return None, {'error': 'Not authenticated'}

    # Decrypt access token
    if encryption_key:
        access_token = decrypt_token(encrypted_access, encryption_key)
    else:
        try:
            access_token = base64.b64decode(encrypted_access).decode()
        except Exception:
            access_token = None

    if not access_token:
        return None, {'error': 'Invalid token'}

    # Verify token is still valid
    verify_response = requests.get(
        "https://api.twitter.com/2/users/me",
        headers={'Authorization': f'Bearer {access_token}'}
    )

    if verify_response.status_code == 401 and encrypted_refresh:
        # Token expired, try to refresh
        refresh_token = decrypt_token(encrypted_refresh, encryption_key) if encryption_key else None
        if not refresh_token:
            try:
                refresh_token = base64.b64decode(encrypted_refresh).decode()
            except Exception:
                refresh_token = None

        if refresh_token:
            new_tokens = refresh_access_token(refresh_token, client_id, client_secret)
            if new_tokens:
                access_token = new_tokens.get('access_token')
                return access_token, None

        return None, {'error': 'Token expired and refresh failed'}

    if verify_response.status_code != 200:
        return None, {'error': f'Token validation failed: status {verify_response.status_code}'}

    return access_token, None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests - return settings or fetch replies to a tweet."""
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        client_id = os.environ.get('X_CLIENT_ID')
        client_secret = os.environ.get('X_CLIENT_SECRET')

        access_token, error = get_access_token(
            self.headers, encryption_key, client_id, client_secret
        )

        if error:
            self._send_json(401, error)
            return

        # Parse query parameters
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        action = params.get('action', [None])[0]

        if action == 'replies':
            # Fetch replies to a specific tweet
            tweet_id = params.get('tweet_id', [None])[0]
            if not tweet_id:
                self._send_json(400, {'error': 'tweet_id is required'})
                return
            self._fetch_replies(tweet_id, access_token)
        else:
            # Return current settings
            settings = dict(DEFAULT_SETTINGS)
            self._send_json(200, settings)

    def _fetch_replies(self, tweet_id, access_token):
        """Fetch replies/comments on a specific tweet using the search endpoint.

        Note: On the free X API tier, the search endpoint has limited access.
        We use the tweets search endpoint to find replies to a specific tweet.
        """
        # Use the search/recent endpoint to find replies to this tweet
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        search_params = {
            'query': f'conversation_id:{tweet_id} is:reply',
            'max_results': 20,
            'tweet.fields': 'author_id,created_at,text,public_metrics,in_reply_to_user_id',
            'expansions': 'author_id',
            'user.fields': 'name,username,verified,profile_image_url'
        }

        try:
            response = requests.get(
                search_url,
                headers={'Authorization': f'Bearer {access_token}'},
                params=search_params
            )

            if response.status_code == 200:
                data = response.json()
                tweets = data.get('data', [])
                users_list = data.get('includes', {}).get('users', [])

                # Build user lookup
                users = {u['id']: u for u in users_list}

                # Process replies
                replies = []
                for tweet in tweets:
                    author = users.get(tweet.get('author_id'), {})
                    replies.append({
                        'id': tweet.get('id'),
                        'text': tweet.get('text'),
                        'created_at': tweet.get('created_at'),
                        'author': {
                            'id': tweet.get('author_id'),
                            'name': author.get('name', 'Unknown'),
                            'username': author.get('username', ''),
                            'verified': author.get('verified', False),
                            'profile_image_url': author.get('profile_image_url', '')
                        },
                        'metrics': tweet.get('public_metrics', {})
                    })

                self._send_json(200, {
                    'tweet_id': tweet_id,
                    'replies': replies,
                    'count': len(replies)
                })
            else:
                # Handle errors (e.g., free tier doesn't have search access)
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', error_data.get('title', f'Status {response.status_code}'))
                except Exception:
                    error_msg = f'X API returned status {response.status_code}'
                    error_data = {}

                self._send_json(response.status_code, {
                    'error': error_msg,
                    'details': error_data,
                    'note': 'The search/recent endpoint may not be available on the free X API tier. Consider upgrading to Basic tier for reply fetching.'
                })

        except requests.exceptions.Timeout:
            self._send_json(504, {'error': 'Request to X API timed out'})
        except requests.exceptions.ConnectionError:
            self._send_json(502, {'error': 'Failed to connect to X API'})
        except Exception as e:
            self._send_json(500, {'error': f'Unexpected error: {str(e)}'})

    def do_POST(self):
        """Handle POST requests - update settings or execute a reply."""
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        client_id = os.environ.get('X_CLIENT_ID')
        client_secret = os.environ.get('X_CLIENT_SECRET')

        access_token, error = get_access_token(
            self.headers, encryption_key, client_id, client_secret
        )

        if error:
            self._send_json(401, error)
            return

        # Parse query parameters to determine action
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        action = params.get('action', [None])[0]

        # Read request body
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_json(400, {'error': 'Invalid JSON in request body'})
            return
        except Exception as e:
            self._send_json(400, {'error': f'Failed to read request body: {str(e)}'})
            return

        if action == 'reply':
            self._handle_reply(data, access_token)
        else:
            self._handle_update_settings(data)

    def _handle_reply(self, data, access_token):
        """Execute a reply to a specific tweet via X API."""
        tweet_id = data.get('tweet_id')
        reply_text = data.get('reply_text')

        if not tweet_id:
            self._send_json(400, {'error': 'tweet_id is required'})
            return

        if not reply_text:
            self._send_json(400, {'error': 'reply_text is required'})
            return

        # Post reply via X API
        tweet_payload = {
            'text': reply_text,
            'reply': {
                'in_reply_to_tweet_id': str(tweet_id)
            }
        }

        try:
            response = requests.post(
                'https://api.twitter.com/2/tweets',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                json=tweet_payload
            )

            if response.status_code in (200, 201):
                response_data = response.json()
                tweet_data = response_data.get('data', {})
                self._send_json(200, {
                    'success': True,
                    'tweet_id': tweet_data.get('id'),
                    'text': tweet_data.get('text'),
                    'in_reply_to': str(tweet_id)
                })
            else:
                # Extract error details from X API response
                try:
                    error_data = response.json()
                    x_error = ''
                    if 'detail' in error_data:
                        x_error = error_data['detail']
                    elif 'errors' in error_data and len(error_data['errors']) > 0:
                        x_error = error_data['errors'][0].get('message', '')
                    elif 'title' in error_data:
                        x_error = error_data['title']
                    error_msg = (
                        f"X API error ({response.status_code}): {x_error}"
                        if x_error
                        else f"X API returned status {response.status_code}"
                    )
                except Exception:
                    error_msg = f"X API returned status {response.status_code}"
                    error_data = {}

                self._send_json(response.status_code, {
                    'success': False,
                    'error': error_msg,
                    'details': error_data
                })

        except requests.exceptions.Timeout:
            self._send_json(504, {
                'success': False,
                'error': 'Request to X API timed out'
            })
        except requests.exceptions.ConnectionError:
            self._send_json(502, {
                'success': False,
                'error': 'Failed to connect to X API'
            })
        except Exception as e:
            self._send_json(500, {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            })

    def _handle_update_settings(self, data):
        """Update bot settings."""
        # Start with defaults, merge in provided settings
        settings = dict(DEFAULT_SETTINGS)

        # Update only the fields that were provided
        if 'enabled' in data:
            settings['enabled'] = bool(data['enabled'])
        if 'gm_enabled' in data:
            settings['gm_enabled'] = bool(data['gm_enabled'])
        if 'gm_templates' in data and isinstance(data['gm_templates'], list):
            settings['gm_templates'] = data['gm_templates']
        if 'verified_only' in data:
            settings['verified_only'] = bool(data['verified_only'])
        if 'reply_speed' in data:
            settings['reply_speed'] = data['reply_speed']
        if 'max_replies_per_post' in data:
            settings['max_replies_per_post'] = int(data['max_replies_per_post'])
        if 'enabled_post_ids' in data and isinstance(data['enabled_post_ids'], list):
            settings['enabled_post_ids'] = data['enabled_post_ids']

        # In production, save settings to persistent storage here

        self._send_json(200, {
            'success': True,
            'settings': settings
        })

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def _send_json(self, code, data):
        """Send a JSON response with CORS headers."""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
