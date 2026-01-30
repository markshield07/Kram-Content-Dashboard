"""
X OAuth 2.0 Login Endpoint - Initiates PKCE flow
"""
import os
import base64
import hashlib
import secrets
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlencode
import json


def generate_pkce():
    """Generate PKCE code verifier and challenge."""
    # Generate code verifier (43-128 characters)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    code_verifier = code_verifier.replace('=', '')[:128]

    # Generate code challenge (SHA256 hash of verifier)
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Get environment variables
        client_id = os.environ.get('X_CLIENT_ID')
        app_url = os.environ.get('APP_URL', 'http://localhost:3000')
        redirect_uri = f"{app_url}/api/auth/callback"

        if not client_id:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'X_CLIENT_ID not configured'}).encode())
            return

        # Generate PKCE parameters
        code_verifier, code_challenge = generate_pkce()

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Build authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': 'tweet.read users.read offline.access',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256'
        }

        auth_url = f"https://twitter.com/i/oauth2/authorize?{urlencode(auth_params)}"

        # Set cookies to store PKCE verifier and state (httponly for security)
        self.send_response(302)
        self.send_header('Location', auth_url)

        # Store code_verifier in cookie (will be needed for token exchange)
        self.send_header('Set-Cookie', f'pkce_verifier={code_verifier}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=600')
        self.send_header('Set-Cookie', f'oauth_state={state}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=600')

        self.end_headers()
