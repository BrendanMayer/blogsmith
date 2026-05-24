import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class BlogsmithWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Blogsmith")
        self.resize(1100, 750)

        label = QLabel("Blogsmith Desktop Editor")
        label.setStyleSheet("font-size: 24px; padding: 24px;")
        self.setCentralWidget(label)


def main() -> None:
    app = QApplication(sys.argv)
    window = BlogsmithWindow()
    window.show()
    sys.exit(app.exec())