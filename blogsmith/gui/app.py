import sys
from pathlib import Path

from PySide6.QtCore import Qt
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
)

from blogsmith.config import load_config
from blogsmith.posts import create_draft, list_drafts, list_posts
from blogsmith.validation import validate_post_file

import frontmatter
import markdown


FILE_PATH_ROLE = Qt.ItemDataRole.UserRole

def parse_tags(raw_tags: str) -> list[str]:
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


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
    
class PreviewDialog(QDialog):
    def __init__(self, title: str, html: str) -> None:
        super().__init__()

        self.setWindowTitle(f"Preview: {title}")
        self.resize(900, 700)

        browser = QTextBrowser()
        browser.setHtml(html)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(browser)
        layout.addWidget(buttons)

        self.setLayout(layout)

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

        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.file_label)
        editor_layout.addWidget(self.editor)

        editor_widget = QWidget()
        editor_widget.setLayout(editor_layout)

        main_layout = QHBoxLayout()
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(editor_widget)

        root = QWidget()
        root.setLayout(main_layout)

        self.setCentralWidget(root)

        self.post_list.itemClicked.connect(self.load_selected_post)
        self.new_button.clicked.connect(self.open_new_draft_dialog)
        self.save_button.clicked.connect(self.save_current_post)
        self.preview_button.clicked.connect(self.preview_current_post)
        self.validate_button.clicked.connect(self.validate_current_post)

        self.refresh_posts()

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

        try:
            post = frontmatter.loads(
                self.current_path.read_text(encoding="utf-8")
            )
            body_html = markdown.markdown(
                post.content,
                extensions=["fenced_code", "tables", "toc"],
            )
        except Exception as exc:
            QMessageBox.critical(self, "Preview failed", str(exc))
            return

        title = post.metadata.get("title", self.current_path.stem)

        html = f"""
        <html>
          <body style="font-family: system-ui; line-height: 1.6;">
            <h1>{title}</h1>
            <hr>
            {body_html}
          </body>
        </html>
        """

        dialog = PreviewDialog(title=title, html=html)
        dialog.exec()
        
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
    


def main() -> None:
    app = QApplication(sys.argv)
    window = BlogsmithWindow()
    window.show()
    sys.exit(app.exec())