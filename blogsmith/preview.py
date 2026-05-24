import tempfile
import webbrowser
from pathlib import Path

import frontmatter
import markdown


def render_markdown_preview(markdown_path: Path) -> Path:
    post = frontmatter.loads(markdown_path.read_text(encoding="utf-8"))

    title = post.metadata.get("title", markdown_path.stem)
    body_html = markdown.markdown(
        post.content,
        extensions=[
            "fenced_code",
            "tables",
            "toc",
        ],
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{
      max-width: 850px;
      margin: 40px auto;
      padding: 0 24px;
      font-family: system-ui, sans-serif;
      line-height: 1.6;
    }}

    pre {{
      padding: 16px;
      overflow-x: auto;
      background: #f4f4f4;
      border-radius: 8px;
    }}

    code {{
      font-family: Consolas, monospace;
    }}

    img {{
      max-width: 100%;
    }}

    .meta {{
      color: #666;
      border-bottom: 1px solid #ddd;
      margin-bottom: 32px;
      padding-bottom: 16px;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">
    <p><strong>Date:</strong> {post.metadata.get("date", "")}</p>
    <p><strong>Tags:</strong> {", ".join(post.metadata.get("tags", []))}</p>
    <p><strong>Excerpt:</strong> {post.metadata.get("excerpt", "")}</p>
  </div>
  {body_html}
</body>
</html>
"""

    preview_dir = Path(tempfile.gettempdir()) / "blogsmith-previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    output_path = preview_dir / f"{markdown_path.stem}.html"
    output_path.write_text(html, encoding="utf-8")

    return output_path


def open_preview(markdown_path: Path) -> Path:
    output_path = render_markdown_preview(markdown_path)
    webbrowser.open(output_path.as_uri())
    return output_path