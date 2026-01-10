# Dependency Check GUI

**DependencyCheckGUI** is a graphical user interface (GUI) for running **OWASP Dependency-Check** command-line tools.  
It simplifies vulnerability scanning of software dependencies with an easy-to-use interface, additional CVE tools, and report management features.  

> ⚡ Built with **Python (PyQt5)** for a modern and optimized experience.  

---

## ✨ Features

### 🛠 Dependency Check Integration
- 📥 Download and install the latest or specific versions of Dependency-Check.  
- 🔄 Check the installed version of Dependency-Check.  
- 🗑 Purge outdated **NVD (National Vulnerability Database)** data.  

### ⚙️ Preferences & Configuration
- 🔑 **NVD API Key Support**: Set your NVD API Key for faster and more reliable CVE lookups.  
- 🔑 **Sonatype OSS Index Support**: Integrate with Sonatype OSS Index for enhanced JAR vulnerability scanning.
- 🎨 **Theme Support**: Choose between **Dark**, **Light**, or **System** themes.

### 📂 Folder & File Selection
- 📁 **Browse Folder**: Scan entire project folders.  
- 📄 **Browse Files**: Select individual files (`.jar`, `.exe`, `.zip`, etc.).  

### 📑 Custom Reports
- 🏷 Define a **project name** for reports and logs.  
- 📊 Automatically organizes report filenames based on project name.  
- 📄 Support for HTML, CSV, and XML report formats.

### 🚀 Scan Execution
- ▶️ Run scans on selected files/folders.  
- 📜 Real-time logs shown in a scrollable text field.  

### 🧰 Tools Menu Enhancements
- 📝 **CVE Details**: 
    - Enter single or multiple CVE IDs to fetch details.
    - **New:** View full **CVE History** (changes, events, source).
- ☕ **Jar Vulnerability Finder**: 
    - Select a JAR file to identify its Maven coordinates (GAV).
    - Scan for vulnerabilities using **Sonatype OSS Index**.

### 📦 Downloads & Updates
- ⬇️ Automatically download the latest Dependency-Check.  
- 📊 Progress bar for downloads and extraction.  

---

## 🖥️ Menu Structure

The GUI contains **three main menus**:  

### 📂 File
- 📑 Open Reports Folder  
- 📑 Open Logs Folder  
- ⚙️ Options → Purge NVD Data  
- 🔧 Settings → Preferences (NVD API Key, Theme)
- ❌ Exit  

### 🧰 Tools
- 📝 CVE Details  
- ☕ Jar Vulnerability Finder  

### ❓ Help
- 🔎 Check Version of DC Tools  
- ⬆️ Update DC Tools to Latest Version  
- ℹ️ About  

---

## 🚀 Usage

### ▶️ Run from Source
```bash
git clone https://github.com/your-username/DependencyCheckGUI.git
cd DependencyCheckGUI
pip install -r requirements.txt
python main.py
```

### ▶️ Run from Executable
- 📦 **Windows Installer / Portable:**  
  Check the **Releases** section for the latest installer or portable `.zip` version.

---

## ⚡ How It Works
- 🧩 Uses OWASP Dependency-Check (`dependency-check.bat`) to perform scans.  
- 📥 Downloads and updates Dependency-Check automatically if missing.  
- 🔑 Stores and uses your NVD and Sonatype API keys for faster, reliable results.  
- ☕ Includes a JAR CVE Finder and CVE ID Lookup tools.  

---

## 📋 Requirements

- ☕ **Java 11+** (Required for OWASP Dependency-Check)
- 🌐 Internet access for Dependency-Check and CVE data  

### 📦 Python Dependencies
- `PyQt5`  
- `requests`  

Install all with:
```bash
pip install -r requirements.txt
```

---

## 📂 Project Structure

- `main.py`: The main entry point of the application.
- `dependency_check_manager.py`: Manages Dependency-Check tool operations (download, update, purge).
- `nvd_config_mgr.py`: Handles NVD API key configuration.
- `sonatype_config_mgr.py`: Handles Sonatype OSS Index API key configuration.
- `fetch_cve_details.py`: Tool for retrieving CVE details and history.
- `jar_vulnerability_finder.py`: Tool for scanning JAR files using Sonatype OSS Index.
- `theme_manager.py`: Manages application themes (Dark/Light/System).
- `configuration.xml`: Stores user preferences and API keys.

---

## 🛠 Troubleshooting
- ❌ **Dependency-Check not found** → Program will prompt to download.  
- 🔑 **NVD API issues** → Ensure valid API key is set in Preferences.  
- 🌐 **Network errors** → Verify internet connectivity.  
- 🗑 **No NVD data to purge** → Tool will notify if purge isn’t needed.  

---

## 📜 License
Licensed under the **MIT License**. See the [LICENSE](LICENSE) file.  

---

## 🙌 Acknowledgements
 
- **PyQt5** – GUI Framework  
- **Requests** – For downloads & API calls  
- **[OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)** – For scanning dependencies for known vulnerabilities.  
- **[Sonatype OSS Index](https://ossindex.sonatype.org/)** – For vulnerability data.
- **[NVD API](https://nvd.nist.gov/developers)** – For detailed CVE information.  

---

✨ *A simple yet powerful GUI to supercharge your OWASP Dependency-Check workflows!* 🚀
