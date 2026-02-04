from http.server import BaseHTTPRequestHandler
import json
import os
import base64
import urllib.request
import urllib.error
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

# Load the Mutant Ape reference image as base64 at module level
# This ensures GPT-4o always has the real image to reference
_MUTANT_APE_B64 = None
def _load_mutant_ape_image():
    global _MUTANT_APE_B64
    if _MUTANT_APE_B64 is not None:
        return _MUTANT_APE_B64
    # Try to find the image - check multiple possible paths for different environments
    possible_paths = [
        Path(__file__).parent.parent / 'assets' / 'mutant-ape' / 'mutant_ape.png',  # Local dev
        Path(__file__).parent / 'assets' / 'mutant-ape' / 'mutant_ape.png',  # Vercel includeFiles
        Path('/var/task/assets/mutant-ape/mutant_ape.png'),  # Vercel absolute
        Path('/var/task/api/assets/mutant-ape/mutant_ape.png'),  # Vercel alt path
    ]
    for img_path in possible_paths:
        if img_path.exists():
            with open(img_path, 'rb') as f:
                img_bytes = f.read()
            _MUTANT_APE_B64 = f"data:image/png;base64,{base64.b64encode(img_bytes).decode('utf-8')}"
            return _MUTANT_APE_B64
    return None

# ============================================
# Prompt Components (matching prompt_template.md)
# ============================================
# Format: "Reimagine this character in a [ART STYLE], [TEXTURE], [LIGHTING],
#          background: [BACKGROUND], [CAMERA/DEPTH EFFECT]."

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
            reference_image = data.get('reference_image', '')  # base64 data URL

            if not prompt:
                self._send_json(400, {'success': False, 'error': 'Prompt is required'})
                return

            # Map aspect ratio to DALL-E 3 sizes
            size_map = {
                '1:1': '1024x1024',
                '16:9': '1792x1024',
                '9:16': '1024x1792',
                '4:3': '1024x1024',
            }
            size = size_map.get(aspect_ratio, '1024x1024')

            # Map quality
            dall_e_quality = 'hd' if quality in ('high', 'ultra') else 'standard'

            # Get the art style from our template components
            art_style = ART_STYLES.get(style, ART_STYLES['realistic'])

            # Always use the Mutant Ape as reference for GPT-4o vision
            # User can override with their own reference image, but default is the Mutant Ape
            mutant_ape_b64 = _load_mutant_ape_image()

            # Determine which image to send to GPT-4o
            # If user uploaded a reference, use that; otherwise use the default Mutant Ape
            vision_image = reference_image if reference_image else mutant_ape_b64

            if vision_image:
                # Use GPT-4o vision to build prompt with the actual image reference
                enhanced = self._enhance_prompt_with_vision(
                    api_key, prompt, art_style, vision_image
                )
                if enhanced.get('error'):
                    self._send_json(500, {'success': False, 'error': enhanced['error']})
                    return
                full_prompt = enhanced['prompt']
                vision_description = enhanced.get('description', '')
            else:
                # Fallback: no image available, use text-only template
                full_prompt = self._build_template_prompt(prompt, art_style)
                vision_description = ''

            # Generate image with DALL-E 3
            result = self._call_dalle(api_key, full_prompt, size, dall_e_quality)

            if result.get('error'):
                self._send_json(500, {'success': False, 'error': result['error']})
            else:
                self._send_json(200, {
                    'success': True,
                    'images': result['images'],
                    'revised_prompt': result.get('revised_prompt', ''),
                    'enhanced_prompt': full_prompt,
                    'vision_description': vision_description,
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

    def _build_template_prompt(self, user_scene, art_style):
        """Build a DALL-E prompt using KRAM's exact template format.

        Template: "Reimagine this character in a [ART STYLE], [TEXTURE], [LIGHTING],
                   background: [BACKGROUND], [CAMERA/DEPTH EFFECT]."
        """
        # The user's prompt IS the scene/background description
        # We build the rest from our component library
        import random
        texture = random.choice(TEXTURES)
        lighting = random.choice(LIGHTING_OPTIONS)
        camera = random.choice(CAMERA_EFFECTS)

        prompt = (
            f"{CHARACTER_DESCRIPTION}. "
            f"Reimagine this character in a {art_style}, {texture}, {lighting}, "
            f"background: {user_scene}, {camera}."
        )
        return prompt

    def _enhance_prompt_with_vision(self, api_key, user_prompt, art_style, image_data):
        """Use GPT-4o to analyze the reference image and create a DALL-E prompt
        using KRAM's exact template format."""
        url = 'https://api.openai.com/v1/chat/completions'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        # GPT-4o system prompt - constrained to output in our EXACT template format
        system_msg = f"""You are an image prompt builder for KRAM's Mutant Ape NFT character.

The user will upload a REFERENCE IMAGE of their character. You MUST output a DALL-E 3 prompt that follows this EXACT template format:

TEMPLATE:
"[CHARACTER DESCRIPTION]. Reimagine this character in a [ART STYLE], [TEXTURE DETAILS], [LIGHTING], background: [BACKGROUND DESCRIPTION], [CAMERA/DEPTH EFFECT]."

KNOWN CHARACTER DETAILS (use as baseline, refine with what you see in the image):
{CHARACTER_DESCRIPTION}

COMPONENT LIBRARIES (pick one from each, or use the user's choice):

TEXTURES: {json.dumps(TEXTURES)}

LIGHTING: {json.dumps(LIGHTING_OPTIONS)}

CAMERA EFFECTS: {json.dumps(CAMERA_EFFECTS)}

RULES:
1. Look at the reference image to confirm/refine the character description
2. The ART STYLE is already chosen by the user: "{art_style}"
3. Pick the best TEXTURE, LIGHTING, and CAMERA EFFECT from the libraries above that match the user's scene request
4. The user's text prompt describes the BACKGROUND/SCENE they want
5. Output MUST follow the exact template format above - no extra narrative, no extra words
6. Keep the prompt under 800 characters total
7. Do NOT exaggerate or add elements not in the reference image

Return your response in this exact JSON format:
{{"description": "Brief 1-sentence description of what you see in the reference image", "prompt": "Your prompt following the exact template above"}}

EXAMPLE OUTPUT:
{{"description": "KRAM's Mutant Ape with cheetah print fur, gold coin eyes, green teeth, bunny ears headpiece, and small cheetah companion.", "prompt": "{CHARACTER_DESCRIPTION}. Reimagine this character in a {art_style}, ultra-detailed fur and skin textures, dramatic rim lighting, background: cozy coffee shop with morning light streaming through windows, shallow depth of field with bokeh."}}"""

        # Build the content array with text and image
        user_content = [
            {
                "type": "text",
                "text": f"Here is my reference image. Generate a DALL-E prompt using the exact template format. Art style: {art_style}. Scene/background I want: {user_prompt}"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data,
                    "detail": "high"
                }
            }
        ]

        payload = {
            'model': 'gpt-4o',
            'messages': [
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': user_content}
            ],
            'temperature': 0.3,
            'max_tokens': 600
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                content = result['choices'][0]['message']['content'].strip()

                # Parse the JSON response - handle markdown code blocks
                clean = content.strip()
                if clean.startswith('```'):
                    # Remove markdown code block wrapper
                    clean = clean.split('\n', 1)[1] if '\n' in clean else clean[3:]
                    if clean.endswith('```'):
                        clean = clean[:-3].strip()

                try:
                    parsed = json.loads(clean)
                    generated_prompt = parsed.get('prompt', '')

                    # Fallback: if GPT didn't follow the template, build it ourselves
                    if not generated_prompt or 'Reimagine this character' not in generated_prompt:
                        import random
                        texture = random.choice(TEXTURES)
                        lighting = random.choice(LIGHTING_OPTIONS)
                        camera = random.choice(CAMERA_EFFECTS)
                        generated_prompt = (
                            f"{CHARACTER_DESCRIPTION}. "
                            f"Reimagine this character in a {art_style}, {texture}, {lighting}, "
                            f"background: {user_prompt}, {camera}."
                        )

                    return {
                        'prompt': generated_prompt,
                        'description': parsed.get('description', '')
                    }
                except json.JSONDecodeError:
                    # If GPT didn't return valid JSON, build template prompt ourselves
                    import random
                    texture = random.choice(TEXTURES)
                    lighting = random.choice(LIGHTING_OPTIONS)
                    camera = random.choice(CAMERA_EFFECTS)
                    fallback_prompt = (
                        f"{CHARACTER_DESCRIPTION}. "
                        f"Reimagine this character in a {art_style}, {texture}, {lighting}, "
                        f"background: {user_prompt}, {camera}."
                    )
                    return {'prompt': fallback_prompt, 'description': ''}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                err_data = json.loads(error_body)
                err_msg = err_data.get('error', {}).get('message', error_body)
            except Exception:
                err_msg = error_body
            return {'error': f'GPT-4o vision error: {err_msg}'}
        except Exception as e:
            return {'error': f'Vision analysis error: {str(e)}'}

    def _call_dalle(self, api_key, prompt, size, quality):
        url = 'https://api.openai.com/v1/images/generations'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        payload = {
            'model': 'dall-e-3',
            'prompt': prompt,
            'n': 1,
            'size': size,
            'quality': quality,
            'response_format': 'url'
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                images = []
                revised_prompt = ''
                for item in result.get('data', []):
                    images.append(item.get('url', ''))
                    if item.get('revised_prompt'):
                        revised_prompt = item['revised_prompt']
                return {'images': images, 'revised_prompt': revised_prompt}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                err_data = json.loads(error_body)
                err_msg = err_data.get('error', {}).get('message', error_body)
            except Exception:
                err_msg = error_body
            return {'error': f'DALL-E error: {err_msg}'}
        except urllib.error.URLError as e:
            return {'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'error': f'Error: {str(e)}'}
