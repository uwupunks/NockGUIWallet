#!/bin/bash

SOCKET=~/nockchain/.socket/nockchain_npc.sock
TXS_DIR="$(pwd)/txs"

echo "========================================"
echo "       Robinhood's Simple Send"
echo "========================================"
echo

# Prompt inputs
read -rp $'📤 Sender pubkey:\n> ' sender
read -rp $'📥 Recipient pubkey:\n> ' recipient
read -rp $'🎁 Gift amount:\n> ' gift
read -rp $'💸 Fee amount:\n> ' fee

total=$((gift + fee))
echo -e "\n➕ Total amount needed (gift + fee): $total\n"

csvfile="notes-${sender}.csv"

echo "📂 Exporting notes CSV, please wait..."
if ! nockchain-wallet --nockchain-socket "$SOCKET" list-notes-by-pubkey-csv "$sender" >/dev/null 2>&1; then
  echo "❌ Failed to export notes CSV. Please check your wallet and connection."
  exit 1
fi

echo -n "⏳ Waiting for notes file ($csvfile)... "
while [ ! -f "$csvfile" ]; do
  sleep 1
done
echo "Found!"

# Select notes until total assets cover required amount
selected_notes=()
selected_assets=0
while IFS=',' read -r name_first name_last assets _block_height _source_hash; do
  [[ "$name_first" == "name_first" ]] && continue
  selected_notes+=("$name_first $name_last")
  selected_assets=$((selected_assets + assets))
  if [ "$selected_assets" -ge "$total" ]; then
    break
  fi
done < "$csvfile"

if [ "$selected_assets" -lt "$total" ]; then
  echo "❌ Insufficient funds: found $selected_assets, need $total"
  exit 1
fi

echo "✅ Selected notes: ${selected_notes[*]}"
echo "💰 Total assets selected: $selected_assets"

# Build --names argument for spend command
names_arg=""
for note in "${selected_notes[@]}"; do
  if [ -n "$names_arg" ]; then
    names_arg+=","
  fi
  names_arg+="[$note]"
done

# Build --recipients argument (single recipient at index 1)
recipients_arg="[1 $recipient]"

# Prepare transaction directory
mkdir -p "$TXS_DIR"

echo -e "\n🧹 Cleaning transaction folder ($TXS_DIR)..."
ls -1 "$TXS_DIR"
rm -f "$TXS_DIR"/*
echo "🗑️ Folder cleaned."

echo -e "\n🛠️ Creating draft transaction..."
if ! nockchain-wallet --nockchain-socket "$SOCKET" spend \
  --names "$names_arg" \
  --recipients "$recipients_arg" \
  --gifts "$gift" \
  --fee "$fee" >/dev/null 2>&1; then
  echo "❌ Failed to create draft transaction."
  exit 1
fi

# Pick any .tx file in txs directory
txfile=$(find "$TXS_DIR" -maxdepth 1 -type f -name '*.tx' | head -n 1)

if [[ -z "$txfile" ]]; then
  echo "❌ No transaction file found in $TXS_DIR after creating draft."
  exit 1
fi

echo "✅ Draft transaction created: $txfile"

echo "🚀 Sending transaction..."
if nockchain-wallet --nockchain-socket "$SOCKET" send-tx "$txfile" >/dev/null 2>&1; then
  echo "✅ Transaction sent successfully!"
else
  echo "❌ Failed to send transaction."
fi
