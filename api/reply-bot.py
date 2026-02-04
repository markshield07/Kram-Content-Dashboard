"""
Reply Bot Endpoint - Manages reply bot settings and executes replies via X API
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
    'gm_enabled': False,
    'gm_templates': [
        'gm',
        'gm! hope you have a great day',
        'gm fren'
    ],
    'verified_only': True,
    'frequency': 'every',
    'active_hours': {
        'start': '07:00',
        'end': '23:00'
    },
    'stats': {
        'today': 0,
        'week': 0,
        'accounts': 0
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
        """Get current bot settings and status."""
        # Require authentication
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        client_id = os.environ.get('X_CLIENT_ID')
        client_secret = os.environ.get('X_CLIENT_SECRET')

        access_token, error = get_access_token(
            self.headers, encryption_key, client_id, client_secret
        )

        if error:
            self._send_json(401, error)
            return

        # Return current settings (in production, these would be loaded from
        # a database or persistent storage keyed by user ID)
        settings = dict(DEFAULT_SETTINGS)
        self._send_json(200, settings)

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
        if 'frequency' in data:
            settings['frequency'] = data['frequency']
        if 'active_hours' in data and isinstance(data['active_hours'], dict):
            active_hours = settings['active_hours']
            if 'start' in data['active_hours']:
                active_hours['start'] = data['active_hours']['start']
            if 'end' in data['active_hours']:
                active_hours['end'] = data['active_hours']['end']
            settings['active_hours'] = active_hours

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
