import os
import sys
import tkinter as tk
from tkinter import Toplevel, messagebox, filedialog
import threading
import subprocess
import queue
import re
import datetime
import requests  # Added for API calls

# --- Detect socket path programmatically ---

def detect_socket_path():
    # Check env var first
    socket_path = os.environ.get("NOCKCHAIN_SOCKET")
    if socket_path and os.path.exists(socket_path):
        return socket_path

    # Common candidate paths relative to home directory
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

    # --- Catch-all: recursive search for socket filename under home ---
    for root_dir, dirs, files in os.walk(home):
        if "nockchain_npc.sock" in files:
            return os.path.join(root_dir, "nockchain_npc.sock")

    return None


SOCKET_PATH = detect_socket_path()

if SOCKET_PATH is None:
    tk.Tk().withdraw()  # hide root window before messagebox
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

# --- Utility Functions ---

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

# --- Pubkey Fetching & Display ---

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def get_pubkeys():
    try:
        proc = subprocess.Popen(
            ["nockchain-wallet", "--nockchain-socket", SOCKET_PATH, "list-pubkeys"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout
            text=True
        )

        pubkeys = []
        capture_next_line = False
        in_keys_section = False

        for raw_line in proc.stdout:
            clean_line = ANSI_ESCAPE.sub('', raw_line).strip()

            # Skip until we reach "Public Keys"
            if not in_keys_section:
                if clean_line.lower().startswith("public keys"):
                    in_keys_section = True
                continue

            # Ignore blank lines
            if not clean_line:
                continue

            # If previous line said "Public Key:" but no value, capture this one
            if capture_next_line:
                match = re.search(r"'([^']+)'", clean_line)
                if match:
                    pubkeys.append(match.group(1))
                capture_next_line = False
                continue

            # Match public key if it's on the same line
            match = re.search(r"public\s+key\s*:\s*'([^']+)'", clean_line, re.IGNORECASE)
            if match:
                pubkeys.append(match.group(1))
            elif re.search(r"public\s+key\s*:\s*$", clean_line, re.IGNORECASE):
                # No value on this line → next line should have the key
                capture_next_line = True

        proc.wait()
        return pubkeys

    except Exception as e:
        print(f"Error while getting pubkeys: {e}")
        return []
        
def copy_to_clipboard(pubkey):
    root.clipboard_clear()
    root.clipboard_append(pubkey)
    messagebox.showinfo("Copied", f"Copied pubkey:\n{pubkey}")

def display_pubkeys(pubkeys):
    for widget in frame_pubkeys.winfo_children():
        widget.destroy()

    if not pubkeys:
        label = tk.Label(frame_pubkeys, text="(No pubkeys found. Click 'Get Pubkeys' to fetch.)", fg="red", bg="#C0C0C0")
        label.pack(pady=5)
    else:
        for pubkey in pubkeys:
            row = tk.Frame(frame_pubkeys, bg="#C0C0C0")
            row.pack(fill=tk.X, pady=2)

            display_pk = truncate_pubkey(pubkey)
            lbl = tk.Label(row, text=f"🔑 {display_pk}", anchor="w", bg="#C0C0C0")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn_copy = tk.Button(row, text="Copy", width=5, command=lambda pk=pubkey: copy_to_clipboard(pk))
            btn_copy.pack(side=tk.RIGHT)

# --- Check Balance Window ---

def open_check_balance_window():
    def on_check():
        pubkey = entry_pubkey.get().strip()
        if not pubkey:
            messagebox.showerror("Input error", "Please enter a pubkey.")
            return
        if not re.fullmatch(r"[A-Za-z0-9]+", pubkey):
            messagebox.showerror("Input error", "❌ Invalid pubkey format. Only alphanumeric characters allowed.")
            return

        output_text.config(state='normal')
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, f"🔍 Checking balance for:\n{pubkey}\n\nLoading...\n")
        output_text.config(state='disabled')

        q = queue.Queue()

        def run_check_balance():
            try:
                proc = subprocess.Popen(
                    ["nockchain-wallet", "--nockchain-socket", SOCKET_PATH,
                     "list-notes-by-pubkey", pubkey],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                total_assets = 0
                required_sigs_list = []

                for line in proc.stdout:
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
                    status_msg = "✅ Coins are Spendable! All required signatures = 1\n"
                else:
                    status_msg = "❌❌❌❌ Some Coins are Unspendable! Required signatures > 1 detected ❌❌❌❌\n"

                output = f"Total Assets: {total_assets} Nicks (~{nocks:.2f} Nocks)\n{status_msg}"

                q.put(output)
            except Exception as e:
                q.put(f"Error checking balance: {e}\n")
            finally:
                q.put(None)

        threading.Thread(target=run_check_balance, daemon=True).start()
        update_output_text(output_text, q)

        win.destroy()

    win = Toplevel(root)
    win.title("Check Balance")

    tk.Label(win, text="Enter pubkey:").pack(padx=10, pady=5)
    entry_pubkey = tk.Entry(win, width=80)
    entry_pubkey.pack(padx=10, pady=5)

    btn_check = tk.Button(win, text="Check Balance", command=on_check)
    btn_check.pack(pady=10)

# --- Event Handlers ---

def on_get_pubkeys():
    btn_get_pubkeys.config(state='disabled')
    output_text.config(state='normal')
    output_text.delete('1.0', tk.END)
    output_text.insert(tk.END, "🔑 Fetching Pubkeys...\nLoading...\n")
    output_text.config(state='disabled')

    def worker():
        pubkeys = get_pubkeys()
        def update_ui():
            display_pubkeys(pubkeys)
            output_text.config(state='normal')
            output_text.insert(tk.END, "\n✅ Pubkeys Loaded.\n")
            output_text.config(state='disabled')
            btn_get_pubkeys.config(state='normal')
        root.after(0, update_ui)

    threading.Thread(target=worker, daemon=True).start()

def on_send():
    inputs = [
        entry_sender.get().strip(),
        entry_recipient.get().strip(),
        entry_gift.get().strip(),
        entry_fee.get().strip()
    ]
    if not all(inputs):
        messagebox.showerror("Input error", "Please fill all fields.")
        return
    if not all(re.fullmatch(r"[A-Za-z0-9]+", inputs[i]) for i in (0, 1)):
        messagebox.showerror("Input error", "❌ Sender and Recipient pubkeys must be alphanumeric.")
        return
    if not (inputs[2].isdigit() and inputs[3].isdigit()):
        messagebox.showerror("Input error", "Gift and Fee must be numeric.")
        return

    btn_send.config(state='disabled')
    output_text.config(state='normal')
    output_text.delete('1.0', tk.END)
    output_text.insert(tk.END, "⏳ Sending transaction...\n")
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
            q.put(f"Error sending transaction: {e}\n")
        finally:
            q.put(None)

    threading.Thread(target=run_send, daemon=True).start()
    update_output_text(output_text, q)

    def reenable_btn():
        btn_send.config(state='normal')
    root.after(10000, reenable_btn)

# --- Date/Time Footer ---

def update_datetime_label():
    now = datetime.datetime.now()
    formatted = now.strftime("%b %d %H:%M")
    datetime_label.config(text=formatted)
    root.after(1000, update_datetime_label)

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

# --- Nocknames Window ---

def open_nocknames_window():
    win = Toplevel(root)
    win.title("Nocknames")
    win.geometry("900x700")
    win.configure(bg="#C0C0C0")

    # Register New button
    def open_register():
        import webbrowser
        webbrowser.open("https://nocknames.com")

    btn_register = tk.Button(win, text="Register New", command=open_register, width=15)
    btn_register.pack(pady=15)

    # Separator line
    sep = tk.Frame(win, height=2, bd=1, relief=tk.SUNKEN, bg="black")
    sep.pack(fill=tk.X, padx=5, pady=5)

    # Resolve Address Section
    frame_resolve_address = tk.LabelFrame(win, text="Resolve Name from Address", bg="#C0C0C0")
    frame_resolve_address.pack(fill=tk.X, padx=20, pady=10)

    lbl_address = tk.Label(frame_resolve_address, text="Address:", bg="#C0C0C0")
    lbl_address.grid(row=0, column=0, sticky="w", padx=5, pady=5)
    entry_address = tk.Entry(frame_resolve_address, width=60)
    entry_address.grid(row=0, column=1, padx=5, pady=5)

    btn_resolve_address = tk.Button(frame_resolve_address, text="Resolve", width=12)
    btn_resolve_address.grid(row=0, column=2, padx=5, pady=5)

    txt_resolved_name = tk.Text(frame_resolve_address, height=3, width=60, state='disabled', bg="#F0F0F0")
    txt_resolved_name.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    btn_copy_name = tk.Button(frame_resolve_address, text="Copy", width=10)
    btn_copy_name.grid(row=2, column=2, padx=5, pady=5, sticky="e")

    # Resolve Name Section
    frame_resolve_name = tk.LabelFrame(win, text="Resolve Address from Name", bg="#C0C0C0")
    frame_resolve_name.pack(fill=tk.X, padx=20, pady=10)

    lbl_name = tk.Label(frame_resolve_name, text="Name:", bg="#C0C0C0")
    lbl_name.grid(row=0, column=0, sticky="w", padx=5, pady=5)
    entry_name = tk.Entry(frame_resolve_name, width=60)
    entry_name.grid(row=0, column=1, padx=5, pady=5)

    btn_resolve_name = tk.Button(frame_resolve_name, text="Resolve", width=12)
    btn_resolve_name.grid(row=0, column=2, padx=5, pady=5)

    txt_resolved_address = tk.Text(frame_resolve_name, height=3, width=60, state='disabled', bg="#F0F0F0")
    txt_resolved_address.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    btn_copy_address = tk.Button(frame_resolve_name, text="Copy", width=10)
    btn_copy_address.grid(row=2, column=2, padx=5, pady=5, sticky="e")

    # Copy helper functions
    def copy_text(widget):
        root.clipboard_clear()
        text = widget.get('1.0', tk.END).strip()
        if text:
            root.clipboard_append(text)
            messagebox.showinfo("Copied", "Copied to clipboard.")
        else:
            messagebox.showwarning("Warning", "Nothing to copy.")

    btn_copy_name.config(command=lambda: copy_text(txt_resolved_name))
    btn_copy_address.config(command=lambda: copy_text(txt_resolved_address))

    # Resolve button functions
    def on_resolve_address():
        address = entry_address.get().strip()
        if not address:
            messagebox.showerror("Input error", "Address field is empty.")
            return
        txt_resolved_name.config(state='normal')
        txt_resolved_name.delete('1.0', tk.END)
        txt_resolved_name.insert(tk.END, "Resolving...")
        txt_resolved_name.config(state='disabled')

        def worker():
            name = resolve_nockname(address)
            result = name if name else "(No name found)"
            def update_ui():
                txt_resolved_name.config(state='normal')
                txt_resolved_name.delete('1.0', tk.END)
                txt_resolved_name.insert(tk.END, result)
                txt_resolved_name.config(state='disabled')
            win.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def on_resolve_name():
        name = entry_name.get().strip()
        if not name:
            messagebox.showerror("Input error", "Name field is empty.")
            return
        txt_resolved_address.config(state='normal')
        txt_resolved_address.delete('1.0', tk.END)
        txt_resolved_address.insert(tk.END, "Resolving...")
        txt_resolved_address.config(state='disabled')

        def worker():
            address = resolve_nockaddress(name)
            result = address if address else "(No address found)"
            def update_ui():
                txt_resolved_address.config(state='normal')
                txt_resolved_address.delete('1.0', tk.END)
                txt_resolved_address.insert(tk.END, result)
                txt_resolved_address.config(state='disabled')
            win.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    btn_resolve_address.config(command=on_resolve_address)
    btn_resolve_name.config(command=on_resolve_name)

# --- Signing ---

import re

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def open_sign_message_window():
    win = Toplevel(root)
    win.title("Sign Message")

    tk.Label(win, text="Enter message to sign:").pack(pady=10)
    entry = tk.Entry(win, width=60)
    entry.pack(pady=5)

    def sign_message():
        message = entry.get().strip()
        if not message:
            messagebox.showerror("Error", "Please enter a message.")
            return

        output_text.config(state='normal')
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, f"🖊 Signing message:\n{message}\n\nProcessing...\n")
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
                    clean_line = ANSI_ESCAPE.sub('', line).strip()  # remove ANSI codes
                    if clean_line:
                        # Only show important messages
                        if "error" in clean_line.lower():
                            q.put(f"⚠️ {clean_line}\n")
                        elif "signed" in clean_line.lower():
                            q.put(f"✅ {clean_line}\n")
                proc.stdout.close()
                proc.wait()
            except Exception as e:
                q.put(f"Error signing message: {e}\n")
            finally:
                q.put(None)

        threading.Thread(target=run_sign, daemon=True).start()
        update_output_text(output_text, q)

        win.destroy()

    tk.Button(win, text="Sign", command=sign_message).pack(pady=10)

# --- Verify Message--

# ANSI escape code regex
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def open_verify_message_window():
    win = Toplevel(root)
    win.title("Verify Message")
    win.attributes('-topmost', True)  # Window always on top

    tk.Label(win, text="Enter message to verify:").pack(pady=5)
    message_entry = tk.Entry(win, width=60)
    message_entry.pack(pady=5)

    folder_frame = tk.Frame(win)
    folder_frame.pack(pady=5, fill=tk.X, padx=5)

    tk.Label(folder_frame, text="Select folder containing signature file:").pack(side=tk.LEFT)
    folder_path_var = tk.StringVar()
    folder_entry = tk.Entry(folder_frame, textvariable=folder_path_var, width=40)
    folder_entry.pack(side=tk.LEFT, padx=5)

    def browse_folder():
        folder = filedialog.askdirectory(initialdir=os.path.expanduser("~"))
        if folder:
            folder_path_var.set(folder)

    tk.Button(folder_frame, text="Browse", command=browse_folder).pack(side=tk.LEFT)

    tk.Label(win, text="Enter public key (Base58):").pack(pady=5)
    pubkey_entry = tk.Entry(win, width=60)
    pubkey_entry.pack(pady=5)

    def verify_message():
        message = message_entry.get().strip()
        folder = folder_path_var.get().strip()
        pubkey = pubkey_entry.get().strip()

        if not message or not folder or not pubkey:
            messagebox.showerror("Error", "Please enter message, folder, and public key.")
            return

        sig_file = os.path.join(folder, "message.sig")
        if not os.path.isfile(sig_file):
            messagebox.showerror("Error", f"Signature file not found in folder:\n{sig_file}")
            return

        output_text.config(state='normal')
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, f"🕵️ Verifying message:\n{message}\n\nProcessing...\n")
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
                    # Remove ANSI codes
                    clean_line = ANSI_ESCAPE.sub('', line).strip()
                    # Skip kernel and nockchain logs
                    if any(x in clean_line.lower() for x in ["kernel::boot", "nockchain_npc.sock", "nockapp"]):
                        continue

                    if not clean_line:
                        continue

                    lower_line = clean_line.lower()
                    if "invalid signature" in lower_line or "not verified" in lower_line:
                        q.put(f"❌ {clean_line}\n")
                    elif "valid signature" in lower_line or "success" in lower_line:
                        q.put(f"✅ {clean_line}\n")

                proc.stdout.close()
                proc.wait()

            except Exception as e:
                # Only show actual verification error
                q.put(f"⚠️ Error verifying message: {e}\n")
            finally:
                q.put(None)

        threading.Thread(target=run_verify, daemon=True).start()
        update_output_text(output_text, q)
        win.destroy()

    tk.Button(win, text="Verify", command=verify_message).pack(pady=10)
    
# --- Main Window ---

root = tk.Tk()
root.title("Robinhood's Nockchain GUI Wallet")
root.geometry("900x700")
root.configure(bg="#C0C0C0")

# Top frame for buttons
top_frame = tk.Frame(root, bg="#C0C0C0")
top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

btn_get_pubkeys = tk.Button(top_frame, text="Get Pubkeys", command=on_get_pubkeys, width=15)
btn_get_pubkeys.pack(side=tk.LEFT, padx=5)

btn_check_balance = tk.Button(top_frame, text="Check Balance", command=open_check_balance_window, width=15)
btn_check_balance.pack(side=tk.LEFT, padx=5)

btn_nocknames = tk.Button(top_frame, text="Nocknames", command=open_nocknames_window, width=15)
btn_nocknames.pack(side=tk.LEFT, padx=5)

btn_sign_message = tk.Button(top_frame, text="Sign Message", command=open_sign_message_window, width=15)
btn_sign_message.pack(side=tk.LEFT, padx=5)

btn_verify_message = tk.Button(top_frame, text="Verify Message", command=open_verify_message_window, width=15)
btn_verify_message.pack(side=tk.LEFT, padx=5)

# Frame for pubkeys
frame_pubkeys = tk.Frame(root, bg="#C0C0C0")
frame_pubkeys.pack(fill=tk.X, padx=10, pady=5)

# Send transaction frame
frame_send = tk.LabelFrame(root, text="Send Transaction", bg="#C0C0C0")
frame_send.pack(fill=tk.X, padx=10, pady=10)

tk.Label(frame_send, text="Sender Pubkey:", bg="#C0C0C0").grid(row=0, column=0, sticky="e", padx=5, pady=5)
entry_sender = tk.Entry(frame_send, width=70)
entry_sender.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_send, text="Recipient Pubkey:", bg="#C0C0C0").grid(row=1, column=0, sticky="e", padx=5, pady=5)
entry_recipient = tk.Entry(frame_send, width=70)
entry_recipient.grid(row=1, column=1, padx=5, pady=5)

tk.Label(frame_send, text="Gift (Nicks):", bg="#C0C0C0").grid(row=2, column=0, sticky="e", padx=5, pady=5)
entry_gift = tk.Entry(frame_send, width=20)
entry_gift.grid(row=2, column=1, sticky="w", padx=5, pady=5)

tk.Label(frame_send, text="Fee (Nicks):", bg="#C0C0C0").grid(row=3, column=0, sticky="e", padx=5, pady=5)
entry_fee = tk.Entry(frame_send, width=20)
entry_fee.grid(row=3, column=1, sticky="w", padx=5, pady=5)

btn_send = tk.Button(frame_send, text="Send Transaction", command=on_send)
btn_send.grid(row=4, column=0, columnspan=2, pady=10)

# Output text box
output_text = tk.Text(root, height=20, bg="#F0F0F0", fg="black", state='disabled')
output_text.pack(fill=tk.BOTH, padx=10, pady=10, expand=True)

# Date/time label
datetime_label = tk.Label(root, text="", bg="#C0C0C0")
datetime_label.pack(side=tk.BOTTOM, pady=5)

update_datetime_label()

root.mainloop()  
