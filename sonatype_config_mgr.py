import os
import xml.etree.ElementTree as ET

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt

CONFIG_NAME = "configuration.xml"
SONATYPE_KEY_TAG = "sonatype_api_key"
API_KEYS_TAG = "api_keys"


# --------------------------------------------------
# Config helpers
# --------------------------------------------------

def get_config_paths():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.join(base_dir, CONFIG_NAME),
        os.path.join(base_dir, "_internal", CONFIG_NAME)
    ]


def load_existing_sonatype_key():
    for path in get_config_paths():
        if not os.path.exists(path):
            continue

        try:
            tree = ET.parse(path)
            root = tree.getroot()

            api_keys = root.find(API_KEYS_TAG)
            if api_keys is None:
                continue

            node = api_keys.find(SONATYPE_KEY_TAG)
            if node is not None and node.text:
                return node.text.strip()

        except ET.ParseError:
            pass

    return None



def save_api_key_to_all_configs(api_key):
    for path in get_config_paths():
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if os.path.exists(path):
            tree = ET.parse(path)
            root = tree.getroot()
        else:
            root = ET.Element("configuration")
            tree = ET.ElementTree(root)

        api_keys = root.find(API_KEYS_TAG)
        if api_keys is None:
            api_keys = ET.SubElement(root, API_KEYS_TAG)

        node = api_keys.find(SONATYPE_KEY_TAG)
        if node is None:
            node = ET.SubElement(api_keys, SONATYPE_KEY_TAG)

        node.text = api_key
        tree.write(path, encoding="utf-8", xml_declaration=True)



# --------------------------------------------------
# Custom Dialog
# --------------------------------------------------

class SonatypeApiKeyDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Sonatype API Key")
        self.setModal(True)
        self.resize(520, 260)

        self.saved_key = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ===== Header =====
        title = QLabel("Sonatype OSS Index – API Key")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel(
            "This API key is required to fetch vulnerability information "
            "from Sonatype OSS Index."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #555;")
        layout.addWidget(subtitle)

        # ===== Input =====
        layout.addSpacing(6)
        input_label = QLabel("API Key (format: username:api_token)")
        layout.addWidget(input_label)

        self.key_entry = QLineEdit()
        self.key_entry.setPlaceholderText("username:api_token")
        self.key_entry.setText(load_existing_sonatype_key() or "")
        self.key_entry.setMinimumHeight(28)
        self.key_entry.setStyleSheet(
            "QLineEdit { padding: 4px; font-family: Consolas; }"
        )
        layout.addWidget(self.key_entry)

        # ===== Help Box =====
        help_box = QLabel(
            "<b>How to obtain a Sonatype API key:</b><br><br>"
            "1. Register at:<br>"
            "<a href='https://ossindex.sonatype.org/user/register'>"
            "https://ossindex.sonatype.org/user/register</a><br><br>"
            "2. Log in to OSS Index<br>"
            "3. Copy your <b>API Token</b><br>"
            "4. Enter it here in the format:<br>"
            "<code>username:api_token</code>"
        )
        help_box.setTextFormat(Qt.RichText)
        help_box.setOpenExternalLinks(True)
        help_box.setWordWrap(True)
        help_box.setStyleSheet("""
            QLabel {
                background-color: #f7f7f7;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout.addWidget(help_box)

        # ===== Buttons =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _save(self):
        text = self.key_entry.text().strip()

        if not text or ":" not in text:
            QMessageBox.critical(
                self,
                "Invalid API Key",
                "Sonatype API key must be in the format:\nusername:api_token"
            )
            return

        save_api_key_to_all_configs(text)
        self.saved_key = text
        self.accept()


# --------------------------------------------------
# Public API (used by main.py & scanners)
# --------------------------------------------------

def open_sonatype_api_key_dialog(parent=None):
    dialog = SonatypeApiKeyDialog(parent)
    result = dialog.exec_()

    if result == QDialog.Accepted:
        return True, dialog.saved_key

    return False, load_existing_sonatype_key()


def load_sonatype_api_key(parent=None):
    key = load_existing_sonatype_key()
    if key:
        return key

    saved, key = open_sonatype_api_key_dialog(parent)
    return key
