# Nockchain GUI Wallet

A modern, user-friendly graphical wallet interface for Nockchain, built with Python and Tkinter. This wallet provides an intuitive way to manage your Nockchain assets with features like wallet creation, transaction management, address derivation, and more.

## Features

- ✨ **Create Wallet**: Generate new Nockchain wallets
- 🧬 **Derive Children**: Derive child addresses from parent keys
- 📂 **Import/Export Keys**: Securely import and export wallet keys
- 🔑 **Address Management**: View and manage wallet addresses
- 💸 **Send Transactions**: Send NOCK tokens with custom fees
- 👨 **Nocknames Integration**: Resolve and use human-readable Nocknames
- 📝 **Message Signing**: Sign and verify messages
- 💰 **Balance Checking**: Real-time balance updates
- 📊 **Price Tracking**: Live NOCK price and market data
- 🔍 **Block Explorer**: Integrated block explorer functionality

## Prerequisites

Before running the Nockchain GUI Wallet, ensure you have the following installed:

### Nockchain CLI

- Nockchain CLI must be installed with all dependencies
- Nockchain-wallet should be on the newest version
- A Nockchain node must be running and synced to the latest block height

### System Requirements

- **Python 3.8+**
- **Tkinter** (usually included with Python)
- **Pillow** (PIL) for image handling
- **Requests** for API calls

### Dependencies

```bash
pip install pillow requests
```

## Installation

### Linux/Ubuntu

```bash
# Update system packages
sudo apt update

# Install Python and Tkinter
sudo apt install python3 python3-tk python3-pip

# Install Python dependencies
pip3 install pillow requests
```

### macOS

```bash
# Install Python (if not already installed)
brew install python3

# Install dependencies
pip3 install pillow requests
```

### Windows

```bash
# Install Python from python.org
# During installation, make sure to check "Add Python to PATH"

# Install dependencies
pip install pillow requests
```

## Setup

1. **Place Files**: Copy all wallet files into your Nockchain directory
2. **Ensure Node**: Make sure your Nockchain node is running and fully synced
3. **Icons**: Ensure `wallet.png` and `wallet.icon` are in the same directory as the main script

## Usage

### Running the Wallet

```bash
python3 main.py
```

### First Time Setup

1. Launch the application
2. Create a new wallet or import existing keys
3. The wallet will automatically connect to your local Nockchain node
4. Start managing your NOCK assets!

### Key Features Usage

#### Creating a Wallet

- Click the "✨ Create Wallet" button
- Follow the on-screen instructions

#### Sending Transactions

- Enter sender address, recipient address, amount, and fee
- Click "Send" to broadcast the transaction

#### Managing Addresses

- Click "🔑 Get Addresses" to load your wallet addresses
- Use "💰 Balance" to check specific address balances

#### Nocknames

- Use the "👨 Names" feature to resolve human-readable names
- Convert between addresses and Nocknames

## Building Standalone Application

### macOS (using py2app)

```bash
# Install py2app
pip3 install py2app

# Build the application
python3 setup.py py2app
```

This will create a standalone `.app` bundle in the `dist/` directory.

## Configuration

The wallet uses several configuration constants defined in `constants.py`:

- API endpoints for price data and Nocknames
- UI colors and styling
- Default window dimensions
- gRPC connection settings

## Troubleshooting

### Common Issues

1. **"No module named 'tkinter'"**

   - Install Tkinter: `sudo apt install python3-tk` (Linux)
   - Tkinter comes pre-installed with Python on macOS and Windows

2. **Connection Issues**

   - Ensure your Nockchain node is running
   - Check that the node is synced to the latest block height
   - Verify network connectivity

3. **Icon Not Loading**

   - Ensure `wallet.png` exists in the application directory
   - Check file permissions

4. **API Errors**
   - Check internet connectivity for price data
   - Nocknames resolution requires internet access

### Logs and Debugging

The wallet provides detailed logging in the output panel. Check the logs for error messages and connection status.

## Security Notes

- Always backup your wallet keys
- Use strong passwords for encrypted wallets
- Verify transaction details before sending
- Keep your Nockchain node updated
- Use the export feature to backup your keys regularly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Support

For issues and questions:

- Check the troubleshooting section above
- Review the application logs for error details
- Ensure all prerequisites are properly installed
- Verify your Nockchain node is running correctly

---

**Note**: This wallet requires a running Nockchain node. Make sure your node is fully synced before use.
