"""Constants used throughout the Nockchain GUI Wallet.

This module contains constants and configuration values used across different
modules in the application.
"""

import os
import re

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
