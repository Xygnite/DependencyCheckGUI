import os
import xml.etree.ElementTree as ET
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox
)

CONFIG_NAME = "configuration.xml"
NVD_KEY_TAG = "nvd_api_key"
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


def load_existing_nvd_key():
    for path in get_config_paths():
        if not os.path.exists(path):
            continue

        try:
            tree = ET.parse(path)
            root = tree.getroot()

            api_keys = root.find(API_KEYS_TAG)
            if api_keys is None:
                continue

            node = api_keys.find(NVD_KEY_TAG)
            if node is not None and node.text:
                return node.text.strip()

        except ET.ParseError:
            pass

    return None



def save_nvd_key_to_all_configs(api_key):
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

        node = api_keys.find(NVD_KEY_TAG)
        if node is None:
            node = ET.SubElement(api_keys, NVD_KEY_TAG)

        node.text = api_key
        tree.write(path, encoding="utf-8", xml_declaration=True)



# --------------------------------------------------
# Dialog
# --------------------------------------------------

class NvdApiKeyDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set NVD API Key")
        self.resize(420, 270)

        self.saved_key = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("NVD API Key:"))

        self.key_entry = QLineEdit()
        self.key_entry.setText(load_existing_nvd_key() or "")
        layout.addWidget(self.key_entry)

        info = QLabel(
            "<b>You can generate an NVD API key here:</b><br>"
            "<a href='https://nvd.nist.gov/developers/request-an-api-key'>"
            "https://nvd.nist.gov/developers/request-an-api-key</a><br><br>"

            "<b>Note:</b> Saving the NVD API key is a <b>one-time setup</b>. "
            "Once saved, you will <b>not be asked again</b> in future runs of this tool.<br><br>"

            "<p style='color:#a94442;'>"
            "If you click <b>Cancel</b> without adding an API key, the tool will run "
            "without an NVD API key. This is <b>strongly discouraged</b> because "
            "requests will be <b>extremely slow or fail</b> due to strict rate limits imposed by NVD."
            "</p>"
        )

        # These three lines are REQUIRED
        info.setTextFormat(Qt.RichText)
        info.setOpenExternalLinks(True)
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self):
        key = self.key_entry.text().strip()
        if not key:
            QMessageBox.warning(self, "Invalid Input", "API key cannot be empty.")
            return

        save_nvd_key_to_all_configs(key)
        self.saved_key = key
        self.accept()


# --------------------------------------------------
# Public API
# --------------------------------------------------

def open_nvd_api_key_dialog(parent=None):
    dialog = NvdApiKeyDialog(parent)
    result = dialog.exec_()

    if result == QDialog.Accepted:
        return True, dialog.saved_key

    return False, load_existing_nvd_key()


def load_nvd_api_key(parent=None):
    key = load_existing_nvd_key()
    if key:
        return key

    saved, key = open_nvd_api_key_dialog(parent)
    return key
