"""
Build Static Dashboard - Generates a standalone HTML file for viewing content

Usage: python build_dashboard.py [--date YYYY-MM-DD]

Outputs:
- dashboard.html in the project root (open directly in browser)
"""

import json
import base64
import argparse
from pathlib import Path
from datetime import date, datetime

# Paths
BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / ".tmp" / "daily_content"


def load_content(target_date):
    """Load content for a specific date."""
    content_file = CONTENT_DIR / f"{target_date}.json"
    if content_file.exists():
        with open(content_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def image_to_base64(image_path):
    """Convert image to base64 data URI for embedding in HTML."""
    try:
        full_path = BASE_DIR / image_path
        if full_path.exists():
            with open(full_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
                return f"data:image/png;base64,{data}"
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
    return None


def generate_html(content, target_date):
    """Generate static HTML dashboard with embedded images."""

    date_display = datetime.strptime(target_date, "%Y-%m-%d").strftime("%A, %B %d, %Y")

    # Calculate stats
    gm_count = sum(1 for p in content.get('posts', []) if p.get('post_type') == 'gm')
    gn_count = sum(1 for p in content.get('posts', []) if p.get('post_type') == 'gn')
    themed_count = sum(1 for p in content.get('posts', []) if p.get('post_type', '').startswith('themed'))
    images_count = sum(1 for p in content.get('posts', []) if p.get('image_path'))

    # Generate post cards
    post_cards = ""
    for i, post in enumerate(content.get('posts', []), 1):
        post_type = post.get('post_type', 'unknown')
        post_text = post.get('post_text', '')
        image_prompt = post.get('image_prompt', '')
        suggested_time = post.get('suggested_time', '')
        image_path = post.get('image_path')

        # Escape quotes for JavaScript
        post_text_js = post_text.replace("'", "\\'").replace('"', '\\"')
        image_prompt_js = image_prompt.replace("'", "\\'").replace('"', '\\"')

        # Generate image section
        if image_path:
            image_data = image_to_base64(image_path)
            if image_data:
                image_section = f'''
                <div class="image-section">
                    <img src="{image_data}" alt="Generated image for post" class="post-image" onclick="openImageModal(this.src)">
                    <button class="btn btn-download" onclick="downloadImage(this, '{image_data}', 'kram_post_{i:02d}.png')">Download Image</button>
                </div>
                '''
            else:
                image_section = '''
                <div class="image-section image-missing">
                    <div class="no-image">Image file not found</div>
                </div>
                '''
        else:
            image_section = '''
            <div class="image-section image-pending">
                <div class="no-image">Image not generated yet<br><small>Run: python execution/generate_images.py</small></div>
            </div>
            '''

        # Get image data URL for X posting
        image_data_url = image_to_base64(image_path) if image_path else ''

        post_cards += f'''
        <div class="post-card" data-post-index="{i}">
            <div class="post-header">
                <span class="post-type {post_type}">{post_type.replace('_', ' ').upper()}</span>
                <span class="post-time">{suggested_time}</span>
            </div>
            {image_section}
            <div class="post-text-container">
                <div class="post-text" id="post-text-{i}">{post_text}</div>
                <button class="btn-edit" onclick="editPost({i})" title="Edit post">&#9998;</button>
            </div>
            <div class="prompt-section">
                <div class="prompt-label">Image Prompt</div>
                <div class="prompt-text">{image_prompt}</div>
            </div>
            <div class="post-actions">
                <button class="btn btn-copy-post" onclick="copyText(this, document.getElementById('post-text-{i}').innerText)">Copy Post</button>
                <button class="btn btn-copy-prompt" onclick="copyText(this, '{image_prompt_js}')">Copy Prompt</button>
                <button class="btn btn-post-x" onclick="postToX({i}, '{image_data_url}')">Post to X</button>
            </div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KRAM Content Dashboard - {date_display}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }}

        .header {{
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}

        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #ffd700;
        }}

        .logo span {{
            color: #00ff88;
        }}

        .current-date {{
            font-size: 18px;
            color: #ffd700;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #00ff88;
        }}

        .stat-label {{
            font-size: 14px;
            color: #888;
            margin-top: 5px;
        }}

        .posts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 25px;
        }}

        .post-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }}

        .post-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(255,215,0,0.3);
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}

        .post-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .post-type {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .post-type.gm {{ background: #ff9500; color: #000; }}
        .post-type.gn {{ background: #5856d6; color: #fff; }}
        .post-type.themed_monday {{ background: #34c759; color: #000; }}
        .post-type.themed_tuesday {{ background: #ff6b6b; color: #fff; }}
        .post-type.themed_wednesday {{ background: #00bcd4; color: #000; }}
        .post-type.themed_thursday {{ background: #9c27b0; color: #fff; }}
        .post-type.themed_friday {{ background: #ffeb3b; color: #000; }}
        .post-type.themed_saturday {{ background: #4caf50; color: #fff; }}
        .post-type.themed_sunday {{ background: #ff5722; color: #fff; }}
        .post-type.engagement {{ background: #e91e63; color: #fff; }}
        .post-type.community {{ background: #2196f3; color: #fff; }}
        .post-type.holiday {{ background: #f44336; color: #fff; }}
        .post-type.gm_extra {{ background: #ff9500; color: #000; }}

        .post-time {{
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
        }}

        .image-section {{
            margin-bottom: 15px;
            border-radius: 12px;
            overflow: hidden;
        }}

        .post-image {{
            width: 100%;
            height: auto;
            display: block;
            cursor: pointer;
            transition: transform 0.2s;
        }}

        .post-image:hover {{
            transform: scale(1.02);
        }}

        .image-pending, .image-missing {{
            background: rgba(0,0,0,0.3);
            border: 2px dashed rgba(255,255,255,0.2);
            border-radius: 12px;
            padding: 40px;
            text-align: center;
        }}

        .no-image {{
            color: #666;
            font-size: 14px;
        }}

        .no-image small {{
            color: #888;
            font-family: monospace;
        }}

        .btn-download {{
            width: 100%;
            margin-top: 10px;
            background: #00ff88;
            color: #000;
        }}

        .prompt-section {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }}

        .prompt-label {{
            font-size: 11px;
            color: #ffd700;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .prompt-text {{
            font-size: 13px;
            color: #aaa;
            line-height: 1.5;
        }}

        .post-actions {{
            display: flex;
            gap: 10px;
        }}

        .btn {{
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
        }}

        .btn-copy-post {{
            background: #ffd700;
            color: #000;
        }}

        .btn-copy-prompt {{
            background: rgba(255,255,255,0.1);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
        }}

        .btn-post-x {{
            background: #000;
            color: #fff;
            border: 1px solid #fff;
        }}

        .btn-post-x:hover {{
            background: #1da1f2;
            border-color: #1da1f2;
        }}

        .post-text-container {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 20px;
        }}

        .post-text {{
            flex: 1;
            font-size: 24px;
            line-height: 1.4;
            color: #fff;
            margin-bottom: 0;
        }}

        .post-text[contenteditable="true"] {{
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 8px;
            outline: 2px solid #ffd700;
        }}

        .btn-edit {{
            background: transparent;
            border: none;
            color: #888;
            font-size: 18px;
            cursor: pointer;
            padding: 5px;
            transition: color 0.2s;
        }}

        .btn-edit:hover {{
            color: #ffd700;
        }}

        .btn-edit.editing {{
            color: #00ff88;
        }}

        .btn:hover {{
            opacity: 0.8;
            transform: scale(1.02);
        }}

        .btn.copied, .btn.posted {{
            background: #00ff88 !important;
            color: #000 !important;
        }}

        .instructions {{
            background: rgba(255,215,0,0.1);
            border: 1px solid rgba(255,215,0,0.3);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
        }}

        .instructions h3 {{
            color: #ffd700;
            margin-bottom: 10px;
        }}

        .instructions code {{
            background: rgba(0,0,0,0.3);
            padding: 2px 8px;
            border-radius: 4px;
            font-family: monospace;
        }}

        /* Image Modal */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
            cursor: pointer;
        }}

        .modal img {{
            display: block;
            max-width: 90%;
            max-height: 90%;
            margin: auto;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}

        .modal-close {{
            position: absolute;
            top: 20px;
            right: 30px;
            color: #fff;
            font-size: 40px;
            cursor: pointer;
        }}

        @media (max-width: 768px) {{
            .posts-grid {{
                grid-template-columns: 1fr;
            }}
            .header {{
                flex-direction: column;
                gap: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">KRAM <span>Content Creator</span></div>
        <div class="current-date">{date_display}</div>
    </div>

    <div class="container">
        <div class="instructions">
            <h3>Daily Content Ready</h3>
            <p><strong>{images_count}/{content.get('post_count', 0)}</strong> images generated. Click any image to view full size. Use the buttons to copy text or download images.</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{content.get('post_count', 0)}</div>
                <div class="stat-label">Total Posts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{images_count}</div>
                <div class="stat-label">Images</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{gm_count}</div>
                <div class="stat-label">GM Posts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{gn_count}</div>
                <div class="stat-label">GN Posts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{themed_count}</div>
                <div class="stat-label">Themed</div>
            </div>
        </div>

        <div class="posts-grid">
            {post_cards}
        </div>
    </div>

    <!-- Image Modal -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="modal-close">&times;</span>
        <img id="modalImage" src="" alt="Full size image">
    </div>

    <script>
        function copyText(btn, text) {{
            navigator.clipboard.writeText(text).then(() => {{
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {{
                    btn.textContent = originalText;
                    btn.classList.remove('copied');
                }}, 1500);
            }});
        }}

        function downloadImage(btn, dataUrl, filename) {{
            const link = document.createElement('a');
            link.href = dataUrl;
            link.download = filename;
            link.click();

            const originalText = btn.textContent;
            btn.textContent = 'Downloaded!';
            btn.classList.add('copied');
            setTimeout(() => {{
                btn.textContent = originalText;
                btn.classList.remove('copied');
            }}, 1500);
        }}

        function openImageModal(src) {{
            document.getElementById('imageModal').style.display = 'block';
            document.getElementById('modalImage').src = src;
        }}

        function closeModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}

        // Close modal with Escape key
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') closeModal();
        }});

        // Edit post text
        function editPost(index) {{
            const textEl = document.getElementById('post-text-' + index);
            const btnEl = textEl.parentElement.querySelector('.btn-edit');

            if (textEl.contentEditable === 'true') {{
                // Save - exit edit mode
                textEl.contentEditable = 'false';
                btnEl.classList.remove('editing');
                btnEl.innerHTML = '&#9998;';
            }} else {{
                // Enter edit mode
                textEl.contentEditable = 'true';
                textEl.focus();
                btnEl.classList.add('editing');
                btnEl.innerHTML = '&#10003;';

                // Select all text
                const range = document.createRange();
                range.selectNodeContents(textEl);
                const sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
            }}
        }}

        // Post to X (Twitter)
        function postToX(index, imageDataUrl) {{
            const textEl = document.getElementById('post-text-' + index);
            const postText = textEl.innerText;

            // For now, open X with pre-filled text (image upload requires API)
            // The image will need to be downloaded and attached manually, or use the API
            const tweetUrl = 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(postText);

            // Open in new window
            window.open(tweetUrl, '_blank', 'width=550,height=420');

            // Show feedback
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = 'Opened!';
            btn.classList.add('posted');
            setTimeout(() => {{
                btn.textContent = originalText;
                btn.classList.remove('posted');
            }}, 2000);
        }}
    </script>
</body>
</html>
'''
    return html


def main():
    parser = argparse.ArgumentParser(description="Build static dashboard HTML")
    parser.add_argument("--date", type=str, help="Date to build for (YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    if args.date:
        target_date = args.date
    else:
        target_date = date.today().isoformat()

    print(f"Building dashboard for: {target_date}")

    content = load_content(target_date)
    if not content:
        print(f"No content found for {target_date}")
        print(f"Run: python execution/generate_content.py --date {target_date}")
        return

    html = generate_html(content, target_date)

    output_file = BASE_DIR / "dashboard.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Dashboard saved to: {output_file}")
    print(f"\nOpen this file in your browser to view your content!")


if __name__ == "__main__":
    main()
