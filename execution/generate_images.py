"""
Generate Images - Uses OpenAI's gpt-image-1 to generate variations of your Mutant Ape

Usage: python generate_images.py [--date YYYY-MM-DD] [--regenerate]

This script uses OpenAI's GPT Image model which can take your actual image
as a reference and create variations in different styles.

Requirements: pip install openai python-dotenv
"""

import os
import sys
import json
import base64
import argparse
import requests
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
from openai import OpenAI

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load environment variables
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# Paths
CONTENT_DIR = BASE_DIR / ".tmp" / "daily_content"
IMAGES_DIR = BASE_DIR / ".tmp" / "images"
REFERENCE_IMAGE = BASE_DIR / "assets" / "mutant-ape" / "mutant_ape.png"

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_image(style_prompt: str, output_path: Path, suggested_time: str = None) -> bool:
    """Generate an image using gpt-image-1 with reference image."""
    try:
        if not REFERENCE_IMAGE.exists():
            print(f"  ERROR: Reference image not found at {REFERENCE_IMAGE}")
            return False

        # Use the style prompt directly (it already starts with "Reimagine this character")
        full_prompt = style_prompt

        # Add coffee cup with "GM" text for morning posts
        if suggested_time == "morning":
            full_prompt += " Include a coffee cup with the text 'GM' on it."

        print(f"  Generating with gpt-image-1...")

        # Read the reference image
        with open(REFERENCE_IMAGE, "rb") as image_file:
            response = client.images.edit(
                model="gpt-image-1",
                image=image_file,
                prompt=full_prompt,
                size="1024x1024",
                quality="high",
            )

        # Get the image data (base64)
        image_data = response.data[0].b64_json

        # Decode and save
        image_bytes = base64.b64decode(image_data)
        with open(output_path, 'wb') as f:
            f.write(image_bytes)

        print(f"  Saved to: {output_path.name}")
        return True

    except Exception as e:
        error_msg = str(e)
        print(f"  Error: {error_msg}")

        # If gpt-image-1 fails, try with dall-e-3 as fallback
        if "model" in error_msg.lower() or "not found" in error_msg.lower():
            print(f"  Trying fallback with dall-e-3...")
            return generate_image_fallback(style_prompt, output_path)
        return False


def generate_image_fallback(style_prompt: str, output_path: Path) -> bool:
    """Fallback to DALL-E 3 if gpt-image-1 isn't available."""
    try:
        character_desc = """A whimsical cartoon ape character with:
- Leopard-print fur in golden-yellow with brown spots
- Large sparkly golden eyes
- A big friendly smile with colorful turquoise teeth
- A fluffy brown beard and mustache
- Wearing a white bunny-ear headband with tiny faces on each ear
- A small spotted kitten companion nearby
- Purple/blue gradient background

NFT art style, cartoon mascot aesthetic."""

        full_prompt = f"""{character_desc}

Style: {style_prompt}

Keep the character friendly and cartoon-like."""

        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x1024",
            quality="hd",
            n=1,
        )

        image_url = response.data[0].url
        img_response = requests.get(image_url)
        if img_response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(img_response.content)
            print(f"  Saved to: {output_path.name} (fallback)")
            return True
        return False

    except Exception as e:
        print(f"  Fallback also failed: {e}")
        return False


def process_daily_content(target_date: str, regenerate: bool = False):
    """Process daily content and generate images for each post."""

    content_file = CONTENT_DIR / f"{target_date}.json"
    if not content_file.exists():
        print(f"No content found for {target_date}")
        print(f"Run: python execution/generate_content.py --date {target_date}")
        return

    # Load content
    with open(content_file, 'r', encoding='utf-8') as f:
        content = json.load(f)

    # Create images directory for this date
    date_images_dir = IMAGES_DIR / target_date
    date_images_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating images for {target_date}")
    print(f"Reference image: {REFERENCE_IMAGE}")
    print(f"Posts to process: {len(content['posts'])}")
    print("=" * 50)

    # Process each post
    for i, post in enumerate(content['posts'], 1):
        print(f"\n[{i}/{len(content['posts'])}] {post['post_type']}: {post['post_text'][:40]}...")

        image_filename = f"post_{i:02d}.png"
        image_path = date_images_dir / image_filename

        # Skip if image already exists (unless regenerate flag)
        if image_path.exists() and not regenerate:
            print(f"  Image already exists, skipping (use --regenerate to overwrite)")
            post['image_path'] = str(image_path.relative_to(BASE_DIR))
            continue

        # Generate image (pass suggested_time for morning coffee cup addition)
        success = generate_image(post['image_prompt'], image_path, post.get('suggested_time'))

        if success:
            post['image_path'] = str(image_path.relative_to(BASE_DIR))
        else:
            post['image_path'] = None

    # Save updated content with image paths
    with open(content_file, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print(f"Done! Updated {content_file}")

    # Count successful images
    successful = sum(1 for p in content['posts'] if p.get('image_path'))
    print(f"Images generated: {successful}/{len(content['posts'])}")


def main():
    parser = argparse.ArgumentParser(description="Generate images for daily content")
    parser.add_argument("--date", type=str, help="Date to generate for (YYYY-MM-DD)", default=None)
    parser.add_argument("--regenerate", action="store_true", help="Regenerate all images even if they exist")
    args = parser.parse_args()

    if args.date:
        target_date = args.date
    else:
        target_date = date.today().isoformat()

    process_daily_content(target_date, args.regenerate)


if __name__ == "__main__":
    main()
