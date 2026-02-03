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
        response = {'status': 'ok', 'endpoint': 'generate', 'api_key_configured': has_key}
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
            platform = data.get('platform', 'twitter')
            tone = data.get('tone', 'professional')
            content_type = data.get('type', 'post')

            system_prompt = self._build_system_prompt(platform, tone, content_type)
            user_prompt = prompt if prompt else f"Create an engaging {content_type} for {platform}"

            result = self._call_openai(api_key, system_prompt, user_prompt)

            if result.get('error'):
                self._send_json(500, {'success': False, 'error': result['error']})
            else:
                self._send_json(200, {
                    'success': True,
                    'content': result['content'],
                    'platform': platform,
                    'tone': tone,
                    'type': content_type
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

    def _build_system_prompt(self, platform, tone, content_type):
        platform_rules = {
            'twitter': 'Keep posts under 280 characters. Make it punchy and engaging.',
            'instagram': 'Can be longer. Use hashtags. Include a call-to-action.',
            'linkedin': 'Professional tone. Can be longer form. End with a question.',
            'tiktok': 'Casual, trendy language. Short and catchy.',
            'facebook': 'Conversational tone. Medium length.'
        }

        tone_desc = {
            'professional': 'Professional and credible.',
            'casual': 'Friendly and approachable.',
            'witty': 'Clever and humorous.',
            'inspirational': 'Motivating and uplifting.',
            'educational': 'Informative and helpful.',
            'humorous': 'Funny and entertaining.'
        }

        type_rules = {
            'post': 'Create a single, standalone post.',
            'thread': 'Create a thread of 3-5 connected posts. Number each (1/, 2/, etc).',
            'reply': 'Create a concise, relevant reply.'
        }

        return f"""You are an expert social media content creator.

Platform: {platform.upper()}
{platform_rules.get(platform, platform_rules['twitter'])}

Tone: {tone}
{tone_desc.get(tone, tone_desc['professional'])}

Type: {content_type}
{type_rules.get(content_type, type_rules['post'])}

Create authentic, engaging content. No cringe phrases. Return ONLY the content text."""

    def _call_openai(self, api_key, system_prompt, user_prompt):
        url = 'https://api.openai.com/v1/chat/completions'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        payload = {
            'model': 'gpt-4o',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.8,
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
                content = result['choices'][0]['message']['content']
                return {'content': content.strip()}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return {'error': f'OpenAI API error: {error_body}'}
        except urllib.error.URLError as e:
            return {'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'error': f'Error: {str(e)}'}
