"""
Dashboard - Web interface for viewing and managing daily generated content

Usage: python dashboard.py
Then open http://localhost:5000 in your browser

Requirements: pip install flask
"""

import json
from pathlib import Path
from datetime import date, datetime, timedelta
from flask import Flask, render_template_string, request, jsonify

# Paths
BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / ".tmp" / "daily_content"

app = Flask(__name__)

# HTML Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KRAM Content Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }

        .header {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #ffd700;
        }

        .logo span {
            color: #00ff88;
        }

        .date-nav {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .date-nav button {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: #fff;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .date-nav button:hover {
            background: rgba(255,255,255,0.2);
        }

        .current-date {
            font-size: 18px;
            color: #ffd700;
            min-width: 200px;
            text-align: center;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #00ff88;
        }

        .stat-label {
            font-size: 14px;
            color: #888;
            margin-top: 5px;
        }

        .posts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 25px;
        }

        .post-card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }

        .post-card:hover {
            transform: translateY(-5px);
            border-color: rgba(255,215,0,0.3);
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }

        .post-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .post-type {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .post-type.gm { background: #ff9500; color: #000; }
        .post-type.gn { background: #5856d6; color: #fff; }
        .post-type.themed_monday { background: #34c759; color: #000; }
        .post-type.themed_tuesday { background: #ff6b6b; color: #fff; }
        .post-type.themed_wednesday { background: #00bcd4; color: #000; }
        .post-type.themed_thursday { background: #9c27b0; color: #fff; }
        .post-type.themed_friday { background: #ffeb3b; color: #000; }
        .post-type.themed_saturday { background: #4caf50; color: #fff; }
        .post-type.themed_sunday { background: #ff5722; color: #fff; }
        .post-type.engagement { background: #e91e63; color: #fff; }
        .post-type.community { background: #2196f3; color: #fff; }
        .post-type.holiday { background: #f44336; color: #fff; }

        .post-time {
            color: #888;
            font-size: 12px;
        }

        .post-text {
            font-size: 24px;
            margin-bottom: 20px;
            line-height: 1.4;
            color: #fff;
        }

        .prompt-section {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }

        .prompt-label {
            font-size: 11px;
            color: #ffd700;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .prompt-text {
            font-size: 13px;
            color: #aaa;
            line-height: 1.5;
        }

        .post-actions {
            display: flex;
            gap: 10px;
        }

        .btn {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
        }

        .btn-copy-post {
            background: #ffd700;
            color: #000;
        }

        .btn-copy-prompt {
            background: rgba(255,255,255,0.1);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
        }

        .btn:hover {
            opacity: 0.8;
            transform: scale(1.02);
        }

        .btn.copied {
            background: #00ff88 !important;
            color: #000 !important;
        }

        .no-content {
            text-align: center;
            padding: 60px;
            color: #888;
        }

        .no-content h2 {
            margin-bottom: 15px;
            color: #ffd700;
        }

        .generate-btn {
            background: linear-gradient(135deg, #ffd700, #ff9500);
            color: #000;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 20px;
        }

        @media (max-width: 768px) {
            .posts-grid {
                grid-template-columns: 1fr;
            }
            .header {
                flex-direction: column;
                gap: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">KRAM <span>Content Creator</span></div>
        <div class="date-nav">
            <button onclick="changeDate(-1)">← Previous</button>
            <div class="current-date" id="currentDate">{{ date_display }}</div>
            <button onclick="changeDate(1)">Next →</button>
        </div>
    </div>

    <div class="container">
        {% if content %}
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ content.post_count }}</div>
                <div class="stat-label">Total Posts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ gm_count }}</div>
                <div class="stat-label">GM Posts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ gn_count }}</div>
                <div class="stat-label">GN Posts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ themed_count }}</div>
                <div class="stat-label">Themed</div>
            </div>
        </div>

        <div class="posts-grid">
            {% for post in content.posts %}
            <div class="post-card">
                <div class="post-header">
                    <span class="post-type {{ post.post_type }}">{{ post.post_type.replace('_', ' ') }}</span>
                    <span class="post-time">{{ post.suggested_time }}</span>
                </div>
                <div class="post-text">{{ post.post_text }}</div>
                <div class="prompt-section">
                    <div class="prompt-label">Image Prompt</div>
                    <div class="prompt-text">{{ post.image_prompt }}</div>
                </div>
                <div class="post-actions">
                    <button class="btn btn-copy-post" onclick="copyText(this, '{{ post.post_text | e }}')">Copy Post</button>
                    <button class="btn btn-copy-prompt" onclick="copyText(this, `{{ post.image_prompt | e }}`)">Copy Prompt</button>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="no-content">
            <h2>No Content for {{ date_display }}</h2>
            <p>Generate content for this date by running:</p>
            <code style="display:block;margin:20px 0;padding:15px;background:rgba(0,0,0,0.3);border-radius:8px;">
                python execution/generate_content.py --date {{ current_date }}
            </code>
        </div>
        {% endif %}
    </div>

    <script>
        let currentDate = '{{ current_date }}';

        function changeDate(delta) {
            const d = new Date(currentDate);
            d.setDate(d.getDate() + delta);
            const newDate = d.toISOString().split('T')[0];
            window.location.href = '/?date=' + newDate;
        }

        function copyText(btn, text) {
            navigator.clipboard.writeText(text).then(() => {
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('copied');
                }, 1500);
            });
        }
    </script>
</body>
</html>
"""


def load_content(target_date):
    """Load content for a specific date."""
    content_file = CONTENT_DIR / f"{target_date}.json"
    if content_file.exists():
        with open(content_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


@app.route('/')
def dashboard():
    """Main dashboard view."""
    # Get date from query param or use today
    date_str = request.args.get('date', date.today().isoformat())

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        target_date = date.today()

    # Load content
    content = load_content(target_date.isoformat())

    # Calculate stats
    gm_count = 0
    gn_count = 0
    themed_count = 0

    if content:
        for post in content.get('posts', []):
            ptype = post.get('post_type', '')
            if ptype == 'gm':
                gm_count += 1
            elif ptype == 'gn':
                gn_count += 1
            elif ptype.startswith('themed'):
                themed_count += 1

    return render_template_string(
        DASHBOARD_HTML,
        content=content,
        current_date=target_date.isoformat(),
        date_display=target_date.strftime("%A, %B %d, %Y"),
        gm_count=gm_count,
        gn_count=gn_count,
        themed_count=themed_count,
    )


if __name__ == '__main__':
    print("=" * 50)
    print("KRAM Content Dashboard")
    print("=" * 50)
    print(f"Content directory: {CONTENT_DIR}")
    print(f"\nStarting server at: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
