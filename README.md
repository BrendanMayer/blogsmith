# Blogsmith

A local CLI tool for creating and publishing Jekyll blog posts to a GitHub Pages site.

Blogsmith creates Markdown drafts, adds Jekyll front matter, publishes posts into `_posts`,
and uses local Git authentication to commit and push changes.

## Features

- Create Jekyll Markdown drafts
- Generate front matter
- List drafts and posts
- Edit drafts/posts in your editor
- Publish drafts into `_posts`
- Commit and push posts with local Git auth

## Installation

```bash
git clone git@github.com:BrendanMayer/blogsmith.git
cd blogsmith
python -m venv .venv
source .venv/bin/activate
pip install -e .