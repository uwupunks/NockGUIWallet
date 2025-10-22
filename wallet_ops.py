"""Wallet operations for the Nockchain GUI Wallet.

This module contains functions for interacting with the Nockchain wallet,
including key management, balance checking, and transaction operations.
"""

import os
import csv
import queue
import subprocess
import threading
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import re

from state import wallet_state
from constants import GRPC_ARGS, ANSI_ESCAPE, CSV_FOLDER, get_nockchain_wallet_path


def get_addresses() -> List[str]:
    """Get list of wallet addresses.

    Returns:
        List of wallet addresses
    """
    try:
        proc = subprocess.Popen(
            [get_nockchain_wallet_path()] + GRPC_ARGS + ["list-master-addresses"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        output, _ = proc.communicate()
        proc.wait()

        addresses = extract_values_from_output("Address:", output)
        return addresses

    except Exception as e:
        wallet_state.log_message(f"Error while getting addresses: {e}")
        return []


def create_wallet() -> None:
    """Create a new wallet."""
    wallet_state.clear_output()
    wallet_state.log_message("Creating new wallet...")

    def worker():
        try:
            proc = subprocess.Popen(
                [get_nockchain_wallet_path()] + GRPC_ARGS + ["keygen"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            if proc.stdout is None:
                raise ValueError("stdout is None")

            for raw_line in proc.stdout:
                clean_line = ANSI_ESCAPE.sub("", raw_line)
                if "kernel::boot" in clean_line or "Tracy" in clean_line:
                    continue
                wallet_state.queue_message(clean_line)

            proc.stdout.close()
            proc.wait()
            wallet_state.queue_message("✅ Wallet created successfully!")

        except Exception as e:
            wallet_state.queue_message(f"❌ Error creating wallet: {e}")

    threading.Thread(target=worker, daemon=True).start()


def export_keys() -> None:
    """Export wallet keys."""
    wallet_state.clear_output()
    wallet_state.log_message("✨ Exporting wallet keys...")

    def worker():
        try:
            proc = subprocess.Popen(
                [get_nockchain_wallet_path()] + GRPC_ARGS + ["export-keys"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            if proc.stdout is None:
                raise ValueError("stdout is None")

            export_path = "keys.export"  # fallback default

            for raw_line in proc.stdout:
                line = ANSI_ESCAPE.sub("", raw_line).strip()
                if not line:
                    continue

                if "kernel::boot" in line or "Tracy tracing" in line:
                    continue

                if "Path:" in line:
                    export_path = line.split("Path:")[-1].strip(" '")
                    wallet_state.log_message(f"📂 Keys exported to: {export_path}")
                    continue

            proc.stdout.close()
            proc.wait()
            wallet_state.log_message("✅ Wallet keys exported successfully!")

        except Exception as e:
            wallet_state.log_message(f"❌ Error exporting keys: {e}")

    threading.Thread(target=worker, daemon=True).start()


def import_keys(file_path: str) -> None:
    """Import wallet keys from file.

    Args:
        file_path: Path to the keys export file
    """
    wallet_state.clear_output()
    wallet_state.log_message(f"📂 Loading Wallet from:\n{file_path}\n\n")
    wallet_state.log_message("⏳ Importing keys, please wait...")

    def worker():
        try:
            process = subprocess.Popen(
                [get_nockchain_wallet_path()]
                + GRPC_ARGS
                + ["import-keys", "--file", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if process.stdout is None or process.stderr is None:
                raise ValueError("stdout or stderr is None")

            # Stream stdout
            for line in process.stdout:
                clean_line = ANSI_ESCAPE.sub("", line.strip())
                if clean_line and not (
                    clean_line.startswith("I [") and "kernel::boot" in clean_line
                ):
                    wallet_state.log_message(clean_line)

            # Stream stderr
            for line in process.stderr:
                clean_line = ANSI_ESCAPE.sub("", line.strip())
                if clean_line:
                    wallet_state.log_message(clean_line)

            return_code = process.wait()

            if return_code == 0:
                wallet_state.log_message("\n✅ Keys imported successfully!")
            else:
                wallet_state.log_message("\n❌ Failed to import keys. See log above.")

        except Exception as e:
            wallet_state.log_message(f"\n❌ Error importing keys: {e}")

    threading.Thread(target=worker, daemon=True).start()


def check_balance(address: str) -> None:
    """Check balance for a given address.

    Args:
        address: The address to check balance for
    """
    wallet_state.clear_output()

    def run_balance_check():
        try:
            wallet_state.log_message(
                f"🔹 Checking balance for {truncate_address(address)}..."
            )

            # Run CSV command; wallet creates CSV automatically
            subprocess.run(
                [get_nockchain_wallet_path()]
                + GRPC_ARGS
                + ["list-notes-by-pubkey-csv", address],
                check=True,
                cwd=CSV_FOLDER,
            )
            wallet_state.log_message("✅ Balance CSV generated successfully!")

            # Set active master address
            # TODO: move this to ui_handlers.py once refactored
            wallet_state.log_message(f"🔹 Setting active master address...")
            subprocess.run(
                [get_nockchain_wallet_path()]
                + GRPC_ARGS
                + ["set-active-master-address", address],
                check=True,
                cwd=CSV_FOLDER,
            )
            wallet_state.log_message("✅ Set active successfully!")

            # Parse CSV for summary
            total_assets, nocks = parse_balance_csv(address)
            wallet_state.update_balance_display(nocks, total_assets)

        except Exception as e:
            wallet_state.log_message(f"❌ Error checking balance: {e}")

    threading.Thread(target=run_balance_check, daemon=True).start()


def parse_balance_csv(address: str) -> Tuple[int, float]:
    """Parse balance CSV file for a given address.

    Args:
        address: The address to parse balance for

    Returns:
        Tuple of (total_assets, nocks)
    """
    csv_files = [f for f in os.listdir(CSV_FOLDER) if f.startswith(f"notes-{address}")]

    if not csv_files:
        wallet_state.log_message("⚠️ No balance CSV found for this address.")
        return 0, 0.0

    # If multiple, pick the latest by modification time
    csv_files.sort(
        key=lambda f: os.path.getmtime(os.path.join(CSV_FOLDER, f)), reverse=True
    )
    latest_csv = csv_files[0]
    csv_path = os.path.join(CSV_FOLDER, latest_csv)
    wallet_state.log_message(f"📄 Reading CSV: {latest_csv}")

    total_assets = 0
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) > 2 and row[2].isdigit():
                total_assets += int(row[2])

    nocks = total_assets / 65536
    usd_balance = nocks * wallet_state.price
    wallet_state.log_message(
        f"💰 Total Assets: {total_assets} Nicks (~{nocks:.4f} NOCK, ${usd_balance:.2f} USD)"
    )
    return total_assets, nocks


def send_transaction(
    sender: str, recipient: str, amount: int, fee: int, index: Optional[str] = None
) -> None:
    """Send a transaction asynchronously using pure Python implementation.

    Args:
        sender: Sender's address
        recipient: Recipient's address
        amount: Amount in Nicks
        fee: Fee in Nicks
        index: Optional index for child key
    """

    def run_transaction():
        try:
            total_needed = amount + fee
            wallet_state.log_message(
                f"➕ Total amount needed (gift + fee): {total_needed}"
            )

            # Export notes CSV
            csvfile = f"notes-{sender}.csv"
            wallet_state.log_message("📂 Exporting notes CSV...")

            subprocess.run(
                [get_nockchain_wallet_path()]
                + GRPC_ARGS
                + ["list-notes-by-pubkey-csv", sender],
                check=True,
                cwd=os.getcwd(),
            )

            # Wait for CSV file
            wallet_state.log_message("⏳ Waiting for notes file...")
            import time

            while not os.path.exists(csvfile):
                time.sleep(1)
            wallet_state.log_message("✅ Found notes CSV!")

            # Parse CSV and select notes
            selected_notes = []
            selected_assets = 0

            with open(csvfile, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row[0] == "name_first":  # Skip header
                        continue
                    name_first, name_last, assets_str, _, _ = row
                    assets = int(assets_str)
                    selected_notes.append(f"{name_first} {name_last}")
                    selected_assets += assets
                    if selected_assets >= total_needed:
                        break

            if selected_assets < total_needed:
                raise ValueError(
                    f"❌ Insufficient funds: found {selected_assets}, need {total_needed}"
                )

            wallet_state.log_message(f"✅ Selected notes: {', '.join(selected_notes)}")
            wallet_state.log_message(f"💰 Total assets selected: {selected_assets}")

            # Build transaction arguments
            names_arg = ",".join(f"[{note}]" for note in selected_notes)
            recipients_arg = f"[1 {recipient}]"

            # Prepare transaction folder
            txs_dir = os.path.join(os.getcwd(), "txs")
            os.makedirs(txs_dir, exist_ok=True)
            wallet_state.log_message(f"🧹 Cleaning transaction folder ({txs_dir})...")

            # Clean existing tx files
            for f in os.listdir(txs_dir):
                if f.endswith(".tx"):
                    os.remove(os.path.join(txs_dir, f))
            wallet_state.log_message("🗑️ Folder cleaned.")

            # Create transaction
            wallet_state.log_message("🛠️ Creating draft transaction...")

            cmd = [
                get_nockchain_wallet_path(),
                "--client",
                "public",
                "--public-grpc-server-addr",
                "https://nockchain-api.zorp.io",
                "create-tx",
                "--names",
                names_arg,
                "--recipients",
                recipients_arg,
                "--gifts",
                str(amount),
                "--fee",
                str(fee),
            ]

            if index:
                cmd.extend(["--index", index])

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=txs_dir)
            if result.returncode != 0:
                raise Exception(f"Failed to create transaction: {result.stderr}")

            # Find the created .tx file
            tx_files = [f for f in os.listdir(txs_dir) if f.endswith(".tx")]
            if not tx_files:
                raise Exception("❌ No transaction file found after creating draft.")

            txfile = os.path.join(txs_dir, tx_files[0])
            wallet_state.log_message(f"✅ Draft transaction created: {txfile}")

            # Send transaction
            wallet_state.log_message("🚀 Sending transaction...")
            result = subprocess.run(
                [get_nockchain_wallet_path()] + GRPC_ARGS + ["send-tx", txfile],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise Exception(f"❌ Failed to send transaction: {result.stderr}")

            wallet_state.log_message("📝 Transaction details:")
            wallet_state.log_message(result.stdout.strip())
            wallet_state.log_message("✅ Transaction sent successfully!")

            # Extract transaction ID and check acceptance
            tx_id = os.path.splitext(os.path.basename(txfile))[0]
            wallet_state.log_message("🔍 Checking transaction acceptance status...")
            wallet_state.log_message(f"Transaction ID: {tx_id}")

            # Check transaction status multiple times
            max_attempts = 5
            for attempt in range(1, max_attempts + 1):
                wallet_state.log_message(f"📊 Attempt {attempt} of {max_attempts}...")

                result = subprocess.run(
                    [get_nockchain_wallet_path()] + GRPC_ARGS + ["tx-accepted", tx_id],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0 and "accepted by node" in result.stdout:
                    wallet_state.log_message("Transaction Status:")
                    wallet_state.log_message(result.stdout.strip())
                    wallet_state.log_message(
                        "✅ Transaction has been accepted by the node!"
                    )
                    break
                elif attempt < max_attempts:
                    wallet_state.log_message(
                        "⏳ Transaction not yet accepted. Waiting before next check..."
                    )
                    time.sleep(10)
                else:
                    wallet_state.log_message("⚠️ Final status check results:")
                    wallet_state.log_message(result.stdout.strip())
                    wallet_state.log_message(
                        f"⚠️ Transaction status unclear after {max_attempts} attempts."
                    )

            # Re-enable button after completion
            def reenable_btn():
                if wallet_state.btn_send:
                    wallet_state.btn_send.configure(text="Send Transaction")
                    wallet_state.btn_send.set_enabled(True)

            if wallet_state.root:
                wallet_state.root.after(0, reenable_btn)

        except Exception as e:
            wallet_state.log_message(f"❌ Error sending transaction: {e}")

            # Re-enable button on error too
            def reenable_btn():
                if wallet_state.btn_send:
                    wallet_state.btn_send.configure(text="Send Transaction")
                    wallet_state.btn_send.set_enabled(True)

            if wallet_state.root:
                wallet_state.root.after(0, reenable_btn)

    # Start transaction in background thread
    thread = threading.Thread(target=run_transaction, daemon=True)
    thread.start()


def truncate_address(address: str, start_chars: int = 8, end_chars: int = 8) -> str:
    """Truncate an address or key for display.

    Args:
        address: The address to truncate
        start_chars: Number of characters to show at start
        end_chars: Number of characters to show at end

    Returns:
        Truncated address string
    """
    if len(address) <= start_chars + end_chars + 3:
        return address
    return f"{address[:start_chars]}...{address[-end_chars:]}"


def export_derived_children_csv(derived_children):
    """Export derived children indexes and addresses to CSV."""
    if not derived_children:
        wallet_state.log_message("⚠️ No derived children found.")
        return

    filename = os.path.join(os.getcwd(), "childrenindexes.csv")
    try:
        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["index", "address"])
            for child in derived_children:
                writer.writerow([child["index"], child.get("address") or ""])

        wallet_state.log_message(f"📊 Derived children CSV exported: {filename}")
    except Exception as e:
        wallet_state.log_message(f"⚠️ Could not export CSV: {str(e)}")


def save_derived_children(children_list):
    """Save derived children information to a JSON file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"derived_children_{timestamp}.json"
        save_data = {
            "derivation_session": timestamp,
            "total_children": len(children_list),
            "children": children_list,
        }
        with open(filename, "w") as f:
            json.dump(save_data, f, indent=2)

        wallet_state.log_message(f"📁 Child indices saved to: {filename}")
    except Exception as e:
        wallet_state.log_message(f"⚠️ Warning: Could not save indices: {str(e)}")


def remove_ansi_and_newlines(text: str) -> str:
    return (
        ANSI_ESCAPE.sub("", text)
        .replace("\r\n", "")
        .replace("\n", "")
        .replace("\r", "")
    )


def extract_values_from_output(value: str, output: str) -> List[str]:
    clean_output = remove_ansi_and_newlines(output)
    values = re.findall(
        r"(?:" + value + r"\s*\n?)([a-z0-9]{30,})", clean_output, re.IGNORECASE
    )
    if not values:
        wallet_state.log_message(f"⚠️ No values found for '{value}' in output.")
        values = [""]
    return values
