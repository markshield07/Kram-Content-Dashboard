"""
Daily Run - Generates content and image for today, then rebuilds dashboard

This script is designed to be run automatically via Windows Task Scheduler.
Automatically commits and pushes to GitHub for GitHub Pages deployment.
"""

import subprocess
import sys
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).parent.parent
PYTHON = sys.executable


def run_script(script_name, *args):
    """Run a Python script and return success status."""
    script_path = BASE_DIR / "execution" / script_name
    cmd = [PYTHON, str(script_path)] + list(args)
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    return result.returncode == 0


def run_git(*args):
    """Run a git command and return success status."""
    cmd = ["git"] + list(args)
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    return result.returncode == 0


def push_to_github(today):
    """Commit and push changes to GitHub."""
    print("\n[4/4] Pushing to GitHub...")

    # Add all changes
    run_git("add", "dashboard.html", ".tmp/images/")

    # Commit with today's date
    run_git("commit", "-m", f"Daily content update - {today}")

    # Push to main branch
    if run_git("push", "origin", "main"):
        print("Successfully pushed to GitHub!")
        return True
    else:
        print("WARNING: Push to GitHub failed (may need to set up remote)")
        return False


def main():
    today = date.today().isoformat()
    print(f"=" * 50)
    print(f"Daily Content Generation - {today}")
    print(f"=" * 50)

    # Step 1: Generate content
    print("\n[1/4] Generating content...")
    if not run_script("generate_content.py"):
        print("ERROR: Content generation failed")
        return 1

    # Step 2: Generate image
    print("\n[2/4] Generating image...")
    if not run_script("generate_images.py"):
        print("ERROR: Image generation failed")
        return 1

    # Step 3: Build dashboard
    print("\n[3/4] Building dashboard...")
    if not run_script("build_dashboard.py"):
        print("ERROR: Dashboard build failed")
        return 1

    # Step 4: Push to GitHub
    push_to_github(today)

    print("\n" + "=" * 50)
    print("Daily generation complete!")
    print(f"Dashboard: {BASE_DIR / 'dashboard.html'}")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
