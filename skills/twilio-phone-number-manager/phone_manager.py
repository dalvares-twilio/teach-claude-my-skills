#!/usr/bin/env python3
"""
Twilio Phone Number Manager
Handles searching, purchasing, and managing Twilio phone numbers.

Usage:
    python3 phone_manager.py search [--area-code=XXX]
    python3 phone_manager.py purchase +1XXXXXXXXXX
    python3 phone_manager.py list
    python3 phone_manager.py set-credentials ACCOUNT_SID AUTH_TOKEN

Credentials are stored in /tmp/twilio_prod_credentials.json
Registry is stored alongside this script in phone-numbers.json
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import base64
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent.resolve()
REGISTRY_FILE = SCRIPT_DIR / "phone-numbers.json"
CREDENTIALS_FILE = Path("/tmp/twilio_prod_credentials.json")
TEMP_RESPONSE_FILE = Path("/tmp/twilio_api_response.json")

# Twilio API (always Prod for phone purchases)
TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"


def load_credentials():
    """Load credentials from file."""
    if not CREDENTIALS_FILE.exists():
        print(f"Error: No credentials found at {CREDENTIALS_FILE}")
        print("Run: python3 phone_manager.py set-credentials ACCOUNT_SID AUTH_TOKEN")
        sys.exit(1)

    with open(CREDENTIALS_FILE) as f:
        creds = json.load(f)
    return creds["account_sid"], creds["auth_token"]


def save_credentials(account_sid, auth_token):
    """Save credentials to file."""
    creds = {
        "account_sid": account_sid,
        "auth_token": auth_token,
        "description": "Prod account for phone number purchases"
    }
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    print(f"Credentials saved to {CREDENTIALS_FILE}")
    print(f"Account: {account_sid[:6]}...{account_sid[-4:]}")


def api_request(method, url, account_sid, auth_token, data=None):
    """Make authenticated request to Twilio API."""
    # Create auth header
    auth_string = f"{account_sid}:{auth_token}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_bytes}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    if data:
        data = data.encode()

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            # Save to temp file for debugging
            with open(TEMP_RESPONSE_FILE, "w") as f:
                json.dump(result, f, indent=2)
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"API Error {e.code}: {error_body}")
        sys.exit(1)


def get_capabilities(caps_dict):
    """Parse capabilities dict with case-insensitive keys."""
    caps_lower = {k.lower(): v for k, v in caps_dict.items()}
    result = []
    if caps_lower.get("sms"): result.append("SMS")
    if caps_lower.get("mms"): result.append("MMS")
    if caps_lower.get("voice"): result.append("Voice")
    if caps_lower.get("fax"): result.append("Fax")
    return result


def search_numbers(area_code=None, limit=5):
    """Search for available US Local SMS-enabled numbers."""
    account_sid, auth_token = load_credentials()

    url = f"{TWILIO_API_BASE}/Accounts/{account_sid}/AvailablePhoneNumbers/US/Local.json?SmsEnabled=true"
    if area_code:
        url += f"&AreaCode={area_code}"

    print("Searching for available US Local SMS-enabled numbers...")
    result = api_request("GET", url, account_sid, auth_token)

    numbers = result.get("available_phone_numbers", [])[:limit]

    if not numbers:
        print("No available numbers found.")
        return []

    print("\nAvailable Phone Numbers (US Local, SMS-enabled):\n")
    print("| #  | Phone Number     | Location           | Capabilities         |")
    print("|----|------------------|--------------------|----------------------|")

    for i, n in enumerate(numbers, 1):
        loc = f"{n.get('locality', 'N/A')}, {n.get('region', 'N/A')}"
        caps = get_capabilities(n.get("capabilities", {}))
        print(f"| {i:<2} | {n['phone_number']:<16} | {loc:<18} | {', '.join(caps):<20} |")

    print(f"\nFirst available: {numbers[0]['phone_number']}")
    return numbers


def purchase_number(phone_number):
    """Purchase a specific phone number."""
    account_sid, auth_token = load_credentials()

    url = f"{TWILIO_API_BASE}/Accounts/{account_sid}/IncomingPhoneNumbers.json"
    data = f"PhoneNumber={phone_number}"

    print(f"Purchasing {phone_number}...")
    result = api_request("POST", url, account_sid, auth_token, data)

    # Extract details
    sid = result.get("sid")
    friendly_name = result.get("friendly_name")
    caps = get_capabilities(result.get("capabilities", {}))

    print(f"\n{'='*50}")
    print("Phone Number Purchased Successfully!")
    print(f"{'='*50}")
    print(f"Phone Number:   {phone_number}")
    print(f"SID:            {sid}")
    print(f"Friendly Name:  {friendly_name}")
    print(f"Capabilities:   {', '.join(caps)}")
    print(f"{'='*50}\n")

    # Add to registry
    add_to_registry(phone_number, result)

    return result


def load_registry():
    """Load phone number registry."""
    if not REGISTRY_FILE.exists():
        return {"purchased_numbers": []}
    with open(REGISTRY_FILE) as f:
        return json.load(f)


def save_registry(registry):
    """Save phone number registry."""
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


def add_to_registry(phone_number, api_response):
    """Add purchased number to registry."""
    registry = load_registry()

    new_entry = {
        "phone_number": phone_number,
        "sid": api_response.get("sid"),
        "friendly_name": api_response.get("friendly_name"),
        "capabilities": get_capabilities(api_response.get("capabilities", {})),
        "purchased_at": datetime.utcnow().isoformat() + "Z"
    }

    registry["purchased_numbers"].append(new_entry)
    save_registry(registry)
    print(f"Added to registry: {REGISTRY_FILE}")


def list_numbers():
    """List all purchased numbers from registry."""
    registry = load_registry()
    numbers = registry.get("purchased_numbers", [])

    if not numbers:
        print("No purchased numbers in registry.")
        return []

    print("\nPurchased Phone Numbers:\n")
    print("| #  | Phone Number     | Purchased            | SID                  |")
    print("|----|------------------|----------------------|----------------------|")

    for i, n in enumerate(numbers, 1):
        purchased = n.get("purchased_at", "N/A")[:10]
        sid = n.get("sid", "N/A")
        sid_short = f"{sid[:8]}...{sid[-4:]}" if len(sid) > 12 else sid
        print(f"| {i:<2} | {n['phone_number']:<16} | {purchased:<20} | {sid_short:<20} |")

    print(f"\nTotal: {len(numbers)} number(s)")
    return numbers


def main():
    parser = argparse.ArgumentParser(description="Twilio Phone Number Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search available numbers")
    search_parser.add_argument("--area-code", help="Filter by area code")
    search_parser.add_argument("--limit", type=int, default=5, help="Max results")

    # Purchase command
    purchase_parser = subparsers.add_parser("purchase", help="Purchase a number")
    purchase_parser.add_argument("phone_number", help="Phone number to purchase (e.g., +17655551234)")

    # List command
    subparsers.add_parser("list", help="List purchased numbers")

    # Set credentials command
    creds_parser = subparsers.add_parser("set-credentials", help="Save API credentials")
    creds_parser.add_argument("account_sid", help="Twilio Account SID")
    creds_parser.add_argument("auth_token", help="Twilio Auth Token")

    args = parser.parse_args()

    if args.command == "search":
        search_numbers(area_code=args.area_code, limit=args.limit)
    elif args.command == "purchase":
        purchase_number(args.phone_number)
    elif args.command == "list":
        list_numbers()
    elif args.command == "set-credentials":
        save_credentials(args.account_sid, args.auth_token)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
