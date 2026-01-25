import os
import shutil
import subprocess
from typing import Tuple

import requests
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QWidget,
    QSizePolicy,
)

from nvd_config_mgr import load_existing_nvd_key


class DiagnosticsDialog(QDialog):
    """
    Presents a one-click diagnostics summary that verifies the local environment
    before Dependency-Check scans run.
    """

    DIAGNOSTIC_ORDER = (
        "Java Availability",
        "Disk Space",
        "NVD Connectivity",
    )

    def __init__(self, parent: QWidget = None, base_dir: str = None):
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.resize(640, 360)
        self.base_dir = base_dir or os.getcwd()
        self._build_ui()
        self._run_all_checks()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        intro = QLabel(
            "Run diagnostics to confirm Java availability, free disk space, "
            "and NVD API reachability before executing Dependency-Check."
        )
        intro.setWordWrap(True)
        intro.setObjectName("diagnosticsIntroLabel")
        layout.addWidget(intro)

        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["Check", "Status", "Details"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        layout.addWidget(self.table, 1)

        self.result_summary = QLabel("")
        self.result_summary.setObjectName("diagnosticsSummaryLabel")
        self.result_summary.setWordWrap(True)
        self.result_summary.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        layout.addWidget(self.result_summary)

        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self.run_button = QPushButton("Run Diagnostics")
        self.run_button.clicked.connect(self._run_all_checks)
        btn_bar.addWidget(self.run_button)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(close_btn)

        layout.addLayout(btn_bar)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def _run_all_checks(self):
        self.run_button.setEnabled(False)
        self.table.setRowCount(0)

        results = []
        results.append(("Java Availability",) + self._check_java_version())
        results.append(("Disk Space",) + self._check_disk_space())
        results.append(("NVD Connectivity",) + self._check_nvd_connectivity())

        for check_name, status, detail in results:
            self._append_result(check_name, status, detail)

        worst = self._worst_status(results)
        summary_text = {
            "OK": "All diagnostics completed successfully.",
            "Warning": "Diagnostics completed with warnings. Review the details above before scanning.",
            "Error": "Diagnostics detected errors that may block scans. Resolve the issues above first.",
        }.get(worst, "Diagnostics finished. Review the results above.")
        self.result_summary.setText(summary_text)
        self._style_summary(worst)
        self.run_button.setEnabled(True)

    def _append_result(self, check_name: str, status: str, detail: str):
        row = self.table.rowCount()
        self.table.insertRow(row)

        check_item = QTableWidgetItem(check_name)
        status_item = QTableWidgetItem(status)
        detail_item = QTableWidgetItem(detail)

        status_item.setTextAlignment(Qt.AlignCenter)
        status_item.setData(Qt.UserRole, status)
        status_item.setForeground(self._status_color(status))

        self.table.setItem(row, 0, check_item)
        self.table.setItem(row, 1, status_item)
        self.table.setItem(row, 2, detail_item)

    @staticmethod
    def _status_color(status: str) -> QColor:
        palette = {
            "OK": QColor("#2E7D32"),
            "Warning": QColor("#FFA000"),
            "Error": QColor("#D32F2F"),
        }
        return palette.get(status, QColor("#CCCCCC"))

    @staticmethod
    def _worst_status(results) -> str:
        ordering = {"OK": 0, "Warning": 1, "Error": 2}
        worst = 0
        for _, status, _ in results:
            worst = max(worst, ordering.get(status, 1))
        inverse = {v: k for k, v in ordering.items()}
        return inverse.get(worst, "Warning")

    def _style_summary(self, status: str):
        color = self._status_color(status)
        palette = self.result_summary.palette()
        palette.setColor(self.result_summary.foregroundRole(), color)
        self.result_summary.setPalette(palette)

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_java_version(self) -> Tuple[str, str]:
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            return "Error", "Java executable not found. Install Java 11+ and ensure it is on PATH."
        except subprocess.SubprocessError as exc:
            return "Error", f"Unable to run java -version: {exc}"

        output = (result.stderr or result.stdout or "").strip()
        first_line = output.splitlines()[0] if output else "java -version executed."

        if result.returncode == 0:
            return "OK", first_line
        return "Warning", f"java -version returned {result.returncode}: {first_line}"

    def _check_disk_space(self) -> Tuple[str, str]:
        try:
            usage = shutil.disk_usage(self.base_dir)
        except FileNotFoundError:
            return "Error", f"Unable to calculate disk usage for {self.base_dir}."
        except OSError as exc:
            return "Error", f"Disk usage check failed: {exc}"

        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        if free_gb >= 2:
            status = "OK"
        elif free_gb >= 1:
            status = "Warning"
        else:
            status = "Error"

        detail = f"Free space: {free_gb:.2f} GB of {total_gb:.2f} GB total."
        if status != "OK":
            detail += " A minimum of 2 GB free space is recommended for database updates."
        return status, detail

    def _check_nvd_connectivity(self) -> Tuple[str, str]:
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=dependency-check&resultsPerPage=1"
        headers = {
            "User-Agent": "DependencyCheckGUI-Diagnostics/1.0",
        }

        api_key = load_existing_nvd_key()
        if api_key:
            headers["apiKey"] = api_key

        try:
            resp = requests.get(url, headers=headers, timeout=8)
        except requests.Timeout:
            return "Error", "Timed out while reaching NVD services."
        except requests.RequestException as exc:
            return "Error", f"NVD connectivity failed: {exc}"

        if resp.status_code == 200:
            return "OK", "NVD API responded successfully."

        if resp.status_code == 403:
            return "Warning", "Received HTTP 403 from NVD. Verify API key and request frequency."

        return "Warning", f"NVD API returned HTTP {resp.status_code}."

