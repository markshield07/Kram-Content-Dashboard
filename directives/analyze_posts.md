# Analyze X Posts Directive

## Goal
Parse the X analytics export and identify top-performing posts to build a style profile for content generation.

## Inputs
- `data/account_analytics_content_*.csv` - X analytics export

## Tools/Scripts
- `execution/analyze_posts.py` - Parses CSV, calculates engagement scores, identifies top performers

## Process
1. Load CSV with post data
2. Calculate engagement score per post: `(likes * 2) + (reposts * 3) + replies + bookmarks + (impressions * 0.001)`
3. Filter out low-effort reply posts (starting with @username and < 50 chars)
4. Identify top 50 posts by engagement score
5. Extract patterns:
   - Common topics/themes
   - Post length distribution
   - Time of day patterns
   - Content types (GM posts, commentary, original thoughts)
   - Emoji usage
   - Hashtag usage
6. Output analysis to `.tmp/post_analysis.json`

## Outputs
- `.tmp/post_analysis.json` - Full analysis with top posts and style profile
- `.tmp/top_posts.json` - Top 50 posts for content generation reference

## Edge Cases
- Handle HTML entities in post text (&amp; etc.)
- Skip posts with 0 impressions (likely deleted)
- Handle date parsing variations

## Learnings
- (Add learnings as they emerge)
