#!/data/data/com.termux/files/usr/bin/python
"""Lightweight Claude CLI for Termux — zero pip dependencies."""

import json
import os
import readline
import ssl
import sys
import urllib.request
from pathlib import Path

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
MAX_TOKENS = int(os.environ.get("CLAUDE_MAX_TOKENS", "4096"))
API_VERSION = "2023-06-01"

SYSTEM_PROMPT = "You are Claude, running inside Termux on Android. You are a helpful coding assistant. The user's working directory is: {cwd}"

GREEN = "\033[1;32m"
CYAN = "\033[1;36m"
YELLOW = "\033[1;33m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"


def get_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key

    key_file = Path.home() / ".config" / "claude" / "api_key"
    if key_file.exists():
        return key_file.read_text().strip()

    print(f"{YELLOW}No API key found.{RESET}")
    print("Get one at: https://console.anthropic.com/settings/keys\n")
    key = input("Paste your Anthropic API key: ").strip()
    if not key:
        sys.exit(1)

    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(key)
    key_file.chmod(0o600)
    print(f"{GREEN}Key saved to {key_file}{RESET}\n")
    return key


def stream_message(api_key, messages):
    body = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT.format(cwd=os.getcwd()),
        "messages": messages,
        "stream": True,
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
            "Anthropic-Version": API_VERSION,
        },
    )

    ctx = ssl.create_default_context()
    full_text = ""

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue

                if event.get("type") == "content_block_delta":
                    text = event.get("delta", {}).get("text", "")
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    full_text += text
                elif event.get("type") == "error":
                    msg = event.get("error", {}).get("message", "Unknown error")
                    print(f"\n{YELLOW}{msg}{RESET}")
                    return None

    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            msg = err.get("error", {}).get("message", body)
        except json.JSONDecodeError:
            msg = body
        print(f"\n{YELLOW}API error ({e.code}): {msg}{RESET}")
        return None

    return full_text


def print_banner():
    print(f"""
{CYAN}╭───────────────────────────────────────────╮
│  Claude for Termux                        │
│                                           │
│  model: {MODEL:<33s}│
│  dir:   {os.getcwd()[:33]:<33s}│
╰───────────────────────────────────────────╯{RESET}
{DIM}  /quit  exit    /clear  reset conversation
  /model <name>  change model{RESET}
""")


def main():
    api_key = get_api_key()
    messages = []
    print_banner()

    while True:
        try:
            user_input = input(f"{GREEN}> {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Bye!{RESET}")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print(f"{DIM}Bye!{RESET}")
            break
        if user_input == "/clear":
            messages.clear()
            print(f"{DIM}Conversation cleared.{RESET}")
            continue
        if user_input.startswith("/model"):
            global MODEL
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                MODEL = parts[1]
                print(f"{DIM}Model set to: {MODEL}{RESET}")
            else:
                print(f"{DIM}Current model: {MODEL}{RESET}")
            continue

        messages.append({"role": "user", "content": user_input})
        sys.stdout.write(f"\n{BOLD}")
        sys.stdout.flush()

        result = stream_message(api_key, messages)

        sys.stdout.write(f"{RESET}\n\n")
        if result:
            messages.append({"role": "assistant", "content": result})
        else:
            messages.pop()


if __name__ == "__main__":
    main()
