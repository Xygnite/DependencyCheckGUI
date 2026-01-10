import os
import datetime
import subprocess

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTextEdit, QMenuBar,
    QAction, QFileDialog, QMessageBox, QRadioButton, QButtonGroup
)
from fetch_cve_details import CVEDetailsRetriever
from jar_vulnerability_finder import JarVulnerabilityScanner
from dependency_check_manager import DependencyCheckManager
from preferences_dialog import PreferencesDialog
from nvd_config_mgr import load_nvd_api_key
from theme_manager import load_theme, get_stylesheet


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

class DependencyCheckGUI(QWidget):

    REPORTS_DIR = "Reports"
    LOGS_DIR = "Logs"
    SCA_TEMPLATES_DIR = "SCA_Jar_Templates"
    BACKUPS_DIR = "Backups"

    def __init__(self):
        super().__init__()
        self.dc_manager = DependencyCheckManager(self)
        self.scan_mode = "folder"
        self._init_ui()
        self._ensure_folders()

    # ======================= UI SETUP ==================================

    def _init_ui(self):
        self.setWindowTitle("Dependency Check GUI")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "assets", "DC.ico")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        layout = QVBoxLayout(self)

        # ---------------- Menu Bar ----------------
        self.menu_bar = QMenuBar(self)
        self._build_menus()
        layout.setMenuBar(self.menu_bar)

        # ---------------- Scan Mode ----------------
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Scan Mode:"))

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
        layout.addLayout(mode_layout)

        # ---------------- Unified Path ----------------
        path_layout = QHBoxLayout()
        self.path_label = QLabel("Folder to scan:")
        self.path_entry = QLineEdit()
        self.path_btn = QPushButton("Select")
        self.path_btn.clicked.connect(self._browse_path)

        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_entry)
        path_layout.addWidget(self.path_btn)
        layout.addLayout(path_layout)

        # ---------------- Project Name ----------------
        project_layout = QHBoxLayout()
        project_layout.addWidget(QLabel("Project Name:"))
        self.project_entry = QLineEdit()
        project_layout.addWidget(self.project_entry)
        layout.addLayout(project_layout)

        # ---------------- Report Format ----------------
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Report Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["HTML", "CSV", "XML"])
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)

        # ---------------- Scan Button ----------------
        self.scan_btn = QPushButton("Start Scan")
        self.scan_btn.clicked.connect(self.start_scan)
        layout.addWidget(self.scan_btn)

        # ---------------- Output ----------------
        self.output = QTextEdit(readOnly=True)
        layout.addWidget(self.output)

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
        help_menu.addAction("About", self.show_about)

    # ======================= MODE HANDLING ==============================

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

        # ✅ CLEAR OUTPUT WINDOW BEFORE EACH SCAN
        self.output.clear()

        project = self.project_entry.text().strip()
        target = self.path_entry.text().strip()

        if not project or not target:
            QMessageBox.warning(self, "Invalid Input", "Project name and scan path required.")
            return

        dc_path = self.dc_manager.get_dc_bat_path()
        if not os.path.exists(dc_path):
            QMessageBox.critical(self, "Error", "Dependency Check not found.")
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

        # ✅ FIXED: use config manager
        api_key = load_nvd_api_key(self)
        if api_key:
            cmd += ["--nvdApiKey", api_key]

        command = " ".join(f'"{c}"' if " " in c else c for c in cmd)
        self.output.append(f"Running:\n{command}\n")

        self._run_thread(command, log_file, out_file)

    # ======================= THREAD ================================

    def _run_thread(self, command, log_file, out_file):
        self.thread = QtCore.QThread(self)
        self.worker = ScanWorker(command, log_file, out_file)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self.output.append)
        self.worker.error.connect(self.output.append)
        self.worker.finished.connect(self._scan_finished)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.scan_btn.setEnabled(False)
        self.thread.start()

    def _scan_finished(self, report):
        self.scan_btn.setEnabled(True)
        QMessageBox.information(self, "Scan Complete", f"Report saved:\n{report}")

    # ======================= CONFIG / API KEY ===========================

    def open_preferences(self):
        dlg = PreferencesDialog(self)
        dlg.exec_()


    # ======================= UTILITIES ================================

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
    gui.resize(900, 650)
    gui.show()

    gui.dc_manager.check_dctools_version_startup()
    app.exec_()
