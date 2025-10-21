"""UI event handlers for the Nockchain GUI Wallet.

This module contains handler functions for UI events like button clicks
and window management.
"""

import re
import os
import sys
import queue
import subprocess
import threading
import webbrowser
from typing import List, Dict, Any, Optional
from tkinter import messagebox, filedialog, simpledialog, ttk
import tkinter as tk
from datetime import datetime

from state import wallet_state
from wallet_ops import (
    get_addresses,
    create_wallet,
    export_keys,
    import_keys,
    check_balance,
    send_transaction,
    truncate_address,
    export_derived_children_csv,
    save_derived_children,
    extract_values_from_output,
)
from ui_display import display_addresses
from api_handlers import resolve_nockname, resolve_nockaddress
from ui_components import ModernButton, ModernEntry, ModernFrame
from constants import COLORS, GRPC_ARGS, ANSI_ESCAPE, get_nockchain_wallet_path


def create_modern_window(title: str, width: int, height: int) -> tk.Toplevel:
    """Create a modern styled window.

    Args:
        title: Window title
        width: Window width
        height: Window height

    Returns:
        The created window
    """
    win = tk.Toplevel()
    win.title(title)
    win.geometry(f"{width}x{height}")
    win.configure(bg="#F9FAFB")
    return win


def show_notification(title: str, message: str) -> None:
    """Show a notification popup.

    Args:
        title: Notification title
        message: Notification message
    """
    if not wallet_state.root:
        return

    notification = tk.Toplevel(wallet_state.root)
    notification.title("")
    notification.configure(bg=COLORS["success"])
    notification.overrideredirect(True)
    notification.attributes("-topmost", True)
    main_x = wallet_state.root.winfo_x()
    main_y = wallet_state.root.winfo_y()
    main_width = wallet_state.root.winfo_width()
    main_height = wallet_state.root.winfo_height()
    notification.geometry(
        f"300x80+{main_x + main_width - 320}+{main_y + main_height - 80}"
    )

    tk.Label(
        notification,
        text="✅ " + title,
        font=("Segoe UI", 10, "bold"),
        bg=COLORS["success"],
        fg="white",
    ).pack(pady=5)

    tk.Label(
        notification,
        text=message,
        font=("Segoe UI", 9),
        bg=COLORS["success"],
        fg="white",
    ).pack()

    notification.after(3000, notification.destroy)


def on_create_wallet() -> None:
    """Handle create wallet button click."""
    create_wallet()


def on_export_keys() -> None:
    """Handle export keys button click."""
    export_keys()


def on_import_keys() -> None:
    """Handle import keys button click."""
    file_path = filedialog.askopenfilename(
        title="Select Keys File", filetypes=[("Export Files", "*.export")]
    )

    if not file_path:
        return

    import_keys(file_path)


def on_get_addresses() -> None:
    """Handle get addresses button click."""
    if not wallet_state.btn_get_addresses:
        messagebox.showerror("Error", "Button not initialized")
        return

    # Update UI state
    button = wallet_state.btn_get_addresses
    button.configure(text="Loading...")
    button.set_enabled(False)
    wallet_state.clear_output()
    wallet_state.log_message("Fetching addresses...\n")

    def worker():
        addresses = get_addresses()

        def update_ui():
            display_addresses(addresses)
            wallet_state.log_message(f"Found {len(addresses)} addresses:")
            wallet_state.log_message("\n".join(f"  {addr}" for addr in addresses))
            button.configure(text="🔑 Get Addresses")
            button.set_enabled(True)

        if wallet_state.root:
            wallet_state.root.after(0, update_ui)

    threading.Thread(target=worker, daemon=True).start()


def on_send() -> None:
    """Handle send transaction button click."""
    details = wallet_state.get_transaction_details()

    # Validate required fields
    if not all(
        [details["sender"], details["recipient"], details["amount"], details["fee"]]
    ):
        messagebox.showerror(
            "Input Error", "Please fill all fields except Index (optional)."
        )
        return

    if not (
        re.fullmatch(r"[A-Za-z0-9]+", details["sender"])
        and re.fullmatch(r"[A-Za-z0-9]+", details["recipient"])
    ):
        messagebox.showerror(
            "Input Error", "Sender and Recipient address must be alphanumeric."
        )
        return

    if not (details["amount"].isdigit() and details["fee"].isdigit()):
        messagebox.showerror("Input Error", "Gift and Fee must be numeric.")
        return

    if wallet_state.btn_send:
        wallet_state.btn_send.configure(text="Sending...")
        wallet_state.btn_send.set_enabled(False)

    # Send transaction
    send_transaction(
        details["sender"],
        details["recipient"],
        int(details["amount"]),
        int(details["fee"]),
        details["index"] if details["index"] else None,
    )

    # Re-enable button after delay
    def reenable_btn():
        if wallet_state.btn_send:
            wallet_state.btn_send.configure(text="Send Transaction")
            wallet_state.btn_send.set_enabled(True)

    if wallet_state.root:
        wallet_state.root.after(8000, reenable_btn)


def open_nocknames_window() -> None:
    """Open the nocknames resolution window."""
    win = create_modern_window("Nocknames", 800, 600)

    # Header
    header_frame = ttk.Frame(win, style="Status.TFrame", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)

    header_content = ttk.Frame(header_frame, style="Status.TFrame")
    header_content.pack(fill="both", expand=True, padx=20, pady=15)

    ttk.Label(
        header_content,
        text="👨 Nocknames Resolution Service",
        style="HeaderLabel.TLabel",
    ).pack(side="left")

    ModernButton(
        header_content,
        text="Register New",
        command=lambda: webbrowser.open_new_tab("https://nocknames.com"),
        style="success",
    ).pack(side="right")

    # Main content frame
    main_frame = ttk.Frame(win, style="Input.TFrame")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Address to Name section
    create_resolution_section(
        main_frame,
        "Resolve Name from Address",
        "Wallet Address",
        "Enter wallet address...",
        resolve_nockname,
    )

    # Name to Address section
    create_resolution_section(
        main_frame,
        "Resolve Address from Name",
        "Nockname",
        "Enter nockname...",
        resolve_nockaddress,
    )


def create_resolution_section(
    parent: ttk.Frame, title: str, label_text: str, placeholder: str, resolver_func: Any
) -> None:
    """Create a resolution section in the nocknames window.

    Args:
        parent: Parent frame
        title: Section title
        label_text: Input label text
        placeholder: Input placeholder text
        resolver_func: Function to resolve the input
    """
    frame = ModernFrame(parent, title=title)
    frame.pack(fill="x", pady=(0, 15))

    ttk.Label(
        frame,
        text=label_text,
        style="FormLabel.TLabel",
    ).pack(anchor="w", padx=20, pady=(15, 5))

    input_frame = ttk.Frame(frame, style="White.TFrame")
    input_frame.pack(fill="x", padx=20, pady=(0, 15))

    entry = ModernEntry(input_frame, placeholder=placeholder)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

    result = tk.Text(
        frame,
        height=2,
        font=("Consolas", 9),
        state="disabled",
        relief="flat",
        bd=0,
    )
    result.pack(fill="x", padx=20, pady=(0, 15))

    def resolve():
        value = entry.get().strip()
        if not value:
            messagebox.showwarning(
                "Input Required", f"Please enter a {label_text.lower()}"
            )
            return

        result.config(state="normal")
        result.delete("1.0", tk.END)
        result.insert(tk.END, "Resolving...")
        result.config(state="disabled")

        def worker():
            resolved = resolver_func(value)

            def update_ui():
                result.config(state="normal")
                result.delete("1.0", tk.END)
                if resolved:
                    result.insert(tk.END, f"✅ Resolved: {resolved}")
                else:
                    result.insert(tk.END, "❌ Not found")
                result.config(state="disabled")

            parent.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    ModernButton(input_frame, text="Resolve", command=resolve, style="secondary").pack(
        side="right"
    )


def on_derive_children():
    num_children = simpledialog.askinteger(
        "Derive Child Keys",
        "How many child keys would you like to derive?",
        minvalue=1,
        maxvalue=100,
    )
    if not num_children:
        wallet_state.log_message("Child key derivation canceled.")
        return

    # Clear previous log
    wallet_state.clear_output()

    derived_children = []

    def worker():
        for i in range(num_children):
            wallet_state.log_message(f"➡️ Deriving child key {i}...")
            try:
                result = subprocess.run(
                    [get_nockchain_wallet_path()]
                    + GRPC_ARGS
                    + ["derive-child", str(i)],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                address = extract_values_from_output("Address:", result.stdout)[0]
                xpubkey = extract_values_from_output(
                    "Extended Public Key:", result.stdout
                )[0]
                xprivkey = extract_values_from_output(
                    "Extended Private Key:", result.stdout
                )[0]
                child_info = {
                    "index": i,
                    "address": address,
                    "xpubkey": xpubkey,
                    "xprivkey": xprivkey,
                    "timestamp": datetime.now().isoformat(),
                    "derive_output": result.stdout.strip() if result.stdout else None,
                }
                derived_children.append(child_info)

                wallet_state.log_message(f"✅ Child key {i} derived successfully")
                if address:
                    preview = (
                        f"{address[:16]}...{address[-8:]}"
                        if len(address) > 24
                        else address
                    )
                    wallet_state.log_message(f"   📋 Pubkey: {preview}")

            except subprocess.CalledProcessError as e:
                wallet_state.log_message(f"❌ Error deriving child {i}: {e.stderr}")
                child_info = {
                    "index": i,
                    "address": None,
                    "pubkey": None,
                    "xprivkey": None,
                    "timestamp": datetime.now().isoformat(),
                    "error": e.stderr.strip() if e.stderr else str(e),
                }
                derived_children.append(child_info)

        # After all children
        wallet_state.log_message(f"\n✅ {len(derived_children)} children processed!")
        wallet_state.log_message("Exporting CSV and saving JSON...")
        export_derived_children_csv(derived_children)
        save_derived_children(derived_children)
        wallet_state.log_message("🔹 Derivation session complete!")

    threading.Thread(target=worker, daemon=True).start()


def update_output_text(output_widget: tk.Text, q: queue.Queue) -> None:
    """Update output text from queue."""

    def process_queue():
        try:
            while True:
                msg = q.get_nowait()
                if msg is None:
                    return
                output_widget.config(state="normal")
                output_widget.insert(tk.END, msg)
                output_widget.see(tk.END)
                output_widget.config(state="disabled")
        except queue.Empty:
            pass
        output_widget.after(100, process_queue)

    process_queue()


def open_sign_message_window():
    win = create_modern_window("Sign Message", 600, 350)
    win.attributes("-topmost", True)  # keep window on top

    # Header
    header_frame = tk.Frame(win, bg="#1F2937", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    ttk.Label(
        header_frame,
        text="📝 Digital Message Signing",
        style="HeaderLabel.TLabel",
    ).pack(pady=15)

    # Content
    content_frame = tk.Frame(win, bg="white")
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)
    content = ModernFrame(content_frame)
    content.pack(fill="both", expand=True)

    ttk.Label(
        content,
        text="Message to Sign",
        style="FormLabel.TLabel",
    ).pack(anchor="w", padx=20, pady=(15, 5))

    message_frame = ttk.Frame(content, style="White.TFrame")
    message_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    message_text = tk.Text(
        message_frame,
        height=6,
        font=("Segoe UI", 10),
        relief="flat",
        bd=1,
        highlightbackground="#E5E7EB",
        highlightthickness=1,
        wrap="word",
    )
    message_text.pack(fill="both", expand=True)

    def sign_message():
        message = message_text.get("1.0", tk.END).strip()
        if not message:
            messagebox.showerror("Error", "Please enter a message to sign.")
            return

        # Clear main output and log initial messages
        wallet_state.clear_output()
        log = wallet_state.log_message
        log(f"--- Signing Message ---\n")
        log(f"Message: {message[:100]}{'...' if len(message) > 100 else ''}\n")
        log("Processing digital signature...\n")

        logAsync = wallet_state.queue_message

        def run_sign():
            try:
                proc = subprocess.Popen(
                    [get_nockchain_wallet_path()]
                    + GRPC_ARGS
                    + ["sign-message", "-m", message],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                if proc.stdout is None:
                    raise ValueError("stdout is None")

                for line in proc.stdout:
                    clean_line = ANSI_ESCAPE.sub("", line).strip()
                    if not clean_line:
                        continue

                    # Remove timestamp/metadata like I (12:20:24) [no]
                    if clean_line.startswith(("I (", "E (")):
                        idx = clean_line.find("]")
                        if idx != -1:
                            clean_line = clean_line[idx + 1 :].strip()
                        else:
                            idx = clean_line.find(")")
                            if idx != -1:
                                clean_line = clean_line[idx + 1 :].strip()

                    lower_line = clean_line.lower()
                    # Skip kernel/system logs
                    if any(
                        term in lower_line
                        for term in ["kernel::boot", "nockchain_npc.sock", "nockapp"]
                    ):
                        continue

                    # Result formatting
                    if "signed" in lower_line or "success" in lower_line:
                        logAsync(f"✅ Success: {clean_line}\n")
                    elif "error" in lower_line or "failed" in lower_line:
                        logAsync(f"Error: {clean_line}\n")
                    # ignore other info lines

                proc.stdout.close()
                proc.wait()
            except Exception as e:
                logAsync(f"Error signing message: {e}\n")

        threading.Thread(target=run_sign, daemon=True).start()
        win.destroy()

    ModernButton(content, text="Sign Message", command=sign_message).pack(
        padx=20, pady=10
    )


def open_verify_message_window():
    win = create_modern_window("Verify Message", 600, 450)
    win.attributes("-topmost", True)  # keep window on top

    # Header
    header_frame = tk.Frame(win, bg="#1F2937", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    ttk.Label(
        header_frame,
        text="🔏 Digital Signature Verification",
        style="HeaderLabel.TLabel",
    ).pack(pady=15)

    # Content
    content_frame = tk.Frame(win, bg="white")
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)
    content = ModernFrame(content_frame)
    content.pack(fill="both", expand=True)

    ttk.Label(
        content,
        text="Original Message",
        style="FormLabel.TLabel",
    ).pack(anchor="w", padx=20, pady=(15, 5))
    message_entry = ModernEntry(content, placeholder="Enter the original message...")
    message_entry.pack(fill="x", padx=20, pady=(0, 15))

    ttk.Label(
        content,
        text="Signature File Location",
        style="FormLabel.TLabel",
    ).pack(anchor="w", padx=20, pady=(0, 5))
    folder_var = tk.StringVar()
    folder_entry = ModernEntry(
        content, placeholder="Select folder containing signature file..."
    )
    folder_entry.pack(fill="x", padx=20, pady=(0, 10))

    def browse_folder():
        folder = filedialog.askdirectory(initialdir=os.path.expanduser("~"))
        if folder:
            folder_var.set(folder)
            folder_entry.entry.delete(0, tk.END)
            folder_entry.entry.insert(0, folder)
            folder_entry.entry.configure(style="Modern.TEntry")

    ModernButton(content, text="Browse", command=browse_folder, style="secondary").pack(
        padx=20, pady=(0, 15)
    )

    ttk.Label(
        content,
        text="Public Key (Base58)",
        style="FormLabel.TLabel",
    ).pack(anchor="w", padx=20, pady=(0, 5))
    pubkey_entry = ModernEntry(
        content, placeholder="Enter public key for verification..."
    )
    pubkey_entry.pack(fill="x", padx=20, pady=(0, 20))

    def verify_message():
        message = message_entry.get().strip()
        folder = folder_var.get().strip()
        pubkey = pubkey_entry.get().strip()

        if not message or not folder or not pubkey:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        sig_file = os.path.join(folder, "message.sig")
        if not os.path.isfile(sig_file):
            messagebox.showerror("Error", f"Signature file not found:\n{sig_file}")
            return

        # Clear main output
        wallet_state.clear_output()
        log = wallet_state.log_message
        log(f"➡️ Verifying message signature...\n")
        log(f"Message: {message[:50]}{'...' if len(message) > 50 else ''}")
        log(f"Signature file: {sig_file}")
        log(f"Public key: {truncate_address(pubkey)}\n")

        logAsync = wallet_state.queue_message

        def run_verify():
            try:
                proc = subprocess.Popen(
                    [get_nockchain_wallet_path()]
                    + GRPC_ARGS
                    + ["verify-message", "-m", message, "-s", sig_file, "-p", pubkey],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )

                if proc.stdout is None:
                    raise ValueError("stdout is None")

                for line in proc.stdout:
                    clean_line = ANSI_ESCAPE.sub("", line).strip()
                    if not clean_line:
                        continue

                    # Remove timestamp/metadata like I (12:12:43) [no]
                    if clean_line.startswith(("I (", "E (")):
                        idx = clean_line.find("]")
                        if idx != -1:
                            clean_line = clean_line[idx + 1 :].strip()
                        else:
                            idx = clean_line.find(")")
                            if idx != -1:
                                clean_line = clean_line[idx + 1 :].strip()

                    lower_line = clean_line.lower()
                    # Skip system logs
                    if any(
                        term in lower_line
                        for term in ["kernel::boot", "nockchain_npc.sock", "nockapp"]
                    ):
                        continue

                    # Result formatting
                    if "valid signature" in lower_line or "success" in lower_line:
                        logAsync(f"✅ Success: {clean_line}\n")
                    elif (
                        "invalid signature" in lower_line
                        or "not verified" in lower_line
                    ):
                        logAsync(f"Failed: {clean_line}\n")
                    # ignore other info lines

                proc.stdout.close()
                proc.wait()
            except Exception as e:
                logAsync(f"Error verifying message: {e}\n")

        threading.Thread(target=run_verify, daemon=True).start()
        win.destroy()

    ModernButton(content, text="Verify Signature", command=verify_message).pack(
        padx=20, pady=10
    )
