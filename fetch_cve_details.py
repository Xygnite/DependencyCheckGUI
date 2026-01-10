# fetch_cve_details.py

import requests

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QTextEdit, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from nvd_config_mgr import load_nvd_api_key

class CVEDetailsRetriever(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CVE Details Retriever")
        self.setGeometry(200, 200, 1100, 500)


        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "CVE-Details-GUI/1.0"})

        self.setup_ui()

    # === UI SETUP ==========================================================

    def setup_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Enter CVE IDs (comma separated):")
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("e.g., CVE-2021-34527, CVE-2021-34528")

        self.button = QPushButton("Retrieve CVE Details")
        self.button.clicked.connect(self.retrieve_cve_details)

        self.table = QTableWidget()
        # Added 1 extra column for History
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "CVE ID", "Description", "Published Date", "Last Modified Date",
            "Severity", "Vector", "Base Score", "History"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

        layout.addWidget(self.label)
        layout.addWidget(self.input_field)
        layout.addWidget(self.button)
        layout.addWidget(self.table)

        self.setLayout(layout)

    # === CORE LOGIC ========================================================

    def retrieve_cve_details(self):
        text = self.input_field.text().strip()
        cve_ids = [c.strip() for c in text.split(",") if c.strip()]

        self.table.setRowCount(0)
        # This will:
        # - load key if exists
        # - otherwise prompt user with popup
        self.api_key = load_nvd_api_key(self)
        if not cve_ids:
            self.display_message("Please enter at least one CVE ID.")
            return

        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key

        for cve_id in cve_ids:
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
            try:
                response = self.session.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                data = response.json()
                self.display_cve_details(data, cve_id)
            except requests.exceptions.HTTPError as e:
                self.display_message(f"{cve_id}: HTTP error {e.response.status_code}")
            except requests.exceptions.Timeout:
                self.display_message(f"{cve_id}: Request timed out.")
            except Exception as e:
                self.display_message(f"{cve_id}: {str(e)}")

    # === HELPERS ===========================================================

    @staticmethod
    def format_date(date_string):
        return date_string.split("T")[0] if date_string else "N/A"

    @staticmethod
    def get_severity_color(severity):
        if not severity:
            return QColor("transparent")
        color_map = {
            "low": QColor("#2E7D32"),
            "medium": QColor("#FFA000"),
            "high": QColor("#D32F2F"),
            "critical": QColor("#C62828"),
        }
        return color_map.get(severity.lower(), QColor("transparent"))

    def display_cve_details(self, details, original_cve_id=None):
        """
        Fill the main table with CVE details and add a 'History' link/button
        per row to fetch and display the CVE history.
        """
        vulns = details.get("vulnerabilities") or []
        if not vulns:
            self.display_message(
                f"No vulnerabilities found for {original_cve_id}."
                if original_cve_id else "No vulnerabilities found for the given CVE ID."
            )
            return

        for vuln in vulns:
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", original_cve_id or "N/A")

            descriptions = cve.get("descriptions") or []
            description = descriptions[0].get("value", "N/A") if descriptions else "N/A"

            published = self.format_date(cve.get("published"))
            modified = self.format_date(cve.get("lastModified"))

            metrics = cve.get("metrics", {})
            metric_list = (
                metrics.get("cvssMetricV31")
                or metrics.get("cvssMetricV30")
                or metrics.get("cvssMetricV2")
                or []
            )
            cvss_data = metric_list[0].get("cvssData", {}) if metric_list else {}

            severity = cvss_data.get("baseSeverity", "N/A")
            vector = cvss_data.get("vectorString", "N/A")
            base_score = cvss_data.get("baseScore", "N/A")

            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)

            data = [cve_id, description, published, modified, severity, vector, str(base_score)]

            # Regular columns
            for col, item in enumerate(data):
                table_item = QTableWidgetItem(item)
                if col == 4:  # Severity column
                    table_item.setBackground(self.get_severity_color(severity))
                self.table.setItem(row_pos, col, table_item)

            # History column: add a clickable "View" button
            history_btn = QPushButton("View")
            history_btn.setCursor(Qt.PointingHandCursor)
            history_btn.setProperty("cve_id", cve_id)
            history_btn.clicked.connect(self.on_history_clicked)
            self.table.setCellWidget(row_pos, 7, history_btn)

    def display_message(self, message):
        row_pos = self.table.rowCount()
        self.table.insertRow(row_pos)

        msg_item = QTableWidgetItem(message)
        self.table.setItem(row_pos, 0, msg_item)
        self.table.setSpan(row_pos, 0, 1, self.table.columnCount())

    # === HISTORY HANDLING ===================================================

    def on_history_clicked(self):
        """Slot called when a 'View' history button is clicked."""
        btn = self.sender()
        if not btn:
            return
        cve_id = btn.property("cve_id")
        if not cve_id:
            return
        self.fetch_and_show_history(cve_id)

    def fetch_and_show_history(self, cve_id: str):
        """Call the NVD CVE History API and show the result in a popup."""
        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key

        url = f"https://services.nvd.nist.gov/rest/json/cvehistory/2.0?cveId={cve_id}"
        try:
            resp = self.session.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            self.show_history_dialog(cve_id, data)
        except requests.exceptions.HTTPError as e:
            QMessageBox.critical(self, "Error", f"{cve_id}: HTTP error {e.response.status_code}")
        except requests.exceptions.Timeout:
            QMessageBox.critical(self, "Error", f"{cve_id}: Request timed out.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"{cve_id}: {str(e)}")

    def show_history_dialog(self, cve_id: str, data: dict):
        """Create and show a dialog with nicely formatted CVE history."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"CVE History - {cve_id}")
        dialog.resize(900, 500)

        layout = QVBoxLayout(dialog)

        # Text area with formatted history
        history_text = QTextEdit()
        history_text.setReadOnly(True)
        history_text.setPlainText(self.format_history_text(data))
        layout.addWidget(history_text)

        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addStretch(1)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        dialog.exec_()

    def format_history_text(self, data: dict) -> str:
        """Convert the CVE history JSON into a readable text representation."""
        lines = []

        total_results = data.get("totalResults", "N/A")
        results_per_page = data.get("resultsPerPage", "N/A")
        timestamp = data.get("timestamp", "N/A")
        fmt = data.get("format", "N/A")
        version = data.get("version", "N/A")

        lines.append(f"Format   : {fmt} (v{version})")
        lines.append(f"Results  : {total_results} (per page: {results_per_page})")
        lines.append(f"Timestamp: {timestamp}")
        lines.append("")

        changes = data.get("cveChanges") or []
        if not changes:
            lines.append("No history entries found for this CVE.")
            return "\n".join(lines)

        for idx, change_wrapper in enumerate(changes, start=1):
            change = change_wrapper.get("change", {})
            event_name = change.get("eventName", "N/A")
            change_id = change.get("cveChangeId", "N/A")
            source = change.get("sourceIdentifier", "N/A")
            created = change.get("created", "N/A")

            lines.append(f"=== Change {idx} ===")
            lines.append(f"Event   : {event_name}")
            lines.append(f"Change ID: {change_id}")
            lines.append(f"Source  : {source}")
            lines.append(f"Created : {created}")

            details = change.get("details") or []
            if details:
                lines.append("Details:")
                for d in details:
                    action = d.get("action", "")
                    d_type = d.get("type", "")
                    old_val = d.get("oldValue")
                    new_val = d.get("newValue")

                    lines.append(f"  - [{action}] {d_type}")
                    if old_val:
                        lines.append(f"      Old: {old_val}")
                    if new_val:
                        lines.append(f"      New: {new_val}")
            else:
                lines.append("Details: (none)")

            lines.append("")  # blank line between changes

        return "\n".join(lines)
