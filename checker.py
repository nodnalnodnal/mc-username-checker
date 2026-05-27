#!/usr/bin/env python3

import re
import sys
import requests

mojangapi = "https://api.mojang.com/users/profiles/minecraft/{}"
usernameregex = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def is_valid_username(username: str) -> bool:
    return bool(usernameregex.match(username))


def check_username(username: str) -> dict:
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
        response = requests.get(mojangapi.format(username), timeout=10)
    except requests.RequestException as e:
        result["error"] = f"Network error: {e}"
        return result

    if response.status_code == 200:
        data = response.json()
        result["available"] = False
        result["owner_uuid"] = data.get("id")
    elif response.status_code == 404 or response.status_code == 204:
        result["available"] = True
    elif response.status_code == 429:
        result["error"] = "Rate limited by Mojang API. Try again in a moment."
    else:
        result["error"] = f"Unexpected response: HTTP {response.status_code}"

    return result


def format_result(result: dict) -> str:
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
        usernames = sys.argv[1:]
        for name in usernames:
            print(format_result(check_username(name)))
    else:
        print("minecraft username checker")
        print("type a usrname to check.\n")
        while True:
            try:
                name = input("username: ").strip()
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
