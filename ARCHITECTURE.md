# DependencyCheckGUI Architecture

## Purpose & Scope
DependencyCheckGUI wraps the OWASP Dependency-Check CLI with a PyQt5 desktop experience tailored for Windows users. The application streamlines scan orchestration, API key management, and supplemental tooling (CVE lookup and JAR analysis) to support secure dependency lifecycle workflows.

## Technology Stack
- **Language & UI**: Python 3 with PyQt5 widgets and threading (`main.py:55`, `main.py:21`).
- **CLI Integration**: OWASP Dependency-Check installed locally under `dependency-check/` and invoked via `dependency-check.bat`.
- **Remote Services**:
  - NVD REST API for CVE detail and history lookups (`fetch_cve_details.py:14`).
  - Sonatype OSS Index for component vulnerability reports (`jar_vulnerability_finder.py:19`).
- **Config & Storage**: XML persisted preferences stored in `configuration.xml` (root and `_internal/`) (`nvd_config_mgr.py:16`, `sonatype_config_mgr.py:16`).
- **Styling Assets**: QSS stylesheets (`stylesheet.qss`, `stylesheet_light.qss`) and icon assets under `assets/`.

## Runtime Flow
1. **Startup**
   - `main.py` boots the Qt application, applies persisted theme settings (`theme_manager.py:34`, `theme_manager.py:80`), and instantiates the primary `DependencyCheckGUI` window (`main.py:55`).
   - Required working folders (`Reports`, `Logs`, `SCA_Jar_Templates`, `Backups`, `dependency-check`) are created on launch (`main.py:168`).
   - Dependency-Check binaries are validated and optionally updated via `DependencyCheckManager.check_dctools_version_startup()` (`dependency_check_manager.py:113`).
2. **Scan Execution**
   - User selects scan mode (folders vs. files) and report format in the main window (`main.py:82`, `main.py:118`).
   - `start_scan()` composes a CLI command, injects API keys if available, and spawns a `ScanWorker` on a dedicated `QThread` to stream logs without blocking the UI (`main.py:137`, `main.py:214`).
   - CLI output is persisted to timestamped log and report files under the managed directories.
3. **Auxiliary Tools**
   - CVE detail lookup opens a standalone window driven by `CVEDetailsRetriever` to query NVD endpoints and render results in a table with history dialogs (`fetch_cve_details.py:43`, `fetch_cve_details.py:138`).
   - JAR scanner resolves Maven coordinates from SHA-1 fingerprints and requests Sonatype OSS Index vulnerability data, displaying severity-colored results (`jar_vulnerability_finder.py:65`, `jar_vulnerability_finder.py:143`).
   - Diagnostics panel bundles environment checks (Java availability, disk space, NVD connectivity) into a single dialog launched from the main window to preempt scan failures (`diagnostics_panel.py:16`).
   - Report list tab surfaces generated reports with timestamps and opens them in the system viewer on demand (`report_browser.py:14`).
4. **Preferences & Theming**
   - The Preferences dialog (`preferences_dialog.py:250`) hosts stacked panels for NVD keys, Sonatype keys, and theme selection.
   - API keys are validated, masked and written to all known config files using dedicated config managers (`nvd_config_mgr.py:97`, `sonatype_config_mgr.py:102`).

## Module Responsibilities
- **Main UI (`main.py`)**
  - Window composition, menu wiring, scan orchestration, and cross-module coordination.
  - `ScanWorker` (`main.py:21`) encapsulates subprocess execution, emitting progress via Qt signals.
- **Dependency Management (`dependency_check_manager.py:11`)**
  - Downloads and unpacks Dependency-Check releases, prunes obsolete content, and exposes purge/version utilities.
  - Progress UI and blocking dialogs centralize feedback for long-running maintenance operations.
- **Configuration Managers**
  - `nvd_config_mgr.py` and `sonatype_config_mgr.py` abstract XML read/write, dialog prompts, and lazy loading of API credentials for both scans and auxiliary tools.
- **Diagnostics (`diagnostics_panel.py`)**
  - Presents a reusable dialog that aggregates runtime checks, color-coding results and surfacing actionable messaging before scans run.
- **Report Browser (`report_browser.py`)**
  - Lists generated reports with metadata, supports double-click launch in the system default viewer, and keeps the UI synced after scans.
- **Preferences & Shared Widgets (`preferences_dialog.py`)**
  - Provides reusable secure `ApiKeyLineEdit` with show/hide toggles (`preferences_dialog.py:81`).
  - Stacked panels isolate concerns (API keys vs. appearance), enabling incremental additions.
- **Theme Handling (`theme_manager.py`)**
  - Resolves persisted theme choice, falls back to system theme on Windows, and loads QSS files to skin the UI.
- **Tool Windows**
  - CVE viewer and JAR scanner each run as independent widgets, preserving responsiveness in the main window while reusing config managers for credential retrieval.

## Data & File Layout
- `Reports/` and `Logs/` store timestamped outputs per scan session.
- `_internal/configuration.xml` mirrors root configuration for bundled deployments; all config writes target both locations.
- `dependency-check/` hosts the unpacked CLI binaries; only the `data/` directory persists across updates (`dependency_check_manager.py:58`).
- Static assets under `assets/` include application icons and password-visibility toggles referenced in UI components.

## External Interactions
- **OWASP Dependency-Check**: invoked via subprocess with command-line arguments surfaced in UI. Failed runs propagate output logs for troubleshooting.
- **NVD API**: requests include optional API keys to mitigate rate limiting; response data populates tables and history dialogs.
- **Sonatype OSS Index**: requires `username:token` credentials; responses populate vulnerability tables with direct URL references for remediation review.

## Extension Points & Design Considerations
- **Scan Types**: `DependencyCheckGUI.start_scan()` centralizes CLI argument assembly, making it a natural hook for additional Dependency-Check flags or profiles.
- **Background Tasks**: `ScanWorker` demonstrates the pattern for long-running subprocesses. Similar signal-based workers can be added for new tooling without altering the main event loop.
- **Preferences Framework**: The stacked widget layout and `save()` contract across panels simplify adding future settings (e.g., proxy configuration, report retention policies).
- **Configuration Stores**: XML schema is minimal; consider versioning or schema validation if future preferences grow more complex.
- **API Integrations**: Both NVD and Sonatype clients rely on `requests.Session`; expanding to other advisories (e.g., GitHub Advisory DB) can reuse the credential-handling pattern.
- **Error Handling & UX**: Current dialogs surface operational feedback; adding centralized logging or toast-style notifications may improve the experience for batch workflows.

## Known Gaps & Risks
- README contains non-ASCII artifacts; ensure documentation updates stay ASCII-compliant if distributing in environments with stricter encoding requirements.
- Dependency-Check path is Windows-centric (`dependency-check.bat`); cross-platform support would require additional path resolution and shell handling.
- Credentials are stored in plaintext XML; future enhancements might encrypt secrets or integrate OS keychains.
