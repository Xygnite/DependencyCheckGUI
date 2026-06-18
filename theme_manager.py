# theme_manager.py
import os
import sys
import xml.etree.ElementTree as ET
try:
    import winreg
except ImportError:
    winreg = None # For non-Windows systems

# Determine base directory (handles both dev and PyInstaller bundled .exe)
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    BASE_DIR = sys._MEIPASS
    # Save config to user's current working directory for .exe
    CONFIG_SAVE_DIR = os.getcwd()
else:
    # Running in development
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_SAVE_DIR = BASE_DIR

CONFIG_FILE = os.path.join(BASE_DIR, "configuration.xml")
CONFIG_SAVE_FILE = os.path.join(CONFIG_SAVE_DIR, "configuration.xml")
STYLESHEET_DARK = os.path.join(BASE_DIR, "stylesheet.qss")
STYLESHEET_LIGHT = os.path.join(BASE_DIR, "stylesheet_light.qss")

def get_system_theme():
    """
    Detects the current Windows theme (light/dark mode).
    Returns "dark" or "light". Defaults to "light" on error or non-Windows.
    """
    if os.name != "nt" or winreg is None: # Not Windows or winreg not available
        return "light"

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        # AppsUseLightTheme: 0 for dark, 1 for light
        value, reg_type = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "light" if value == 1 else "dark"
    except OSError:
        # Registry key not found, default to light
        return "light"

def load_theme():
    """
    Loads the theme from configuration.xml.
    Defaults to 'dark' if not found.
    If theme is 'system', it detects the system theme.
    Checks both the bundled config and the saved config location.
    """
    configured_theme = "dark" # Default if no config file or theme node
    
    # Try to load from saved location first (CONFIG_SAVE_FILE), then from bundled location (CONFIG_FILE)
    config_paths = [CONFIG_SAVE_FILE, CONFIG_FILE]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                tree = ET.parse(config_path)
                root = tree.getroot()
                theme_node = root.find("theme")
                if theme_node is not None:
                    configured_theme = theme_node.text.lower()
                    break  # Found a valid theme, no need to check other paths
            except ET.ParseError:
                pass  # Try next path

    if configured_theme == "system":
        return get_system_theme()
    else:
        return configured_theme

def save_theme(theme_name):
    """
    Saves the selected theme to configuration.xml.
    Attempts to read from BASE_DIR, but saves to CONFIG_SAVE_DIR (which is writable).
    """
    try:
        # Try to read existing config from BASE_DIR first
        if os.path.exists(CONFIG_FILE):
            tree = ET.parse(CONFIG_FILE)
            root = tree.getroot()
        else:
            root = ET.Element("configuration")
            tree = ET.ElementTree(root)
            
        theme_node = root.find("theme")
        if theme_node is None:
            theme_node = ET.SubElement(root, "theme")
        
        theme_node.text = theme_name.lower()
        
        # Save to writable location
        tree.write(CONFIG_SAVE_FILE, encoding='utf-8', xml_declaration=True)
        return True
    except Exception as e:
        print(f"Error saving theme: {e}")
        return False

def get_stylesheet(theme_name):
    """
    Returns the content of the stylesheet file for the given theme.
    """
    if theme_name.lower() == "light":
        stylesheet_file = STYLESHEET_LIGHT
    else:
        stylesheet_file = STYLESHEET_DARK
        
    try:
        with open(stylesheet_file, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""
