"""State management for the Nockchain GUI Wallet.

This module contains the WalletState class that manages the application's state
and provides methods for updating the UI.
"""

import queue
import tkinter as tk
from tkinter import ttk
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ui_components import ModernButton, ModernEntry, StatusBar


class WalletState:
    """Manages application state and UI updates."""

    def __init__(self):
        """Initialize wallet state."""
        # Root window
        self.root: Optional[tk.Tk] = None

        # State values
        self.price = 0.0
        self.change_24h = 0.0
        self.balance_queue = queue.Queue()
        self.message_queue = queue.Queue()

        # UI Elements
        self.address_content: Optional[ttk.Frame] = None
        self.balance_main: Optional[ttk.Label] = None
        self.balance_details: Optional[ttk.Label] = None
        self.status_bar: Optional["StatusBar"] = None
        self.output_text: Optional[tk.Text] = None

        # Transaction UI Elements
        self.btn_get_addresses: Optional["ModernButton"] = None
        self.btn_send: Optional["ModernButton"] = None
        self.sender_entry: Optional["ModernEntry"] = None
        self.recipient_entry: Optional["ModernEntry"] = None
        self.gift_entry: Optional["ModernEntry"] = None
        self.fee_entry: Optional["ModernEntry"] = None
        self.index_entry: Optional["ModernEntry"] = None

    def set_root(self, root: tk.Tk) -> None:
        """Set the root window.

        Args:
            root: Root window instance
        """
        self.root = root

    def update_price(self, price: float, change: float) -> None:
        """Update price information.

        Args:
            price: Current NOCK price in USD
            change: 24h price change percentage
        """
        self.price = price
        self.change_24h = change

    def get_usd_value(self, nocks: float) -> float:
        """Convert NOCK amount to USD.

        Args:
            nocks: Amount of NOCK

        Returns:
            USD value
        """
        return nocks * self.price

    def log_message(self, message: str) -> None:
        """Add a message to the output log.

        Args:
            message: Message to log
        """
        if self.output_text:
            self.output_text.config(state="normal")
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.output_text.config(state="disabled")

    def clear_output(self) -> None:
        """Clear the output log."""
        if self.output_text:
            self.output_text.config(state="normal")
            self.output_text.delete("1.0", tk.END)
            self.output_text.config(state="disabled")

    def queue_message(self, message: str) -> None:
        """Queue a message for asynchronous display.

        Args:
            message: Message to queue
        """
        self.message_queue.put(message)
        if self.output_text:
            self.output_text.after(100, self.process_message_queue)

    def process_message_queue(self) -> None:
        """Process queued messages."""
        try:
            while True:
                message = self.message_queue.get_nowait()
                self.log_message(message)
        except queue.Empty:
            pass
        if self.output_text:
            self.output_text.after(100, self.process_message_queue)

    def update_node_status(self, is_connected: bool) -> None:
        """Update node status in the status bar.

        Args:
            is_connected: Whether node is connected
        """
        if self.status_bar:
            if is_connected:
                self.status_bar.node_label.configure(
                    text="API: Connected ✅", foreground="#10B981"
                )
            else:
                self.status_bar.node_label.configure(
                    text="API: Disconnected 💢", foreground="#EF4444"
                )

    def update_balance_display(self, nocks: float, total_assets: int) -> None:
        """Update balance display in the UI.

        Args:
            nocks: Amount in NOCK
            total_assets: Total assets in Nicks
        """
        if self.balance_main and self.balance_details:
            self.balance_main.configure(
                text=f"{nocks:,.4f} NOCK",
                foreground="#10b93d" if total_assets > 0 else "#FF0000",
            )
            self.balance_details.configure(
                text=f"{total_assets:,} Nicks\n${self.get_usd_value(nocks):,.2f} USD",
                foreground="#6B7280",
            )

    def enable_transaction_controls(self, enabled: bool = True) -> None:
        """Enable or disable transaction-related controls.

        Args:
            enabled: Whether controls should be enabled
        """
        if self.btn_send:
            self.btn_send.set_enabled(enabled)
        if self.btn_get_addresses:
            self.btn_get_addresses.set_enabled(enabled)

    def get_transaction_details(self) -> dict:
        """Get transaction details from entry fields.

        Returns:
            Dict with transaction details
        """
        return {
            "sender": self.sender_entry.get() if self.sender_entry else "",
            "recipient": self.recipient_entry.get() if self.recipient_entry else "",
            "amount": self.gift_entry.get() if self.gift_entry else "",
            "fee": self.fee_entry.get() if self.fee_entry else "",
            "index": self.index_entry.get() if self.index_entry else "",
        }


# Create global state instance
wallet_state = WalletState()
