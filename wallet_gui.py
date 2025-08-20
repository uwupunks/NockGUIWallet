import os
import sys
import tkinter as tk
from tkinter import ttk, Toplevel, messagebox, filedialog
import threading
import subprocess
import queue
import re
import datetime
import requests
from tkinter import font

# --- Enhanced Visual Components ---

class ModernButton(tk.Frame):
    def __init__(self, parent, text, command=None, style="primary", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.command = command
        self.style = style
        self.enabled = True
        
        # Style definitions
        styles = {
            "primary": {"bg": "#4F46E5", "fg": "white", "hover": "#4338CA"},
            "secondary": {"bg": "#6B7280", "fg": "white", "hover": "#4B5563"},
            "success": {"bg": "#059669", "fg": "white", "hover": "#047857"},
            "danger": {"bg": "#DC2626", "fg": "white", "hover": "#B91C1C"}
        }
        
        self.colors = styles.get(style, styles["primary"])
        
        self.button = tk.Label(
            self, 
            text=text,
            bg=self.colors["bg"],
            fg=self.colors["fg"],
            padx=20,
            pady=10,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        )
        self.button.pack(fill="both", expand=True)
        
        # Hover effects
        self.button.bind("<Enter>", self.on_enter)
        self.button.bind("<Leave>", self.on_leave)
        self.button.bind("<Button-1>", self.on_click)
        
    def on_enter(self, e):
        if self.enabled:
            self.button.config(bg=self.colors["hover"])
        
    def on_leave(self, e):
        if self.enabled:
            self.button.config(bg=self.colors["bg"])
        
    def on_click(self, e):
        if self.command and self.enabled:
            self.command()
            
    def set_enabled(self, enabled):
        self.enabled = enabled
        if enabled:
            self.button.config(cursor="hand2", bg=self.colors["bg"])
        else:
            self.button.config(cursor="arrow", bg="#9CA3AF")

class ModernFrame(tk.Frame):
    def __init__(self, parent, title=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.config(bg="#FFFFFF", relief="flat", bd=0)
        
        if title:
            title_frame = tk.Frame(self, bg="#f8fafc", height=40)
            title_frame.pack(fill="x", pady=(0, 10))
            title_frame.pack_propagate(False)
            
            title_label = tk.Label(
                title_frame,
                text=title,
                font=("Segoe UI", 12, "bold"),
                bg="#f8fafc",
                fg="#1F2937"
            )
            title_label.pack(pady=10)

class ModernEntry(tk.Frame):
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg="white")
        
        self.entry = tk.Entry(
            self,
            font=("Segoe UI", 10),
            bg="white",
            fg="#374151",
            relief="flat",
            bd=0,
            insertbackground="#4F46E5"
        )
        self.entry.pack(fill="both", expand=True, padx=12, pady=8)
        
        # Border frame
        self.border = tk.Frame(self, height=1, bg="#D1D5DB")
        self.border.pack(fill="x", side="bottom")
        
        # Placeholder functionality
        self.placeholder = placeholder
        if placeholder:
            self.show_placeholder()
            self.entry.bind("<FocusIn>", self.hide_placeholder)
            self.entry.bind("<FocusOut>", self.show_placeholder)
    
    def show_placeholder(self, event=None):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg="#9CA3AF")
    
    def hide_placeholder(self, event=None):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg="#374151")
    
    def get(self):
        value = self.entry.get()
        return "" if value == self.placeholder else value

class StatusBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg="#1F2937", height=30)
        self.pack_propagate(False)
        
        # Price info
        self.price_frame = tk.Frame(self, bg="#1F2937")
        self.price_frame.pack(side="left", padx=20)
        
        self.price_label = tk.Label(
            self.price_frame,
            text="NOCK: $0.000000",
            font=("Segoe UI", 9),
            bg="#1F2937",
            fg="#10B981"
        )
        self.price_label.pack(side="left")
        
        self.change_label = tk.Label(
            self.price_frame,
            text="▲ 0.00%",
            font=("Segoe UI", 9),
            bg="#1F2937",
            fg="#10B981"
        )
        self.change_label.pack(side="left", padx=(10, 0))
        
        # Time
        self.time_label = tk.Label(
            self,
            text="",
            font=("Segoe UI", 9),
            bg="#1F2937",
            fg="#9CA3AF"
        )
        self.time_label.pack(side="right", padx=20)
        
        self.update_time()
        self.update_price()
    
    def update_time(self):
        now = datetime.datetime.now()
        self.time_label.config(text=now.strftime("%b %d %H:%M:%S"))
        self.after(1000, self.update_time)
    
    def update_price(self):
        # Mock price update - replace with actual API call
        price, change = get_price()
        if price:
            self.price_label.config(text=f"NOCK: ${price:.6f}")
            color = "#10B981" if change >= 0 else "#EF4444"
            symbol = "▲" if change >= 0 else "▼"
            self.change_label.config(text=f"{symbol} {abs(change):.2f}%", fg=color)
        
        self.after(60000, self.update_price)  # Update every minute

# --- Original utility functions with enhancements ---

def detect_socket_path():
    socket_path = os.environ.get("NOCKCHAIN_SOCKET")
    if socket_path and os.path.exists(socket_path):
        return socket_path

    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".nockchain", ".socket", "nockchain_npc.sock"),
        os.path.join(home, "nockchain", ".socket", "nockchain_npc.sock"),
        os.path.join(home, "nockchain", "socket", "nockchain_npc.sock"),
        "/tmp/nockchain_npc.sock",
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    for root_dir, dirs, files in os.walk(home):
        if "nockchain_npc.sock" in files:
            return os.path.join(root_dir, "nockchain_npc.sock")

    return None

SOCKET_PATH = detect_socket_path()

if SOCKET_PATH is None:
    tk.Tk().withdraw()
    messagebox.showerror(
        "Error",
        "Nockchain socket path not found.\n"
        "Please set NOCKCHAIN_SOCKET environment variable or place socket in a default location:\n"
        "~/.nockchain/.socket/nockchain_npc.sock\n"
        "~/nockchain/.socket/nockchain_npc.sock\n"
        "~/nockchain/socket/nockchain_npc.sock\n"
        "/tmp/nockchain_npc.sock"
    )
    sys.exit(1)

def create_modern_window(title, width, height):
    """Helper function to create modern styled windows"""
    win = tk.Toplevel(root)
    win.title(title)
    win.geometry(f"{width}x{height}")
    win.configure(bg="#F9FAFB")
    return win

def print_to_output(text):
    output_text.config(state='normal')
    output_text.insert(tk.END, text + "\n")
    output_text.see(tk.END)
    output_text.config(state='disabled')

def update_output_text(output_text_widget, output_queue):
    try:
        while True:
            item = output_queue.get_nowait()
            if item is None:
                return
            output_text_widget.config(state='normal')
            output_text_widget.insert(tk.END, item)
            output_text_widget.see(tk.END)
            output_text_widget.config(state='disabled')
    except queue.Empty:
        pass
    output_text_widget.after(100, update_output_text, output_text_widget, output_queue)

def truncate_pubkey(pk, front=8, back=8):
    if len(pk) <= front + back + 3:
        return pk
    return f"{pk[:front]}...{pk[-back:]}"

# Price API
API_URL = "https://api.coinpaprika.com/v1/tickers/nock-nockchain"

def get_price():
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        price = data["quotes"]["USD"]["price"]
        change_24h = data["quotes"]["USD"]["percent_change_24h"]
        return price, change_24h
    except Exception:
        return 0.000123, 2.45  # Mock data
        
# Remove ANSI escape sequences
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# -------------------- PUBKEY PARSER -------------------- #
def get_pubkeys():
    try:
        proc = subprocess.Popen(
            ["nockchain-wallet", "--nockchain-socket", SOCKET_PATH, "list-pubkeys"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        pubkeys = []
        collecting_key = False
        current_key_lines = []

        for raw_line in proc.stdout:
            line = ANSI_ESCAPE.sub('', raw_line).strip()
            if not line:
                continue

            if line.startswith("- Public Key:"):
                key_part = line[len("- Public Key:"):].strip().strip("'")
                if key_part:
                    # Single-line key
                    pubkeys.append(key_part.replace(" ", ""))
                    collecting_key = False
                    current_key_lines = []
                else:
                    # Multi-line key
                    collecting_key = True
                    current_key_lines = []
                continue

            if collecting_key and line.startswith("- Chain Code:"):
                key = ''.join(current_key_lines).replace(" ", "").strip("'")
                if key:
                    pubkeys.append(key)
                collecting_key = False
                current_key_lines = []
                continue

            if collecting_key:
                current_key_lines.append(line.strip("'").strip())

        # In case the last key was not followed by a chain code
        if collecting_key and current_key_lines:
            key = ''.join(current_key_lines).replace(" ", "").strip("'")
            if key:
                pubkeys.append(key)

        proc.wait()
        return pubkeys

    except Exception as e:
        print(f"Error while getting pubkeys: {e}")
        return []

def copy_to_clipboard(pubkey):
    root.clipboard_clear()
    root.clipboard_append(pubkey)
    # Show modern notification
    show_notification("Copied!", f"Pubkey copied to clipboard")

def show_notification(title, message):
    notification = tk.Toplevel(root)
    notification.title("")
    notification.geometry("300x80+{}+{}".format(
        root.winfo_x() + root.winfo_width() - 320,
        root.winfo_y() + 50
    ))
    notification.configure(bg="#10B981")
    notification.overrideredirect(True)
    notification.attributes("-topmost", True)
    
    tk.Label(
        notification,
        text="✅ " + title,
        font=("Segoe UI", 10, "bold"),
        bg="#10B981",
        fg="white"
    ).pack(pady=5)
    
    tk.Label(
        notification,
        text=message,
        font=("Segoe UI", 9),
        bg="#10B981",
        fg="white"
    ).pack()
    
    # Auto close after 2 seconds
    notification.after(2000, notification.destroy)
    
def truncate_pubkey(key, start_chars=18, end_chars=18):
    """Shorten a public key for display purposes."""
    if len(key) <= start_chars + end_chars + 3:
        return key
    return f"{key[:start_chars]}...{key[-end_chars:]}"
    
def display_pubkeys(pubkeys):
    for widget in pubkeys_content.winfo_children():
        widget.destroy()

    if not pubkeys:
        tk.Label(pubkeys_content, text="🔑 No public keys found",
                 font=("Segoe UI", 12), bg="white", fg="#6B7280").pack(pady=20)
        return

    # State variables
    selected_index = tk.IntVar(value=0)
    dropdown_open = tk.BooleanVar(value=False)

    # Frame for dropdown
    dropdown_frame = tk.Frame(pubkeys_content, bg="white", bd=1, relief="solid")
    dropdown_frame.pack(fill="x", padx=10, pady=10)

    # Button to toggle dropdown
    selected_btn = tk.Button(
        dropdown_frame,
        text=f"Key 1: {truncate_pubkey(pubkeys[0])} ▼",
        font=("Consolas", 10),
        bg="white",
        fg="#374151",
        bd=0,
        anchor="w",
        command=lambda: toggle_dropdown()
    )
    selected_btn.pack(fill="x", padx=10, pady=5)

    # --- Scrollable dropdown (Canvas + Scrollbar) ---
    dropdown_canvas = tk.Canvas(dropdown_frame, bg="white", highlightthickness=0, height=300)
    scrollbar = tk.Scrollbar(dropdown_frame, orient="vertical", command=dropdown_canvas.yview)
    options_frame = tk.Frame(dropdown_canvas, bg="white")

    options_frame.bind(
        "<Configure>",
        lambda e: dropdown_canvas.configure(scrollregion=dropdown_canvas.bbox("all"))
    )

    window_id = dropdown_canvas.create_window((0, 0), window=options_frame, anchor="nw")
    dropdown_canvas.configure(yscrollcommand=scrollbar.set)

    # Hide initially
    dropdown_canvas.pack_forget()
    scrollbar.pack_forget()

    # Copy button + display label
    info_frame = tk.Frame(pubkeys_content, bg="white")
    info_frame.pack(fill="x", padx=10, pady=(0, 10))

    key_label = tk.Label(
        info_frame,
        text=truncate_pubkey(pubkeys[0]),
        font=("Consolas", 10),
        bg="white",
        fg="#374151"
    )
    key_label.pack(side="left", padx=(0, 10))

    copy_btn = ModernButton(
        info_frame,
        text="📋 Copy",
        style="secondary",
        command=lambda: copy_to_clipboard(pubkeys[selected_index.get()])
    )
    copy_btn.pack(side="right")
    copy_btn.config(width=80, height=35)

    # Toggle dropdown
    def toggle_dropdown():
        if dropdown_open.get():
            dropdown_canvas.pack_forget()
            scrollbar.pack_forget()
        else:
            dropdown_canvas.pack(side="left", fill="both", expand=True, padx=0, pady=5)
            scrollbar.pack(side="right", fill="y")
        dropdown_open.set(not dropdown_open.get())

    # Populate options
    for i, pk in enumerate(pubkeys):
        def select_key(idx=i):
            selected_index.set(idx)
            selected_btn.config(text=f"Key {idx+1}: {truncate_pubkey(pubkeys[idx])} ▼")
            key_label.config(text=truncate_pubkey(pubkeys[idx]))
            toggle_dropdown()

        btn = tk.Button(
            options_frame,
            text=f"Key {i+1}: {truncate_pubkey(pk)}",
            font=("Consolas", 10),
            bg="white",
            fg="#374151",
            bd=0,
            anchor="w",
            command=select_key
        )
        btn.pack(fill="x", pady=2)

        # Hover effect
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#F3F4F6"))
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg="white"))



# --- Nocknames API Calls ---

def resolve_nockname(address):
    try:
        url = f"https://api.nocknames.com/resolve?address={address}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            name = data.get("name")
            if name:
                return name
            else:
                return None
        else:
            return None
    except Exception:
        return None

def resolve_nockaddress(name):
    try:
        url = f"https://api.nocknames.com/resolve?name={name}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            address = data.get("address")
            if address:
                return address
            else:
                return None
        else:
            return None
    except Exception:
        return None

def open_check_balance_window():
    win = create_modern_window("💰 Check Balance", 600, 250)
    
    # Header
    header_frame = tk.Frame(win, bg="#1F2937", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    tk.Label(
        header_frame,
        text="💰 Check Account Balance",
        font=("Segoe UI", 14, "bold"),
        bg="#1F2937",
        fg="white"
    ).pack(pady=15)
    
    # Content frame
    content = tk.Frame(win, bg="white")
    content.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Input section
    tk.Label(content, text="Enter Pubkey:", font=("Segoe UI", 11, "bold"), bg="white", fg="#374151").pack(anchor="w", pady=(5,5))
    
    # Input frame with entry and button
    input_frame = tk.Frame(content, bg="white")
    input_frame.pack(fill="x", pady=(0,10))
    
    pubkey_entry = tk.Entry(input_frame, font=("Segoe UI", 11))
    pubkey_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    pubkey_entry.focus_set()
    
    def check_balance():
        pubkey = pubkey_entry.get().strip()
        if not pubkey:
            messagebox.showerror("Input Error", "Please enter a public key.")
            return
        if not re.fullmatch(r"[A-Za-z0-9]+", pubkey):
            messagebox.showerror("Input Error", "❌ Invalid pubkey format. Only alphanumeric characters allowed.")
            return
        
        # Show initial "Checking..." message in main GUI
        output_text.config(state='normal')
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, f"💰 Checking balance...\nAddress: {truncate_pubkey(pubkey)}\nPlease wait...\n\n")
        output_text.config(state='disabled')
        
        # Close popup immediately
        win.destroy()
        
        # Queue for main GUI output
        main_q = queue.Queue()
        
        def run_check_balance():
            try:
                proc = subprocess.Popen(
                    ["nockchain-wallet", "--nockchain-socket", SOCKET_PATH, "list-notes-by-pubkey", pubkey],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                total_assets = 0
                required_sigs_list = []
                
                for line in proc.stdout:
                    # Only extract assets and required signatures
                    m_asset = re.search(r"- Assets:\s*(\d+)", line)
                    if m_asset:
                        total_assets += int(m_asset.group(1))
                    m_sig = re.search(r"- Required Signatures:\s*(\d+)", line)
                    if m_sig:
                        required_sigs_list.append(int(m_sig.group(1)))
                
                proc.stdout.close()
                proc.wait()
                
                nocks = total_assets / 65536
                
                if not required_sigs_list:
                    status_msg = "ℹ️ No 'Required Signatures' info found in notes.\n"
                elif all(m == 1 for m in required_sigs_list):
                    status_msg = "✅ Coins are Spendable! All required signatures = 1"
                else:
                    status_msg = "❌ Some Coins are Unspendable! Required signatures > 1 detected ❌"
                
                summary = f"\n{'='*50}\n"
                summary += f"💰 BALANCE SUMMARY\n"
                summary += f"{'='*50}\n"
                summary += f"Total Assets: {total_assets:,} Nicks\n"
                summary += f"Equivalent: ~{nocks:,.4f} Nocks\n"
                summary += f"Status: {status_msg}\n"
                
                main_q.put(summary)
            except Exception as e:
                main_q.put(f"❌ Error checking balance: {e}\n")
            finally:
                main_q.put(None)
        
        threading.Thread(target=run_check_balance, daemon=True).start()
        update_output_text(output_text, main_q)
    
    check_btn = tk.Button(input_frame, text="Check", command=check_balance, bg="#4F46E5", fg="white", font=("Segoe UI", 10, "bold"), padx=20)
    check_btn.pack(side="right")

def open_nocknames_window():
    win = create_modern_window("🌐 Nocknames", 800, 600)
    
    # Header
    header_frame = tk.Frame(win, bg="#1F2937", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    header_content = tk.Frame(header_frame, bg="#1F2937")
    header_content.pack(fill="both", expand=True, padx=20, pady=15)
    
    tk.Label(
        header_content,
        text="🌐 Nocknames Resolution Service",
        font=("Segoe UI", 14, "bold"),
        bg="#1F2937",
        fg="white"
    ).pack(side="left")
    
    register_btn = ModernButton(
        header_content, 
        text="🔗 Register New",
        command=lambda: __import__('webbrowser').open("https://nocknames.com"),
        style="success"
    )
    register_btn.pack(side="right")
    
    # Main content
    main_frame = tk.Frame(win, bg="#F9FAFB")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Address to Name section
    addr_frame = ModernFrame(main_frame, title="🔍 Resolve Name from Address")
    addr_frame.pack(fill="x", pady=(0, 15))
    
    tk.Label(addr_frame, text="Wallet Address", font=("Segoe UI", 10, "bold"), bg="white", fg="#374151").pack(anchor="w", padx=20, pady=(15, 5))
    
    addr_input_frame = tk.Frame(addr_frame, bg="white")
    addr_input_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    address_entry = ModernEntry(addr_input_frame, placeholder="Enter wallet address...")
    address_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    
    addr_result = tk.Text(addr_frame, height=2, bg="#F8FAFC", fg="#374151", font=("Consolas", 9), state='disabled', relief="flat", bd=0)
    addr_result.pack(fill="x", padx=20, pady=(0, 15))
    
    def resolve_address():
        address = address_entry.get().strip()
        if not address:
            messagebox.showerror("Input Error", "Address field is empty.")
            return
        addr_result.config(state='normal')
        addr_result.delete('1.0', tk.END)
        addr_result.insert(tk.END, "🔍 Resolving...")
        addr_result.config(state='disabled')

        def worker():
            name = resolve_nockname(address)
            result = name if name else "(No name found for this address)"
            def update_ui():
                addr_result.config(state='normal')
                addr_result.delete('1.0', tk.END)
                addr_result.insert(tk.END, result)
                addr_result.config(state='disabled')
            win.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()
    
    resolve_addr_btn = ModernButton(addr_input_frame, text="🔍 Resolve", command=resolve_address, style="secondary")
    resolve_addr_btn.pack(side="right")
    
    # Name to Address section
    name_frame = ModernFrame(main_frame, title="🔍 Resolve Address from Name")
    name_frame.pack(fill="x")
    
    tk.Label(name_frame, text="Nockname", font=("Segoe UI", 10, "bold"), bg="white", fg="#374151").pack(anchor="w", padx=20, pady=(15, 5))
    
    name_input_frame = tk.Frame(name_frame, bg="white")
    name_input_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    name_entry = ModernEntry(name_input_frame, placeholder="Enter nockname...")
    name_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    
    name_result = tk.Text(name_frame, height=2, bg="#F8FAFC", fg="#374151", font=("Consolas", 9), state='disabled', relief="flat", bd=0)
    name_result.pack(fill="x", padx=20, pady=(0, 15))
    
    def resolve_name():
        name = name_entry.get().strip()
        if not name:
            messagebox.showerror("Input Error", "Name field is empty.")
            return
        name_result.config(state='normal')
        name_result.delete('1.0', tk.END)
        name_result.insert(tk.END, "🔍 Resolving...")
        name_result.config(state='disabled')

        def worker():
            address = resolve_nockaddress(name)
            result = address if address else "(No address found for this name)"
            def update_ui():
                name_result.config(state='normal')
                name_result.delete('1.0', tk.END)
                name_result.insert(tk.END, result)
                name_result.config(state='disabled')
            win.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()
    
    resolve_name_btn = ModernButton(name_input_frame, text="🔍 Resolve", command=resolve_name, style="secondary")
    resolve_name_btn.pack(side="right")

def open_sign_message_window():
    win = create_modern_window("✍️ Sign Message", 600, 350)
    
    # Header
    header_frame = tk.Frame(win, bg="#1F2937", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(
        header_frame,
        text="✍️ Digital Message Signing",
        font=("Segoe UI", 14, "bold"),
        bg="#1F2937",
        fg="white"
    ).pack(pady=15)
    
    # Content
    content = ModernFrame(win)
    content.pack(fill="both", expand=True, padx=20, pady=20)
    
    tk.Label(content, text="Message to Sign", font=("Segoe UI", 11, "bold"), bg="white", fg="#374151").pack(anchor="w", padx=20, pady=(15, 5))
    
    message_frame = tk.Frame(content, bg="white")
    message_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    message_text = tk.Text(
        message_frame, 
        height=6, 
        bg="white", 
        fg="#374151", 
        font=("Segoe UI", 10),
        relief="flat",
        bd=1,
        highlightbackground="#E5E7EB",
        highlightthickness=1,
        wrap="word"
    )
    message_text.pack(fill="both", expand=True)
    
    def sign_message():
        message = message_text.get("1.0", tk.END).strip()
        if not message:
            messagebox.showerror("Error", "Please enter a message to sign.")
            return

        output_text.config(state='normal')
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, f"✍️ Signing message...\n")
        output_text.insert(tk.END, f"Message: {message[:100]}{'...' if len(message) > 100 else ''}\n\n")
        output_text.insert(tk.END, "Processing digital signature...\n")
        output_text.config(state='disabled')

        q = queue.Queue()

        def run_sign():
            try:
                proc = subprocess.Popen(
                    ["nockchain-wallet", "--nockchain-socket", SOCKET_PATH,
                     "sign-message", "-m", message],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                for line in proc.stdout:
                    clean_line = ANSI_ESCAPE.sub('', line).strip()
                    if clean_line:
                        if "error" in clean_line.lower():
                            q.put(f"⚠️ {clean_line}\n")
                        elif "signed" in clean_line.lower():
                            q.put(f"✅ {clean_line}\n")
                        else:
                            q.put(f"{clean_line}\n")
                proc.stdout.close()
                proc.wait()
            except Exception as e:
                q.put(f"❌ Error signing message: {e}\n")
            finally:
                q.put(None)

        threading.Thread(target=run_sign, daemon=True).start()
        update_output_text(output_text, q)
        win.destroy()

    sign_btn = ModernButton(content, text="✍️ Sign Message", command=sign_message)
    sign_btn.pack(padx=20, pady=10)

def open_verify_message_window():
    win = create_modern_window("🔍 Verify Message", 700, 500)
    
    # Header
    header_frame = tk.Frame(win, bg="#1F2937", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(
        header_frame,
        text="🔍 Digital Signature Verification",
        font=("Segoe UI", 14, "bold"),
        bg="#1F2937",
        fg="white"
    ).pack(pady=15)
    
    # Content
    content = ModernFrame(win)
    content.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Message field
    tk.Label(content, text="Original Message", font=("Segoe UI", 10, "bold"), bg="white", fg="#374151").pack(anchor="w", padx=20, pady=(15, 5))
    
    message_frame = tk.Frame(content, bg="white")
    message_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    message_entry = ModernEntry(message_frame, placeholder="Enter the original message...")
    message_entry.pack(fill="x")
    
    # Signature folder
    tk.Label(content, text="Signature File Location", font=("Segoe UI", 10, "bold"), bg="white", fg="#374151").pack(anchor="w", padx=20, pady=(0, 5))
    
    folder_frame = tk.Frame(content, bg="white")
    folder_frame.pack(fill="x", padx=20, pady=(0, 15))
    
    folder_var = tk.StringVar()
    folder_entry = ModernEntry(folder_frame, placeholder="Select folder containing signature file...")
    folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    
    def browse_folder():
        folder = filedialog.askdirectory(initialdir=os.path.expanduser("~"))
        if folder:
            folder_var.set(folder)
            # Update the entry display
            folder_entry.entry.delete(0, tk.END)
            folder_entry.entry.insert(0, folder)
            folder_entry.entry.config(fg="#374151")

    browse_btn = ModernButton(folder_frame, text="📁 Browse", command=browse_folder, style="secondary")
    browse_btn.pack(side="right")
    
    # Public key field
    tk.Label(content, text="Public Key (Base58)", font=("Segoe UI", 10, "bold"), bg="white", fg="#374151").pack(anchor="w", padx=20, pady=(0, 5))
    
    pubkey_frame = tk.Frame(content, bg="white")
    pubkey_frame.pack(fill="x", padx=20, pady=(0, 20))
    
    pubkey_entry = ModernEntry(pubkey_frame, placeholder="Enter public key for verification...")
    pubkey_entry.pack(fill="x")
    
    def verify_message():
        message = message_entry.get().strip()
        folder = folder_var.get().strip() or folder_entry.get().strip()
        pubkey = pubkey_entry.get().strip()

        if not message or not folder or not pubkey:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        sig_file = os.path.join(folder, "message.sig")
        if not os.path.isfile(sig_file):
            messagebox.showerror("Error", f"Signature file not found:\n{sig_file}")
            return

        output_text.config(state='normal')
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, f"🔍 Verifying digital signature...\n")
        output_text.insert(tk.END, f"Message: {message[:50]}{'...' if len(message) > 50 else ''}\n")
        output_text.insert(tk.END, f"Signature file: {sig_file}\n")
        output_text.insert(tk.END, f"Public key: {truncate_pubkey(pubkey)}\n\n")
        output_text.config(state='disabled')

        q = queue.Queue()

        def run_verify():
            try:
                proc = subprocess.Popen(
                    [
                        "nockchain-wallet",
                        "--nockchain-socket", SOCKET_PATH,
                        "verify-message",
                        "-m", message,
                        "-s", sig_file,
                        "-p", pubkey
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in proc.stdout:
                    clean_line = ANSI_ESCAPE.sub('', line).strip()
                    if any(x in clean_line.lower() for x in ["kernel::boot", "nockchain_npc.sock", "nockapp"]):
                        continue
                    if not clean_line:
                        continue

                    lower_line = clean_line.lower()
                    if "invalid signature" in lower_line or "not verified" in lower_line:
                        q.put(f"❌ VERIFICATION FAILED: {clean_line}\n")
                    elif "valid signature" in lower_line or "success" in lower_line:
                        q.put(f"✅ VERIFICATION SUCCESS: {clean_line}\n")
                    else:
                        q.put(f"ℹ️ {clean_line}\n")

                proc.stdout.close()
                proc.wait()

            except Exception as e:
                q.put(f"⚠️ Error verifying message: {e}\n")
            finally:
                q.put(None)

        threading.Thread(target=run_verify, daemon=True).start()
        update_output_text(output_text, q)
        win.destroy()

    verify_btn = ModernButton(content, text="🔍 Verify Signature", command=verify_message)
    verify_btn.pack(padx=20, pady=10)

def on_get_pubkeys():
    btn_get_pubkeys.button.config(text="Loading...")
    btn_get_pubkeys.set_enabled(False)
    
    output_text.config(state='normal')
    output_text.delete('1.0', tk.END)
    output_text.insert(tk.END, "🔑 Fetching Public Keys...\nThis may take a moment...\n\n")
    output_text.config(state='disabled')

    def worker():
        pubkeys = get_pubkeys()
        def update_ui():
            display_pubkeys(pubkeys)
            output_text.config(state='normal')
            output_text.insert(tk.END, f"✅ Found {len(pubkeys)} public keys\n")
            if pubkeys:
                for i, pk in enumerate(pubkeys, 1):
                    output_text.insert(tk.END, f"   {i}. {pk}\n")
            output_text.config(state='disabled')
            btn_get_pubkeys.button.config(text="🔑 Get Pubkeys")
            btn_get_pubkeys.set_enabled(True)
        root.after(0, update_ui)

    threading.Thread(target=worker, daemon=True).start()

def on_send():
    # Get values from modern entries
    inputs = [
        sender_entry.get().strip(),
        recipient_entry.get().strip(),
        gift_entry.get().strip(),
        fee_entry.get().strip()
    ]
    
    if not all(inputs):
        messagebox.showerror("Input Error", "Please fill all fields.")
        return
    if not all(re.fullmatch(r"[A-Za-z0-9]+", inputs[i]) for i in (0, 1)):
        messagebox.showerror("Input Error", "❌ Sender and Recipient pubkeys must be alphanumeric.")
        return
    if not (inputs[2].isdigit() and inputs[3].isdigit()):
        messagebox.showerror("Input Error", "Gift and Fee must be numeric.")
        return

    btn_send.button.config(text="Sending...")
    btn_send.set_enabled(False)
        
    output_text.config(state='normal')
    output_text.delete('1.0', tk.END)
    output_text.insert(tk.END, "⏳ Initiating transaction...\n")
    output_text.insert(tk.END, f"From: {truncate_pubkey(inputs[0])}\n")
    output_text.insert(tk.END, f"To: {truncate_pubkey(inputs[1])}\n")
    output_text.insert(tk.END, f"Amount: {inputs[2]} Nicks\n")
    output_text.insert(tk.END, f"Fee: {inputs[3]} Nicks\n\n")
    output_text.config(state='disabled')

    q = queue.Queue()

    def run_send():
        try:
            proc = subprocess.Popen(
                ["./sendsimple.sh", "--nockchain-socket", SOCKET_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            proc.stdin.write("\n".join(inputs) + "\n")
            proc.stdin.flush()
            proc.stdin.close()

            for line in proc.stdout:
                q.put(line)
            proc.stdout.close()
            proc.wait()
        except Exception as e:
            q.put(f"❌ Error sending transaction: {e}\n")
        finally:
            q.put(None)

    threading.Thread(target=run_send, daemon=True).start()
    update_output_text(output_text, q)

    def reenable_btn():
        btn_send.button.config(text="💸 Send Transaction")
        btn_send.set_enabled(True)
    root.after(8000, reenable_btn)
    
# Header
root = tk.Tk()
root.title("Robinhood's Nockchain Wallet Pro Edition")
root.geometry("1500x1000")
root.configure(bg="#1F2937")
header = tk.Frame(root, bg="#1F2937", height=60)
header.pack(fill="x")
header.pack_propagate(False)

header_content = tk.Frame(header, bg="#1F2937")
header_content.pack(fill="both", expand=True, padx=30, pady=15)

# Logo and title
logo_frame = tk.Frame(header_content, bg="#1F2937")
logo_frame.pack(side="left")

tk.Label(
    logo_frame,
    text="💎",
    font=("Segoe UI", 20),
    bg="#1F2937"
).pack(side="left")

tk.Label(
    logo_frame,
    text="Robinhood's Nockchain Wallet Pro",
    font=("Segoe UI", 16, "bold"),
    bg="#1F2937",
    fg="white"
).pack(side="left", padx=(10, 0))

# Action buttons in header
header_buttons = tk.Frame(header_content, bg="#1F2937")
header_buttons.pack(side="right")

btn_get_pubkeys = ModernButton(header_buttons, text="🔑 Get Pubkeys", command=on_get_pubkeys)
btn_get_pubkeys.pack(side="left", padx=2)

btn_check_balance = ModernButton(header_buttons, text="💰 Balance", command=open_check_balance_window, style="secondary")
btn_check_balance.pack(side="left", padx=2)

btn_nocknames = ModernButton(header_buttons, text="🌐 Names", command=open_nocknames_window, style="secondary")
btn_nocknames.pack(side="left", padx=2)

btn_sign = ModernButton(header_buttons, text="✍️ Sign", command=open_sign_message_window, style="secondary")
btn_sign.pack(side="left", padx=2)

btn_verify = ModernButton(header_buttons, text="🔍 Verify", command=open_verify_message_window, style="secondary")
btn_verify.pack(side="left", padx=2)

# Main content area
main_container = tk.Frame(root, bg="#1F2937")
main_container.pack(fill="both", expand=True, padx=20, pady=20)

# Left panel - Main content
left_panel = tk.Frame(main_container, bg="#1F2937")
left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

# Pubkeys section
pubkeys_frame = ModernFrame(left_panel, title="🔑 Public Keys")
pubkeys_frame.pack(fill="x", pady=(0, 15))

pubkeys_content = tk.Frame(pubkeys_frame, bg="white")
pubkeys_content.pack(fill="both", expand=True, pady=10)

# Activity Log section (moved to left, below pubkeys)
output_frame = ModernFrame(left_panel, title="📋 Activity Log")
output_frame.pack(fill="both", expand=True)

output_text = tk.Text(
    output_frame,
    bg="white",
    fg="#1F2937",
    font=("Consolas", 9),
    relief="flat",
    bd=0,
    state='disabled',
    wrap="word"
)
output_text.pack(fill="both", expand=True, padx=20, pady=20)

# Scrollbar for output
scrollbar = ttk.Scrollbar(output_text)
scrollbar.pack(side="right", fill="y")
output_text.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=output_text.yview)

# Right panel - Send Transaction only
right_panel = tk.Frame(main_container, bg="#F9FAFB")
right_panel.pack(side="right", fill="y", padx=(10, 0))

# Send Transaction Panel
send_frame = ModernFrame(right_panel, title="💸 Send Transaction")
send_frame.pack(fill="x")
send_frame.config(width=400)

# Modern form fields
fields_frame = tk.Frame(send_frame, bg="white")
fields_frame.pack(fill="both", expand=True, padx=20, pady=10)

tk.Label(fields_frame, text="Sender Public Key", font=("Segoe UI", 10, "bold"), bg="white", fg="#374151").pack(anchor="w", pady=(0, 5))
sender_entry = ModernEntry(fields_frame, placeholder="Enter sender pubkey...")
sender_entry.pack(fill="x", pady=(0, 15))

tk.Label(fields_frame, text="Recipient Public Key", font=("Segoe UI", 10, "bold"), bg="white", fg="#374151").pack(anchor="w", pady=(0, 5))
recipient_entry = ModernEntry(fields_frame, placeholder="Enter recipient pubkey...")
recipient_entry.pack(fill="x", pady=(0, 15))

amounts_frame = tk.Frame(fields_frame, bg="white")
amounts_frame.pack(fill="x", pady=(0, 15))

gift_frame = tk.Frame(amounts_frame, bg="white")
gift_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
tk.Label(gift_frame, text="Gift Amount (Nicks)", font=("Segoe UI", 10, "bold"), bg="white", fg="#374151").pack(anchor="w", pady=(0, 5))
gift_entry = ModernEntry(gift_frame, placeholder="0")
gift_entry.pack(fill="x")

fee_frame = tk.Frame(amounts_frame, bg="white")
fee_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))
tk.Label(fee_frame, text="Fee (Nicks)", font=("Segoe UI", 10, "bold"), bg="white", fg="#374151").pack(anchor="w", pady=(0, 5))
fee_entry = ModernEntry(fee_frame, placeholder="0")
fee_entry.pack(fill="x")

btn_send = ModernButton(fields_frame, text="💸 Send Transaction", command=on_send, style="primary")
btn_send.pack(fill="x", pady=15)

# Status bar
status_bar = StatusBar(root)
status_bar.pack(side="bottom", fill="x")

# Initial message
output_text.config(state='normal')
output_text.insert(tk.END, "🚀 Welcome to Robinhood's Nockchain Wallet Pro Edition!\n")
output_text.insert(tk.END, "─" * 50 + "\n")
output_text.insert(tk.END, "Click 'Get Pubkeys' to load your public keys.\n\n")
output_text.insert(tk.END, f"Socket Path: {SOCKET_PATH}\n")
output_text.insert(tk.END, f"Status: Ready ✅\n")
output_text.insert(
    "end", 
    "🙏 Donate to Robinhood if you like the GUI : 2deHSdGpxFh1hhC2qMjM5ujBvG7auCeoJLcLAwGKpfSsb8zfaTms8SMdax7fCyjoVTmbqXgUDWLc7GURXtMeEZbPz57LeakGKTAWZSVYcBwyHvcHuskqL4rVrw56rPXT6wSt\n"
)
output_text.config(state='disabled')

# Initialize with empty pubkeys display
display_pubkeys([])

root.mainloop()
