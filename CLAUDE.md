# X Content Creator

## Project Overview

A personalized X (Twitter) content generation system that analyzes the user's best-performing posts, learns their voice/style, and generates daily content with custom images featuring their Mutant Ape NFT.

## Goals

1. **Analyze X Data** - Parse exported X data to identify top-performing posts and engagement patterns
2. **Learn User Voice** - Extract writing style, tone, topics, and posting patterns
3. **Generate Daily Content** - Create 10+ post ideas per day that match the user's style
4. **Create Custom Images** - Generate images for each post featuring the user's Mutant Ape
5. **Dashboard Interface** - Web-based dashboard to view, manage, and export daily content

## Project Structure

```
X Content Creator/
├── CLAUDE.md                 # Project documentation
├── data/                     # X export data (to be added)
│   ├── posts/               # Raw post data
│   └── analytics/           # Engagement metrics
├── assets/                   # Static assets
│   └── mutant-ape/          # User's Mutant Ape image(s)
├── prompts/                  # Image generation prompts
│   └── samples/             # User-provided sample prompts
├── src/                      # Source code
│   ├── analyzer/            # Post analysis and pattern recognition
│   ├── generator/           # Content generation logic
│   ├── images/              # Image prompt generation
│   └── dashboard/           # Web dashboard
├── output/                   # Generated content
│   └── daily/               # Daily generated posts and images
└── config/                   # Configuration files
```

## Pending Items

- [ ] X data export (waiting for user)
- [ ] Mutant Ape image (waiting for user)
- [ ] Sample image prompts (waiting for user)
- [ ] Dashboard preference decision (local HTML vs web app)

## Technical Decisions

### Content Analysis
- Parse X export JSON/CSV files
- Extract engagement metrics (likes, retweets, replies, impressions)
- Identify patterns in top performers (time of day, content type, topics, length)
- Build a style profile (vocabulary, tone, hashtag usage, emoji patterns)

### Content Generation
- Use analyzed patterns to generate contextually relevant posts
- Maintain user's authentic voice and style
- Vary content types (threads, single posts, quote-style, questions)
- Include trending topic integration when relevant

### Image Generation
- Create prompts that incorporate the Mutant Ape as a central element
- Match image style to post content/mood
- Use user-provided sample prompts as style reference
- Generate descriptive prompts suitable for AI image generators (DALL-E, Midjourney, etc.)

### Dashboard
- Display daily generated content (posts + image prompts)
- Show original inspiration posts for reference
- Allow favoriting/filtering content
- Export functionality for selected posts

## User Style Profile

*(To be populated after X data analysis)*

- **Topics:** TBD
- **Tone:** TBD
- **Posting frequency:** TBD
- **Best performing content types:** TBD
- **Hashtag strategy:** TBD
- **Engagement patterns:** TBD

## Image Style Guidelines

*(To be populated after receiving sample prompts)*

- **Art style:** TBD
- **Color palette:** TBD
- **Mutant Ape integration:** TBD
- **Mood/aesthetic:** TBD

## Commands

*(To be added as development progresses)*

```bash
# Example future commands
npm run analyze      # Analyze X data
npm run generate     # Generate daily content
npm run dashboard    # Start dashboard server
```

## Notes

- All generated content should be reviewed before posting
- Image prompts are designed for external AI image generators
- System learns and improves based on which generated posts perform well

# CLAUDE.md

> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same instructions load in any AI environment.

You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs are probabilistic, whereas most business logic is deterministic and requires consistency. This system fixes that mismatch.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**
- SOPs written in Markdown, live in `directives/`
- Define the goals, inputs, tools/scripts to use, outputs, and edge cases
- Natural language instructions, like you'd give a mid-level employee

**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing.
- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings
- You're the glue between intent and execution. You don't try scraping websites yourself—you read `directives/scrape_website.md`, determine inputs/outputs, then run `execution/scrape_single_site.py`

**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts in `execution/`
- Environment variables, API tokens, etc stored in `.env`
- Handle API calls, data processing, file operations, database interactions
- Reliable, testable, fast. Use scripts instead of manual work. Commented well.

**Why this works:** If you do everything yourself, errors compound. 90% accuracy per step = 59% success over 5 steps. Push complexity into deterministic code so you focus on decision-making.

## Operating Principles

**1. Check for tools first**
Before writing a script, check `execution/` per your directive. Only create new scripts if none exist.

**2. Self-anneal when things break**
- Read error message and stack trace
- Fix the script and test it again (unless it uses paid tokens/credits—check with user first)
- Update the directive with what you learned (API limits, timing, edge cases)
- Example: hit API rate limit → investigate API → find batch endpoint → rewrite script → test → update directive

**3. Update directives as you learn**
Directives are living documents. When you discover API constraints, better approaches, common errors, or timing expectations—update the directive. Don't create or overwrite directives without asking unless explicitly told to. Directives are your instruction set and must be preserved (and improved over time).

## Self-Annealing Loop

Errors are learning opportunities. When something breaks:
1. Fix it
2. Update the tool
3. Test tool, make sure it works
4. Update directive to include new flow
5. System is now stronger

## File Organization

**Deliverables vs Intermediates:**
- **Deliverables**: Google Sheets, Google Slides, or other cloud-based outputs the user can access
- **Intermediates**: Temporary files needed during processing

**Directory structure:**
```
.
├── CLAUDE.md           # These instructions (mirrored to AGENTS.md, GEMINI.md)
├── directives/         # SOPs in Markdown (the instruction set)
├── execution/          # Python scripts (deterministic tools)
├── .tmp/               # Intermediate files (never commit, always regenerated)
├── .env                # Environment variables and API keys
├── credentials.json    # Google OAuth credentials (in .gitignore)
└── token.json          # Google OAuth token (in .gitignore)
```

**Key principle:** Local files are only for processing. Deliverables live in cloud services (Google Sheets, Slides, etc.) where the user can access them. Everything in `.tmp/` can be deleted and regenerated.

## Workflow

1. **Receive task** from user
2. **Check directives/** for relevant SOP
3. **Check execution/** for existing tools
4. **Execute** using Python scripts, not manual work
5. **Handle errors** by fixing scripts and updating directives
6. **Deliver** to cloud services, not local files

## Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.

