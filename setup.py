from setuptools import setup

APP = ["main.py"]
DATA_FILES = [("", ["wallet.icon", "wallet.png", "nockchain-wallet"])]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "wallet.icon",
    "plist": {
        "CFBundleName": "NockGUIWallet",
        "CFBundleDisplayName": "NockGUIWallet",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleIconFile": "wallet.icon",
    },
    "packages": ["setuptools"],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
)
