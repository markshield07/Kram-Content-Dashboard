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

            # Style descriptions
            style_prompts = {
                'realistic': 'Photorealistic, highly detailed, professional photography style.',
                'anime': 'Anime art style, vibrant colors, detailed illustration, manga-inspired.',
                'cartoon': 'Cartoon illustration style, bold outlines, vibrant colors, playful.',
                'pixel': 'Pixel art style, retro 8-bit/16-bit aesthetic, clean pixel grid.',
                'cyberpunk': 'Cyberpunk aesthetic, neon lights, dark atmosphere, futuristic technology, rain-slicked streets.',
                'watercolor': 'Watercolor painting style, soft edges, flowing colors, artistic brush strokes.',
            }
            style_suffix = style_prompts.get(style, style_prompts['realistic'])

            # If reference image provided, use GPT-4o vision to create an enhanced prompt
            if reference_image:
                enhanced = self._enhance_prompt_with_vision(
                    api_key, prompt, style_suffix, reference_image
                )
                if enhanced.get('error'):
                    self._send_json(500, {'success': False, 'error': enhanced['error']})
                    return
                full_prompt = enhanced['prompt']
                vision_description = enhanced.get('description', '')
            else:
                full_prompt = f"{prompt}. {style_suffix}"
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
                    'enhanced_prompt': full_prompt if reference_image else '',
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

    def _enhance_prompt_with_vision(self, api_key, user_prompt, style_suffix, image_data):
        """Use GPT-4o to analyze the reference image and create a detailed DALL-E prompt."""
        url = 'https://api.openai.com/v1/chat/completions'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        system_msg = """You are an expert at describing images in extreme detail for image generation.

The user uploaded a REFERENCE IMAGE. Your job is to describe the main subject/character in that image with EXTREME PRECISION so that DALL-E 3 can recreate it as accurately as possible in a new scene.

STEP 1: Describe the reference image subject in hyper-specific detail:
- Exact colors (not just "blue" but "deep cobalt blue with cyan highlights")
- Physical features, proportions, distinguishing marks
- Clothing, accessories, textures, patterns
- Facial expression, pose, body language
- Any unique/distinctive elements that make this character recognizable

STEP 2: Combine that detailed character description with the user's creative direction and style.

STEP 3: Write a single DALL-E 3 prompt that:
- Starts with the detailed character description so DALL-E knows EXACTLY what the subject looks like
- Then places that character in the scene/setting the user requested
- Applies the requested art style
- Is under 1500 characters

Return your response in this exact JSON format:
{"description": "2-3 sentence summary of the reference image", "prompt": "Your hyper-detailed DALL-E 3 prompt"}

CRITICAL: The more specific and detailed your character description, the closer DALL-E's output will match the reference. Be obsessively detailed about the subject's appearance."""

        # Build the content array with text and image
        user_content = [
            {
                "type": "text",
                "text": f"Here is my reference image. Describe the main subject in extreme detail, then place them in this scene: {user_prompt}. Apply this style: {style_suffix}"
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
            'temperature': 0.5,
            'max_tokens': 1000
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
                    return {
                        'prompt': parsed.get('prompt', f"{user_prompt}. {style_suffix}"),
                        'description': parsed.get('description', '')
                    }
                except json.JSONDecodeError:
                    # If GPT didn't return valid JSON, use the raw text as the prompt
                    return {'prompt': content, 'description': ''}

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
