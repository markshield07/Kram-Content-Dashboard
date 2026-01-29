# Dashboard Directive

## Goal
Provide a web-based dashboard to view and manage daily generated content.

## Inputs
- `.tmp/daily_content/*.json` - Generated daily content files

## Tools/Scripts
- `execution/dashboard.py` - Flask web server for dashboard

## Features
1. View today's generated posts with image prompts
2. Navigate between dates
3. Copy post text or image prompt to clipboard
4. Mark favorites (stored locally)
5. Visual preview of post types (GM, GN, themed, etc.)

## Process
1. Start Flask server on localhost:5000
2. Load daily content JSON files
3. Render HTML dashboard with all posts
4. Allow date navigation

## Outputs
- Web dashboard at http://localhost:5000

## Usage
```bash
cd "X Content Creator"
python execution/dashboard.py
```

Then open http://localhost:5000 in browser.
