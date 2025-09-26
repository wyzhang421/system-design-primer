# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

The System Design Primer is an educational repository containing resources for learning system design and preparing for technical interviews. It consists of:

- **Main content**: Comprehensive system design guide in README.md (109KB+ markdown file)
- **Solutions**: Practical implementations of system design problems in `./solutions/`
- **Resources**: Anki flashcards and additional learning materials in `./resources/`
- **Translations**: Multi-language versions (Japanese, Chinese Simplified/Traditional)

## Architecture and Structure

### Core Components

1. **Documentation Structure**:
   - Main guide: `README.md` - comprehensive system design primer
   - Translations: `README-{language}.md` files
   - Contributing guidelines: `CONTRIBUTING.md`

2. **Solutions Directory** (`./solutions/`):
   - `system_design/`: Implementation examples for scalable systems
     - Each subdirectory contains a specific system design problem
     - Includes both README.md explanations and Python implementation files
     - Examples: twitter, pastebin, web_crawler, query_cache, mint, etc.
   - `object_oriented_design/`: OOP design pattern examples

3. **Resources Directory** (`./resources/`):
   - `flash_cards/`: Anki flashcard decks for spaced repetition learning

### System Design Solutions Pattern

Each solution follows a consistent structure:
- `README.md`: Problem description, requirements, and detailed solution walkthrough
- `README-zh-Hans.md`: Chinese translation
- Python implementation files (e.g., `*_snippets.py`, `*_mapreduce.py`)
- `__init__.py`: Python package initialization

### Key Implementation Examples

- **Query Cache**: LRU cache implementation with linked list (`query_cache_snippets.py`)
- **Web Crawler**: Distributed crawling system with MapReduce
- **Twitter-like Service**: Scalable social media backend design
- **Pastebin**: URL shortening and paste sharing service

## Development Commands

### Building Documentation
```bash
# Generate EPUB versions of all README files
./generate-epub.sh
```
This script requires `pandoc` and creates EPUB files for the main guide and translations.

### No Traditional Build Process
This is primarily a documentation and educational repository. There are no compile steps, test suites, or traditional development workflows. The Python files in solutions are code snippets for illustration rather than runnable applications.

## Working with Content

### File Reading Strategy
- The main README.md is very large (30K+ tokens). Use offset/limit parameters or search tools when reading
- Each solution directory is self-contained with its own README
- Code examples are in Python but focus on algorithmic concepts rather than production implementations

### Translation Maintenance
- English is the source of truth
- All content changes should be made to English first, then translated
- Each translation has a dedicated maintainer
- Use language prefixes in PRs (e.g., "zh: Fix typo")

### Contributing Pattern
- Fork-based workflow via GitHub
- Submit issues for bugs or content requests
- Pull requests should target specific improvements
- Content under development is marked as such in the main guide