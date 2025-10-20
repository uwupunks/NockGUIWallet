from setuptools import setup

APP = ["main.py"]  # Your main script
DATA_FILES = [("", ["wallet.icon", "wallet.png"])]  # Include icons and other resources
OPTIONS = {
    "argv_emulation": False,  # For GUI apps
    "iconfile": "wallet.icon",  # Path to .icns icon file
    "plist": {
        "CFBundleName": "NockGUIWallet",  # App name
        "CFBundleDisplayName": "NockGUIWallet",
        "CFBundleVersion": "1.0.0",  # Version
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleIconFile": "wallet.icon",  # Icon reference
    },
    "packages": ["tkinter", "pyobjc", "pillow"],  # Include dependencies
    "includes": ["AppKit"],  # For macOS-specific modules
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
