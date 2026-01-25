import os
import subprocess
from datetime import datetime

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QLabel,
    QSizePolicy,
    QHeaderView,
)


class ReportListWidget(QWidget):
    """
    Displays generated reports in a sortable list with quick-open support.
    Double-click opens the report in the system viewer; single selection
    highlights it within the list.
    """

    SUPPORTED_EXTENSIONS = {".html", ".htm", ".csv", ".xml"}

    report_selected = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, reports_dir="Reports"):
        super().__init__(parent)
        self.reports_dir = os.path.abspath(reports_dir)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.status_label = QLabel("No reports available.")
        self.status_label.setObjectName("reportStatusLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(self.status_label)

        load_btn = QPushButton("Browse...")
        load_btn.clicked.connect(self._browse_for_report)
        toolbar.addWidget(load_btn, 0, Qt.AlignRight)

        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Report", "Generated"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._emit_selection)
        self.table.itemDoubleClicked.connect(self._open_selected)
        layout.addWidget(self.table, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self, select_path=None):
        """
        Reload report list from disk. Optionally select a specific report path.
        """
        reports = self._collect_reports()
        self.table.setRowCount(len(reports))

        for row, (path, display_name, timestamp) in enumerate(reports):
            name_item = QTableWidgetItem(display_name)
            name_item.setData(Qt.UserRole, path)
            date_item = QTableWidgetItem(timestamp)
            date_item.setData(Qt.UserRole, path)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, date_item)

        if reports:
            self.status_label.setText(f"{len(reports)} report(s) available.")
        else:
            self.status_label.setText("No reports available.")

        if select_path:
            self._select_report(select_path)
        elif reports:
            self.table.selectRow(0)
        else:
            self.table.clearSelection()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _collect_reports(self):
        if not os.path.isdir(self.reports_dir):
            return []

        entries = []
        for name in os.listdir(self.reports_dir):
            full_path = os.path.abspath(os.path.join(self.reports_dir, name))
            if not os.path.isfile(full_path):
                continue

            ext = os.path.splitext(name)[1].lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                continue

            try:
                mtime = os.path.getmtime(full_path)
            except OSError:
                continue

            timestamp = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            entries.append((full_path, name, timestamp, mtime))

        entries.sort(key=lambda item: item[3], reverse=True)
        return [(path, name, timestamp) for path, name, timestamp, _ in entries]

    def _select_report(self, path):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == path:
                self.table.selectRow(row)
                self.table.scrollToItem(item, QTableWidget.PositionAtCenter)
                return

    def _emit_selection(self):
        items = self.table.selectedItems()
        if not items:
            return
        path = items[0].data(Qt.UserRole)
        if path:
            self.report_selected.emit(path)

    def _open_selected(self, item):
        path = item.data(Qt.UserRole)
        if not path or not os.path.exists(path):
            return
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            # Silently ignore; double-click is best-effort.
            pass

    def _browse_for_report(self):
        start_dir = os.path.abspath(self.reports_dir)
        if not os.path.isdir(start_dir):
            start_dir = os.getcwd()

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Report",
            start_dir,
            "Reports (*.html *.htm *.csv *.xml);;All Files (*)",
        )
        if path:
            self.refresh(select_path=path)
