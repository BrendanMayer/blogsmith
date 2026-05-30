from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from blogsmith.settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Blogsmith Settings")
        self.setMinimumWidth(720)

        self.settings = settings

        title = QLabel("Workspace Settings")
        title.setObjectName("AppTitle")

        subtitle = QLabel(
            "Connect Blogsmith to a local portfolio repository and choose where posts are stored."
        )
        subtitle.setObjectName("AppSubtitle")
        subtitle.setWordWrap(True)

        header = QVBoxLayout()
        header.addWidget(title)
        header.addWidget(subtitle)

        self.repo_input = QLineEdit(settings.site_repo_path)
        self.repo_input.setPlaceholderText(
            "Example: C:/Users/you/Documents/GitHub/portfolio"
        )
        self.repo_input.setToolTip(
            "The local folder for your portfolio or blog repository. "
            "It must already be a Git repository."
        )

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_repo)

        repo_row = QHBoxLayout()
        repo_row.addWidget(self.repo_input)
        repo_row.addWidget(self.browse_button)

        self.drafts_input = QLineEdit(settings.drafts_dir)
        self.drafts_input.setPlaceholderText("_drafts")
        self.drafts_input.setToolTip(
            "Folder inside your repo where unpublished draft posts are stored."
        )

        self.posts_input = QLineEdit(settings.posts_dir)
        self.posts_input.setPlaceholderText("_posts")
        self.posts_input.setToolTip(
            "Folder inside your repo where published posts are stored."
        )

        self.assets_input = QLineEdit(settings.assets_dir)
        self.assets_input.setPlaceholderText("assets/images/blog")
        self.assets_input.setToolTip(
            "Folder inside your repo where blog images should be stored."
        )

        self.branch_input = QLineEdit(settings.branch)
        self.branch_input.setPlaceholderText("main")
        self.branch_input.setToolTip(
            "The Git branch Blogsmith should publish to. Usually main or master."
        )

        self.remote_input = QLineEdit(settings.remote_name)
        self.remote_input.setPlaceholderText("origin")
        self.remote_input.setToolTip(
            "The Git remote name Blogsmith should push to. Usually origin."
        )

        self.author_name_input = QLineEdit(settings.git_author_name)
        self.author_name_input.setPlaceholderText("Example: Brendan Mayer")
        self.author_name_input.setToolTip(
            "Optional Git author name for commits made by Blogsmith."
        )

        self.author_email_input = QLineEdit(settings.git_author_email)
        self.author_email_input.setPlaceholderText("Example: you@example.com")
        self.author_email_input.setToolTip(
            "Optional Git author email for commits made by Blogsmith."
        )

        self.auto_push_checkbox = QCheckBox(
            "Push to GitHub after publishing by default"
        )
        self.auto_push_checkbox.setChecked(settings.auto_push)
        self.auto_push_checkbox.setToolTip(
            "When enabled, Blogsmith will push commits after publishing by default."
        )

        form = QFormLayout()
        form.setSpacing(14)
        form.addRow("Portfolio repo", repo_row)
        form.addRow("Drafts folder", self.drafts_input)
        form.addRow("Posts folder", self.posts_input)
        form.addRow("Assets folder", self.assets_input)
        form.addRow("Branch", self.branch_input)
        form.addRow("Remote", self.remote_input)
        form.addRow("Git author name", self.author_name_input)
        form.addRow("Git author email", self.author_email_input)

        card = QFrame()
        card.setObjectName("Panel")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(22, 22, 22, 22)
        card_layout.setSpacing(16)
        card_layout.addLayout(form)
        card_layout.addWidget(self.auto_push_checkbox)
        card.setLayout(card_layout)

        help_text = QLabel(
            "Blogsmith uses your existing local Git authentication. "
            "Before publishing, make sure you can push from this repo in a terminal."
        )
        help_text.setObjectName("MutedLabel")
        help_text.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addLayout(header)
        layout.addWidget(card)
        layout.addWidget(help_text)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def browse_repo(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select portfolio repository",
            self.repo_input.text() or str(Path.home()),
        )

        if folder:
            self.repo_input.setText(folder)

    def validate_and_accept(self) -> None:
        repo_path = Path(self.repo_input.text()).expanduser()

        if not repo_path.exists():
            QMessageBox.warning(
                self,
                "Invalid repository",
                "That folder does not exist.",
            )
            return

        if not (repo_path / ".git").exists():
            QMessageBox.warning(
                self,
                "Not a Git repository",
                "That folder does not appear to be a Git repository. "
                "Select the root folder of your portfolio repo.",
            )
            return

        if not self.drafts_input.text().strip():
            QMessageBox.warning(
                self,
                "Missing drafts folder",
                "Enter a drafts folder.",
            )
            return

        if not self.posts_input.text().strip():
            QMessageBox.warning(
                self,
                "Missing posts folder",
                "Enter a posts folder.",
            )
            return

        if not self.assets_input.text().strip():
            QMessageBox.warning(
                self,
                "Missing assets folder",
                "Enter an assets folder.",
            )
            return

        self.settings.site_repo_path = str(repo_path.resolve())
        self.settings.drafts_dir = self.drafts_input.text().strip()
        self.settings.posts_dir = self.posts_input.text().strip()
        self.settings.assets_dir = self.assets_input.text().strip()
        self.settings.branch = self.branch_input.text().strip() or "main"
        self.settings.remote_name = self.remote_input.text().strip() or "origin"
        self.settings.git_author_name = self.author_name_input.text().strip()
        self.settings.git_author_email = self.author_email_input.text().strip()
        self.settings.auto_push = self.auto_push_checkbox.isChecked()

        self.accept()