"""API handlers for the Nockchain GUI Wallet.

This module contains functions for interacting with external APIs,
including price data and nockname resolution.
"""

import requests
from typing import Optional, Tuple

from state import wallet_state
from constants import API_URL


def get_price() -> Tuple[float, float]:
    """Get current NOCK price and 24h change from API.

    Returns:
        Tuple of (price, change_percentage)
    """
    try:
        response = requests.get(API_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            price = float(data["quotes"]["USD"]["price"])
            change = float(data["quotes"]["USD"]["percent_change_24h"])
            wallet_state.update_price(price, change)
            return price, change
        return 0.0, 0.0
    except Exception:
        return 0.0, 0.0


def is_rpc_up() -> bool:
    """Check if Nockchain API is running.

    Returns:
        True if API is running, False otherwise
    """
    try:
        response = requests.get("https://nockchain-api.zorp.io", timeout=5)
        is_connected = response.status_code == 200
        wallet_state.update_node_status(is_connected)
        return is_connected
    except Exception as e:
        wallet_state.queue_message(f"Error checking API: {e}")
        wallet_state.update_node_status(False)
        return False


def resolve_nockname(address: str) -> Optional[str]:
    """Resolve nockname from address.

    Args:
        address: The address to resolve

    Returns:
        The resolved nockname or None if not found
    """
    try:
        url = f"https://api.nocknames.com/resolve?address={address}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("name"):
                return data["name"]
        return None
    except Exception:
        return None


def resolve_nockaddress(name: str) -> Optional[str]:
    """Resolve address from nockname.

    Args:
        name: The nockname to resolve

    Returns:
        The resolved address or None if not found
    """
    try:
        url = f"https://api.nocknames.com/resolve?name={name}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("address"):
                return data["address"]
        return None
    except Exception:
        return None
