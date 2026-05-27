#!/usr/bin/env python3
"""
Minecraft Username Availability Checker

Checks if a Minecraft username is available by querying Mojang's API.
- If the API returns a profile, the name is TAKEN.
- If the API returns 404 / empty, the name is AVAILABLE.
- Also validates the username against Mojang's rules (3-16 chars, a-z, A-Z, 0-9, underscore).
"""

import re
import sys
import requests

MOJANG_API = "https://api.mojang.com/users/profiles/minecraft/{}"
USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def is_valid_username(username: str) -> bool:
    """Check if a username follows Mojang's format rules."""
    return bool(USERNAME_REGEX.match(username))


def check_username(username: str) -> dict:
    """
    Check availability of a Minecraft username.

    Returns a dict with:
      - username: the name checked
      - valid: whether the format is valid
      - available: True/False/None (None if we couldn't determine)
      - owner_uuid: UUID of owner if taken
      - error: error message if something went wrong
    """
    result = {
        "username": username,
        "valid": is_valid_username(username),
        "available": None,
        "owner_uuid": None,
        "error": None,
    }

    if not result["valid"]:
        result["error"] = (
            "Invalid format. Usernames must be 3-16 characters "
            "and only contain letters, numbers, and underscores."
        )
        return result

    try:
        response = requests.get(MOJANG_API.format(username), timeout=10)
    except requests.RequestException as e:
        result["error"] = f"Network error: {e}"
        return result

    if response.status_code == 200:
        # Name is taken — Mojang returned a profile
        data = response.json()
        result["available"] = False
        result["owner_uuid"] = data.get("id")
    elif response.status_code == 404 or response.status_code == 204:
        # Name is available
        result["available"] = True
    elif response.status_code == 429:
        result["error"] = "Rate limited by Mojang API. Try again in a moment."
    else:
        result["error"] = f"Unexpected response: HTTP {response.status_code}"

    return result


def format_result(result: dict) -> str:
    """Pretty-print a check result."""
    name = result["username"]

    if result["error"]:
        return f"[!] {name}: {result['error']}"

    if result["available"] is True:
        return f"[✓] {name} — AVAILABLE"
    elif result["available"] is False:
        uuid = result["owner_uuid"]
        return f"[✗] {name} — TAKEN (owner UUID: {uuid})"
    else:
        return f"[?] {name} — unknown"


def main():
    if len(sys.argv) > 1:
        # Command-line mode: check each username passed as an argument
        usernames = sys.argv[1:]
        for name in usernames:
            print(format_result(check_username(name)))
    else:
        # Interactive mode
        print("Minecraft Username Checker")
        print("Type a username to check, or 'quit' to exit.\n")
        while True:
            try:
                name = input("Username: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not name:
                continue
            if name.lower() in ("quit", "exit", "q"):
                break
            print(format_result(check_username(name)))
            print()


if __name__ == "__main__":
    main()
