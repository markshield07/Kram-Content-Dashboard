"""
Generate Daily Content - Creates 10+ posts with image prompts matching KRAM's style

Usage: python generate_content.py [--date YYYY-MM-DD]

Outputs:
- .tmp/daily_content/YYYY-MM-DD.json - Daily generated content
"""

import json
import random
import argparse
from pathlib import Path
from datetime import datetime, date

# Paths
BASE_DIR = Path(__file__).parent.parent
TMP_DIR = BASE_DIR / ".tmp"
ASSETS_DIR = BASE_DIR / "assets" / "mutant-ape"
OUTPUT_DIR = TMP_DIR / "daily_content"


# ============================================
# KRAM'S VOICE - Post Templates
# ============================================

GM_POSTS = [
    "GM ☀️☕️",
    "GM fam ☀️☕️",
    "Gm ☕️☀️",
    "Good Morning ☀️☕️",
    "GM fam ☕️",
    "Can I get a GM?",
    "Can I get a GM??",
    "Can I get a GM???",
    "Gm 🍌",
    "GM ☀️🙏",
]

GN_POSTS = [
    "Gn fam 🌙",
    "Goodnight fam 🌙",
    "Gn family Catch y'all tomorrow ✌️",
    "Gn fam 🌙 Catch yall tomorrow✌🏾",
    "Gn fam Catch yall tomorrow ✌🏾",
]

THEMED_POSTS = {
    "monday": [
        "GM & Happy Mutant Monday 🧪",
        "Happy Mutant Monday 🧪🧪",
        "GM fam🍌 Happy Mutant Monday 🧪",
        "🧪🧪 Happy Mutant Monday 🧪🧪",
        "Mutant Monday vibes 🧪",
    ],
    "tuesday": [
        "GM fam ☀️ Happy Taco Tuesday 🌮",
        "Happy Taco Tuesday 🌮",
        "Taco Tuesday LFG 🌮",
    ],
    "wednesday": [
        "GM ☀️☕️ Hump day!",
        "Halfway there fam ☕️",
    ],
    "thursday": [
        "GM ☀️☕️ Almost Friday!",
        "Thursday vibes ☕️",
    ],
    "friday": [
        "GM ☕️☀️ Happy Friday!",
        "Happy Friday fam! ☀️",
        "Friday vibes ☕️🔥",
        "TGIF ☀️☕️",
    ],
    "saturday": [
        "GM fam ☕️ Happy Saturday, go touch some grass",
        "Weekend vibes ☀️",
        "Saturday GM ☕️",
    ],
    "sunday": [
        "GM fam ☕️ Happy Sunday 🫡",
        "GM ☀️☕️ Happy Sunday Everyone!",
        "Happy Sunday fam ☀️",
        "Sunday reset ☕️🙏",
    ],
}

HOLIDAY_POSTS = {
    "new_year": ["Good morning ☀️☕️ Happy New Year!🎆", "Happy New Year fam! 🎆🎉"],
    "mlk_day": ["GM fam ☀️ Happy MLK Day 🙏"],
    "valentines": ["Happy Valentine's Day fam 💝", "GM ☀️☕️ Happy Valentine's Day"],
    "presidents_day": ["GM fam ☀️ Happy Presidents Day"],
    "st_patricks": ["GM fam ☀️ Happy St. Patrick's Day ☘️", "☘️ Happy St. Paddy's ☘️"],
    "easter": ["GM fam ☀️ Happy Easter 🐰"],
    "memorial_day": ["GM fam ☀️ Happy Memorial Day 🇺🇸"],
    "juneteenth": ["GM fam ☀️ Happy Juneteenth ✊🏾"],
    "july_4th": ["GM fam ☀️ Happy 4th of July 🇺🇸🎆", "Happy Independence Day 🇺🇸"],
    "labor_day": ["GM fam ☀️ Happy Labor Day"],
    "halloween": ["GM fam ☀️ Happy Halloween 🎃👻", "Spooky SZN 🎃"],
    "thanksgiving": ["GM and Happy Thanksgiving 🦃 🍁", "Happy Thanksgiving fam 🦃🍁"],
    "christmas_eve": ["GM fam ☀️☕️ Merry Christmas Eve 🎄🎁"],
    "christmas": ["GM & Merry Christmas 🎄🎁", "Merry Christmas fam 🎄🎁"],
    "new_years_eve": ["GM fam ☀️ Last day of the year!", "NYE vibes 🎆"],
}

ENGAGEMENT_HOOKS = [
    "Can I get a GM?",
    "Can I get a GM??",
    "Can I get a GM???",
    "Who's up? ☕️",
    "Roll call 🫡",
    "Apes awake? 🍌",
]

COMMUNITY_POSTS = [
    "LFG! Time to cook!",
    "Best Club on the Internet 🍌",
    "Ape together strong 🦍",
    "Building 🔨",
    "Keep building fam 🔨",
    "Stay locked in 🔒",
]


# ============================================
# IMAGE PROMPT COMPONENTS
# ============================================

ART_STYLES = [
    "hyper-realistic cinematic 3D style",
    "anime/manga style with bold linework",
    "retro pixel art 16-bit gaming aesthetic",
    "loose watercolor painting style",
    "classical oil painting portrait style",
    "cyberpunk neon aesthetic",
    "vaporwave 80s retro style",
    "comic book pop art with halftone dots",
    "low-poly geometric 3D style",
    "ukiyo-e Japanese woodblock print style",
    "graffiti street art style",
    "stained glass medieval art style",
    "claymation stop-motion style",
    "psychedelic 70s concert poster style",
    "synthwave retrofuturism style",
    "Studio Ghibli inspired illustration",
    "neon noir detective style",
    "ancient Greek pottery art style",
    "art deco 1920s glamour style",
    "impressionist painting style",
]

TEXTURES = [
    "ultra-detailed fur and skin textures",
    "smooth cel-shaded surfaces",
    "glossy metallic chrome finish",
    "rough painterly brushstrokes",
    "crisp vector-clean edges",
    "grainy vintage film texture",
    "soft pastel gradient shading",
    "hard geometric faceted surfaces",
    "organic flowing liquid forms",
    "holographic iridescent sheen",
    "matte rubber-like finish",
    "crystalline gem-like surfaces",
    "weathered aged patina texture",
    "glowing bioluminescent skin",
    "fur rendered as geometric shapes",
]

LIGHTING = [
    "dramatic rim lighting",
    "soft golden hour warm glow",
    "harsh neon pink and blue underglow",
    "moody chiaroscuro deep shadows",
    "bright flat even lighting",
    "bioluminescent ethereal glow",
    "sunset backlit silhouette effect",
    "studio three-point professional lighting",
    "warm candlelit ambiance",
    "cold blue moonlight wash",
    "RGB gaming setup lighting",
    "cinematic lens flares",
    "dramatic spotlight from above",
    "soft diffused overcast lighting",
    "harsh midday sun shadows",
]

BACKGROUNDS_MORNING = [
    "cozy coffee shop with morning light streaming through windows",
    "sunrise over city skyline with orange and pink clouds",
    "peaceful beach at dawn with gentle waves",
    "mountain peak with golden sunrise rays",
    "modern kitchen with steaming coffee cup",
    "zen garden with morning mist",
    "rooftop terrace overlooking waking city",
]

BACKGROUNDS_NIGHT = [
    "smoky midnight blue with subtle volumetric fog",
    "Tokyo neon cityscape at night with rain reflections",
    "starry night sky with northern lights",
    "moody jazz club with dim lighting",
    "city apartment with window showing night skyline",
    "moonlit forest clearing",
    "neon-lit gaming setup room",
]

BACKGROUNDS_CRYPTO = [
    "Bitcoin mining rig server room with glowing LEDs",
    "crypto trading floor with multiple screens showing charts",
    "blockchain data streams and code flowing in background",
    "futuristic Web3 metaverse environment",
    "digital vault with Bitcoin and Ethereum symbols",
    "matrix-style falling code with green on black",
    "holographic crypto exchange interface",
]

BACKGROUNDS_APE_CULTURE = [
    "yacht club party on deck at sunset",
    "jungle canopy with golden light rays filtering through",
    "exclusive club lounge with velvet ropes",
    "tropical island paradise beach",
    "banana plantation with lush greenery",
    "NFT gallery with framed apes on walls",
    "Otherside metaverse landscape",
]

BACKGROUNDS_THEMED = {
    "mutant_monday": [
        "laboratory with bubbling green serum vials",
        "toxic waste facility with glowing barrels",
        "mad scientist lab with tesla coils",
        "mutant jungle with oversized plants",
    ],
    "taco_tuesday": [
        "vibrant Mexican cantina with papel picado",
        "colorful taco truck with festive lights",
        "Day of the Dead altar with marigolds",
    ],
    "holiday": [
        "cozy living room with Christmas tree and fireplace",
        "snowy winter wonderland scene",
        "festive party with confetti",
        "New Year's Eve celebration with fireworks",
    ],
}

CAMERA_EFFECTS = [
    "shallow depth of field with bokeh",
    "wide-angle dramatic perspective",
    "subtle fisheye lens distortion",
    "tilt-shift miniature effect",
    "cinematic widescreen 2.35:1 crop",
    "portrait orientation with blurred background",
    "isometric three-quarter angle view",
    "Dutch angle for dynamic tension",
    "macro close-up on face details",
    "symmetrical centered composition",
]


# ============================================
# GENERATION LOGIC
# ============================================

def get_day_theme(target_date):
    """Get the theme for a specific date."""
    day_name = target_date.strftime("%A").lower()
    return day_name


def check_holiday(target_date):
    """Check if date is a holiday and return holiday key."""
    month_day = (target_date.month, target_date.day)

    holidays = {
        (1, 1): "new_year",
        (2, 14): "valentines",
        (3, 17): "st_patricks",
        (7, 4): "july_4th",
        (10, 31): "halloween",
        (12, 24): "christmas_eve",
        (12, 25): "christmas",
        (12, 31): "new_years_eve",
    }

    return holidays.get(month_day)


def generate_image_prompt(mood="morning", theme=None):
    """Generate a unique image prompt."""

    art_style = random.choice(ART_STYLES)
    texture = random.choice(TEXTURES)
    lighting = random.choice(LIGHTING)
    camera = random.choice(CAMERA_EFFECTS)

    # Select background based on mood/theme
    if theme and theme in BACKGROUNDS_THEMED:
        background = random.choice(BACKGROUNDS_THEMED[theme])
    elif mood == "morning":
        # Mix morning and crypto/ape backgrounds
        bg_pool = BACKGROUNDS_MORNING + BACKGROUNDS_CRYPTO[:2] + BACKGROUNDS_APE_CULTURE[:2]
        background = random.choice(bg_pool)
    elif mood == "night":
        bg_pool = BACKGROUNDS_NIGHT + BACKGROUNDS_CRYPTO[:2]
        background = random.choice(bg_pool)
    else:
        bg_pool = BACKGROUNDS_CRYPTO + BACKGROUNDS_APE_CULTURE
        background = random.choice(bg_pool)

    prompt = f"Reimagine this character in a {art_style}, {texture}, {lighting}, background: {background}, {camera}."

    return prompt


def generate_daily_posts(target_date):
    """Generate 1 post with image prompt for a given date."""

    day_theme = get_day_theme(target_date)
    holiday = check_holiday(target_date)

    # Determine which post to generate based on priority
    if holiday and holiday in HOLIDAY_POSTS:
        # Holiday takes priority
        text = random.choice(HOLIDAY_POSTS[holiday])
        post_type = "holiday"
        mood = "morning"
        theme = "holiday"
        time_slot = "morning"
    elif day_theme in THEMED_POSTS:
        # Themed day post
        text = random.choice(THEMED_POSTS[day_theme])
        post_type = f"themed_{day_theme}"
        theme_key = "mutant_monday" if day_theme == "monday" else ("taco_tuesday" if day_theme == "tuesday" else None)
        mood = "morning"
        theme = theme_key
        time_slot = "morning"
    else:
        # Default to GM post
        text = random.choice(GM_POSTS)
        post_type = "gm"
        mood = "morning"
        theme = None
        time_slot = "morning"

    # Generate the image prompt
    prompt = generate_image_prompt(mood, theme)

    post = {
        "post_text": text,
        "post_type": post_type,
        "image_prompt": prompt,
        "suggested_time": time_slot,
        "day_theme": day_theme,
        "holiday": holiday,
    }

    return [post]


def main():
    parser = argparse.ArgumentParser(description="Generate daily X content")
    parser.add_argument("--date", type=str, help="Date to generate for (YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today()

    print(f"Generating content for: {target_date.strftime('%A, %B %d, %Y')}")

    # Generate posts
    posts = generate_daily_posts(target_date)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save to file
    output_file = OUTPUT_DIR / f"{target_date.isoformat()}.json"
    output_data = {
        "date": target_date.isoformat(),
        "day_of_week": target_date.strftime("%A"),
        "generated_at": datetime.now().isoformat(),
        "post_count": len(posts),
        "posts": posts,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(posts)} posts")
    print(f"Saved to: {output_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("GENERATED CONTENT PREVIEW")
    print("=" * 60)

    for i, post in enumerate(posts, 1):
        print(f"\n{i}. [{post['post_type']}] {post['suggested_time'].upper()}")
        print(f"   Post: {post['post_text']}")
        print(f"   Prompt: {post['image_prompt'][:80]}...")


if __name__ == "__main__":
    main()
