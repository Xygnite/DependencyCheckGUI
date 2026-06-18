import os
import datetime
import subprocess

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTextEdit, QAction, QFileDialog,
    QMessageBox, QRadioButton, QButtonGroup, QGroupBox, QFormLayout, QFrame,
    QProgressBar, QTabWidget, QCheckBox
)
from fetch_cve_details import CVEDetailsRetriever
from jar_vulnerability_finder import JarVulnerabilityScanner
from dependency_check_manager import DependencyCheckManager
from preferences_dialog import PreferencesDialog
from nvd_config_mgr import load_nvd_api_key
from theme_manager import load_theme, get_stylesheet
from diagnostics_panel import DiagnosticsDialog
from report_browser import ReportListWidget


# ======================= QTHREAD WORKER ================================

class ScanWorker(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(str)

    def __init__(self, command, log_file, output_file):
        super().__init__()
        self.command = command
        self.log_file = log_file
        self.output_file = output_file

    @QtCore.pyqtSlot()
    def run(self):
        try:
            with open(self.log_file, "w", encoding="utf-8") as lf:
                lf.write(f"Command: {self.command}\n\n")
                process = subprocess.Popen(
                    self.command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    text=True
                )
                for line in iter(process.stdout.readline, ""):
                    self.log.emit(line.strip())
                    lf.write(line)
                process.wait()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit(self.output_file)

# ======================= MAIN GUI ======================================

class DependencyCheckGUI(QMainWindow):

    REPORTS_DIR = "Reports"
    LOGS_DIR = "Logs"
    SCA_TEMPLATES_DIR = "SCA_Jar_Templates"
    BACKUPS_DIR = "Backups"

    def __init__(self):
        super().__init__()
        self.dc_manager = DependencyCheckManager(self)
        self.scan_mode = "folder"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(base_dir, "assets", "DC.ico")
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        self._error_actions = {}
        self._init_ui()
        self._ensure_folders()
        self.report_list.refresh()

    # ======================= UI SETUP ==================================

    def _init_ui(self):
        self.setWindowTitle("Dependency Check GUI")

        self.setWindowIcon(QtGui.QIcon(self.icon_path))

        central = QWidget(self)
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(24, 24, 24, 24)
        central_layout.setSpacing(20)
        central.setLayout(central_layout)
        self.setCentralWidget(central)

        central_layout.addWidget(self._build_header())
        central_layout.addWidget(self._build_scan_group())
        central_layout.addWidget(self._build_execution_row())
        insights_group = self._build_insights_group()
        central_layout.addWidget(insights_group, 1)

        self.menu_bar = self.menuBar()
        self._build_menus()

    # ======================= MENU BAR ==================================

    def _build_menus(self):
        file_menu = self.menu_bar.addMenu("File")
        file_menu.addAction("Open Reports", lambda: self._open_folder(self.REPORTS_DIR))
        file_menu.addAction("Open Logs", lambda: self._open_folder(self.LOGS_DIR))

        options_menu = file_menu.addMenu("Options")
        options_menu.addAction("Purge NVD Data", self.dc_manager.purge_NVD_data)

        pref_menu = file_menu.addMenu("Settings")
        pref_menu.addAction("Preferences", self.open_preferences)

        file_menu.addSeparator()
        file_menu.addAction("Exit", QApplication.quit)

        tools_menu = self.menu_bar.addMenu("Tools")
        tools_menu.addAction("CVE Details", self.fetch_cve_details)
        tools_menu.addAction("Jar Vulnerability Finder", self.jar_vulnerability_finder)

        help_menu = self.menu_bar.addMenu("Help")
        help_menu.addAction("Update DC Tools", self.dc_manager.download_dependency_check)
        help_menu.addAction("Check DC Tools Version", self.dc_manager.check_dctools_version)
        help_menu.addAction("Diagnostics", self.open_diagnostics)
        help_menu.addAction("About", self.show_about)

    # ======================= MODE HANDLING ==============================

    def _build_header(self):
        frame = QFrame()
        frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(frame)
        header_layout.setContentsMargins(18, 18, 18, 18)
        header_layout.setSpacing(18)

        icon_label = QLabel()
        icon_pixmap = QtGui.QPixmap(self.icon_path)
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(56, 56, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        icon_label.setObjectName("headerIcon")

        text_container = QVBoxLayout()
        text_container.setSpacing(2)
        text_container.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Dependency Check GUI")
        title.setObjectName("appTitle")
        subtitle = QLabel("Orchestrate OWASP Dependency-Check scans with guided configuration and live insight.")
        subtitle.setObjectName("taglineLabel")
        subtitle.setWordWrap(True)
        text_container.addWidget(title)
        text_container.addWidget(subtitle)

        header_layout.addWidget(icon_label, 0, QtCore.Qt.AlignTop)
        header_layout.addLayout(text_container)
        header_layout.addStretch()
        return frame

    def _build_scan_group(self):
        group = QGroupBox("Scan Configuration")
        group.setObjectName("scanConfigGroup")
        form = QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        form.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        form.setSpacing(14)

        # Scan mode
        mode_widget = QWidget()
        mode_layout = QHBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(16)

        self.rb_folder = QRadioButton("Folder")
        self.rb_files = QRadioButton("Files")
        self.rb_folder.setChecked(True)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.rb_folder)
        self.mode_group.addButton(self.rb_files)

        self.rb_folder.toggled.connect(self._on_mode_change)

        mode_layout.addWidget(self.rb_folder)
        mode_layout.addWidget(self.rb_files)
        mode_layout.addStretch()
        form.addRow("Scan Mode:", mode_widget)

        # Scan target path
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(12)

        self.path_label = QLabel("Folder to scan:")
        self.path_entry = QLineEdit()
        self.path_entry.setPlaceholderText("Select a folder or provide comma-separated files")
        self.path_btn = QPushButton("Browse...")
        self.path_btn.clicked.connect(self._browse_path)
        self.path_entry.textChanged.connect(lambda: self._clear_field_error(self.path_entry))

        path_layout.addWidget(self.path_entry)
        path_layout.addWidget(self.path_btn)

        form.addRow(self.path_label, path_widget)

        # Project name
        self.project_entry = QLineEdit()
        self.project_entry.setPlaceholderText("Name used for generated reports and logs")
        self.project_entry.textChanged.connect(lambda: self._clear_field_error(self.project_entry))
        form.addRow("Project Name:", self.project_entry)

        # Report format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["HTML", "CSV", "XML"])
        form.addRow("Report Format:", self.format_combo)

        # Skip Update
        mode_widget = QWidget()
        mode_layout = QHBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(16)

        self.checkSkipUpdate = QCheckBox(" ")

        mode_layout.addWidget(self.checkSkipUpdate)
        mode_layout.addStretch()
        form.addRow("Skip Update (NOT RECOMMENDED):", mode_widget)

        group.setLayout(form)
        return group

    def _build_execution_row(self):
        frame = QFrame()
        frame.setObjectName("executionFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.scan_btn = QPushButton("Start Scan")
        self.scan_btn.setMinimumWidth(160)
        self.scan_btn.clicked.connect(self.start_scan)

        self.scan_progress = QProgressBar()
        self.scan_progress.setRange(0, 1)
        self.scan_progress.setValue(0)
        self.scan_progress.setTextVisible(False)
        self.scan_progress.setMinimumWidth(320)

        hint = QLabel("Reports and logs will be timestamped and saved automatically.")
        hint.setObjectName("executionHint")
        hint.setWordWrap(True)

        layout.addWidget(self.scan_btn)
        layout.addWidget(self.scan_progress, 1)
        layout.addWidget(hint, 2)
        return frame

    def _build_insights_group(self):
        group = QGroupBox("Insights")
        group.setObjectName("insightsGroup")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.insights_tabs = QTabWidget()

        self.output = QTextEdit(readOnly=True)
        self.output.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.output.setPlaceholderText("Scan output and Dependency-Check messages will appear here.")

        self.report_list = ReportListWidget(self, reports_dir=self.REPORTS_DIR)
        self.report_list.report_selected.connect(self._on_report_selected)

        self.insights_tabs.addTab(self.output, "Activity Log")
        self.insights_tabs.addTab(self.report_list, "Reports")

        layout.addWidget(self.insights_tabs)
        group.setLayout(layout)
        return group

    def _on_mode_change(self):
        if self.rb_folder.isChecked():
            self.scan_mode = "folder"
            self.path_label.setText("Folder to scan:")
        else:
            self.scan_mode = "files"
            self.path_label.setText("Files to scan:")
        self.path_entry.clear()

    def _browse_path(self):
        if self.scan_mode == "folder":
            folder = QFileDialog.getExistingDirectory(self, "Select Folder")
            if folder:
                self.path_entry.setText(folder)
        else:
            files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
            if files:
                self.path_entry.setText(",".join(files))

    # ======================= SCAN LOGIC ================================

    def start_scan(self):

        # CLEAR OUTPUT WINDOW BEFORE EACH SCAN
        self.output.clear()

        project = self.project_entry.text().strip()
        target = self.path_entry.text().strip()
        self._clear_input_errors()

        first_invalid = None
        if not project:
            self._set_input_error(self.project_entry, "Project name is required before running a scan.")
            first_invalid = first_invalid or self.project_entry
        if not target:
            self._set_input_error(self.path_entry, "Provide a folder path or file list to scan.")
            first_invalid = first_invalid or self.path_entry

        if first_invalid:
            first_invalid.setFocus()
            self._flash_status("Please address the highlighted fields.", duration=4000)
            return

        dc_path = self.dc_manager.get_dc_bat_path()
        if not os.path.exists(dc_path):
            QMessageBox.critical(self, "Error", "Dependency Check not found.")
            self._flash_status("Dependency-Check tools not available.")
            return

        scan_paths = (
            [target] if self.scan_mode == "folder"
            else [p.strip() for p in target.split(",")]
        )

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fmt = self.format_combo.currentText().upper()

        out_file = os.path.abspath(
            os.path.join(self.REPORTS_DIR, f"{project}_{ts}.{fmt.lower()}")
        )
        log_file = os.path.abspath(
            os.path.join(self.LOGS_DIR, f"{project}_{ts}.log")
        )

        cmd = [dc_path, "--project", project]
        for p in scan_paths:
            cmd += ["--scan", os.path.abspath(p)]
        cmd += ["--out", out_file, "--format", fmt]

        # CONFIG MANAGER INJECTION
        api_key = load_nvd_api_key(self)
        if api_key:
            cmd += ["--nvdApiKey", api_key]

        if self.checkSkipUpdate.isChecked():
            cmd += ["--noupdate"]

        command = " ".join(f'"{c}"' if " " in c else c for c in cmd)
        self.output.append(f"Running:\n{command}\n")
        self.scan_progress.setRange(0, 0)
        self._flash_status("Dependency-Check scan in progress...", duration=0)

        self._run_thread(command, log_file, out_file)

    # ======================= THREAD ================================

    def _run_thread(self, command, log_file, out_file):
        self.thread = QtCore.QThread(self)
        self.worker = ScanWorker(command, log_file, out_file)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.append_output)
        self.worker.error.connect(self.append_output)
        self.worker.finished.connect(self._scan_finished)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.scan_btn.setEnabled(False)
        self.thread.start()

    def _scan_finished(self, report):
        self.scan_btn.setEnabled(True)
        self.scan_progress.setRange(0, 1)
        self.scan_progress.setValue(0)
        self._flash_status("Scan complete! Report ready.", duration=4000)
        self.report_list.refresh(select_path=report)
        self.insights_tabs.setCurrentWidget(self.report_list)
        QMessageBox.information(self, "Scan Complete", f"Report saved:\n{report}")

    # ======================= CONFIG / API KEY ===========================

    def open_preferences(self):
        dlg = PreferencesDialog(self)
        dlg.exec_()
        self.report_list.refresh()

    def open_diagnostics(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dlg = DiagnosticsDialog(self, base_dir=base_dir)
        dlg.exec_()
        self.report_list.refresh()

    def append_output(self, text):
        self.output.append(text)

    def _on_report_selected(self, path):
        name = os.path.basename(path)
        self._flash_status(f"Selected report: {name}", duration=4000)

    def _flash_status(self, message, duration=3000):
        """
        Show a status-bar message for a fixed duration (0 = persistent)
        before returning to the default Ready state.
        """
        if duration == 0:
            self.status_bar.showMessage(message)
            return

        self.status_bar.showMessage(message)
        QtCore.QTimer.singleShot(duration, lambda: self.status_bar.showMessage("Ready"))

    # ======================= UTILITIES ================================

    def _set_input_error(self, widget, message):
        """
        Mark a field as invalid by showing a warning icon, tooltip, and error border.
        """
        if widget in self._error_actions:
            widget.setToolTip(message)
            return

        warning_icon = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        action = widget.addAction(warning_icon, QtWidgets.QLineEdit.TrailingPosition)
        self._error_actions[widget] = action
        widget.setProperty("hasError", True)
        widget.setToolTip(message)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _clear_field_error(self, widget):
        """
        Remove the error visuals for a specific field once the user starts correcting it.
        """
        action = self._error_actions.pop(widget, None)
        if action:
            widget.removeAction(action)
        widget.setProperty("hasError", False)
        widget.setToolTip("")
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _clear_input_errors(self):
        """
        Clear any lingering error indicators before validating anew.
        """
        for widget in list(self._error_actions.keys()):
            self._clear_field_error(widget)

    def _ensure_folders(self):
        for d in (
            self.REPORTS_DIR,
            self.LOGS_DIR,
            self.SCA_TEMPLATES_DIR,
            self.BACKUPS_DIR,
            DependencyCheckManager.DC_DIR,
        ):
            os.makedirs(d, exist_ok=True)

    def _open_folder(self, folder):
        path = os.path.abspath(folder)
        if os.name == "nt":
            subprocess.run(["explorer", path])
        else:
            subprocess.run(["xdg-open", path])

    def show_about(self):
        QMessageBox.about(
            self,
            "About Dependency Check GUI",
            (
                "<h3>Dependency Check GUI</h3>"
                "<p><b>Version:</b> 1.3</p>"
                "<p>A lightweight GUI interface for managing OWASP Dependency Check scans.</p>"
                "<p>This tool provides a user-friendly interface for Windows users to download and run "
                "OWASP Dependency Check command-line tools and generate reports.</p>"
                "<p>It simplifies the use of Dependency Check by abstracting the complexity of the command-line.</p>"
                "<p><b>Developed by:</b> Vaibhav Patil</p>"
            )
        )

    def fetch_cve_details(self):
        self.cve_win = CVEDetailsRetriever()
        self.cve_win.show()

    def jar_vulnerability_finder(self):
        self.jar_win = JarVulnerabilityScanner()
        self.jar_win.show()


# ======================= APP START =====================================

if __name__ == "__main__":
    app = QApplication([])
    app.setWindowIcon(QtGui.QIcon("assets/DC.ico"))

    # Load and apply theme
    theme = load_theme()
    stylesheet = get_stylesheet(theme)
    if stylesheet:
        app.setStyleSheet(stylesheet)

    gui = DependencyCheckGUI()
    gui.resize(1020, 820)
    gui.show()

    gui.dc_manager.check_dctools_version_startup()
    app.exec_()
