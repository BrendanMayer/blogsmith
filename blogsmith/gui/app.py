import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QTextBrowser,
    QSplitter,
    QTabWidget,
    QCheckBox,
)

from blogsmith.config import load_config
from blogsmith.posts import create_draft, list_drafts, list_posts, publish_draft
from blogsmith.git_service import commit_and_push, validate_git_repo
from blogsmith.validation import validate_post_file

import frontmatter
import markdown


FILE_PATH_ROLE = Qt.ItemDataRole.UserRole

def parse_tags(raw_tags: str) -> list[str]:
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]

def render_preview_html(markdown_text: str, fallback_title: str = "Untitled") -> str:
    try:
        post = frontmatter.loads(markdown_text)
        title = post.metadata.get("title", fallback_title)
        date = post.metadata.get("date", "")
        tags = post.metadata.get("tags", [])
        excerpt = post.metadata.get("excerpt", "")
        body_html = markdown.markdown(
            post.content,
            extensions=["fenced_code", "tables", "toc"],
        )

        if isinstance(tags, list):
            tag_text = ", ".join(str(tag) for tag in tags)
        else:
            tag_text = str(tags)

        return f"""
        <!doctype html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    line-height: 1.65;
                    padding: 24px;
                    color: #f2f2f2;
                    background: #111;
                }}
                h1, h2, h3 {{
                    line-height: 1.25;
                }}
                pre {{
                    background: #1f1f1f;
                    padding: 14px;
                    border-radius: 8px;
                    overflow-x: auto;
                }}
                code {{
                    font-family: Consolas, monospace;
                }}
                img {{
                    max-width: 100%;
                    border-radius: 8px;
                }}
                blockquote {{
                    border-left: 4px solid #666;
                    padding-left: 12px;
                    color: #ccc;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    border: 1px solid #444;
                    padding: 8px;
                }}
                .meta {{
                    color: #aaa;
                    border-bottom: 1px solid #333;
                    margin-bottom: 24px;
                    padding-bottom: 16px;
                }}
                .excerpt {{
                    font-style: italic;
                    color: #ccc;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="meta">
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Tags:</strong> {tag_text}</p>
                <p class="excerpt"><strong>Excerpt:</strong> {excerpt}</p>
            </div>
            {body_html}
        </body>
        </html>
        """
    except Exception as exc:
        return f"""
        <html>
        <body style="font-family: system-ui; padding: 24px;">
            <h2>Preview error</h2>
            <p>{exc}</p>
        </body>
        </html>
        """


class NewDraftDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("New Draft")

        self.title_input = QLineEdit()
        self.tags_input = QLineEdit()
        self.excerpt_input = QTextEdit()
        self.excerpt_input.setFixedHeight(90)

        form = QFormLayout()
        form.addRow("Title", self.title_input)
        form.addRow("Tags", self.tags_input)
        form.addRow("Excerpt", self.excerpt_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.setLayout(layout)

    @property
    def title(self) -> str:
        return self.title_input.text().strip()

    @property
    def tags(self) -> list[str]:
        return parse_tags(self.tags_input.text())

    @property
    def excerpt(self) -> str:
        return self.excerpt_input.toPlainText().strip()
    
        
class PublishDialog(QDialog):
    def __init__(self, default_message: str) -> None:
        super().__init__()

        self.setWindowTitle("Publish Draft")

        self.message_input = QLineEdit(default_message)

        form = QFormLayout()
        form.addRow("Commit message", self.message_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.setLayout(layout)

    @property
    def commit_message(self) -> str:
        return self.message_input.text().strip()

class BlogsmithWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.config = load_config()
        self.current_path: Path | None = None

        self.setWindowTitle("Blogsmith")
        self.resize(1200, 800)

        self.post_list = QListWidget()
        self.editor = QTextEdit()

        self.file_label = QLabel("No file selected")

        self.new_button = QPushButton("New")
        self.save_button = QPushButton("Save")
        self.preview_button = QPushButton("Preview")
        self.validate_button = QPushButton("Validate")
        self.publish_button = QPushButton("Publish")

        sidebar = QVBoxLayout()
        sidebar.addWidget(QLabel("Posts"))
        sidebar.addWidget(self.post_list)
        sidebar.addWidget(self.new_button)
        sidebar.addWidget(self.save_button)
        sidebar.addWidget(self.preview_button)
        sidebar.addWidget(self.validate_button)
        sidebar.addWidget(self.publish_button)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(320)

        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenExternalLinks(True)

        self.preview_tabs = QTabWidget()
        self.preview_tabs.addTab(self.preview_browser, "Live Preview")

        self.word_count_label = QLabel("Words: 0")
        self.validation_label = QLabel("Validation: Not checked")

        editor_header = QHBoxLayout()
        editor_header.addWidget(self.file_label)
        editor_header.addStretch()
        editor_header.addWidget(self.word_count_label)
        editor_header.addWidget(self.validation_label)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(editor_header)
        editor_layout.addWidget(self.editor)

        editor_widget = QWidget()
        editor_widget.setLayout(editor_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(editor_widget)
        splitter.addWidget(self.preview_tabs)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout = QHBoxLayout()
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(splitter)

        root = QWidget()
        root.setLayout(main_layout)

        self.setCentralWidget(root)

        self.post_list.itemClicked.connect(self.load_selected_post)
        self.new_button.clicked.connect(self.open_new_draft_dialog)
        self.save_button.clicked.connect(self.save_current_post)
        self.preview_button.clicked.connect(self.preview_current_post)
        self.validate_button.clicked.connect(self.validate_current_post)
        self.publish_button.clicked.connect(self.publish_current_post)
        
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(250)
        self.preview_timer.timeout.connect(self.update_live_preview)

        self.editor.textChanged.connect(self.on_editor_changed)

        self.refresh_posts()

    def current_is_draft(self) -> bool:
        if self.current_path is None:
            return False

        try:
            self.current_path.relative_to(self.config.drafts_path)
            return True
        except ValueError:
            return False
        
    def refresh_posts(self) -> None:
        self.post_list.clear()

        for draft in list_drafts(self.config):
            item = QListWidgetItem(f"Draft | {draft.name}")
            item.setData(FILE_PATH_ROLE, str(draft))
            self.post_list.addItem(item)

        for post in list_posts(self.config):
            item = QListWidgetItem(f"Post  | {post.name}")
            item.setData(FILE_PATH_ROLE, str(post))
            self.post_list.addItem(item)

    def load_selected_post(self, item: QListWidgetItem) -> None:
        path = Path(item.data(FILE_PATH_ROLE))
        self.load_path(path)

    def load_path(self, path: Path) -> None:
        self.current_path = path
        self.file_label.setText(str(path))
        self.editor.setPlainText(path.read_text(encoding="utf-8"))
        self.update_word_count()
        self.update_live_preview()
        
    def save_current_post(self) -> None:
        if self.current_path is None:
            self.statusBar().showMessage("No file selected.", 3000)
            return

        self.current_path.write_text(
            self.editor.toPlainText(),
            encoding="utf-8",
        )

        self.statusBar().showMessage(f"Saved {self.current_path.name}", 3000)
        
    def open_new_draft_dialog(self) -> None:
        dialog = NewDraftDialog()

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if not dialog.title:
            QMessageBox.warning(self, "Missing title", "Please enter a title.")
            return

        try:
            path = create_draft(
                config=self.config,
                title=dialog.title,
                tags=dialog.tags,
                excerpt=dialog.excerpt,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Could not create draft", str(exc))
            return

        self.refresh_posts()
        self.load_path(path)
        self.statusBar().showMessage(f"Created draft {path.name}", 3000)
        
    def preview_current_post(self) -> None:
        if self.current_path is None:
            QMessageBox.information(self, "No file selected", "Select a post first.")
            return

        self.save_current_post()
        self.update_live_preview()
        self.preview_tabs.setCurrentWidget(self.preview_browser)
        self.statusBar().showMessage("Preview updated.", 3000)
            
        def validate_current_post(self) -> None:
            if self.current_path is None:
                QMessageBox.information(self, "No file selected", "Select a post first.")
                return

            self.save_current_post()

            errors = validate_post_file(self.current_path)

            if errors:
                QMessageBox.warning(
                    self,
                    "Validation failed",
                    "\n".join(errors),
                )
                return

            QMessageBox.information(
                self,
                "Validation passed",
                "This post looks ready.",
            )
        
    def publish_current_post(self) -> None:
        if self.current_path is None:
            QMessageBox.information(self, "No file selected", "Select a draft first.")
            return

        if not self.current_is_draft():
            QMessageBox.information(
                self,
                "Not a draft",
                "Only drafts can be published.",
            )
            return

        self.save_current_post()

        errors = validate_post_file(self.current_path)
        if errors:
            QMessageBox.warning(
                self,
                "Validation failed",
                "Fix these issues before publishing:\n\n" + "\n".join(errors),
            )
            return

        default_message = f"Add blog post: {self.current_path.stem}"
        dialog = PublishDialog(default_message)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        should_push = QMessageBox.question(
            self,
            "Push to GitHub?",
            "Publish, commit, and push this post to GitHub?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        try:
            validate_git_repo(self.config.site_repo_path, self.config.branch)

            published_path, _draft_path = publish_draft(
                config=self.config,
                slug_or_filename=self.current_path.stem,
            )

            if should_push == QMessageBox.StandardButton.Yes:
                commit_and_push(
                    repo_path=self.config.site_repo_path,
                    files=[published_path],
                    message=dialog.commit_message or f"Add blog post: {published_path.stem}",
                )

                self.statusBar().showMessage(
                    f"Published and pushed {published_path.name}",
                    5000,
                )
            else:
                self.statusBar().showMessage(
                    f"Published locally: {published_path.name}",
                    5000,
                )

            self.refresh_posts()
            self.load_path(published_path)

        except Exception as exc:
            QMessageBox.critical(self, "Publish failed", str(exc))
            
    def on_editor_changed(self) -> None:
        self.update_word_count()
        self.validation_label.setText("Validation: Not checked")
        self.preview_timer.start()

    def update_word_count(self) -> None:
        text = self.editor.toPlainText()
        body = text
        try:
            post = frontmatter.loads(text)
            body = post.content
        except Exception:
            pass

        words = [word for word in body.split() if word.strip()]
        self.word_count_label.setText(f"Words: {len(words)}")

    def update_live_preview(self) -> None:
        fallback_title = self.current_path.stem if self.current_path else "Untitled"
        html = render_preview_html(self.editor.toPlainText(), fallback_title)
        self.preview_browser.setHtml(html)
    


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet("""
    QMainWindow {
        background: #f6f6f6;
    }

    QListWidget {
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 6px;
        background: black;
    }

    QTextEdit {
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 10px;
        font-family: Consolas, monospace;
        font-size: 14px;
        background: black;
    }

    QPushButton {
        padding: 8px 10px;
        border-radius: 8px;
        background: #222;
        color: white;
    }

    QPushButton:hover {
        background: #444;
    }

    QLabel {
        font-size: 14px;
    }
    """)
    window = BlogsmithWindow()
    window.show()
    sys.exit(app.exec())