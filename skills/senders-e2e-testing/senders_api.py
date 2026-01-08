#!/usr/bin/env python3
"""
Senders API E2E Testing Script
Handles CREATE, GET, UPDATE, DELETE operations for Senders API.

Usage:
    python3 senders_api.py set-credentials ACCOUNT_SID AUTH_TOKEN ENV
    python3 senders_api.py list-credentials
    python3 senders_api.py create --sender-id "whatsapp:+1234567890" [--waba-id WABA_ID]
    python3 senders_api.py get SENDER_SID
    python3 senders_api.py update SENDER_SID [--description "New desc"] [--name "New name"]
    python3 senders_api.py delete SENDER_SID

Credentials are stored in /tmp/twilio_senders_test_credentials.json
Responses are saved to /tmp/senders_api_response.json
Headers are saved to /tmp/senders_api_headers.json
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import base64
from pathlib import Path

# Paths
CREDENTIALS_FILE = Path("/tmp/twilio_senders_test_credentials.json")
RESPONSE_FILE = Path("/tmp/senders_api_response.json")
HEADERS_FILE = Path("/tmp/senders_api_headers.json")

# Environment to URL mapping
ENV_URLS = {
    "dev": "https://messaging.dev.twilio.com",
    "stage": "https://messaging.stage.twilio.com",
    "prod": "https://messaging.twilio.com"
}

# Default profile template
DEFAULT_PROFILE = {
    "name": "Twilio Test1",
    "description": "Senders API UAT",
    "logo_url": "https://www.logomaker.com/wp-content/uploads/2018/10/twitter.png",
    "emails": [{"email": "twilio@twilio.com"}],
    "websites": [{"website": "https://twilio.com"}]
}


def load_credentials(environment):
    """Load credentials for a specific environment."""
    if not CREDENTIALS_FILE.exists():
        print(f"Error: No credentials found at {CREDENTIALS_FILE}")
        print("Run: python3 senders_api.py set-credentials ACCOUNT_SID AUTH_TOKEN ENV")
        sys.exit(1)

    with open(CREDENTIALS_FILE) as f:
        data = json.load(f)

    for cred in data.get("credentials", []):
        if cred.get("environment") == environment:
            return cred["account_sid"], cred["auth_token"]

    print(f"Error: No credentials found for environment '{environment}'")
    print("Available environments:", [c["environment"] for c in data.get("credentials", [])])
    sys.exit(1)


def save_credentials(account_sid, auth_token, environment):
    """Save credentials for an environment."""
    data = {"credentials": []}
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE) as f:
            data = json.load(f)

    # Update or add credential
    found = False
    for cred in data["credentials"]:
        if cred.get("environment") == environment:
            cred["account_sid"] = account_sid
            cred["auth_token"] = auth_token
            found = True
            break

    if not found:
        data["credentials"].append({
            "account_sid": account_sid,
            "auth_token": auth_token,
            "environment": environment
        })

    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Credentials saved for environment: {environment}")
    print(f"Account: {account_sid[:6]}...{account_sid[-4:]}")


def list_credentials():
    """List all saved credentials."""
    if not CREDENTIALS_FILE.exists():
        print("No credentials file found.")
        print(f"Create one with: python3 senders_api.py set-credentials ACCOUNT_SID AUTH_TOKEN ENV")
        return

    with open(CREDENTIALS_FILE) as f:
        data = json.load(f)

    print("\nSaved test credentials:\n")
    envs = {c["environment"]: c["account_sid"] for c in data.get("credentials", [])}

    for env in ["dev", "stage", "prod"]:
        if env in envs:
            sid = envs[env]
            print(f"  - {env:6}: {sid[:6]}...{sid[-4:]} OK")
        else:
            print(f"  - {env:6}: (not configured)")

    print()


def api_request(method, url, account_sid, auth_token, data=None):
    """Make authenticated request to Senders API."""
    # Create auth header
    auth_string = f"{account_sid}:{auth_token}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_bytes}",
        "Content-Type": "application/json"
    }

    encoded_data = None
    if data:
        encoded_data = json.dumps(data).encode()

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)

    response_headers = {}
    response_body = {}
    status_code = 0

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.status
            response_headers = dict(response.headers)
            body = response.read().decode()
            if body:
                response_body = json.loads(body)
    except urllib.error.HTTPError as e:
        status_code = e.code
        response_headers = dict(e.headers)
        body = e.read().decode()
        if body:
            try:
                response_body = json.loads(body)
            except json.JSONDecodeError:
                response_body = {"raw_error": body}

    # Save to files
    with open(RESPONSE_FILE, "w") as f:
        json.dump(response_body, f, indent=2)

    with open(HEADERS_FILE, "w") as f:
        json.dump(response_headers, f, indent=2)

    return status_code, response_headers, response_body


def print_response(operation, method, url, env, status_code, headers, body, payload=None, key_params=None):
    """Print formatted response."""
    print("=" * 60)
    print(f"SENDERS API: {operation}")
    print("=" * 60)
    print(f"Environment:    {env}")
    print(f"URL:            {url}")
    print(f"Method:         {method}")

    if payload:
        print("\n=== REQUEST PAYLOAD ===")
        print(json.dumps(payload, indent=2))

    rq_id = headers.get("Twilio-Request-Id", headers.get("twilio-request-id", "N/A"))

    print(f"\n=== RESPONSE (HTTP {status_code}) ===")
    print(json.dumps(body, indent=2))
    print("=" * 60)

    # Always print summary with RQ ID and key parameters prominently
    print("\n" + "-" * 60)
    print("SUMMARY")
    print("-" * 60)
    print(f"Request ID:     {rq_id}")
    print(f"HTTP Status:    {status_code}")
    if key_params:
        for key, value in key_params.items():
            print(f"{key + ':':<16}{value}")
    print("-" * 60)

    # Return RQ ID for collection
    return rq_id


def create_sender(environment, sender_id, waba_id=None, profile_name=None, profile_desc=None):
    """Create a new sender."""
    account_sid, auth_token = load_credentials(environment)
    base_url = ENV_URLS.get(environment)
    if not base_url:
        print(f"Error: Unknown environment '{environment}'")
        sys.exit(1)

    url = f"{base_url}/v2/Channels/Senders"

    # Build payload
    profile = DEFAULT_PROFILE.copy()
    if profile_name:
        profile["name"] = profile_name
    if profile_desc:
        profile["description"] = profile_desc

    payload = {
        "sender_id": sender_id,
        "profile": profile
    }

    if waba_id:
        payload["configuration"] = {"waba_id": waba_id}

    status, headers, body = api_request("POST", url, account_sid, auth_token, payload)

    # Extract key params for summary
    sender_sid = body.get("sid", "N/A")
    key_params = {
        "Sender ID": sender_id,
        "Sender SID": sender_sid,
        "Status": body.get("status", "N/A"),
        "Account SID": account_sid[:6] + "..." + account_sid[-4:]
    }
    if waba_id:
        key_params["WABA ID"] = waba_id

    rq_id = print_response("CREATE", "POST", url, environment, status, headers, body, payload, key_params)

    return sender_sid, rq_id


def get_sender(environment, sender_sid):
    """Get a sender by SID."""
    account_sid, auth_token = load_credentials(environment)
    base_url = ENV_URLS.get(environment)
    if not base_url:
        print(f"Error: Unknown environment '{environment}'")
        sys.exit(1)

    url = f"{base_url}/v2/Channels/Senders/{sender_sid}"

    status, headers, body = api_request("GET", url, account_sid, auth_token)

    # Extract key params for summary
    key_params = {
        "Sender SID": sender_sid,
        "Sender ID": body.get("sender_id", "N/A"),
        "Status": body.get("status", "N/A"),
        "Account SID": account_sid[:6] + "..." + account_sid[-4:]
    }

    rq_id = print_response("GET", "GET", url, environment, status, headers, body, key_params=key_params)

    return rq_id


def update_sender(environment, sender_sid, profile_name=None, profile_desc=None):
    """Update a sender."""
    account_sid, auth_token = load_credentials(environment)
    base_url = ENV_URLS.get(environment)
    if not base_url:
        print(f"Error: Unknown environment '{environment}'")
        sys.exit(1)

    url = f"{base_url}/v2/Channels/Senders/{sender_sid}"

    # Build update payload - only profile fields allowed
    profile = DEFAULT_PROFILE.copy()
    if profile_name:
        profile["name"] = profile_name
    if profile_desc:
        profile["description"] = profile_desc

    payload = {"profile": profile}

    status, headers, body = api_request("PATCH", url, account_sid, auth_token, payload)

    # Extract key params for summary
    key_params = {
        "Sender SID": sender_sid,
        "Sender ID": body.get("sender_id", "N/A"),
        "Status": body.get("status", "N/A"),
        "Account SID": account_sid[:6] + "..." + account_sid[-4:]
    }

    rq_id = print_response("UPDATE", "PATCH", url, environment, status, headers, body, payload, key_params)

    return rq_id


def delete_sender(environment, sender_sid):
    """Delete a sender."""
    account_sid, auth_token = load_credentials(environment)
    base_url = ENV_URLS.get(environment)
    if not base_url:
        print(f"Error: Unknown environment '{environment}'")
        sys.exit(1)

    url = f"{base_url}/v2/Channels/Senders/{sender_sid}"

    status, headers, body = api_request("DELETE", url, account_sid, auth_token)

    # Extract key params for summary
    key_params = {
        "Sender SID": sender_sid,
        "Account SID": account_sid[:6] + "..." + account_sid[-4:]
    }

    rq_id = print_response("DELETE", "DELETE", url, environment, status, headers, body, key_params=key_params)

    return rq_id


def main():
    parser = argparse.ArgumentParser(description="Senders API E2E Testing Script")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # set-credentials command
    creds_parser = subparsers.add_parser("set-credentials", help="Save API credentials")
    creds_parser.add_argument("account_sid", help="Twilio Account SID")
    creds_parser.add_argument("auth_token", help="Twilio Auth Token")
    creds_parser.add_argument("environment", choices=["dev", "stage", "prod"], help="Environment")

    # list-credentials command
    subparsers.add_parser("list-credentials", help="List saved credentials")

    # create command
    create_parser = subparsers.add_parser("create", help="Create a sender")
    create_parser.add_argument("--env", "-e", required=True, choices=["dev", "stage", "prod"], help="Environment")
    create_parser.add_argument("--sender-id", "-s", required=True, help="Sender ID (e.g., whatsapp:+1234567890)")
    create_parser.add_argument("--waba-id", "-w", help="WABA ID (optional)")
    create_parser.add_argument("--name", "-n", help="Profile name (default: Twilio Test1)")
    create_parser.add_argument("--description", "-d", help="Profile description")

    # get command
    get_parser = subparsers.add_parser("get", help="Get a sender")
    get_parser.add_argument("--env", "-e", required=True, choices=["dev", "stage", "prod"], help="Environment")
    get_parser.add_argument("sender_sid", help="Sender SID (XE...)")

    # update command
    update_parser = subparsers.add_parser("update", help="Update a sender")
    update_parser.add_argument("--env", "-e", required=True, choices=["dev", "stage", "prod"], help="Environment")
    update_parser.add_argument("sender_sid", help="Sender SID (XE...)")
    update_parser.add_argument("--name", "-n", help="New profile name")
    update_parser.add_argument("--description", "-d", help="New profile description")

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a sender")
    delete_parser.add_argument("--env", "-e", required=True, choices=["dev", "stage", "prod"], help="Environment")
    delete_parser.add_argument("sender_sid", help="Sender SID (XE...)")

    args = parser.parse_args()

    if args.command == "set-credentials":
        save_credentials(args.account_sid, args.auth_token, args.environment)
    elif args.command == "list-credentials":
        list_credentials()
    elif args.command == "create":
        create_sender(args.env, args.sender_id, args.waba_id, args.name, args.description)
    elif args.command == "get":
        get_sender(args.env, args.sender_sid)
    elif args.command == "update":
        update_sender(args.env, args.sender_sid, args.name, args.description)
    elif args.command == "delete":
        delete_sender(args.env, args.sender_sid)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
