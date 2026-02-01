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
    """Generate static HTML dashboard with AxeOS-inspired design."""

    date_display = datetime.strptime(target_date, "%Y-%m-%d").strftime("%A, %B %d, %Y")

    # Calculate stats
    total_posts = content.get('post_count', 0)
    images_count = sum(1 for p in content.get('posts', []) if p.get('image_path'))
    gm_count = sum(1 for p in content.get('posts', []) if p.get('post_type') == 'gm')
    themed_count = sum(1 for p in content.get('posts', []) if p.get('post_type', '').startswith('themed'))

    # Generate post cards
    post_cards = ""
    for i, post in enumerate(content.get('posts', []), 1):
        post_type = post.get('post_type', 'unknown')
        post_text = post.get('post_text', '')
        image_prompt = post.get('image_prompt', '')
        suggested_time = post.get('suggested_time', '')
        image_path = post.get('image_path')

        # Escape quotes for JavaScript
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

        # Post type badge color
        type_colors = {
            'gm': '#f7931a',
            'gn': '#5856d6',
            'themed_monday': '#34c759',
            'themed_tuesday': '#ff6b6b',
            'holiday': '#f44336'
        }
        badge_color = type_colors.get(post_type, '#f7931a')

        post_cards += f'''
        <div class="post-card">
            <div class="post-header">
                <span class="post-type" style="background: {badge_color};">{post_type.replace('_', ' ').upper()}</span>
                <span class="post-time">{suggested_time.upper()}</span>
            </div>
            {image_section}
            <div class="post-text-container">
                <div class="post-text" id="post-text-{i}">{post_text}</div>
                <button class="btn-edit" onclick="editPost({i})" title="Edit post">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                </button>
            </div>
            <div class="prompt-section">
                <div class="prompt-label">IMAGE PROMPT</div>
                <div class="prompt-text">{image_prompt}</div>
            </div>
            <div class="feedback-section">
                <span class="feedback-label">Rate this content:</span>
                <div class="feedback-buttons">
                    <button class="feedback-btn thumbs-up" data-post="{i}" data-date="{target_date}" onclick="rateFeedback({i}, '{target_date}', 'up')" title="I like this">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                        </svg>
                    </button>
                    <button class="feedback-btn thumbs-down" data-post="{i}" data-date="{target_date}" onclick="rateFeedback({i}, '{target_date}', 'down')" title="Not for me">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="post-actions">
                <button class="btn btn-primary" onclick="copyText(this, document.getElementById('post-text-{i}').innerText)">Copy Post</button>
                <button class="btn btn-secondary" onclick="copyText(this, '{image_prompt_js}')">Copy Prompt</button>
                <button class="btn btn-dark" onclick="postToX({i}, '{image_data_url}')">Post to X</button>
            </div>
        </div>
        '''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KRAM Content Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --bg-primary: #0d0d0d;
            --bg-secondary: #141414;
            --bg-card: #1a1a1a;
            --bg-elevated: #222222;
            --accent: #f7931a;
            --accent-hover: #ffa940;
            --text-primary: #ffffff;
            --text-secondary: #888888;
            --text-muted: #555555;
            --border: #2a2a2a;
            --success: #00d084;
            --sidebar-width: 220px;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', sans-serif;
            background: var(--bg-primary);
            min-height: 100vh;
            color: var(--text-primary);
            display: flex;
        }}

        /* Sidebar */
        .sidebar {{
            width: var(--sidebar-width);
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            padding: 20px 0;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
        }}

        .sidebar-logo {{
            padding: 0 20px 30px 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
        }}

        .sidebar-logo h1 {{
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.5px;
        }}

        .sidebar-logo span {{
            color: var(--accent);
        }}

        .sidebar-logo .subtitle {{
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }}

        .nav-section {{
            margin-bottom: 25px;
        }}

        .nav-section-title {{
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 0 20px;
            margin-bottom: 10px;
        }}

        .nav-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 20px;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.2s;
            cursor: pointer;
            border-left: 3px solid transparent;
        }}

        .nav-item:hover {{
            background: var(--bg-card);
            color: var(--text-primary);
        }}

        .nav-item.active {{
            background: var(--bg-card);
            color: var(--accent);
            border-left-color: var(--accent);
        }}

        .nav-item svg {{
            width: 18px;
            height: 18px;
            opacity: 0.7;
        }}

        .nav-item.active svg {{
            opacity: 1;
        }}

        /* Main Content */
        .main-content {{
            margin-left: var(--sidebar-width);
            flex: 1;
            min-height: 100vh;
        }}

        /* Top Header */
        .top-header {{
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .header-left {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .menu-toggle {{
            display: none;
            background: none;
            border: none;
            color: var(--text-primary);
            cursor: pointer;
            padding: 5px;
        }}

        .current-date {{
            font-size: 14px;
            color: var(--text-secondary);
        }}

        .header-right {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .header-icon {{
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .header-icon:hover {{
            border-color: var(--accent);
        }}

        .header-icon svg {{
            width: 18px;
            height: 18px;
            color: var(--text-secondary);
        }}

        /* User Profile */
        .user-profile {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 6px 12px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .user-profile:hover {{
            border-color: var(--accent);
        }}

        .user-profile img {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
        }}

        .user-profile .username {{
            font-size: 13px;
            color: var(--text-primary);
        }}

        .login-btn {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 13px;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }}

        .login-btn:hover {{
            border-color: var(--accent);
            background: var(--bg-secondary);
        }}

        .login-btn svg {{
            width: 16px;
            height: 16px;
        }}

        .user-dropdown {{
            position: relative;
        }}

        .dropdown-menu {{
            display: none;
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            min-width: 180px;
            z-index: 100;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        .dropdown-menu.show {{
            display: block;
        }}

        .dropdown-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.2s;
        }}

        .dropdown-item:hover {{
            background: var(--bg-secondary);
            color: var(--text-primary);
        }}

        .dropdown-item svg {{
            width: 16px;
            height: 16px;
        }}

        .dropdown-divider {{
            height: 1px;
            background: var(--border);
            margin: 4px 0;
        }}

        /* Analytics Section */
        .analytics-section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}

        .analytics-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }}

        .analytics-title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .analytics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }}

        .analytics-stat {{
            text-align: center;
            padding: 12px;
            background: var(--bg-secondary);
            border-radius: 8px;
        }}

        .analytics-stat-value {{
            font-size: 24px;
            font-weight: 600;
            color: var(--accent);
        }}

        .analytics-stat-label {{
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        .top-tweets {{
            margin-top: 20px;
        }}

        .top-tweets-title {{
            font-size: 14px;
            color: var(--text-secondary);
            margin-bottom: 12px;
        }}

        .tweet-item {{
            padding: 12px;
            background: var(--bg-secondary);
            border-radius: 8px;
            margin-bottom: 8px;
        }}

        .tweet-text {{
            font-size: 13px;
            color: var(--text-primary);
            margin-bottom: 8px;
            line-height: 1.4;
        }}

        .tweet-metrics {{
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: var(--text-secondary);
        }}

        .tweet-metric {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        @media (max-width: 768px) {{
            .analytics-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            padding: 25px 30px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
        }}

        .stat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }}

        .stat-label {{
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1;
        }}

        .stat-value span {{
            font-size: 14px;
            color: var(--accent);
            font-weight: 400;
            margin-left: 8px;
        }}

        .stat-subtitle {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 6px;
        }}

        /* Content Area */
        .content-area {{
            padding: 30px;
        }}

        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }}

        .section-title {{
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        /* Posts Grid */
        .posts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 25px;
        }}

        .post-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
        }}

        .post-card:hover {{
            border-color: var(--accent);
            box-shadow: 0 0 30px rgba(247, 147, 26, 0.1);
        }}

        .post-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .post-type {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #000;
        }}

        .post-time {{
            font-size: 11px;
            color: var(--text-muted);
            letter-spacing: 0.5px;
        }}

        .image-section {{
            margin-bottom: 15px;
            border-radius: 8px;
            overflow: hidden;
            background: var(--bg-elevated);
        }}

        .post-image {{
            width: 100%;
            height: auto;
            display: block;
            cursor: pointer;
            transition: transform 0.3s ease;
        }}

        .post-image:hover {{
            transform: scale(1.02);
        }}

        .image-pending, .image-missing {{
            background: var(--bg-elevated);
            border: 1px dashed var(--border);
            border-radius: 8px;
            padding: 40px;
            text-align: center;
        }}

        .no-image {{
            color: var(--text-muted);
            font-size: 13px;
        }}

        .no-image small {{
            color: var(--text-muted);
            font-family: monospace;
            font-size: 11px;
        }}

        .btn-download {{
            width: 100%;
            margin-top: 10px;
        }}

        .post-text-container {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 15px;
        }}

        .post-text {{
            flex: 1;
            font-size: 20px;
            line-height: 1.4;
            color: var(--text-primary);
        }}

        .post-text[contenteditable="true"] {{
            background: var(--bg-elevated);
            padding: 12px;
            border-radius: 8px;
            outline: 2px solid var(--accent);
        }}

        .btn-edit {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            padding: 8px;
            border-radius: 6px;
            transition: all 0.2s;
        }}

        .btn-edit:hover {{
            background: var(--bg-elevated);
            color: var(--accent);
        }}

        .btn-edit.editing {{
            color: var(--success);
        }}

        .prompt-section {{
            background: var(--bg-elevated);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}

        .prompt-label {{
            font-size: 10px;
            color: var(--accent);
            letter-spacing: 1px;
            margin-bottom: 8px;
            font-weight: 600;
        }}

        .prompt-text {{
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.5;
        }}

        .post-actions {{
            display: flex;
            gap: 10px;
        }}

        .btn {{
            flex: 1;
            padding: 10px 15px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .btn-primary {{
            background: var(--accent);
            color: #000;
        }}

        .btn-primary:hover {{
            background: var(--accent-hover);
        }}

        .btn-secondary {{
            background: var(--bg-elevated);
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }}

        .btn-secondary:hover {{
            border-color: var(--text-muted);
            color: var(--text-primary);
        }}

        .btn-dark {{
            background: #000;
            color: var(--text-primary);
            border: 1px solid var(--border);
        }}

        .btn-dark:hover {{
            border-color: var(--accent);
            color: var(--accent);
        }}

        .btn.copied, .btn.posted {{
            background: var(--success) !important;
            color: #000 !important;
            border-color: var(--success) !important;
        }}

        /* Feedback Section */
        .feedback-section {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            margin-bottom: 15px;
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
        }}

        .feedback-label {{
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .feedback-buttons {{
            display: flex;
            gap: 8px;
        }}

        .feedback-btn {{
            width: 40px;
            height: 40px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--bg-elevated);
            color: var(--text-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }}

        .feedback-btn:hover {{
            border-color: var(--text-secondary);
            color: var(--text-primary);
        }}

        .feedback-btn.active.thumbs-up {{
            background: rgba(0, 208, 132, 0.2);
            border-color: var(--success);
            color: var(--success);
        }}

        .feedback-btn.active.thumbs-down {{
            background: rgba(255, 82, 82, 0.2);
            border-color: #ff5252;
            color: #ff5252;
        }}

        .feedback-btn svg {{
            pointer-events: none;
        }}

        /* Filter Toggle */
        .filter-toggle {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .toggle-label {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        .toggle-switch {{
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
        }}

        .toggle-switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}

        .toggle-slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 24px;
            transition: 0.3s;
        }}

        .toggle-slider:before {{
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 2px;
            bottom: 2px;
            background-color: var(--text-muted);
            border-radius: 50%;
            transition: 0.3s;
        }}

        .toggle-switch input:checked + .toggle-slider {{
            background-color: var(--accent);
            border-color: var(--accent);
        }}

        .toggle-switch input:checked + .toggle-slider:before {{
            transform: translateX(20px);
            background-color: #000;
        }}

        .post-card.hidden {{
            display: none;
        }}

        .post-card.fade-out {{
            opacity: 0;
            transform: scale(0.95);
            transition: all 0.3s ease;
        }}

        /* Modal */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.95);
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
            border-radius: 8px;
        }}

        .modal-close {{
            position: absolute;
            top: 20px;
            right: 30px;
            color: #fff;
            font-size: 32px;
            cursor: pointer;
            opacity: 0.7;
            transition: opacity 0.2s;
        }}

        .modal-close:hover {{
            opacity: 1;
        }}

        /* Mobile Responsive */
        @media (max-width: 1024px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        @media (max-width: 768px) {{
            .sidebar {{
                transform: translateX(-100%);
                transition: transform 0.3s ease;
                z-index: 200;
            }}

            .sidebar.open {{
                transform: translateX(0);
            }}

            .main-content {{
                margin-left: 0;
            }}

            .menu-toggle {{
                display: block;
            }}

            .stats-grid {{
                grid-template-columns: 1fr 1fr;
                padding: 15px;
                gap: 10px;
            }}

            .stat-card {{
                padding: 15px;
            }}

            .stat-value {{
                font-size: 24px;
            }}

            .posts-grid {{
                grid-template-columns: 1fr;
            }}

            .content-area {{
                padding: 15px;
            }}

            .top-header {{
                padding: 15px;
            }}
        }}

        /* Overlay for mobile menu */
        .sidebar-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 150;
        }}

        .sidebar-overlay.show {{
            display: block;
        }}
    </style>
</head>
<body>
    <!-- Sidebar -->
    <nav class="sidebar" id="sidebar">
        <div class="sidebar-logo">
            <h1>KRAM<span>.</span></h1>
            <div class="subtitle">Content Generator</div>
        </div>

        <div class="nav-section">
            <div class="nav-item active">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="7" height="7"></rect>
                    <rect x="14" y="3" width="7" height="7"></rect>
                    <rect x="14" y="14" width="7" height="7"></rect>
                    <rect x="3" y="14" width="7" height="7"></rect>
                </svg>
                Dashboard
            </div>
            <div class="nav-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                History
            </div>
            <div class="nav-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                Schedule
            </div>
        </div>

        <div class="nav-section">
            <div class="nav-section-title">Settings</div>
            <div class="nav-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
                Settings
            </div>
            <div class="nav-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                </svg>
                Notifications
            </div>
        </div>
    </nav>

    <!-- Overlay for mobile -->
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

    <!-- Main Content -->
    <main class="main-content">
        <!-- Top Header -->
        <header class="top-header">
            <div class="header-left">
                <button class="menu-toggle" onclick="toggleSidebar()">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="3" y1="12" x2="21" y2="12"></line>
                        <line x1="3" y1="6" x2="21" y2="6"></line>
                        <line x1="3" y1="18" x2="21" y2="18"></line>
                    </svg>
                </button>
                <span class="current-date">{date_display}</span>
            </div>
            <div class="header-right">
                <div class="header-icon" onclick="location.reload()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="23 4 23 10 17 10"></polyline>
                        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                    </svg>
                </div>

                <!-- User Profile / Login -->
                <div class="user-dropdown" id="userDropdown">
                    <!-- Login Button (shown when not logged in) -->
                    <a href="/login" class="login-btn" id="loginBtn">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                        </svg>
                        Sign in
                    </a>

                    <!-- User Profile (shown when logged in) -->
                    <div class="user-profile" id="userProfile" style="display: none;" onclick="toggleDropdown()">
                        <img id="userAvatar" src="" alt="Profile">
                        <span class="username" id="userName">@username</span>
                    </div>

                    <!-- Dropdown Menu -->
                    <div class="dropdown-menu" id="dropdownMenu">
                        <a href="/api/profile" class="dropdown-item">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                            View Profile
                        </a>
                        <a href="#" class="dropdown-item" onclick="loadAnalytics()">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 20V10"></path>
                                <path d="M12 20V4"></path>
                                <path d="M6 20v-6"></path>
                            </svg>
                            Refresh Analytics
                        </a>
                        <div class="dropdown-divider"></div>
                        <a href="/api/logout" class="dropdown-item">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                                <polyline points="16 17 21 12 16 7"></polyline>
                                <line x1="21" y1="12" x2="9" y2="12"></line>
                            </svg>
                            Logout
                        </a>
                    </div>
                </div>
            </div>
        </header>

        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Posts</div>
                <div class="stat-value">{total_posts}<span>today</span></div>
                <div class="stat-subtitle">Content generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Images</div>
                <div class="stat-value">{images_count}<span>ready</span></div>
                <div class="stat-subtitle">Generated with AI</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Liked</div>
                <div class="stat-value"><span id="stat-liked" style="color: var(--success); font-size: 32px; margin: 0;">0</span></div>
                <div class="stat-subtitle">Posts you liked</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Disliked</div>
                <div class="stat-value"><span id="stat-disliked" style="color: #ff5252; font-size: 32px; margin: 0;">0</span></div>
                <div class="stat-subtitle">Needs improvement</div>
            </div>
        </div>

        <!-- Analytics Section (shown when logged in) -->
        <div class="content-area" id="analyticsContainer" style="display: none;">
            <div class="analytics-section">
                <div class="analytics-header">
                    <span class="analytics-title">Your X Analytics</span>
                    <button class="btn btn-copy" onclick="loadAnalytics()" style="padding: 6px 12px; font-size: 12px;">Refresh</button>
                </div>
                <div class="analytics-grid">
                    <div class="analytics-stat">
                        <div class="analytics-stat-value" id="totalLikes">-</div>
                        <div class="analytics-stat-label">Total Likes</div>
                    </div>
                    <div class="analytics-stat">
                        <div class="analytics-stat-value" id="totalRetweets">-</div>
                        <div class="analytics-stat-label">Total Retweets</div>
                    </div>
                    <div class="analytics-stat">
                        <div class="analytics-stat-value" id="totalReplies">-</div>
                        <div class="analytics-stat-label">Total Replies</div>
                    </div>
                    <div class="analytics-stat">
                        <div class="analytics-stat-value" id="avgLikes">-</div>
                        <div class="analytics-stat-label">Avg Likes/Post</div>
                    </div>
                </div>
                <div class="top-tweets">
                    <div class="top-tweets-title">Your Top Performing Tweets</div>
                    <div id="topTweetsList">
                        <div class="tweet-item" style="color: var(--text-secondary); text-align: center;">
                            Click "Refresh" to load your analytics
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Content Area -->
        <div class="content-area">
            <div class="section-header">
                <h2 class="section-title">Today's Content</h2>
                <div class="filter-toggle">
                    <label class="toggle-switch">
                        <input type="checkbox" id="showDisliked" onchange="toggleDislikedFilter()">
                        <span class="toggle-slider"></span>
                    </label>
                    <span class="toggle-label">Show disliked (<span id="hidden-count">0</span> hidden)</span>
                </div>
            </div>

            <div class="posts-grid">
                {post_cards}
            </div>
        </div>
    </main>

    <!-- Image Modal -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="modal-close">&times;</span>
        <img id="modalImage" src="" alt="Full size image">
    </div>

    <script>
        // ===== AUTH & USER MANAGEMENT =====
        function getCookie(name) {{
            const value = `; ${{document.cookie}}`;
            const parts = value.split(`; ${{name}}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }}

        function checkAuthState() {{
            const userCookie = getCookie('x_user');
            const loginBtn = document.getElementById('loginBtn');
            const userProfile = document.getElementById('userProfile');
            const analyticsContainer = document.getElementById('analyticsContainer');

            if (userCookie) {{
                try {{
                    const userData = JSON.parse(atob(userCookie));
                    loginBtn.style.display = 'none';
                    userProfile.style.display = 'flex';
                    analyticsContainer.style.display = 'block';

                    document.getElementById('userAvatar').src = userData.profile_image_url || '/api/placeholder/28/28';
                    document.getElementById('userName').textContent = '@' + userData.username;

                    // Auto-load analytics on login
                    loadAnalytics();
                }} catch (e) {{
                    console.error('Error parsing user data:', e);
                }}
            }} else {{
                loginBtn.style.display = 'flex';
                userProfile.style.display = 'none';
                analyticsContainer.style.display = 'none';
            }}
        }}

        function toggleDropdown() {{
            document.getElementById('dropdownMenu').classList.toggle('show');
        }}

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {{
            const dropdown = document.getElementById('userDropdown');
            if (!dropdown.contains(e.target)) {{
                document.getElementById('dropdownMenu').classList.remove('show');
            }}
        }});

        // ===== ANALYTICS =====
        async function loadAnalytics() {{
            const topTweetsList = document.getElementById('topTweetsList');
            topTweetsList.innerHTML = '<div class="tweet-item" style="color: var(--text-secondary); text-align: center;">Loading analytics...</div>';

            try {{
                const response = await fetch('/api/tweets?max_results=50');

                if (response.status === 401) {{
                    topTweetsList.innerHTML = '<div class="tweet-item" style="color: var(--text-secondary); text-align: center;">Please sign in to view analytics</div>';
                    return;
                }}

                if (!response.ok) {{
                    throw new Error('Failed to load analytics');
                }}

                const data = await response.json();

                // Update summary stats
                document.getElementById('totalLikes').textContent = data.summary.total_likes.toLocaleString();
                document.getElementById('totalRetweets').textContent = data.summary.total_retweets.toLocaleString();
                document.getElementById('totalReplies').textContent = data.summary.total_replies.toLocaleString();
                document.getElementById('avgLikes').textContent = data.summary.avg_likes.toFixed(1);

                // Show top 5 tweets
                const topTweets = data.tweets.slice(0, 5);
                if (topTweets.length === 0) {{
                    topTweetsList.innerHTML = '<div class="tweet-item" style="color: var(--text-secondary); text-align: center;">No tweets found</div>';
                    return;
                }}

                topTweetsList.innerHTML = topTweets.map(tweet => `
                    <div class="tweet-item">
                        <div class="tweet-text">${{tweet.text.substring(0, 150)}}${{tweet.text.length > 150 ? '...' : ''}}</div>
                        <div class="tweet-metrics">
                            <span class="tweet-metric">&#10084; ${{tweet.metrics.like_count}}</span>
                            <span class="tweet-metric">&#128257; ${{tweet.metrics.retweet_count}}</span>
                            <span class="tweet-metric">&#128172; ${{tweet.metrics.reply_count}}</span>
                        </div>
                    </div>
                `).join('');

            }} catch (error) {{
                console.error('Analytics error:', error);
                topTweetsList.innerHTML = '<div class="tweet-item" style="color: var(--error); text-align: center;">Failed to load analytics. Please try again.</div>';
            }}
        }}

        // Initialize auth state on page load
        document.addEventListener('DOMContentLoaded', checkAuthState);

        // ===== SIDEBAR =====
        function toggleSidebar() {{
            document.getElementById('sidebar').classList.toggle('open');
            document.getElementById('sidebarOverlay').classList.toggle('show');
        }}

        function copyText(btn, text) {{
            navigator.clipboard.writeText(text).then(() => {{
                const originalText = btn.textContent;
                btn.textContent = 'COPIED!';
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
            btn.textContent = 'DOWNLOADED!';
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

        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') closeModal();
        }});

        function editPost(index) {{
            const textEl = document.getElementById('post-text-' + index);
            const btnEl = textEl.parentElement.querySelector('.btn-edit');

            if (textEl.contentEditable === 'true') {{
                textEl.contentEditable = 'false';
                btnEl.classList.remove('editing');
            }} else {{
                textEl.contentEditable = 'true';
                textEl.focus();
                btnEl.classList.add('editing');

                const range = document.createRange();
                range.selectNodeContents(textEl);
                const sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
            }}
        }}

        function postToX(index, imageDataUrl) {{
            const textEl = document.getElementById('post-text-' + index);
            const postText = textEl.innerText;

            const tweetUrl = 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(postText);
            window.open(tweetUrl, '_blank', 'width=550,height=420');

            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = 'OPENED!';
            btn.classList.add('posted');
            setTimeout(() => {{
                btn.textContent = originalText;
                btn.classList.remove('posted');
            }}, 2000);
        }}

        // Feedback system
        function getFeedbackData() {{
            const data = localStorage.getItem('kram_feedback');
            return data ? JSON.parse(data) : {{}};
        }}

        function saveFeedbackData(data) {{
            localStorage.setItem('kram_feedback', JSON.stringify(data));
        }}

        function rateFeedback(postIndex, date, rating) {{
            const feedbackData = getFeedbackData();
            const key = date + '_' + postIndex;

            // Get current rating for this post
            const currentRating = feedbackData[key]?.rating;

            // Get post card for animation
            const postTextEl = document.getElementById('post-text-' + postIndex);
            const postCard = postTextEl.closest('.post-card');

            // Toggle off if clicking same rating, otherwise set new rating
            if (currentRating === rating) {{
                delete feedbackData[key];
            }} else {{
                // Get post details for learning
                const postType = postCard.querySelector('.post-type').textContent;
                const promptText = postCard.querySelector('.prompt-text').textContent;

                feedbackData[key] = {{
                    date: date,
                    postIndex: postIndex,
                    rating: rating,
                    postType: postType,
                    postText: postTextEl.innerText,
                    imagePrompt: promptText,
                    timestamp: new Date().toISOString()
                }};

                // If disliked and filter is on, animate and hide
                if (rating === 'down' && !document.getElementById('showDisliked').checked) {{
                    postCard.classList.add('fade-out');
                    setTimeout(() => {{
                        postCard.classList.add('hidden');
                        postCard.classList.remove('fade-out');
                        updateHiddenCount();
                    }}, 300);
                }}
            }}

            saveFeedbackData(feedbackData);
            updateFeedbackUI(postIndex, date);
            updateFeedbackStats();
            updateHiddenCount();
        }}

        function updateFeedbackUI(postIndex, date) {{
            const feedbackData = getFeedbackData();
            const key = date + '_' + postIndex;
            const rating = feedbackData[key]?.rating;

            // Find the buttons for this post
            const upBtn = document.querySelector(`.thumbs-up[data-post="${{postIndex}}"][data-date="${{date}}"]`);
            const downBtn = document.querySelector(`.thumbs-down[data-post="${{postIndex}}"][data-date="${{date}}"]`);

            if (upBtn) {{
                upBtn.classList.toggle('active', rating === 'up');
            }}
            if (downBtn) {{
                downBtn.classList.toggle('active', rating === 'down');
            }}
        }}

        function updateFeedbackStats() {{
            const feedbackData = getFeedbackData();
            const entries = Object.values(feedbackData);
            const liked = entries.filter(e => e.rating === 'up').length;
            const disliked = entries.filter(e => e.rating === 'down').length;

            // Update stats if elements exist
            const likedEl = document.getElementById('stat-liked');
            const dislikedEl = document.getElementById('stat-disliked');
            if (likedEl) likedEl.textContent = liked;
            if (dislikedEl) dislikedEl.textContent = disliked;
        }}

        // Filter disliked posts
        function toggleDislikedFilter() {{
            const showDisliked = document.getElementById('showDisliked').checked;
            const feedbackData = getFeedbackData();

            document.querySelectorAll('.post-card').forEach(card => {{
                const postIndex = card.querySelector('.thumbs-up')?.dataset.post;
                const date = card.querySelector('.thumbs-up')?.dataset.date;
                const key = date + '_' + postIndex;
                const rating = feedbackData[key]?.rating;

                if (rating === 'down' && !showDisliked) {{
                    card.classList.add('hidden');
                }} else {{
                    card.classList.remove('hidden');
                }}
            }});

            updateHiddenCount();
        }}

        function updateHiddenCount() {{
            const feedbackData = getFeedbackData();
            let hiddenCount = 0;

            document.querySelectorAll('.post-card').forEach(card => {{
                const postIndex = card.querySelector('.thumbs-up')?.dataset.post;
                const date = card.querySelector('.thumbs-up')?.dataset.date;
                const key = date + '_' + postIndex;
                const rating = feedbackData[key]?.rating;

                if (rating === 'down') {{
                    hiddenCount++;
                }}
            }});

            const countEl = document.getElementById('hidden-count');
            if (countEl) countEl.textContent = hiddenCount;
        }}

        // Initialize feedback UI on page load
        document.addEventListener('DOMContentLoaded', function() {{
            const feedbackData = getFeedbackData();
            Object.keys(feedbackData).forEach(key => {{
                const [date, postIndex] = key.split('_');
                updateFeedbackUI(parseInt(postIndex), date);
            }});
            updateFeedbackStats();

            // Hide disliked posts on load (filter is off by default)
            toggleDislikedFilter();
        }});

        // Export feedback data (for analysis)
        function exportFeedback() {{
            const data = getFeedbackData();
            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'kram_feedback_' + new Date().toISOString().split('T')[0] + '.json';
            a.click();
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
