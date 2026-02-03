"""
Analytics Profile Endpoint - Fetches user's profile information
"""
import os
import json
import base64
import requests
from http.server import BaseHTTPRequestHandler
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


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Get encryption key and tokens
        encryption_key = os.environ.get('ENCRYPTION_KEY')

        cookie_header = self.headers.get('Cookie', '')
        encrypted_access = get_cookie(cookie_header, 'x_access_token')

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

        # Fetch user profile with extended fields
        user_response = requests.get(
            "https://api.twitter.com/2/users/me",
            headers={'Authorization': f'Bearer {access_token}'},
            params={
                'user.fields': 'profile_image_url,username,name,description,public_metrics,created_at,verified'
            }
        )

        if user_response.status_code != 200:
            self.send_response(user_response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Failed to fetch profile'}).encode())
            return

        user_data = user_response.json().get('data', {})

        # Format response
        profile = {
            'id': user_data.get('id'),
            'username': user_data.get('username'),
            'name': user_data.get('name'),
            'description': user_data.get('description'),
            'profile_image_url': user_data.get('profile_image_url', '').replace('_normal', '_400x400'),  # Get larger image
            'verified': user_data.get('verified', False),
            'created_at': user_data.get('created_at'),
            'metrics': user_data.get('public_metrics', {})
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(profile).encode())
