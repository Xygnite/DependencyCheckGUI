import os
import re
import shutil
import subprocess
import zipfile

import requests
from PyQt5 import QtCore, QtWidgets


class DependencyCheckManager(QtCore.QObject):
    """
    Encapsulates all operations related to OWASP Dependency-Check:
    - Locating the DC binary
    - Downloading / updating DC
    - Purging NVD data
    - Checking DC version (startup & on-demand)
    """

    DC_DIR = "dependency-check"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # main window (used for dialogs, append_output)

    # === PATH / CONFIG HELPERS =============================================

    @staticmethod
    def get_program_dir() -> str:
        return os.path.dirname(os.path.abspath(__file__))

    @classmethod
    def get_dc_bat_path(cls) -> str:
        return os.path.abspath(os.path.join(cls.DC_DIR, "bin", "dependency-check.bat"))

    # === INTERNAL UTILS =====================================================

    def _append_output(self, text: str):
        """Convenience wrapper to append to main window output if available."""
        if self.parent is not None and hasattr(self.parent, "append_output"):
            self.parent.append_output(text)

    def _show_question(self, title: str, text: str):
        return QtWidgets.QMessageBox.question(
            self.parent,
            title,
            text,
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
        )

    # === CLEAN DC FOLDER (KEEP DATA) =======================================

    def clean_dependency_check_folder(self, extract_path: str):
        if not os.path.exists(extract_path):
            return

        for item in os.listdir(extract_path):
            item_path = os.path.join(extract_path, item)
            if item == "data":
                continue  # preserve 'data' folder
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

    # === DOWNLOAD / UPDATE DC ==============================================

    def download_dependency_check(self):
        """Download and extract the latest Dependency Check version safely."""
        version_url = "https://dependency-check.github.io/DependencyCheck/current.txt"

        try:
            self._append_output("Fetching latest Dependency Check version...")
            version_response = requests.get(version_url, timeout=15)
            version_response.raise_for_status()

            version = version_response.text.strip()
            download_url = (
                f"https://github.com/dependency-check/DependencyCheck/releases/download/"
                f"v{version}/dependency-check-{version}-release.zip"
            )

            zip_path = "dependency-check.zip"
            extract_temp = "dependency-check-temp"
            extract_final = self.DC_DIR

            self._append_output("Cleaning up existing Dependency Check folder...")
            self.clean_dependency_check_folder(extract_final)

            self._append_output(f"Downloading Dependency Check {version}...")

            progress_dialog = QtWidgets.QProgressDialog(
                "Downloading Dependency Check...", "Cancel", 0, 100, self.parent
            )
            progress_dialog.setWindowTitle("Downloading")
            progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
            progress_dialog.setMinimumDuration(0)

            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 1))
            downloaded = 0

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)

                    percent = int((downloaded / total_size) * 100)
                    progress_dialog.setValue(percent)
                    QtWidgets.QApplication.processEvents()

                    if progress_dialog.wasCanceled():
                        self._append_output("Download canceled.")
                        os.remove(zip_path)
                        return

            self._append_output("Download complete. Extracting files...")

            # === Extract ZIP =====================================================
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_temp)

            os.remove(zip_path)

            # === Locate dependency-check directory ==============================
            def find_dependency_check_dir(root):
                for base, dirs, _ in os.walk(root):
                    if "bin" in dirs:
                        return base
                return None

            dc_source_dir = find_dependency_check_dir(extract_temp)

            if not dc_source_dir:
                raise RuntimeError("Dependency Check 'bin' directory not found after extraction")

            os.makedirs(extract_final, exist_ok=True)

            for item in os.listdir(dc_source_dir):
                shutil.move(
                    os.path.join(dc_source_dir, item),
                    extract_final
                )

            shutil.rmtree(extract_temp)

            self._append_output("Dependency Check is ready to use.")

        except Exception as e:
            self._append_output(f"Error: {e}")

    # === PURGE NVD DATA =====================================================

    def purge_NVD_data(self):
        """
        Purge NVD data using Dependency-Check.
        If Dependency-Check is not found, prompt user to download it.
        """
        dep_check_path = self.get_dc_bat_path()

        if not os.path.exists(dep_check_path):
            response = self._show_question(
                "Dependency Check Not Found",
                "The 'dependency-check.bat' file could not be found.\n\n"
                "Would you like to download the latest version?",
            )
            if response == QtWidgets.QMessageBox.Ok:
                self.download_dependency_check()
            return

        command = f'"{dep_check_path}" --purge'
        try:
            self._append_output("Purging NVD data...")
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )

            stderr = result.stderr or ""
            if "Unable to purge database; the database file does not exist" in stderr:
                QtWidgets.QMessageBox.information(
                    self.parent, "No Data to Purge", "No NVD data found to purge."
                )
            elif result.returncode == 0:
                QtWidgets.QMessageBox.information(
                    self.parent, "Purge Successful", "NVD data has been successfully purged."
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self.parent, "Purge Failed", f"Failed to purge NVD data:\n{stderr}"
                )

        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""
            if "Unable to purge database; the database file does not exist" in stderr:
                QtWidgets.QMessageBox.information(
                    self.parent, "No Data to Purge", "No NVD data found to purge."
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self.parent, "Purge Failed", f"Failed to purge NVD data:\n{stderr}"
                )

    # === VERSION CHECKS ======================================================

    def check_dctools_version_startup(self):
        """Check for newer DC version on startup and suggest updating."""
        dep_check_path = self.get_dc_bat_path()

        if not os.path.exists(dep_check_path):
            reply = self._show_question(
                "Dependency Check Not Found",
                "The 'dependency-check.bat' file could not be found.\n"
                "You can download the latest version of Dependency-Check.\n\n"
                "Do you want to download it?",
            )
            if reply == QtWidgets.QMessageBox.Ok:
                self.download_dependency_check()
            return

        try:
            # Local version
            result = subprocess.run(
                [dep_check_path, "--version"],
                capture_output=True,
                text=True,
                shell=True,
            )
            local_version_output = result.stdout.strip()
            match = re.search(r"version (\d+\.\d+\.\d+)", local_version_output)
            local_version = match.group(1) if match else None

            # Latest version
            version_url = "https://dependency-check.github.io/DependencyCheck/current.txt"
            response = requests.get(version_url, timeout=15)
            latest_version = response.text.strip() if response.status_code == 200 else None

            if local_version and latest_version and local_version != latest_version:
                reply = QtWidgets.QMessageBox.question(
                    self.parent,
                    "Update Available",
                    f"A newer version of Dependency-Check Tools is available.\n\n"
                    f"Current version: {local_version}\n"
                    f"Latest version:  {latest_version}\n\n"
                    f"Do you want to download the latest version?",
                    QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
                )
                if reply == QtWidgets.QMessageBox.Ok:
                    self.download_dependency_check()

        except Exception as e:
            self._append_output(f"Error checking Dependency-Check version: {str(e)}")

    def check_dctools_version(self):
        """Show current DC version (invoked from menu)."""
        dep_check_path = self.get_dc_bat_path()

        if not os.path.exists(dep_check_path):
            reply = QtWidgets.QMessageBox.question(
                self.parent,
                "Dependency Check Not Found",
                "The 'dependency-check.bat' file could not be found.\n"
                "You can download the latest version of Dependency-Check.\n\n"
                "Do you want to download it?",
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
            )
            if reply == QtWidgets.QMessageBox.Ok:
                self.download_dependency_check()
            return

        command = f'"{dep_check_path}" --version'
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                QtWidgets.QMessageBox.information(
                    self.parent, "Dependency Check Version", stdout.strip()
                )
            else:
                QtWidgets.QMessageBox.critical(self.parent, "Error", stderr.strip())
        except subprocess.CalledProcessError as e:
            QtWidgets.QMessageBox.critical(self.parent, "Error", str(e))
