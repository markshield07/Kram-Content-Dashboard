from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error


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

            if not prompt:
                self._send_json(400, {'success': False, 'error': 'Prompt is required'})
                return

            # Map aspect ratio to DALL-E 3 sizes
            size_map = {
                '1:1': '1024x1024',
                '16:9': '1792x1024',
                '9:16': '1024x1792',
                '4:3': '1024x1024',  # DALL-E 3 doesn't support 4:3, use square
            }
            size = size_map.get(aspect_ratio, '1024x1024')

            # Map quality
            dall_e_quality = 'hd' if quality in ('high', 'ultra') else 'standard'

            # Build enhanced prompt with style
            style_prompts = {
                'realistic': 'Photorealistic, highly detailed, professional photography style.',
                'anime': 'Anime art style, vibrant colors, detailed illustration, manga-inspired.',
                'cartoon': 'Cartoon illustration style, bold outlines, vibrant colors, playful.',
                'pixel': 'Pixel art style, retro 8-bit/16-bit aesthetic, clean pixel grid.',
                'cyberpunk': 'Cyberpunk aesthetic, neon lights, dark atmosphere, futuristic technology, rain-slicked streets.',
                'watercolor': 'Watercolor painting style, soft edges, flowing colors, artistic brush strokes.',
            }

            style_suffix = style_prompts.get(style, style_prompts['realistic'])
            full_prompt = f"{prompt}. {style_suffix}"

            result = self._call_dalle(api_key, full_prompt, size, dall_e_quality)

            if result.get('error'):
                self._send_json(500, {'success': False, 'error': result['error']})
            else:
                self._send_json(200, {
                    'success': True,
                    'images': result['images'],
                    'revised_prompt': result.get('revised_prompt', ''),
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
            return {'error': f'OpenAI API error: {err_msg}'}
        except urllib.error.URLError as e:
            return {'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'error': f'Error: {str(e)}'}
