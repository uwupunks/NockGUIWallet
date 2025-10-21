"""Main application module for the Nockchain GUI Wallet.

This module handles application initialization, setup, and the main event loop.
It ties together all the components and manages the application lifecycle.
"""

import sys
import tkinter as tk
from tkinter import ttk
from typing import Optional

from state import wallet_state
from ui_components import (
    ModernButton,
    ModernFrame,
    ModernEntry,
    StatusBar,
)
from ui_handlers import (
    on_create_wallet,
    on_derive_children,
    on_import_keys,
    on_export_keys,
    on_get_addresses,
    on_send,
    open_nocknames_window,
    open_sign_message_window,
    open_verify_message_window,
)
from api_handlers import get_price, is_rpc_up
from constants import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, COLORS, FONT_FAMILY
import ui_styles


class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window initially
        wallet_state.set_root(self.root)  # Set root in global state

        self._configure_window()
        ui_styles.setup_styles(self.root)
        self._load_splash_screen()

    def _configure_window(self) -> None:
        self.root.title("Robinhood's Nockchain Wallet Pro Edition")
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.root.configure(bg=COLORS["background"])
        self.root.iconphoto(True, tk.PhotoImage(file="wallet.png"))
        if sys.platform == "darwin":
            from AppKit import NSApp, NSImage  # type: ignore

            image = NSImage.alloc().initWithContentsOfFile_("wallet.icon")
            NSApp.setApplicationIconImage_(image)
        else:
            self.root.iconbitmap("wallet.icon")

    def _load_splash_screen(self) -> None:
        from splash_screen import SplashScreen

        self.splash = SplashScreen(self.root)

    def _create_header(self) -> None:
        # Header frame
        header = ttk.Frame(self.root, style="Status.TFrame", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        header_content = ttk.Frame(header, style="Status.TFrame")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)

        # Action buttons container
        header_buttons = ttk.Frame(header_content, style="Status.TFrame")
        header_buttons.pack(side="top", pady=0)
        header_buttons.place(relx=0.5, rely=0.5, anchor="center")

        # Create action buttons
        self._create_action_buttons(header_buttons)

    def _create_action_buttons(self, parent: ttk.Frame) -> None:
        buttons = [
            ("✨ Create Wallet", on_create_wallet, "secondary"),
            ("🧬 Derive Children", on_derive_children, "secondary"),
            ("📂 Import Keys", on_import_keys, "secondary"),
            ("💾 Export Keys", on_export_keys, "secondary"),
            ("🔑 Get Addresses", on_get_addresses, "primary"),
            ("👨 Names", open_nocknames_window, "secondary"),
            ("📝 Sign", open_sign_message_window, "secondary"),
            ("🔏 Verify", open_verify_message_window, "secondary"),
        ]

        for text, command, style in buttons:
            btn = ModernButton(parent, text=text, command=command, style=style)
            btn.pack(side="left", padx=2)

            # Store references to buttons we need to access later
            if text == "🔑 Get Addresses":
                wallet_state.btn_get_addresses = btn

    def _create_main_content(self) -> None:
        # Main container
        main_container = ttk.Frame(self.root, style="Status.TFrame")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Create left and right panels
        self._create_left_panel(main_container)
        self._create_right_panel(main_container)

    def _create_left_panel(self, parent: ttk.Frame) -> None:
        left_panel = ttk.Frame(parent, style="Input.TFrame")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Addresses section
        address_frame = ModernFrame(left_panel, title="Addresses")
        address_frame.pack(fill="both", expand=True, pady=(0, 15))

        address_content = ttk.Frame(address_frame, style="Input.TFrame")
        address_content.pack(fill="both", expand=True, padx=20, pady=20)

        wallet_state.address_content = address_content

        # Activity Log section
        output_frame = ModernFrame(left_panel, title="Activity Log")
        output_frame.pack(fill="both", expand=True)
        output_text = tk.Text(
            output_frame,
            font=("Consolas", 9),
            relief="flat",
            bd=0,
            state="disabled",
            wrap="none",
            height=20,
        )
        output_text.pack(fill="both", expand=True, padx=20, pady=20)
        wallet_state.output_text = output_text

    def _create_right_panel(self, parent: ttk.Frame) -> None:
        right_side = ttk.Frame(parent, style="Status.TFrame")
        right_side.pack(side="right", fill="both", expand=True, padx=(10, 0))
        right_side.grid_columnconfigure(0, weight=1)
        right_side.rowconfigure(0, weight=0)  # Balance section (shrink to content)
        right_side.rowconfigure(1, weight=9)  # Transaction section (most space)
        right_side.rowconfigure(2, weight=3)  # Explorer section

        self._create_balance_section(right_side)
        self._create_transaction_section(right_side)
        self._create_explorer_section(right_side)

    def _create_balance_section(self, parent: ttk.Frame) -> None:
        balance_frame = ModernFrame(parent, title="🏦 Balance 🏦")
        balance_frame.grid(row=0, column=0, sticky="nsew")

        balance_content = ttk.Frame(balance_frame, style="White.TFrame")
        balance_content.pack(fill="x", expand=False, padx=10, pady=10)

        # Balance display elements
        balance_main = ttk.Label(
            balance_content,
            text="0.00 NOCK",
            style="BalanceMain.TLabel",
        )
        balance_main.pack(pady=(10, 5))
        wallet_state.balance_main = balance_main

        balance_details = ttk.Label(
            balance_content,
            text="Select a key to view balance",
            style="BalanceDetails.TLabel",
        )
        balance_details.pack(pady=(0, 10))
        wallet_state.balance_details = balance_details

    def _create_transaction_section(self, parent: ttk.Frame) -> None:
        # Transaction panel
        right_panel = ttk.Frame(parent)
        right_panel.grid(row=1, column=0, sticky="nsew")

        send_frame = ModernFrame(right_panel, title="Send Transaction")
        send_frame.pack(fill="both", expand=True)

        # Form fields container
        fields_frame = ttk.Frame(send_frame, style="Input.TFrame")
        fields_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create form fields
        field_specs = [
            ("Sender Public Key", "sender_entry", "Enter sender address..."),
            ("Recipient Public Key", "recipient_entry", "Enter recipient address..."),
            ("Gift Amount (Nicks)", "gift_entry", "0"),
            ("Fee (Nicks)", "fee_entry", "0"),
        ]

        for label, attr_name, placeholder in field_specs:
            ttk.Label(
                fields_frame,
                text=label,
                style="FormLabel.TLabel",
            ).pack(anchor="w", pady=(0, 5))

            entry = ModernEntry(fields_frame, placeholder=placeholder)
            entry.pack(fill="x", pady=(0, 15))
            setattr(wallet_state, attr_name, entry)

        # Send button
        send_btn = ModernButton(
            fields_frame,
            text="Send Transaction",
            command=on_send,
        )
        send_btn.pack(pady=10)
        wallet_state.btn_send = send_btn

    def _create_explorer_section(self, parent: ttk.Frame) -> None:
        # Explorer panel
        explorer_panel = ttk.Frame(parent, style="Input.TFrame")
        explorer_panel.grid(row=2, column=0, sticky="nsew")

        explorer_content = ttk.Frame(explorer_panel, style="Input.TFrame")
        explorer_content.pack(fill="both", expand=True, padx=20, pady=20)

        # Configure grid for side-by-side layout
        explorer_content.grid_columnconfigure(0, weight=1)
        explorer_content.grid_columnconfigure(1, weight=1)

        # Block Explorers (left side)
        block_frame = ttk.Frame(explorer_content, style="Input.TFrame")
        block_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ttk.Label(
            block_frame,
            text="📡 Block Explorers",
            style="SectionTitle.TLabel",
        ).pack(pady=(0, 10))

        ModernButton(
            block_frame,
            text="🌐 NockBlocks",
            command=lambda: self._open_url("https://nockblocks.com"),
            style="secondary",
        ).pack(pady=(0, 10))

        # Mining Pools (right side)
        pool_frame = ttk.Frame(explorer_content, style="Input.TFrame")
        pool_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ttk.Label(
            pool_frame,
            text="🛟 Mining Pools",
            style="SectionTitle.TLabel",
        ).pack(pady=(0, 10))

        ModernButton(
            pool_frame,
            text="🐬 NockPool",
            command=lambda: self._open_url("https://nockpool.com"),
            style="secondary",
        ).pack(pady=(0, 10))

    def _open_url(self, url: str) -> None:
        """Open URL in default browser.

        Args:
            url: URL to open
        """
        import webbrowser

        webbrowser.open_new_tab(url)

    def initialize(self) -> None:
        """Initialize application UI and services."""
        self.splash.update_progress(10, "Initializing application...")

        # Create UI components
        self.splash.update_progress(30, "Creating main interface...")
        self._create_header()
        self.splash.update_progress(40, "Setting up UI...")
        status_frame = ttk.Frame(self.root, style="Status.TFrame")
        status_frame.pack(fill="x", side="bottom")
        status_bar = StatusBar(status_frame, get_price, is_rpc_up)
        status_bar.pack(side="bottom", fill="x")
        wallet_state.status_bar = status_bar

        self.splash.update_progress(50, "Setting up components...")
        self._create_main_content()

        self.splash.update_progress(80, "Setting up UI...")

        self.splash.update_progress(90, "Checking API status...")
        self.root.update()
        is_rpc_up()  # Initial API check

        self.splash.update_progress(95, "Getting price data...")
        self.root.update()
        get_price()  # Initial price check

        self.splash.update_progress(98, "Loading addresses...")
        self.root.update()
        on_get_addresses()  # Load addresses on startup

        # Setup periodic updates
        self._setup_periodic_updates()

        def _show_welcome_message() -> None:
            wallet_state.clear_output()
            log = wallet_state.log_message
            log("Welcome to Robinhood's Nockchain Wallet Pro Edition!\n")
            log("─" * 50 + "\n")
            log(f"API Server: https://nockchain-api.zorp.io\n")
            log(f"Connection Status: ✅ Ready\n")
            # Node status check
            if is_rpc_up():
                node_status = "✅ Nockchain RPC is up"
            else:
                node_status = "💢 Nockchain RPC is down 💢"

            log(f"Node Status: {node_status}\n\n")

            log(
                "💝 Donations 💝: 2deHSdGpxFh1hhC2qMjM5ujBvG7auCeoJLcLAwGKpfSsb8zfaTms8SMdax7fCyjoVTmbqXgUDWLc7GURXtMeEZbPz57LeakGKTAWZSVYcBwyHvcHuskqL4rVrw56rPXT6wSt\n",
            )

        _show_welcome_message()

        # Show main window
        self.splash.update_progress(100, "Ready!")
        self.root.deiconify()
        self.splash.destroy()

    def _setup_periodic_updates(self) -> None:
        """Setup periodic updates for price and status."""

        def update():
            get_price()
            is_rpc_up()
            self.root.after(30000, update)  # Every 30 seconds

        self.root.after(30000, update)

    def run(self) -> None:
        """Start the application."""
        self.initialize()
        self.root.mainloop()


def main() -> None:
    """Main entry point."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
