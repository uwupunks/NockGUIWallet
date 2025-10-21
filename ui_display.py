"""Display functions for the Nockchain GUI Wallet.

This module contains functions for displaying and managing UI elements
that don't fit into other categories.
"""

import tkinter as tk
import re
from tkinter import ttk
from typing import List, Optional

from constants import ANSI_ESCAPE, COLORS
from state import wallet_state
from ui_components import ModernButton
from wallet_ops import check_balance, truncate_address


def remove_ansi_and_newlines(text: str) -> str:
    return (
        ANSI_ESCAPE.sub("", text)
        .replace("\r\n", "")
        .replace("\n", "")
        .replace("\r", "")
    )


def display_addresses(addresses: List[str]) -> None:
    """Display list of addresses in the UI.

    Args:
        addresses: List of addresses to display
    """
    if not addresses:
        wallet_state.log_message("⚠️ No addresses found.")
        return

    if wallet_state.address_content is None:
        return

    # Clear existing content
    for widget in wallet_state.address_content.winfo_children():
        widget.destroy()

    # Create address list
    for i, address in enumerate(addresses):
        # Address frame
        addr_frame = ttk.Frame(wallet_state.address_content, style="Addr.TFrame")
        addr_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Label frame (left side)
        label_frame = ttk.Frame(addr_frame, style="White.TFrame")
        label_frame.pack(side="left", fill="x", expand=True)

        # Address number
        ttk.Label(
            label_frame,
            text=f"Address {i + 1}",
            style="AddrLabel.TLabel",
        ).pack(anchor="w")

        # Public key
        key_label = ttk.Label(
            label_frame,
            text=truncate_address(address),
            style="Key.TLabel",
            cursor="hand2",
        )
        key_label.pack(anchor="w")
        key_label.bind("<Button-1>", lambda e, addr=address: select_address(addr))

        # Buttons frame (right side)
        buttons_frame = ttk.Frame(addr_frame, style="White.TFrame")
        buttons_frame.pack(side="right")

        # Copy button
        copy_btn = ModernButton(
            buttons_frame,
            text="📋 Copy",
            command=lambda a=address: copy_to_clipboard(a),
            style="secondary",
        )
        copy_btn.pack(side="right", padx=5)

        # Check balance button
        check_btn = ModernButton(
            buttons_frame,
            text="💰 Balance",
            command=lambda a=address: check_balance(a),
        )
        check_btn.pack(side="right", padx=5)


def select_address(address: str) -> None:
    """Select an address - copy to clipboard and populate sender field.

    Args:
        address: The address to select
    """
    # Copy to clipboard
    copy_to_clipboard(address)

    # Populate sender field
    if wallet_state.sender_entry:
        wallet_state.sender_entry.entry.delete(0, tk.END)
        wallet_state.sender_entry.entry.insert(0, address)


def copy_to_clipboard(text: str) -> None:
    """Copy text to clipboard and show notification.

    Args:
        text: Text to copy
    """
    if wallet_state.root is not None:
        wallet_state.root.clipboard_clear()
        wallet_state.root.clipboard_append(text)
        # Import locally to avoid circular import
        from ui_handlers import show_notification

        show_notification("Copied!", "Address copied to clipboard")
