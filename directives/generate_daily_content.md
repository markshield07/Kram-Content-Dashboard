# Generate Daily Content Directive

## Goal
Generate 10+ daily post ideas with matching image prompts that match KRAM's voice and style.

## Inputs
- `.tmp/top_posts.json` - Top performing original posts for style reference
- `.tmp/post_analysis.json` - Full style profile
- `assets/mutant-ape/character_description.json` - Mutant Ape traits
- `assets/mutant-ape/prompt_template.md` - Image prompt components

## Tools/Scripts
- `execution/generate_content.py` - Generates daily posts and image prompts

## Process
1. Load style profile and top posts
2. Determine today's themed content opportunities:
   - Monday = Mutant Monday
   - Tuesday = Taco Tuesday
   - Friday = Happy Friday
   - Saturday/Sunday = Weekend vibes
   - Check for holidays/special days
3. Generate 10+ post ideas in categories:
   - 3-4 GM/GN posts (signature style)
   - 2-3 Engagement hooks ("Can I get a GM?")
   - 2-3 Themed day posts
   - 2-3 Community/culture posts
4. For each post, generate a matching image prompt using the template
5. Vary art styles, backgrounds, and moods across the 10 prompts
6. Output to daily folder with timestamp

## Output Format
Each generated item includes:
```json
{
  "post_text": "GM fam ☀️☕️ Happy Mutant Monday 🧪",
  "post_type": "gm_themed",
  "image_prompt": "Reimagine this character in a [style]...",
  "suggested_time": "morning",
  "engagement_hook": null
}
```

## KRAM's Voice Rules
- Keep posts SHORT (under 50 chars preferred, max 100)
- Use signature emojis: ☀️☕️ (morning), 🧪 (mutant), 🍌 (ape), 🌙 (night), 🫡 (salute)
- Casual, never preachy
- Community-first energy
- No hashtags (he doesn't use them)
- Authentic crypto/NFT culture references

## Image Prompt Rules
- Always reference the Mutant Ape character
- Vary art styles across the batch (no repeats)
- Match mood to post content (morning = warm lighting, night = moody)
- Include at least 2 crypto/blockchain themed backgrounds per batch
- Always end with a camera/depth effect

## Outputs
- `.tmp/daily_content/YYYY-MM-DD.json` - Daily generated content
- Dashboard reads from this folder

## Edge Cases
- If it's a major holiday, prioritize holiday-themed content
- Weekend posts can be more relaxed/casual
- Avoid generating duplicate post texts
