import tkinter as tk
from tkinter import messagebox, Toplevel
import threading
import subprocess
import queue
import re
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Utility Functions ---

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
    except Exception as e:
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
    except Exception as e:
        return None

def show_resolved_name(address):
    if not address:
        messagebox.showerror("Input error", "Address field is empty.")
        return
    name = resolve_nockname(address)
    messagebox.showinfo("Resolved Name", f"Address: {address}\nName: {name}")

def show_resolved_address(name):
    if not name:
        messagebox.showerror("Input error", "Name field is empty.")
        return
    address = resolve_nockaddress(name)
    messagebox.showinfo("Resolved Address", f"Name: {name}\nAddress: {address}")
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

def format_pubkey(pk, front=8, back=8):
    #return resolved nockname if possible
    name = resolve_nockname(pk)
    if name:
        return name
    if len(pk) <= front + back + 3:
        return pk
    return f"{pk[:front]}...{pk[-back:]}"

# --- Pubkey Fetching & Display ---

def get_pubkeys():
    try:
        # Load environment variables
        socket_path = os.getenv('NOCKCHAIN_SOCKET')
        if not socket_path:
            messagebox.showerror("Error", "NOCKCHAIN_SOCKET not set in .env file")
            return []
            
        result = subprocess.run(
            ["nockchain-wallet", "--nockchain-socket", socket_path, "list-pubkeys"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        # Extract pubkeys from output - format depends on your wallet output
        lines = result.stdout.splitlines()
        pubkeys = []
        capture = False
        buffer = []

        for line in lines:
            if "- Public Key:" in line:
                capture = True
                buffer = []
                continue
            if capture:
                if line.strip().startswith("- Chain Code:"):
                    key = "".join(buffer).replace("'", "").replace("\n", "").strip()
                    if key:
                        pubkeys.append(key)
                    capture = False
                else:
                    buffer.append(line.strip())
        return pubkeys

    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to get pubkeys:\n{e.stderr}")
        return []

def copy_to_clipboard(pubkey):
    root.clipboard_clear()
    root.clipboard_append(pubkey)
    messagebox.showinfo("Copied", f"Copied pubkey:\n{pubkey}")

def display_pubkeys(pubkeys):
    for widget in frame_pubkeys.winfo_children():
        widget.destroy()

    if not pubkeys:
        label = tk.Label(frame_pubkeys, text="(No pubkeys found. Click 'Get Pubkeys' to fetch.)", fg="red")
        label.pack(pady=5)
    else:
        for pubkey in pubkeys:
            row = tk.Frame(frame_pubkeys)
            row.pack(fill=tk.X, pady=2)

            display_pk = format_pubkey(pubkey)
            lbl = tk.Label(row, text=f"🔑 {display_pk}", anchor="w")
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

        # Clear and show checking message
        output_text.config(state='normal')
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, f"🔍 Checking balance for:\n{pubkey}\n\nLoading...\n")
        output_text.config(state='disabled')

        q = queue.Queue()

        def run_check_balance():
            try:
                # Run list-notes-by-pubkey command
                proc = subprocess.Popen(
                    ["nockchain-wallet", "--nockchain-socket", "/home/nikos/nockchain/.socket/nockchain_npc.sock",
                     "list-notes-by-pubkey", pubkey],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                all_lines = []
                total_assets = 0
                required_sigs_list = []

                for line in proc.stdout:
                    all_lines.append(line.rstrip('\n'))

                    # Extract asset line (e.g., "- Assets: 12345678")
                    m_asset = re.search(r"- Assets:\s*(\d+)", line)
                    if m_asset:
                        total_assets += int(m_asset.group(1))

                    # Extract required signatures (e.g., "- Required Signatures: 2")
                    m_sig = re.search(r"- Required Signatures:\s*(\d+)", line)
                    if m_sig:
                        required_sigs_list.append(int(m_sig.group(1)))

                proc.stdout.close()
                proc.wait()

                # Convert total assets from Nicks to Nocks
                nocks = total_assets / 65536

                # Determine if coins are spendable
                if not required_sigs_list:
                    status_msg = "ℹ️ No 'Required Signatures' info found in notes.\n"
                elif all(m == 1 for m in required_sigs_list):
                    status_msg = "✅ Coins are Spendable! All required signatures = 1\n"
                else:
                    status_msg = "❌❌❌❌ Some Coins are Unspendable! Required signatures > 1 detected ❌❌❌❌\n"

                # Prepare output
                output = f"Total Assets: {total_assets} Nicks (~{nocks:.2f} Nocks)\n{status_msg}"

                q.put(output)
            except Exception as e:
                q.put(f"Error checking balance: {e}\n")
            finally:
                q.put(None)

        threading.Thread(target=run_check_balance, daemon=True).start()
        update_output_text(output_text, q)

        # Close the check balance window immediately after pressing check
        win.destroy()

    win = Toplevel(root)
    win.title("Check Balance")

    tk.Label(win, text="Enter pubkey:").pack(padx=10, pady=5)
    entry_pubkey = tk.Entry(win, width=80)
    entry_pubkey.pack(padx=10, pady=5)

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    btn_check = tk.Button(btn_frame, text="Check Balance", command=on_check)
    btn_check.pack(side=tk.LEFT, padx=5)
    btn_resolve = tk.Button(btn_frame, text="Resolve Name", command=lambda: show_resolved_name(entry_pubkey.get().strip()))
    btn_resolve.pack(side=tk.LEFT, padx=5)
    btn_resolve_addr = tk.Button(btn_frame, text="Resolve Address", command=lambda: show_resolved_address(entry_pubkey.get().strip()))
    btn_resolve_addr.pack(side=tk.LEFT, padx=5)

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
    output_text.insert(tk.END, "🚀 Sending transaction...\n")
    output_text.config(state='disabled')

    q = queue.Queue()

    def run_send():
        try:
            proc = subprocess.Popen(
                ["./sendsimple.sh"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            input_text = "\n".join(inputs) + "\n"
            proc.stdin.write(input_text)
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
    btn_send.config(state='normal')

# --- Main Window Setup ---

root = tk.Tk()
root.title("Robinhood's Nockchain GUI Wallet")
root.geometry("800x600")
root.configure(bg="#C0C0C0")

# Frame for pubkeys display
frame_pubkeys = tk.Frame(root, bg="#C0C0C0")
frame_pubkeys.pack(fill=tk.X, padx=10, pady=5)

# Buttons
btn_get_pubkeys = tk.Button(root, text="Get Pubkeys", command=on_get_pubkeys, width=15)
btn_get_pubkeys.pack(pady=5)

btn_check_balance = tk.Button(root, text="Check Balance", command=open_check_balance_window, width=15)
btn_check_balance.pack(pady=5)

# Inputs for send
frame_send = tk.Frame(root, bg="#C0C0C0")
frame_send.pack(padx=10, pady=10, fill=tk.X)

tk.Label(frame_send, text="Sender Pubkey:", bg="#C0C0C0").grid(row=0, column=0, sticky="e", padx=5, pady=2)
entry_sender = tk.Entry(frame_send, width=80)
entry_sender.grid(row=0, column=1, pady=2)

tk.Label(frame_send, text="Recipient Pubkey:", bg="#C0C0C0").grid(row=1, column=0, sticky="e", padx=5, pady=2)
entry_recipient = tk.Entry(frame_send, width=80)
entry_recipient.grid(row=1, column=1, pady=2)

tk.Label(frame_send, text="Gift Amount (Nicks):", bg="#C0C0C0").grid(row=2, column=0, sticky="e", padx=5, pady=2)
entry_gift = tk.Entry(frame_send, width=20)
entry_gift.grid(row=2, column=1, sticky="w", pady=2)

tk.Label(frame_send, text="Fee (Nicks):", bg="#C0C0C0").grid(row=3, column=0, sticky="e", padx=5, pady=2)
entry_fee = tk.Entry(frame_send, width=20)
entry_fee.grid(row=3, column=1, sticky="w", pady=2)

btn_send = tk.Button(root, text="Send Transaction", command=on_send, width=20)
btn_send.pack(pady=10)

# Output Text widget with Win95 style
output_text = tk.Text(root, height=15, bg="white", fg="black", relief="sunken", borderwidth=2)
output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
output_text.config(state='disabled')

root.mainloop()
