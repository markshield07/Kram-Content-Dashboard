from http.server import BaseHTTPRequestHandler
import os
import base64
import hashlib
import secrets
from urllib.parse import urlencode


def generate_pkce():
    """Generate PKCE code verifier and challenge."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    code_verifier = code_verifier.replace('=', '')[:128]

    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_id = os.environ.get('X_CLIENT_ID')
        app_url = os.environ.get('APP_URL', 'https://kram-content-dashboard.vercel.app')
        redirect_uri = f"{app_url}/api/auth/callback"

        if not client_id:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "X_CLIENT_ID not configured"}')
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

        # Redirect with cookies
        self.send_response(302)
        self.send_header('Location', auth_url)
        self.send_header('Set-Cookie', f'pkce_verifier={code_verifier}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=600')
        self.send_header('Set-Cookie', f'oauth_state={state}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=600')
        self.end_headers()
