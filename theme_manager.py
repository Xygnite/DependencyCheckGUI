# theme_manager.py
import os
import xml.etree.ElementTree as ET
try:
    import winreg
except ImportError:
    winreg = None # For non-Windows systems

CONFIG_FILE = "configuration.xml"
STYLESHEET_DARK = "stylesheet.qss"
STYLESHEET_LIGHT = "stylesheet_light.qss"

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
    """
    configured_theme = "dark" # Default if no config file or theme node
    if os.path.exists(CONFIG_FILE):
        try:
            tree = ET.parse(CONFIG_FILE)
            root = tree.getroot()
            theme_node = root.find("theme")
            if theme_node is not None:
                configured_theme = theme_node.text.lower()
        except ET.ParseError:
            pass # Keep default

    if configured_theme == "system":
        return get_system_theme()
    else:
        return configured_theme

def save_theme(theme_name):
    """
    Saves the selected theme to configuration.xml.
    """
    try:
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
        
        tree.write(CONFIG_FILE, encoding='utf-8', xml_declaration=True)
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
