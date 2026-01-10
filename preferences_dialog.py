from PyQt5.QtWidgets import (
    QDialog, QListWidget, QStackedWidget,
    QHBoxLayout, QVBoxLayout, QPushButton,
    QWidget, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt
import os
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtGui import QIcon

# Import config helpers
from nvd_config_mgr import (
    load_existing_nvd_key,
    save_nvd_key_to_all_configs
)
from sonatype_config_mgr import (
    load_existing_sonatype_key,
    save_api_key_to_all_configs
)
from theme_manager import load_theme, save_theme
from PyQt5.QtWidgets import QComboBox


# ============================================================
# APPEARANCE SETTINGS PANEL
# ============================================================

class AppearanceSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_theme = load_theme()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Appearance")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        desc = QLabel("Select the application color theme. Requires restart to take full effect.")
        desc.setWordWrap(True)
        desc.setObjectName("descriptionLabel")
        layout.addWidget(desc)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Dark", "Light"])
        
        if self.original_theme.lower() == "light":
            self.theme_combo.setCurrentIndex(2) # Light is at index 2
        elif self.original_theme.lower() == "dark":
            self.theme_combo.setCurrentIndex(1) # Dark is at index 1
        else: # System
            self.theme_combo.setCurrentIndex(0) # System is at index 0
            
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        layout.addLayout(theme_layout)
        layout.addStretch()

    def save(self) -> bool:
        theme = self.theme_combo.currentText().lower()
        save_theme(theme)
        return True
    
    def has_theme_changed(self):
        return self.original_theme.lower() != self.theme_combo.currentText().lower()


# ============================================================
# SHARED HELP BOX
# ============================================================

def create_help_box(html_text: str) -> QLabel:
    label = QLabel(html_text)
    label.setTextFormat(Qt.RichText)
    label.setOpenExternalLinks(True)
    label.setWordWrap(True)
    label.setObjectName("helpBox")
    return label


# ============================================================
# SECURE LINE EDIT WITH SHOW / HIDE TOGGLE
# ============================================================

class ApiKeyLineEdit(QLineEdit):
    """
    QLineEdit with clickable show / hide toggle using local eye icons
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setEchoMode(QLineEdit.Password)
        self._visible = False

        # Resolve absolute icon paths (safe for PyInstaller too)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._eye_icon = QIcon(os.path.join(base_dir, "assets", "eye.png"))
        self._eye_off_icon = QIcon(os.path.join(base_dir, "assets", "eye-off.png"))

        self._toggle_action = self.addAction(
            self._eye_icon,QLineEdit.TrailingPosition
        )
        self._toggle_action.setToolTip("Show API key")
        self._toggle_action.triggered.connect(self._toggle_visibility)

        self.setMinimumHeight(28)

    def _toggle_visibility(self):
        cursor_pos = self.cursorPosition()

        self._visible = not self._visible
        self.setEchoMode(
            QLineEdit.Normal if self._visible else QLineEdit.Password
        )

        self._toggle_action.setIcon(
            self._eye_off_icon if self._visible else self._eye_icon
        )
        self._toggle_action.setToolTip(
            "Hide API key" if self._visible else "Show API key"
        )

        self.setCursorPosition(cursor_pos)


# ============================================================
# NVD SETTINGS PANEL
# ============================================================

class NvdSettingsWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("NVD API Key")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        desc = QLabel(
            "The NVD API key is required to fetch CVE data from the "
            "National Vulnerability Database (NIST)."
        )
        desc.setWordWrap(True)
        desc.setObjectName("descriptionLabel")
        layout.addWidget(desc)

        layout.addWidget(QLabel("API Key:"))

        self.key_entry = ApiKeyLineEdit()
        self.key_entry.setPlaceholderText("Paste your NVD API key here")
        self.key_entry.setText(load_existing_nvd_key() or "")
        layout.addWidget(self.key_entry)

        help_box = create_help_box(
            "<b>How to obtain an NVD API key:</b><br><br>"
            "1. Visit: "
            "<a href='https://nvd.nist.gov/developers/request-an-api-key'>"
            "https://nvd.nist.gov/developers/request-an-api-key</a><br><br>"
            "2. Complete the request form<br>"
            "3. Copy the generated API key<br>"
            "4. Paste it here"
        )
        layout.addWidget(help_box)

        layout.addStretch()

    def save(self) -> bool:
        key = self.key_entry.text().strip()
        save_nvd_key_to_all_configs(key)
        return True


# ============================================================
# SONATYPE SETTINGS PANEL
# ============================================================

class SonatypeSettingsWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Sonatype OSS Index API Key")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        desc = QLabel(
            "This API key is required to fetch vulnerability data "
            "from Sonatype OSS Index."
        )
        desc.setWordWrap(True)
        desc.setObjectName("descriptionLabel")
        layout.addWidget(desc)

        layout.addWidget(QLabel("API Key (username:api_token):"))

        self.key_entry = ApiKeyLineEdit()
        self.key_entry.setPlaceholderText("username:api_token")
        self.key_entry.setText(load_existing_sonatype_key() or "")
        layout.addWidget(self.key_entry)

        help_box = create_help_box(
            "<b>How to obtain a Sonatype API key:</b><br><br>"
            "1. Register at:<br>"
            "<a href='https://ossindex.sonatype.org/user/register'>"
            "https://ossindex.sonatype.org/user/register</a><br><br>"
            "2. Log in to OSS Index<br>"
            "3. Copy your <b>API Token</b><br>"
            "4. Enter it in the format:<br>"
            "<code>username:api_token</code>"
        )
        layout.addWidget(help_box)

        layout.addStretch()

    def save(self) -> bool:
        key = self.key_entry.text().strip()
        if key and ":" not in key:
            QMessageBox.critical(
                self,
                "Invalid API Key",
                "Sonatype API key must be in the format:\nusername:api_token"
            )
            return False

        save_api_key_to_all_configs(key)
        return True


# ============================================================
# PREFERENCES DIALOG
# ============================================================

class PreferencesDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(760, 440)
        self.setModal(True)
        self._build_ui()
        self.theme_changed = False

    def _build_ui(self):
        self.nav_list = QListWidget()
        self.nav_list.addItem("NVD API Key")
        self.nav_list.addItem("Sonatype API Key")
        self.nav_list.addItem("Appearance")
        self.nav_list.setFixedWidth(200)

        self.stack = QStackedWidget()
        self.nvd_panel = NvdSettingsWidget()
        self.sonatype_panel = SonatypeSettingsWidget()
        self.appearance_panel = AppearanceSettingsWidget()

        self.stack.addWidget(self.nvd_panel)
        self.stack.addWidget(self.sonatype_panel)
        self.stack.addWidget(self.appearance_panel)

        content_layout = QHBoxLayout()
        content_layout.addWidget(self.nav_list)
        content_layout.addWidget(self.stack)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_all)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        root_layout = QVBoxLayout(self)
        root_layout.addLayout(content_layout)
        root_layout.addLayout(btn_layout)

        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)

    def _save_all(self):
        if not self.nvd_panel.save():
            return

        if not self.sonatype_panel.save():
            return
        
        # Always save appearance settings, even if theme hasn't changed.
        # This will save the last selected value to config.
        self.appearance_panel.save()

        # Check if theme was actually changed from the original loaded theme
        if self.appearance_panel.has_theme_changed():
            QMessageBox.information(
                self,
                "Preferences Saved",
                "All settings have been saved successfully.\n"
                "Please restart the application for theme changes to take effect."
            )
        else:
            QMessageBox.information(
                self,
                "Preferences Saved",
                "All settings have been saved successfully."
            )
            
        self.accept()
