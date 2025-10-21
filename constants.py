"""Constants used throughout the Nockchain GUI Wallet.

This module contains constants and configuration values used across different
modules in the application.
"""

import os
import re
import shutil
import sys
import tkinter as tk
from tkinter import messagebox


def get_nockchain_wallet_path() -> str:
    """Get the path to the nockchain-wallet executable.

    First checks if nockchain-wallet is available in PATH.
    If not, uses the bundled executable if running from a py2app bundle.

    Returns:
        Path to the nockchain-wallet executable
    """
    # Check if nockchain-wallet is in PATH
    if shutil.which("nockchain-wallet"):
        return "nockchain-wallet"

    # Check if we're running from a py2app bundle
    if getattr(sys, "frozen", False):
        # Running in a bundle - executable is in MacOS, bundled files in Resources
        app_dir = os.path.dirname(
            os.path.dirname(sys.executable)
        )  # Go up from MacOS to Contents
        bundled_path = os.path.join(app_dir, "Resources", "nockchain-wallet")
        if os.path.exists(bundled_path):
            # Show warning dialog if using bundled version (only once)
            # Check if we have a display available before showing dialog
            try:
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                messagebox.showwarning(
                    "Warning: Using Bundled nockchain-wallet",
                    "Warning: nockchain-wallet is not built. Using bundled version. "
                    "For best results build the official wallet binary from source: "
                    "https://github.com/zorp-corp/nockchain?tab=readme-ov-file#install-wallet",
                )
                root.destroy()
            except tk.TclError:
                # No display available, skip the warning dialog
                pass
            return bundled_path

    # Fallback - assume it's in the current directory (for development)
    local_path = os.path.join(os.path.dirname(__file__), "nockchain-wallet")
    if os.path.exists(local_path):
        return local_path

    # Last resort - just use the command name and hope it's in PATH
    return "nockchain-wallet"


# API Configuration
API_URL = "https://api.coinpaprika.com/v1/tickers/nock-nockchain"
GRPC_ARGS = [
    "--client",
    "public",
    "--public-grpc-server-addr",
    "https://nockchain-api.zorp.io",
]

# File System
CSV_FOLDER = os.path.expanduser("~/nockchain")

# Regular Expressions
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# Window Dimensions
DEFAULT_WINDOW_WIDTH = 1920
DEFAULT_WINDOW_HEIGHT = 1080

# UI Constants
FONT_FAMILY = "Segoe UI"
COLORS = {
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "secondary": "#6B7280",
    "secondary_hover": "#4B5563",
    "success": "#10B981",
    "success_hover": "#059669",
    "danger": "#DC2626",
    "danger_hover": "#B91C1C",
    "background": "#1F2937",
    "text": "#374151",
    "text_light": "#6B7280",
    "border": "#D1D5DB",
    "input_background": "#F9FAFB",
}

# Button Styles
BUTTON_STYLES = {
    "primary": {
        "bg": COLORS["primary"],
        "fg": "white",
        "hover": COLORS["primary_hover"],
    },
    "secondary": {
        "bg": COLORS["secondary"],
        "fg": "white",
        "hover": COLORS["secondary_hover"],
    },
    "success": {
        "bg": COLORS["success"],
        "fg": "white",
        "hover": COLORS["success_hover"],
    },
    "danger": {"bg": COLORS["danger"], "fg": "white", "hover": COLORS["danger_hover"]},
}
