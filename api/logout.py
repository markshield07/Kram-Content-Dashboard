"""
X OAuth 2.0 Logout Endpoint - Revokes tokens and clears session
"""
import os
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
        # Fallback: try base64 decode
        try:
            return base64.b64decode(encrypted_token).decode()
        except Exception:
            return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        app_url = os.environ.get('APP_URL', 'https://kram-content-dashboard.vercel.app')
        client_id = os.environ.get('X_CLIENT_ID')
        client_secret = os.environ.get('X_CLIENT_SECRET')
        encryption_key = os.environ.get('ENCRYPTION_KEY')

        # Get tokens from cookies
        cookie_header = self.headers.get('Cookie', '')
        encrypted_access = get_cookie(cookie_header, 'x_access_token')

        # Try to revoke the token with X API
        if encrypted_access and client_id:
            if encryption_key:
                access_token = decrypt_token(encrypted_access, encryption_key)
            else:
                try:
                    access_token = base64.b64decode(encrypted_access).decode()
                except Exception:
                    access_token = None

            if access_token:
                try:
                    revoke_url = "https://api.twitter.com/2/oauth2/revoke"
                    revoke_data = {
                        'token': access_token,
                        'token_type_hint': 'access_token',
                        'client_id': client_id,
                    }

                    auth = None
                    if client_secret:
                        auth = (client_id, client_secret)

                    requests.post(
                        revoke_url,
                        data=revoke_data,
                        auth=auth,
                        headers={'Content-Type': 'application/x-www-form-urlencoded'}
                    )
                except Exception:
                    pass  # Continue with logout even if revoke fails

        # Redirect to login page and clear all auth cookies
        self.send_response(302)
        self.send_header('Location', f"{app_url}/login?logged_out=true")

        # Clear all auth cookies
        self.send_header('Set-Cookie', 'x_access_token=; Path=/; Max-Age=0')
        self.send_header('Set-Cookie', 'x_refresh_token=; Path=/; Max-Age=0')
        self.send_header('Set-Cookie', 'x_user=; Path=/; Max-Age=0')

        self.end_headers()
