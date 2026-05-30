from __future__ import annotations

import sys
from pathlib import Path

import frontmatter
import markdown
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from blogsmith.config import BlogsmithConfig
from blogsmith.git_service import commit_and_push, validate_git_repo
from blogsmith.gui.settings_dialog import SettingsDialog
from blogsmith.posts import create_draft, list_drafts, list_posts, publish_draft
from blogsmith.settings import is_configured, load_settings, save_settings
from blogsmith.validation import validate_post_file

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
        self.title_input.setPlaceholderText("Example: Building a Unity Dialogue System")
        self.title_input.setToolTip(
            "The visible title of your blog post. This usually becomes the H1 heading "
            "and helps generate the filename slug."
        )

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Example: unity, csharp, tools")
        self.tags_input.setToolTip(
            "Comma-separated topics. These help group posts on your portfolio and make "
            "filtering/search easier."
        )

        self.excerpt_input = QTextEdit()
        self.excerpt_input.setFixedHeight(90)
        self.excerpt_input.setPlaceholderText(
            "Example: How I built a lightweight dialogue system for Unity with branching choices and reusable nodes."
        )
        self.excerpt_input.setToolTip(
            "A short summary of the post. Usually shown on blog cards, previews, search results, "
            "and SEO metadata. Think of it as the elevator pitch for the article."
        )

        form = QFormLayout()
        form.addRow("Title", self.title_input)
        form.addRow("Tags", self.tags_input)
        form.addRow("Excerpt / summary", self.excerpt_input)

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
    def __init__(self, default_message: str, default_push: bool = True) -> None:
        super().__init__()

        self.setWindowTitle("Publish Draft")

        self.message_input = QLineEdit(default_message)
        self.message_input.setPlaceholderText(
            "Example: Add blog post about Unity dialogue system"
        )
        self.message_input.setToolTip(
            "This is the Git commit message used when Blogsmith commits the published post "
            "to your portfolio repository."
        )

        self.push_checkbox = QCheckBox("Commit and push to GitHub after publishing")
        self.push_checkbox.setChecked(default_push)
        self.push_checkbox.setToolTip(
            "If enabled, Blogsmith will commit this post and push it using your existing "
            "local Git authentication."
        )

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
        layout.addWidget(self.push_checkbox)
        layout.addWidget(buttons)

        self.setLayout(layout)

    @property
    def commit_message(self) -> str:
        return self.message_input.text().strip()

    @property
    def should_push(self) -> bool:
        return self.push_checkbox.isChecked()


class BlogsmithWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.settings = load_settings()
        self.config: BlogsmithConfig | None = None
        self.current_path: Path | None = None

        self.setWindowTitle("Blogsmith")
        self.resize(1200, 800)

        self.post_list = QListWidget()
        self.editor = QTextEdit()
        self.file_label = QLabel("No file selected")

        self.settings_button = QPushButton("Settings")
        self.new_button = QPushButton("New")
        self.save_button = QPushButton("Save")
        self.preview_button = QPushButton("Preview")
        self.validate_button = QPushButton("Validate")
        self.publish_button = QPushButton("Publish")

        self.settings_button.setToolTip(
            "Configure your portfolio repository and publishing options."
        )

        sidebar = QVBoxLayout()
        sidebar.addWidget(QLabel("Posts"))
        sidebar.addWidget(self.post_list)
        sidebar.addWidget(self.settings_button)
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
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.new_button.clicked.connect(self.open_new_draft_dialog)
        self.save_button.clicked.connect(self.save_current_post)
        self.preview_button.clicked.connect(self.preview_current_post)
        self.validate_button.clicked.connect(self.validate_current_post)
        self.publish_button.clicked.connect(self.publish_current_post)

        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(250)
        self.preview_timer.timeout.connect(self.update_live_preview)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(30_000)
        self.autosave_timer.timeout.connect(self.autosave_current_post)
        self.autosave_timer.start()

        self.editor.textChanged.connect(self.on_editor_changed)

        if is_configured(self.settings):
            self.reload_config_from_settings()
            self.ensure_blog_folders()
            self.set_app_enabled(True)
            self.refresh_posts()
        else:
            self.set_app_enabled(False)
            self.open_settings_dialog(first_run=True)

    def require_config(self) -> BlogsmithConfig | None:
        if self.config is None:
            QMessageBox.information(
                self,
                "Setup required",
                "Open Settings and choose your portfolio repository first.",
            )
            return None

        return self.config

    def set_app_enabled(self, enabled: bool) -> None:
        self.new_button.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.preview_button.setEnabled(enabled)
        self.validate_button.setEnabled(enabled)
        self.publish_button.setEnabled(enabled)
        self.post_list.setEnabled(enabled)
        self.editor.setEnabled(enabled)

    def reload_config_from_settings(self) -> None:
        self.config = BlogsmithConfig.from_settings(self.settings)

    def ensure_blog_folders(self) -> None:
        config = self.require_config()

        if config is None:
            return

        config.drafts_path.mkdir(parents=True, exist_ok=True)
        config.posts_path.mkdir(parents=True, exist_ok=True)
        config.assets_path.mkdir(parents=True, exist_ok=True)

    def open_settings_dialog(self, first_run: bool = False) -> None:
        dialog = SettingsDialog(self.settings, self)

        if first_run:
            dialog.setWindowTitle("Set up Blogsmith")

        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            save_settings(self.settings)
            self.reload_config_from_settings()
            self.ensure_blog_folders()
            self.set_app_enabled(True)
            self.refresh_posts()
            self.statusBar().showMessage("Settings saved.", 3000)
            return

        if first_run:
            QMessageBox.warning(
                self,
                "Setup required",
                "Blogsmith needs a portfolio repository before it can create or publish posts.",
            )
            self.set_app_enabled(False)

    def current_is_draft(self) -> bool:
        config = self.require_config()

        if config is None or self.current_path is None:
            return False

        try:
            self.current_path.relative_to(config.drafts_path)
            return True
        except ValueError:
            return False

    def refresh_posts(self) -> None:
        config = self.require_config()

        if config is None:
            return

        self.post_list.clear()

        for draft in list_drafts(config):
            item = QListWidgetItem(f"Draft | {draft.name}")
            item.setData(FILE_PATH_ROLE, str(draft))
            self.post_list.addItem(item)

        for post in list_posts(config):
            item = QListWidgetItem(f"Post | {post.name}")
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

    def autosave_current_post(self) -> None:
        if self.current_path is None:
            return

        self.current_path.write_text(
            self.editor.toPlainText(),
            encoding="utf-8",
        )

        self.statusBar().showMessage(f"Autosaved {self.current_path.name}", 2000)

    def open_new_draft_dialog(self) -> None:
        config = self.require_config()

        if config is None:
            return

        dialog = NewDraftDialog()

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if not dialog.title:
            QMessageBox.warning(self, "Missing title", "Please enter a title.")
            return

        try:
            path = create_draft(
                config=config,
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
            self.validation_label.setText("Validation: Failed")
            QMessageBox.warning(
                self,
                "Validation failed",
                "\n".join(errors),
            )
            return

        self.validation_label.setText("Validation: Passed")
        QMessageBox.information(
            self,
            "Validation passed",
            "This post looks ready.",
        )

    def publish_current_post(self) -> None:
        config = self.require_config()

        if config is None:
            return

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
        dialog = PublishDialog(
            default_message=default_message,
            default_push=self.settings.auto_push,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            validate_git_repo(config.site_repo_path, config.branch)

            published_path, _draft_path = publish_draft(
                config=config,
                slug_or_filename=self.current_path.stem,
            )

            if dialog.should_push:
                commit_and_push(
                    repo_path=config.site_repo_path,
                    files=[published_path],
                    message=dialog.commit_message
                    or f"Add blog post: {published_path.stem}",
                    remote_name=config.remote_name,
                    branch=config.branch,
                    push=True,
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

    app.setStyleSheet(
        """
        QMainWindow {
            background: #2f2f2f;
        }

        QListWidget {
            border: 1px solid #555;
            border-radius: 8px;
            padding: 6px;
            background: #111;
            color: white;
        }

        QTextEdit {
            border: 1px solid #555;
            border-radius: 8px;
            padding: 10px;
            font-family: Consolas, monospace;
            font-size: 14px;
            background: #111;
            color: white;
        }

        QTextBrowser {
            border: 1px solid #555;
            border-radius: 8px;
            background: #111;
            color: white;
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

        QPushButton:disabled {
            background: #333;
            color: #777;
        }

        QLabel {
            font-size: 14px;
            color: white;
        }

        QTabWidget::pane {
            border: 1px solid #555;
            border-radius: 8px;
        }

        QTabBar::tab {
            background: #222;
            color: white;
            padding: 8px 12px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }

        QTabBar::tab:selected {
            background: #444;
        }
        """
    )

    window = BlogsmithWindow()
    window.show()

    sys.exit(app.exec())