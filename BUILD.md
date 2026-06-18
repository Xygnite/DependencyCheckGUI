# Building DependencyCheckGUI into an .exe

This guide will help you build the DependencyCheckGUI project into a standalone Windows executable (.exe file) with all styling and assets included.

## Prerequisites

- Python 3.7 or higher installed
- Windows operating system

## Quick Build (Easiest Method)

Simply double-click `build.bat` in the project root directory. The script will:
1. Install all required dependencies (including PyInstaller)
2. Clean previous builds
3. Build the executable with all assets included
4. Place the final .exe in the `dist` folder

The entire process typically takes 5-10 minutes depending on your system.

## Manual Build Steps

If you prefer to build manually or the batch script doesn't work:

### Step 1: Install Dependencies

Open PowerShell or Command Prompt in the project root and run:

```bash
pip install -r requirements.txt
```

This installs:
- **PyQt5**: GUI framework
- **requests**: HTTP library
- **PyInstaller**: Executable builder

### Step 2: Build the Executable

Run the following command:

```bash
pyinstaller build.spec
```

This command uses the `build.spec` configuration file which specifies:
- All assets to include (images from `assets/` folder)
- Stylesheets (`stylesheet.qss`, `stylesheet_light.qss`)
- Configuration file (`configuration.xml`)
- Application icon (`assets/DC.ico`)

### Step 3: Locate Your Executable

After the build completes, your executable will be at:

```
dist\DependencyCheckGUI.exe
```

## What's Included in the Build

The generated `.exe` includes:

✅ All Python dependencies (PyQt5, requests, etc.)
✅ Application icon (DC.ico)
✅ Stylesheets (stylesheet.qss, stylesheet_light.qss)
✅ Configuration file (configuration.xml)
✅ Asset images (eye.png, eye-off.png)
✅ Internal modules (_internal folder)
✅ Everything else needed to run the application

## Distribution

You can distribute the `DependencyCheckGUI.exe` file to other users. They do NOT need Python installed to run it.

**Optional:** For easier distribution, you can compress the entire `dist` folder into a ZIP file and share it.

## Customization

If you need to modify the build:

1. **Change the icon**: Edit `build.spec` and update the icon path
2. **Add more data files**: Edit the `datas=` section in `build.spec`
3. **Change console behavior**: Set `console=True` in `build.spec` to show a console window

## Troubleshooting

### Build fails with "module not found" error
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're running from the project root directory

### Icon doesn't appear in the .exe
- Verify `assets/DC.ico` exists
- Check the `icon=` path in `build.spec`

### Assets/Stylesheets not loading in the built .exe
- Verify the file paths in your Python code use relative paths (not absolute)
- Check that files are listed in the `datas=` section of `build.spec`

## File Sizes

- The uncompressed `dist` folder: ~200-300 MB (includes all Python libraries)
- The `DependencyCheckGUI.exe`: ~20-30 MB

## Cleanup

Build artifacts are stored in:
- `build/` - Build artifacts
- `dist/` - Final executable and dependencies

To clean up after building, delete these folders. They can be regenerated anytime.

---

**Need to rebuild?** Just run `build.bat` again or repeat the manual steps.
