from http.server import BaseHTTPRequestHandler
import json
import os
import base64
import random
import urllib.request
import urllib.error
import io
from pathlib import Path


# ============================================
# KRAM's Mutant Ape - Character Reference
# ============================================
CHARACTER_DESCRIPTION = (
    "KRAM's Mutant Ape Yacht Club NFT character - a stylized ape with cheetah/leopard print fur "
    "(yellow-gold base with brown spots), glowing golden coin eyes with sparkle effects and dripping gold, "
    "wide grin with mint green gradient teeth and pink gums visible, brown shaggy mustache and beard, "
    "white bunny ears headpiece with pink/brown inner ears and a small cartoon face on each ear, "
    "small silver piercing in left ear, mischievous grin with wild energy, "
    "and a small cheetah companion creature at bottom with orange eyes and spotted fur"
)

# ============================================
# Prompt Components (matching prompt_template.md)
# ============================================
ART_STYLES = {
    'realistic': 'hyper-realistic cinematic 3D style',
    'anime': 'anime/manga style with bold linework',
    'pixel': 'retro pixel art 16-bit gaming aesthetic',
    'watercolor': 'loose watercolor painting style',
    'oil_painting': 'classical oil painting portrait style',
    'cyberpunk': 'cyberpunk neon aesthetic',
    'vaporwave': 'vaporwave 80s retro style',
    'comic': 'comic book pop art with halftone dots',
    'low_poly': 'low-poly geometric 3D style',
    'ukiyoe': 'ukiyo-e Japanese woodblock print style',
    'graffiti': 'graffiti street art style',
    'stained_glass': 'stained glass medieval art style',
    'claymation': 'claymation stop-motion style',
    'psychedelic': 'psychedelic 70s concert poster style',
    'synthwave': 'synthwave retrofuturism style',
    'ghibli': 'Studio Ghibli inspired illustration',
    'noir': 'neon noir detective style',
    'greek': 'ancient Greek pottery art style',
    'art_deco': 'art deco 1920s glamour style',
    'impressionist': 'impressionist painting style',
}

TEXTURES = [
    'ultra-detailed fur and skin textures',
    'smooth cel-shaded surfaces',
    'glossy metallic chrome finish',
    'rough painterly brushstrokes',
    'crisp vector-clean edges',
    'grainy vintage film texture',
    'soft pastel gradient shading',
    'hard geometric faceted surfaces',
    'organic flowing liquid forms',
    'holographic iridescent sheen',
    'matte rubber-like finish',
    'crystalline gem-like surfaces',
    'weathered aged patina texture',
    'glowing bioluminescent skin',
]

LIGHTING_OPTIONS = [
    'dramatic rim lighting',
    'soft golden hour warm glow',
    'harsh neon pink and blue underglow',
    'moody chiaroscuro deep shadows',
    'bright flat even lighting',
    'bioluminescent ethereal glow',
    'sunset backlit silhouette effect',
    'studio three-point professional lighting',
    'warm candlelit ambiance',
    'cold blue moonlight wash',
    'RGB gaming setup lighting',
    'cinematic lens flares',
]

CAMERA_EFFECTS = [
    'shallow depth of field with bokeh',
    'wide-angle dramatic perspective',
    'subtle fisheye lens distortion',
    'tilt-shift miniature effect',
    'cinematic widescreen 2.35:1 crop',
    'portrait orientation with blurred background',
    'isometric three-quarter angle view',
    'Dutch angle for dynamic tension',
    'macro close-up on face details',
    'symmetrical centered composition',
]


# ============================================
# Load the Mutant Ape reference image bytes
# ============================================
_MUTANT_APE_BYTES = None

def _load_mutant_ape_bytes():
    """Load the mutant ape PNG as raw bytes for the images/edits endpoint."""
    global _MUTANT_APE_BYTES
    if _MUTANT_APE_BYTES is not None:
        return _MUTANT_APE_BYTES
    possible_paths = [
        Path(__file__).parent.parent / 'assets' / 'mutant-ape' / 'mutant_ape.png',
        Path(__file__).parent / 'assets' / 'mutant-ape' / 'mutant_ape.png',
        Path('/var/task/assets/mutant-ape/mutant_ape.png'),
        Path('/var/task/api/assets/mutant-ape/mutant_ape.png'),
    ]
    for img_path in possible_paths:
        if img_path.exists():
            with open(img_path, 'rb') as f:
                _MUTANT_APE_BYTES = f.read()
            return _MUTANT_APE_BYTES
    return None


def _decode_data_url(data_url):
    """Decode a base64 data URL (data:image/png;base64,...) to raw bytes."""
    if ',' in data_url:
        encoded = data_url.split(',', 1)[1]
    else:
        encoded = data_url
    return base64.b64decode(encoded)


def _build_multipart(fields, files):
    """Build a multipart/form-data request body manually.

    fields: dict of {name: value} for text fields
    files: list of (field_name, filename, content_bytes, content_type)
    Returns (content_type_header, body_bytes)
    """
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    parts = []

    for key, value in fields.items():
        parts.append(f'--{boundary}\r\n'.encode())
        parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        parts.append(f'{value}\r\n'.encode())

    for field_name, filename, content_bytes, content_type in files:
        parts.append(f'--{boundary}\r\n'.encode())
        parts.append(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
        )
        parts.append(f'Content-Type: {content_type}\r\n\r\n'.encode())
        parts.append(content_bytes)
        parts.append(b'\r\n')

    parts.append(f'--{boundary}--\r\n'.encode())

    body = b''.join(parts)
    content_type = f'multipart/form-data; boundary={boundary}'
    return content_type, body


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        api_key = os.environ.get('OPENAI_API_KEY', '')
        has_key = 'yes' if api_key else 'no'
        response = {'status': 'ok', 'endpoint': 'image', 'api_key_configured': has_key}
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        try:
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                self._send_json(500, {'success': False, 'error': 'OPENAI_API_KEY not configured'})
                return

            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            prompt = data.get('prompt', '')
            style = data.get('style', 'realistic')
            aspect_ratio = data.get('aspect_ratio', '1:1')
            quality = data.get('quality', 'standard')
            reference_image = data.get('reference_image', '')  # base64 data URL from frontend

            if not prompt:
                self._send_json(400, {'success': False, 'error': 'Prompt is required'})
                return

            # Map aspect ratio to gpt-image-1 sizes
            size_map = {
                '1:1': '1024x1024',
                '16:9': '1536x1024',
                '9:16': '1024x1536',
                '4:3': '1024x1024',
            }
            size = size_map.get(aspect_ratio, '1024x1024')

            # Map quality for gpt-image-1
            gpt_quality = 'high' if quality in ('high', 'ultra') else 'medium'

            # Get the art style from our template components
            art_style = ART_STYLES.get(style, ART_STYLES['realistic'])

            # Build the full prompt using our template format
            texture = random.choice(TEXTURES)
            lighting = random.choice(LIGHTING_OPTIONS)
            camera = random.choice(CAMERA_EFFECTS)

            full_prompt = (
                f"Reimagine the character from the reference image in a {art_style}, "
                f"{texture}, {lighting}, "
                f"background: {prompt}, {camera}. "
                f"Keep the character's exact appearance, features, colors, and proportions "
                f"faithful to the reference image. Do not add or remove any features."
            )

            # Get image bytes - user upload takes priority, otherwise use default Mutant Ape
            if reference_image:
                image_bytes = _decode_data_url(reference_image)
            else:
                image_bytes = _load_mutant_ape_bytes()

            if not image_bytes:
                self._send_json(500, {'success': False, 'error': 'No reference image available. Please upload an image.'})
                return

            # Generate with gpt-image-1 via /images/edits (can see the reference image)
            result = self._call_gpt_image(api_key, full_prompt, image_bytes, size, gpt_quality)

            if result.get('error'):
                self._send_json(500, {'success': False, 'error': result['error']})
            else:
                self._send_json(200, {
                    'success': True,
                    'images': result['images'],
                    'revised_prompt': '',
                    'enhanced_prompt': full_prompt,
                    'vision_description': '',
                })

        except json.JSONDecodeError:
            self._send_json(400, {'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            self._send_json(500, {'success': False, 'error': str(e)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _call_gpt_image(self, api_key, prompt, image_bytes, size, quality):
        """Generate image using gpt-image-1 /images/edits endpoint.

        This model actually SEES the reference image and generates based on it,
        unlike DALL-E 3 which only takes text prompts.
        """
        url = 'https://api.openai.com/v1/images/edits'

        # Build multipart form data
        fields = {
            'model': 'gpt-image-1',
            'prompt': prompt,
            'size': size,
            'quality': quality,
            'n': '1',
        }

        files = [
            ('image', 'reference.png', image_bytes, 'image/png'),
        ]

        content_type, body = _build_multipart(fields, files)

        headers = {
            'Content-Type': content_type,
            'Authorization': f'Bearer {api_key}'
        }

        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
                images = []
                for item in result.get('data', []):
                    # gpt-image-1 returns base64, convert to data URL
                    b64 = item.get('b64_json', '')
                    if b64:
                        images.append(f'data:image/png;base64,{b64}')
                    elif item.get('url'):
                        images.append(item['url'])
                return {'images': images}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                err_data = json.loads(error_body)
                err_msg = err_data.get('error', {}).get('message', error_body)
            except Exception:
                err_msg = error_body
            return {'error': f'GPT Image error: {err_msg}'}
        except urllib.error.URLError as e:
            return {'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'error': f'Error: {str(e)}'}
