import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from blogsmith.config import load_config
from blogsmith.posts import list_drafts, list_posts


FILE_PATH_ROLE = Qt.ItemDataRole.UserRole


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

        self.current_path = path
        self.file_label.setText(str(path))
        self.editor.setPlainText(path.read_text(encoding="utf-8"))


def main() -> None:
    app = QApplication(sys.argv)
    window = BlogsmithWindow()
    window.show()
    sys.exit(app.exec())