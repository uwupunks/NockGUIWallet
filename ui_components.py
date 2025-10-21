"""UI Components for the Nockchain GUI Wallet.

This module contains modern, styled UI components used throughout the wallet application.
Components are designed with a consistent look and feel, following a modern design language.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional, Callable, Dict, Any


class ModernButton(ttk.Button):
    """A modern styled button widget with hover effects and rounded corners."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Optional[Callable] = None,
        style: str = "primary",
        **kwargs: Any,
    ) -> None:
        # Create style name
        style_name = f"{style.capitalize()}.TButton"

        init_kwargs: Dict[str, Any] = {
            "text": text,
            "style": style_name,
        }
        if command is not None:
            init_kwargs["command"] = command

        init_kwargs.update(kwargs)

        super().__init__(parent, **init_kwargs)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the button."""
        if enabled:
            self.configure(state="normal")
        else:
            self.configure(state="disabled")


class ModernFrame(ttk.Frame):
    """A modern styled frame widget with optional title."""

    def __init__(
        self, parent: tk.Widget, title: Optional[str] = None, **kwargs: Any
    ) -> None:
        super().__init__(parent, style="Modern.TFrame", **kwargs)

        if title:
            title_frame = ttk.Frame(self, style="ModernTitle.TFrame")
            title_frame.pack(fill="x", pady=(0, 5))
            title_frame.pack_propagate(False)
            title_frame.configure(height=45)

            title_label = ttk.Label(
                title_frame,
                text=title,
                style="ModernTitle.TLabel",
            )
            title_label.pack(anchor="w", pady=(0, 5))


class ModernEntry(ttk.Frame):
    """A modern styled entry widget with placeholder support."""

    def __init__(self, parent: tk.Widget, placeholder: str = "", **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)

        self.entry = ttk.Entry(
            self,
            style="Modern.TEntry",
        )
        self.entry.pack(fill="both", expand=True)

        self.border = ttk.Frame(self, style="ModernBorder.TFrame")
        self.border.pack(fill="x", side="bottom")
        self.border.configure(height=1)

        self.placeholder = placeholder
        if placeholder:
            self.show_placeholder()
            self.entry.bind("<FocusIn>", self.hide_placeholder)
            self.entry.bind("<FocusOut>", self.show_placeholder)

    def show_placeholder(self, event: Optional[Any] = None) -> None:
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.configure(style="Placeholder.TEntry")

    def hide_placeholder(self, event: Optional[Any] = None) -> None:
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.configure(style="Modern.TEntry")

    def get(self) -> str:
        value = self.entry.get()
        return "" if value == self.placeholder else value


class StatusBar(ttk.Frame):
    """Status bar showing price, API status, and time information."""

    def __init__(
        self,
        parent: tk.Widget,
        price_callback: Callable[[], tuple[float, float]],
        status_callback: Callable[[], bool],
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, style="Status.TFrame", **kwargs)
        self.pack_propagate(False)
        self.configure(height=30)

        self.price_callback = price_callback
        self.status_callback = status_callback

        self.price_frame = ttk.Frame(self, style="Status.TFrame")
        self.price_frame.pack(side="left", padx=20)

        self.price_label = ttk.Label(
            self.price_frame,
            text="NOCK: $0.00",
            style="Price.TLabel",
        )
        self.price_label.pack(side="left")

        self.change_label = ttk.Label(
            self.price_frame,
            text="▲ 0.00%",
            style="Change.TLabel",
        )
        self.change_label.pack(side="left", padx=(10, 0))

        self.node_label = ttk.Label(
            self,
            text="API: Checking...",
            style="Node.TLabel",
        )
        self.node_label.pack(side="left", padx=20)

        self.connection_label = ttk.Label(
            self,
            text="API: https://nockchain-api.zorp.io ✅",
            style="Connection.TLabel",
        )
        self.connection_label.pack(side="left", padx=20)

        self.time_label = ttk.Label(
            self,
            text="",
            style="Time.TLabel",
        )
        self.time_label.pack(side="right", padx=20)

        self.update_time()
        self.update_price()
        self.update_node_status()

    def update_node_status(self) -> None:
        def check_status() -> None:
            try:
                if self.status_callback():
                    self.node_label.configure(
                        text="API: Connected ✅", foreground="#10B981"
                    )
                else:
                    self.node_label.configure(
                        text="API: Disconnected 💢", foreground="#EF4444"
                    )
            except Exception:
                self.node_label.configure(text="API: Error", foreground="#EF4444")

        check_status()
        self.after(30000, self.update_node_status)

    def update_time(self) -> None:
        now = datetime.now()
        self.time_label.configure(text=now.strftime("%b %d %H:%M:%S"))
        self.after(1000, self.update_time)

    def update_price(self) -> None:
        price, change = self.price_callback()
        if price:
            self.price_label.configure(text=f"NOCK: ${price:.2f}")
            color = "#10B981" if change >= 0 else "#EF4444"
            symbol = "▲" if change >= 0 else "▼"
            self.change_label.configure(
                text=f"{symbol} {abs(change):.2f}%", foreground=color
            )

        self.after(60000, self.update_price)
