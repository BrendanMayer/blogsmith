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
```

## Version 2 workflow
```bash
Preview a draft or post:

blogsmith preview building-a-unity-dialogue-system

Validate front matter and content:

blogsmith validate building-a-unity-dialogue-system

Check linked portfolio repository status:

blogsmith status

Import an image into the portfolio repository:

blogsmith image building-a-unity-dialogue-system "C:\path\to\screenshot.png" --alt "Dialogue graph screenshot"

Publish with a custom commit message:

blogsmith publish building-a-unity-dialogue-system --push --message "Add dialogue system blog post"
```

## All Commands

blogsmith new "Building a Unity Dialogue System" --tags "unity,csharp,tools" --excerpt "How I built a lightweight dialogue system."
blogsmith edit building-a-unity-dialogue-system
blogsmith image building-a-unity-dialogue-system "C:\Users\brend\Pictures\dialogue-graph.png" --alt "Dialogue graph"
blogsmith preview building-a-unity-dialogue-system
blogsmith validate building-a-unity-dialogue-system
blogsmith status
blogsmith publish building-a-unity-dialogue-system --push --message "Add dialogue system blog post"

