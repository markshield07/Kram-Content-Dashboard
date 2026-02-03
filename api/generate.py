from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get OpenAI API key from environment
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                self.send_error_response(500, 'OPENAI_API_KEY not configured')
                return

            # Parse request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body) if body else {}

            # Extract parameters
            prompt = data.get('prompt', '')
            platform = data.get('platform', 'twitter')
            tone = data.get('tone', 'professional')
            content_type = data.get('type', 'post')  # post, thread, reply
            topic = data.get('topic', '')
            brand_voice = data.get('brandVoice', {})

            # Build the system prompt
            system_prompt = self._build_system_prompt(platform, tone, content_type, brand_voice)

            # Build user prompt
            user_prompt = self._build_user_prompt(prompt, topic, content_type, platform)

            # Call OpenAI API
            result = self._call_openai(api_key, system_prompt, user_prompt)

            if result.get('error'):
                self.send_error_response(500, result['error'])
                return

            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = {
                'success': True,
                'content': result['content'],
                'platform': platform,
                'tone': tone,
                'type': content_type
            }
            self.wfile.write(json.dumps(response).encode())

        except json.JSONDecodeError:
            self.send_error_response(400, 'Invalid JSON in request body')
        except Exception as e:
            self.send_error_response(500, str(e))

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {'success': False, 'error': message}
        self.wfile.write(json.dumps(response).encode())

    def _build_system_prompt(self, platform, tone, content_type, brand_voice):
        # Platform-specific constraints
        platform_rules = {
            'twitter': 'Keep posts under 280 characters. Use hashtags sparingly (1-2 max). Make it punchy and engaging.',
            'instagram': 'Can be longer (up to 2200 chars). Use more hashtags (5-10). Include a call-to-action. Use line breaks for readability.',
            'linkedin': 'Professional tone. Can be longer form. Use line breaks. End with a question or call-to-action to drive engagement.',
            'tiktok': 'Casual, trendy language. Short and catchy. Use relevant trending phrases. Hook in the first line.',
            'facebook': 'Conversational tone. Medium length. Encourage comments and shares.'
        }

        tone_descriptions = {
            'professional': 'Professional, authoritative, and credible. Use industry terms appropriately.',
            'casual': 'Friendly, relaxed, and approachable. Use conversational language.',
            'witty': 'Clever, humorous, and engaging. Use wordplay and wit where appropriate.',
            'inspirational': 'Motivating, uplifting, and empowering. Use powerful, emotional language.',
            'educational': 'Informative, clear, and helpful. Break down complex topics simply.',
            'provocative': 'Bold, thought-provoking, and contrarian. Challenge conventional thinking.'
        }

        content_type_rules = {
            'post': 'Create a single, standalone post.',
            'thread': 'Create a thread of 3-5 connected posts. Number each post (1/, 2/, etc). Each post should be under 280 chars for Twitter.',
            'reply': 'Create a reply that adds value to the conversation. Be concise and relevant.'
        }

        # Build voice description from brand settings
        voice_desc = ''
        if brand_voice:
            if brand_voice.get('traits'):
                voice_desc += f"Voice traits: {', '.join(brand_voice['traits'])}. "
            if brand_voice.get('audience'):
                voice_desc += f"Target audience: {brand_voice['audience']}. "
            if brand_voice.get('avoid'):
                voice_desc += f"Words/phrases to avoid: {brand_voice['avoid']}. "
            if brand_voice.get('signatures'):
                voice_desc += f"Signature phrases to occasionally use: {brand_voice['signatures']}. "

        system = f"""You are an expert social media content creator. Your job is to create highly engaging content that drives interaction and growth.

Platform: {platform.upper()}
{platform_rules.get(platform, platform_rules['twitter'])}

Tone: {tone}
{tone_descriptions.get(tone, tone_descriptions['professional'])}

Content Type: {content_type}
{content_type_rules.get(content_type, content_type_rules['post'])}

{voice_desc}

Guidelines:
- Create content that feels authentic, not AI-generated
- Focus on providing value (entertainment, education, or inspiration)
- Use hooks that grab attention in the first line
- Include a clear call-to-action when appropriate
- Never use cringe phrases like "game-changer", "dive in", "let's unpack"
- Avoid excessive emojis unless the tone calls for it
- Make the content shareable and engaging

Return ONLY the content text, no explanations or meta-commentary."""

        return system

    def _build_user_prompt(self, prompt, topic, content_type, platform):
        if prompt:
            return prompt
        elif topic:
            if content_type == 'thread':
                return f"Create an engaging thread about: {topic}"
            else:
                return f"Create an engaging post about: {topic}"
        else:
            return f"Create an engaging {content_type} for {platform} that will drive engagement and provide value to the audience."

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
            return {'error': f'Unexpected error: {str(e)}'}
