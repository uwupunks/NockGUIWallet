#!/bin/bash
set -euo pipefail

# ---------------- CONFIG ---------------- #
GRPC_ARGS=(--client public --public-grpc-server-addr https://nockchain-api.zorp.io)
TXS_DIR="$(pwd)/txs"

echo "========================================"
echo "       Robinhood's Simple Send"
echo "========================================"
echo

# ---------------- ARGUMENT PARSING ---------------- #
index=""  # optional wallet index
while [[ $# -gt 0 ]]; do
  case $1 in
    --index)
      index="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

# ---------------- PROMPT INPUTS ---------------- #
read -rp $'📤 Sender pubkey:\n> ' sender
read -rp $'📥 Recipient pubkey:\n> ' recipient
read -rp $'🎁 Gift amount:\n> ' gift
read -rp $'💸 Fee amount:\n> ' fee

# Validate gift and fee
if ! [[ "$gift" =~ ^[0-9]+$ ]] || ! [[ "$fee" =~ ^[0-9]+$ ]]; then
  echo "❌ Gift and fee must be integers."
  exit 1
fi

total=$((gift + fee))
echo -e "\n➕ Total amount needed (gift + fee): $total\n"

# ---------------- EXPORT NOTES CSV ---------------- #
csvfile="notes-${sender}.csv"
echo "📂 Exporting notes CSV..."
nockchain-wallet "${GRPC_ARGS[@]}" list-notes-by-pubkey-csv "$sender" >/dev/null 2>&1 || {
  echo "❌ Failed to export notes CSV."
  exit 1
}

echo -n "⏳ Waiting for notes file ($csvfile)... "
while [ ! -f "$csvfile" ]; do sleep 1; done
echo "Found!"

# ---------------- SELECT NOTES ---------------- #
selected_notes=()
selected_assets=0

# Skip header
tail -n +2 "$csvfile" | while IFS=',' read -r name_first name_last assets _block_height _source_hash; do
  # Clean whitespace
  name_first=$(echo "$name_first" | xargs)
  name_last=$(echo "$name_last" | xargs)
  assets=$(echo "$assets" | xargs)

  # Skip if assets is not a number
  [[ "$assets" =~ ^[0-9]+$ ]] || continue

  selected_notes+=("$name_first $name_last")
  selected_assets=$((selected_assets + assets))

  # Stop once total assets >= required amount
  if [ "$selected_assets" -ge "$total" ]; then
    break
  fi
done

if [ "$selected_assets" -lt "$total" ]; then
  echo "❌ Insufficient funds: found $selected_assets, need $total"
  exit 1
fi

echo "✅ Selected notes: ${selected_notes[*]}"
echo "💰 Total assets selected: $selected_assets"

# ---------------- BUILD ARGUMENTS ---------------- #
names_arg=""
for note in "${selected_notes[@]}"; do
  [[ -n "$names_arg" ]] && names_arg+=","
  names_arg+="\"[$note]\""
done

recipients_arg="\"[${gift} ${recipient}]\""

# Clean transaction folder
mkdir -p "$TXS_DIR"
echo -e "\n🧹 Cleaning transaction folder ($TXS_DIR)..."
rm -f "$TXS_DIR"/*
echo "🗑️ Folder cleaned."

# Build optional index array
index_arg=()
if [[ -n "$index" ]]; then
  index_arg=(--index "$index")
fi

# ---------------- CREATE TRANSACTION ---------------- #
echo -e "\n🛠️ Creating draft transaction..."
echo "Command: nockchain-wallet ${GRPC_ARGS[*]} create-tx --names $names_arg --recipients $recipients_arg --gifts $gift --fee $fee ${index_arg[*]}"

nockchain-wallet "${GRPC_ARGS[@]}" create-tx \
  --names "$names_arg" \
  --recipients "$recipients_arg" \
  --gifts "$gift" \
  --fee "$fee" \
  "${index_arg[@]}" >/dev/null || {
    echo "❌ Failed to create draft transaction."
    exit 1
}

# ---------------- PICK TX FILE ---------------- #
txfile=$(find "$TXS_DIR" -maxdepth 1 -type f -name '*.tx' | head -n 1)
if [[ -z "$txfile" ]]; then
  echo "❌ No transaction file found after creating draft."
  exit 1
fi

echo "✅ Draft transaction created: $txfile"

# ---------------- SEND TRANSACTION ---------------- #
echo "🚀 Sending transaction..."
if output=$(nockchain-wallet "${GRPC_ARGS[@]}" send-tx "$txfile" 2>&1 | grep -vE '^\x1b\[.*m(I|\[I)'); then
  echo "$output" | grep -v "nockchain_wallet"
  echo "✅ Transaction sent successfully!"
else
  echo "❌ Failed to send transaction."
fi
