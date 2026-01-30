"""
X OAuth 2.0 Callback Endpoint - Exchanges code for tokens
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


def encrypt_token(token, key):
    """Encrypt a token for secure storage."""
    cipher = Fernet(key.encode() if isinstance(key, str) else key)
    return cipher.encrypt(token.encode()).decode()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]
        error = params.get('error', [None])[0]

        app_url = os.environ.get('APP_URL', 'http://localhost:3000')

        # Handle errors from X
        if error:
            error_desc = params.get('error_description', ['Unknown error'])[0]
            self.send_response(302)
            self.send_header('Location', f"{app_url}/login?error={error_desc}")
            self.end_headers()
            return

        if not code:
            self.send_response(302)
            self.send_header('Location', f"{app_url}/login?error=No authorization code received")
            self.end_headers()
            return

        # Get cookies
        cookie_header = self.headers.get('Cookie', '')
        stored_state = get_cookie(cookie_header, 'oauth_state')
        code_verifier = get_cookie(cookie_header, 'pkce_verifier')

        # Validate state (CSRF protection)
        if not stored_state or stored_state != state:
            self.send_response(302)
            self.send_header('Location', f"{app_url}/login?error=Invalid state parameter")
            self.end_headers()
            return

        if not code_verifier:
            self.send_response(302)
            self.send_header('Location', f"{app_url}/login?error=Missing PKCE verifier")
            self.end_headers()
            return

        # Exchange code for tokens
        client_id = os.environ.get('X_CLIENT_ID')
        client_secret = os.environ.get('X_CLIENT_SECRET')
        redirect_uri = f"{app_url}/api/auth/callback"

        token_url = "https://api.twitter.com/2/oauth2/token"

        # Prepare token request
        token_data = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier,
            'client_id': client_id,
        }

        # Use Basic Auth if client_secret is available
        auth = None
        if client_secret:
            auth = (client_id, client_secret)

        try:
            response = requests.post(
                token_url,
                data=token_data,
                auth=auth,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            if response.status_code != 200:
                error_msg = response.json().get('error_description', 'Token exchange failed')
                self.send_response(302)
                self.send_header('Location', f"{app_url}/login?error={error_msg}")
                self.end_headers()
                return

            tokens = response.json()
            access_token = tokens.get('access_token')
            refresh_token = tokens.get('refresh_token')
            expires_in = tokens.get('expires_in', 7200)

            # Get user info
            user_response = requests.get(
                "https://api.twitter.com/2/users/me",
                headers={'Authorization': f'Bearer {access_token}'},
                params={'user.fields': 'profile_image_url,username,name'}
            )

            user_data = {}
            if user_response.status_code == 200:
                user_data = user_response.json().get('data', {})

            # Encrypt tokens for cookie storage
            encryption_key = os.environ.get('ENCRYPTION_KEY')
            if encryption_key:
                encrypted_access = encrypt_token(access_token, encryption_key)
                encrypted_refresh = encrypt_token(refresh_token, encryption_key) if refresh_token else ''
            else:
                # Fallback: base64 encode (less secure, for dev only)
                encrypted_access = base64.b64encode(access_token.encode()).decode()
                encrypted_refresh = base64.b64encode(refresh_token.encode()).decode() if refresh_token else ''

            # Redirect to dashboard with success
            self.send_response(302)
            self.send_header('Location', f"{app_url}/?logged_in=true")

            # Set auth cookies
            self.send_header('Set-Cookie', f'x_access_token={encrypted_access}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age={expires_in}')
            if encrypted_refresh:
                self.send_header('Set-Cookie', f'x_refresh_token={encrypted_refresh}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=15552000')  # 6 months

            # Set user info cookie (not sensitive, readable by JS)
            user_info = {
                'id': user_data.get('id', ''),
                'username': user_data.get('username', ''),
                'name': user_data.get('name', ''),
                'profile_image_url': user_data.get('profile_image_url', '')
            }
            user_info_b64 = base64.b64encode(json.dumps(user_info).encode()).decode()
            self.send_header('Set-Cookie', f'x_user={user_info_b64}; Secure; SameSite=Lax; Path=/; Max-Age={expires_in}')

            # Clear PKCE cookies
            self.send_header('Set-Cookie', 'pkce_verifier=; Path=/; Max-Age=0')
            self.send_header('Set-Cookie', 'oauth_state=; Path=/; Max-Age=0')

            self.end_headers()

        except Exception as e:
            self.send_response(302)
            self.send_header('Location', f"{app_url}/login?error={str(e)}")
            self.end_headers()
