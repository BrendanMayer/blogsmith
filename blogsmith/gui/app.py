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
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
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
from blogsmith.gui.theme import apply_theme
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
                    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    line-height: 1.72;
                    padding: 32px;
                    color: #e5e7eb;
                    background: #020617;
                }}

                .container {{
                    max-width: 860px;
                    margin: 0 auto;
                }}

                h1 {{
                    font-size: 42px;
                    line-height: 1.1;
                    margin-bottom: 12px;
                    color: #f8fafc;
                }}

                h2, h3 {{
                    line-height: 1.25;
                    color: #f8fafc;
                    margin-top: 32px;
                }}

                p {{
                    color: #cbd5e1;
                    font-size: 16px;
                }}

                a {{
                    color: #60a5fa;
                }}

                pre {{
                    background: #0f172a;
                    border: 1px solid #1e293b;
                    padding: 16px;
                    border-radius: 14px;
                    overflow-x: auto;
                }}

                code {{
                    font-family: Consolas, "Cascadia Mono", monospace;
                    color: #bfdbfe;
                }}

                img {{
                    max-width: 100%;
                    border-radius: 14px;
                    border: 1px solid #1e293b;
                }}

                blockquote {{
                    border-left: 4px solid #3b82f6;
                    padding-left: 16px;
                    color: #cbd5e1;
                    margin-left: 0;
                }}

                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}

                th, td {{
                    border: 1px solid #334155;
                    padding: 10px;
                }}

                th {{
                    background: #0f172a;
                    color: #f8fafc;
                }}

                .meta {{
                    color: #94a3b8;
                    border: 1px solid #1e293b;
                    background: #0f172a;
                    margin-bottom: 28px;
                    padding: 16px;
                    border-radius: 16px;
                }}

                .meta p {{
                    margin: 6px 0;
                    color: #94a3b8;
                }}

                .excerpt {{
                    font-style: italic;
                    color: #cbd5e1;
                }}
            </style>
        </head>
        <body>
            <main class="container">
                <h1>{title}</h1>
                <div class="meta">
                    <p><strong>Date:</strong> {date}</p>
                    <p><strong>Tags:</strong> {tag_text}</p>
                    <p class="excerpt"><strong>Excerpt:</strong> {excerpt}</p>
                </div>
                {body_html}
            </main>
        </body>
        </html>
        """

    except Exception as exc:
        return f"""
        <html>
        <body style="font-family: system-ui; padding: 24px; background: #020617; color: #e5e7eb;">
            <h2>Preview error</h2>
            <p>{exc}</p>
        </body>
        </html>
        """


class NewDraftDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Create New Draft")
        self.setMinimumWidth(620)

        title = QLabel("Create Draft")
        title.setObjectName("AppTitle")

        subtitle = QLabel("Start a polished portfolio blog post with clean front matter.")
        subtitle.setObjectName("AppSubtitle")

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
        self.excerpt_input.setFixedHeight(110)
        self.excerpt_input.setPlaceholderText(
            "Example: How I built a lightweight dialogue system for Unity with branching choices and reusable nodes."
        )
        self.excerpt_input.setToolTip(
            "A short summary of the post. Usually shown on blog cards, previews, search results, "
            "and SEO metadata. Think of it as the elevator pitch for the article."
        )

        form = QFormLayout()
        form.setSpacing(14)
        form.addRow("Title", self.title_input)
        form.addRow("Tags", self.tags_input)
        form.addRow("Excerpt", self.excerpt_input)

        card = QFrame()
        card.setObjectName("Panel")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.addLayout(form)
        card.setLayout(card_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(card)
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
        self.setMinimumWidth(620)

        title = QLabel("Publish Draft")
        title.setObjectName("AppTitle")

        subtitle = QLabel("Validate, commit, and optionally push this post to GitHub.")
        subtitle.setObjectName("AppSubtitle")

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
        form.setSpacing(14)
        form.addRow("Commit message", self.message_input)

        card = QFrame()
        card.setObjectName("Panel")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(16)
        card_layout.addLayout(form)
        card_layout.addWidget(self.push_checkbox)
        card.setLayout(card_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(card)
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

        self.setWindowTitle("Blogsmith v5")
        self.resize(1440, 900)

        self.post_list = QListWidget()
        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "Choose a draft or create a new one. Then write something brilliant enough to justify Markdown."
        )

        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("FileLabel")

        self.word_count_label = QLabel("Words: 0")
        self.word_count_label.setObjectName("Pill")

        self.validation_label = QLabel("Validation: Not checked")
        self.validation_label.setObjectName("Pill")

        self.settings_button = QPushButton("Settings")
        self.new_button = QPushButton("New Draft")
        self.save_button = QPushButton("Save")
        self.preview_button = QPushButton("Refresh Preview")
        self.validate_button = QPushButton("Validate")
        self.publish_button = QPushButton("Publish")

        self.publish_button.setObjectName("PrimaryButton")

        for button in [
            self.settings_button,
            self.new_button,
            self.save_button,
            self.preview_button,
            self.validate_button,
        ]:
            button.setObjectName("SidebarButton")

        self.settings_button.setToolTip(
            "Configure your portfolio repository and publishing options."
        )

        sidebar = self.build_sidebar()
        workspace = self.build_workspace()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(sidebar)
        main_layout.addWidget(workspace)

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

    def build_sidebar(self) -> QFrame:
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("Sidebar")
        sidebar_frame.setFixedWidth(340)

        app_title = QLabel("Blogsmith")
        app_title.setObjectName("AppTitle")

        app_subtitle = QLabel("Write. Preview. Publish.")
        app_subtitle.setObjectName("AppSubtitle")

        header_layout = QVBoxLayout()
        header_layout.addWidget(app_title)
        header_layout.addWidget(app_subtitle)

        posts_title = QLabel("Library")
        posts_title.setObjectName("SectionTitle")

        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.preview_button)
        button_layout.addWidget(self.validate_button)
        button_layout.addWidget(self.publish_button)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.settings_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 24, 20, 20)
        layout.setSpacing(18)
        layout.addLayout(header_layout)
        layout.addWidget(posts_title)
        layout.addWidget(self.post_list, 1)
        layout.addLayout(button_layout)

        sidebar_frame.setLayout(layout)
        return sidebar_frame

    def build_workspace(self) -> QWidget:
        self.preview_browser = QTextBrowser()
        self.preview_browser.setOpenExternalLinks(True)

        self.preview_tabs = QTabWidget()
        self.preview_tabs.addTab(self.preview_browser, "Live Preview")

        top_bar = QFrame()
        top_bar.setObjectName("TopBar")

        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(18, 14, 18, 14)
        top_bar_layout.setSpacing(12)
        top_bar_layout.addWidget(self.file_label, 1)
        top_bar_layout.addWidget(self.word_count_label)
        top_bar_layout.addWidget(self.validation_label)
        top_bar.setLayout(top_bar_layout)

        editor_title = QLabel("Editor")
        editor_title.setObjectName("SectionTitle")

        preview_title = QLabel("Preview")
        preview_title.setObjectName("SectionTitle")

        editor_panel = QFrame()
        editor_panel.setObjectName("Panel")
        editor_panel_layout = QVBoxLayout()
        editor_panel_layout.setContentsMargins(16, 16, 16, 16)
        editor_panel_layout.setSpacing(12)
        editor_panel_layout.addWidget(editor_title)
        editor_panel_layout.addWidget(self.editor)
        editor_panel.setLayout(editor_panel_layout)

        preview_panel = QFrame()
        preview_panel.setObjectName("Panel")
        preview_panel_layout = QVBoxLayout()
        preview_panel_layout.setContentsMargins(16, 16, 16, 16)
        preview_panel_layout.setSpacing(12)
        preview_panel_layout.addWidget(preview_title)
        preview_panel_layout.addWidget(self.preview_tabs)
        preview_panel.setLayout(preview_panel_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(editor_panel)
        splitter.addWidget(preview_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        workspace_layout = QVBoxLayout()
        workspace_layout.setContentsMargins(22, 22, 22, 22)
        workspace_layout.setSpacing(16)
        workspace_layout.addWidget(top_bar)
        workspace_layout.addWidget(splitter, 1)

        workspace = QWidget()
        workspace.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        workspace.setLayout(workspace_layout)

        return workspace

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
            item = QListWidgetItem(f"Draft    {draft.name}")
            item.setData(FILE_PATH_ROLE, str(draft))
            self.post_list.addItem(item)

        for post in list_posts(config):
            item = QListWidgetItem(f"Post      {post.name}")
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
    apply_theme(app)

    window = BlogsmithWindow()
    window.show()

    sys.exit(app.exec())