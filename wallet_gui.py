import tkinter as tk
from tkinter import messagebox, Toplevel
import threading
import subprocess
import queue
import re

def print_to_output(text):
    output_text.config(state='normal')
    output_text.insert(tk.END, text + "\n")
    output_text.see(tk.END)
    output_text.config(state='disabled')

def run_script_collect(command, inputs, output_queue):
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        input_text = "\n".join(inputs) + "\n"
        process.stdin.write(input_text)
        process.stdin.flush()
        process.stdin.close()

        all_lines = []
        for line in process.stdout:
            output_queue.put(line)
            all_lines.append(line.rstrip('\n'))
        process.stdout.close()
        process.wait()

        if len(all_lines) >= 2:
            output_queue.put(("LAST_TWO_LINES", all_lines[-2:]))
        else:
            output_queue.put(("LAST_TWO_LINES", all_lines))
    except Exception as e:
        output_queue.put(f"Error: {e}\n")
    finally:
        output_queue.put(None)

def run_script_stream(command, inputs, output_queue):
    try:
        full_command = ["stdbuf", "-oL"] + command if command[0].startswith("./") else command
        
        process = subprocess.Popen(
            full_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        input_text = "\n".join(inputs) + "\n"
        process.stdin.write(input_text)
        process.stdin.flush()
        process.stdin.close()

        while True:
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break
            if line:
                output_queue.put(line)
        process.stdout.close()
        process.wait()
    except Exception as e:
        output_queue.put(f"Error: {e}\n")
    finally:
        output_queue.put(None)

def update_output_text(output_text_widget, output_queue):
    try:
        while True:
            item = output_queue.get_nowait()
            if item is None:
                return
            if isinstance(item, tuple) and item[0] == "LAST_TWO_LINES":
                last_two = item[1]
                output_text_widget.config(state='normal')
                output_text_widget.insert(tk.END, "\n🧾 === Amount Summary ===\n")
                for line in last_two:
                    output_text_widget.insert(tk.END, f"{line}\n")
                output_text_widget.insert(tk.END, "======================\n")
                output_text_widget.see(tk.END)
                output_text_widget.config(state='disabled')
            else:
                output_text_widget.config(state='normal')
                output_text_widget.insert(tk.END, item)
                output_text_widget.see(tk.END)
                output_text_widget.config(state='disabled')
    except queue.Empty:
        pass
    output_text_widget.after(100, update_output_text, output_text_widget, output_queue)

def open_check_balance_window():
    def on_check():
        pubkey = entry_pubkey.get().strip()
        if not pubkey:
            messagebox.showerror("Input error", "Please enter a pubkey.")
            return
        if not re.fullmatch(r"[A-Za-z0-9]+", pubkey):
            messagebox.showerror("Input error", "❌ Invalid pubkey format. Only alphanumeric characters are allowed.")
            return

        output_text.config(state='normal')
        output_text.delete('1.0', tk.END)
        output_text.insert(tk.END, f"🔍 Checking balance for:\n{pubkey}\n\n")
        output_text.config(state='disabled')

        q = queue.Queue()
        threading.Thread(target=run_script_collect, args=(["./checkbalance.sh"], [pubkey], q), daemon=True).start()
        update_output_text(output_text, q)

        win.destroy()

    win = Toplevel(root)
    win.title("Check Balance")

    tk.Label(win, text="Enter pubkey:").pack(padx=10, pady=5)
    entry_pubkey = tk.Entry(win, width=80)
    entry_pubkey.pack(padx=10, pady=5)

    btn_check = tk.Button(win, text="Check Balance", command=on_check)
    btn_check.pack(pady=10)

def get_pubkeys():
    try:
        result = subprocess.run(
            ["nockchain-wallet", "--nockchain-socket", "/home/nikos/nockchain/.socket/nockchain_npc.sock", "list-pubkeys"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=True
        )

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

def truncate_pubkey(pk, front=8, back=8):
    if len(pk) <= front + back + 3:
        return pk
    return f"{pk[:front]}...{pk[-back:]}"

def on_get_pubkeys():
    btn_get_pubkeys.config(state='disabled')
    print_to_output("⏳ Gathering Public Keys...")

    def worker():
        pubkeys = get_pubkeys()
        root.after(0, lambda: display_pubkeys(pubkeys))

    threading.Thread(target=worker, daemon=True).start()

def display_pubkeys(pubkeys):
    print_to_output("✅ Public Keys Loaded:\n")

    for widget in frame_pubkeys.winfo_children():
        widget.destroy()

    if not pubkeys:
        print_to_output("❌ No pubkeys found.\n")
    else:
        for pubkey in pubkeys:
            row = tk.Frame(frame_pubkeys)
            row.pack(fill=tk.X, pady=2)

            display_pk = truncate_pubkey(pubkey)
            lbl = tk.Label(row, text=f"📋 {display_pk}", anchor="w")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            btn_copy = tk.Button(row, text="Copy", width=5, command=lambda pk=pubkey: copy_to_clipboard(pk))
            btn_copy.pack(side=tk.RIGHT)

    btn_get_pubkeys.config(state='normal')

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
    if not all(re.fullmatch(r"[A-Za-z0-9]+", inputs[i]) for i in (0,1)):
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
    def run_and_enable_button():
        run_script_stream(["./sendsimple.sh"], inputs, q)
        btn_send.after(0, lambda: btn_send.config(state='normal'))

    threading.Thread(target=run_and_enable_button, daemon=True).start()
    update_output_text(output_text, q)

root = tk.Tk()
root.title("Robinhood's Nockchain GUI Wallet")
root.geometry("700x600")

btn_get_pubkeys = tk.Button(root, text="Get Pubkeys", width=20, command=on_get_pubkeys)
btn_get_pubkeys.pack(pady=10)

frame_pubkeys = tk.Frame(root)
frame_pubkeys.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

btn_check_balance = tk.Button(root, text="Check Balance", width=20, command=open_check_balance_window)
btn_check_balance.pack(pady=10)

frame_send = tk.Frame(root)
frame_send.pack(pady=10, fill=tk.X, padx=10)

tk.Label(frame_send, text="Sender pubkey:").grid(row=0, column=0, sticky="w")
entry_sender = tk.Entry(frame_send, width=80)
entry_sender.grid(row=0, column=1, pady=2)

tk.Label(frame_send, text="Recipient pubkey:").grid(row=1, column=0, sticky="w")
entry_recipient = tk.Entry(frame_send, width=80)
entry_recipient.grid(row=1, column=1, pady=2)

tk.Label(frame_send, text="Gift amount:").grid(row=2, column=0, sticky="w")
entry_gift = tk.Entry(frame_send, width=20)
entry_gift.grid(row=2, column=1, sticky="w", pady=2)

tk.Label(frame_send, text="Fee amount:").grid(row=3, column=0, sticky="w")
entry_fee = tk.Entry(frame_send, width=20)
entry_fee.grid(row=3, column=1, sticky="w", pady=2)

btn_send = tk.Button(frame_send, text="Send Transaction", command=on_send)
btn_send.grid(row=4, column=0, columnspan=2, pady=10)

output_text = tk.Text(root, height=20, width=80, state='disabled')
output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

root.mainloop()
