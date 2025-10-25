# Nockchain GUI Wallet

A modern, user-friendly graphical wallet interface for Nockchain, built with Python and Tkinter. This wallet provides an intuitive way to manage your Nockchain assets with features like wallet creation, transaction management, address derivation, and more.

<img width="1449" height="834" alt="image" src="https://github.com/user-attachments/assets/ffdb3618-f555-44e9-9a44-dec7ffd8b5cf" />

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

- Nockchain wallet CLI must be installed with all dependencies
- Nockchain-wallet should be on the newest version

### System Requirements

- **Python 3.8+**
- **Tkinter** (usually included with Python)
- **Pillow** (PIL) for image handling

### Dependencies

The project dependencies are defined in `pyproject.toml`. To install them:

```bash
pip install -e .
```

Or manually:

```bash
pip install pillow requests importlib-resources base58
```

## Installation

### Linux/Ubuntu

```bash
# Update system packages
sudo apt update

# Install Python and Tkinter
sudo apt install python3 python3-tk python3-pip

# Install Python dependencies
pip3 install pillow requests base58
```

### macOS

```bash
# Install Python (if not already installed)
brew install python3

# Install dependencies
pip3 install pillow requests base58
```

### Windows

```bash
# Install Python from python.org
# During installation, make sure to check "Add Python to PATH"

# Install dependencies
pip install pillow requests base58
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
3. The wallet will automatically connect to the Zorp public RPC
4. Start managing your NOCK

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

### Automatic GitHub Releases

The application is automatically built and released on GitHub:

1. **Push to main branch**: Triggers a build and creates artifacts
2. **Create a release**: Automatically builds and attaches the macOS `.app` file to the release

The built application includes the bundled `nockchain-wallet` executable for users who don't have it installed system-wide.

### Manual Building (macOS using py2app)

The build configuration is defined in `pyproject.toml` for modern PEP 517 compliance.

```bash
# Install build dependencies
pip3 install setuptools py2app pillow jaraco.text

# Build the application (alias mode for development)
python setup.py py2app --alias

# Or build full distributable app
python setup.py py2app
```

This creates a standalone `.app` bundle in the `dist/` directory.

### Download Pre-built Releases

Visit the [Releases](https://github.com/uwupunks/NockGUIWallet/releases) page to download the latest pre-built macOS application.

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

## Binary Verification

For security, the `nockchain-wallet` binary releases are signed with GPG. To verify a downloaded binary:

1. Download the binary (`nockchain-wallet`) and its signature file (`nockchain-wallet.asc`)

2. Import the public key:

   ```bash
   gpg --import keys/public_key.asc
   ```

3. Verify the signature:

   ```bash
   gpg --verify nockchain-wallet.asc nockchain-wallet
   ```

   You should see "Good signature from 'NockGUIWallet Release Signing Key <uwupunks@github.com>'".

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:

- Check the troubleshooting section above
- Review the application logs for error details
- Ensure all prerequisites are properly installed

---
