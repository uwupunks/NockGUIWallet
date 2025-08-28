#!/bin/bash

GRPC_ADDRESS="http://localhost:5555"

read -p "Enter pubkey: " PUBKEY

# Validate pubkey format (alphanumeric only)
if [[ ! "$PUBKEY" =~ ^[a-zA-Z0-9]+$ ]]; then
  echo "❌ Invalid pubkey format. Only alphanumeric characters are allowed."
  exit 1
fi

CSV_FILE="notes-${PUBKEY}.csv"

# Delete old CSV if it exists
if [[ -f "$CSV_FILE" ]]; then
  echo "🧹 Removing old CSV file: $CSV_FILE"
  rm -f "$CSV_FILE"
fi

# Generate new CSV using gRPC address (suppress output)
echo "📄 Generating new CSV file for pubkey: $PUBKEY"
nockchain-wallet --grpc-address "$GRPC_ADDRESS" list-notes-by-pubkey-csv "$PUBKEY" > /dev/null 2>&1

# Wait briefly for file creation
sleep 1

# Confirm new file was created
if [[ ! -f "$CSV_FILE" ]]; then
  echo "❌ Failed to generate CSV file for pubkey."
  exit 1
fi

echo "✅ Using CSV file: $CSV_FILE"
echo

TOTAL_NICKS=0
NOTE_NUM=1

# Read and process the CSV, skipping header and malformed lines
while IFS=',' read -r name_first name_last assets block_height source_hash; do
  if [[ "$name_first" == "name_first" || -z "$assets" ]]; then
    continue
  fi
  if [[ "$assets" =~ ^[0-9]+$ ]]; then
    NICKS=$assets
    NOCKS=$(awk -v n="$NICKS" 'BEGIN { printf "%.4f", n/65536 }')
    echo "Note $NOTE_NUM: $NICKS Nicks / ≈ $NOCKS Nocks"
    TOTAL_NICKS=$((TOTAL_NICKS + NICKS))
    NOTE_NUM=$((NOTE_NUM + 1))
  fi
done < <(tr -d '\000' < "$CSV_FILE")  # Strip null bytes just in case

# Check total balance
if (( TOTAL_NICKS == 0 )); then
  echo "ℹ️  No assets found for pubkey: $PUBKEY"
  exit 0
fi

TOTAL_NOCKS=$(awk -v t="$TOTAL_NICKS" 'BEGIN { printf "%.4f", t/65536 }')

echo
echo "💰 Total balance for pubkey: $PUBKEY"
echo "  $TOTAL_NICKS Nicks"
echo "  ≈ $TOTAL_NOCKS Nocks (decimal)"
