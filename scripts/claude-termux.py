#!/data/data/com.termux/files/usr/bin/python
"""Lightweight Claude CLI for Termux — works on linux-arm64-android."""

import os
import sys
import readline
import subprocess
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Installing anthropic SDK...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic"])
    import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
MAX_TOKENS = int(os.environ.get("CLAUDE_MAX_TOKENS", "4096"))

SYSTEM_PROMPT = """You are Claude, running inside Termux on Android.
You are a helpful coding assistant. The user's working directory is: {cwd}
When the user asks you to run commands, show them the command to run.
When the user asks you to edit files, show the changes clearly."""

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
    print(f"Get one at: https://console.anthropic.com/settings/keys\n")
    key = input("Paste your Anthropic API key: ").strip()
    if not key:
        print("No key provided. Exiting.")
        sys.exit(1)

    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(key)
    key_file.chmod(0o600)
    print(f"{GREEN}Key saved to {key_file}{RESET}\n")
    return key


def print_banner():
    print(f"""
{CYAN}╭───────────────────────────────────────────╮
│  Claude for Termux                        │
│                                           │
│  model: {MODEL:<33s}│
│  dir:   {os.getcwd()[:33]:<33s}│
╰───────────────────────────────────────────╯{RESET}
{DIM}  Type your message. /quit to exit.
  /model <name> to change model.
  /clear to reset conversation.{RESET}
""")


def main():
    api_key = get_api_key()
    client = anthropic.Anthropic(api_key=api_key)
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

        try:
            sys.stdout.write(f"\n{BOLD}")
            sys.stdout.flush()

            with client.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT.format(cwd=os.getcwd()),
                messages=messages,
            ) as stream:
                full_response = ""
                for text in stream.text_stream:
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    full_response += text

            sys.stdout.write(f"{RESET}\n\n")
            sys.stdout.flush()
            messages.append({"role": "assistant", "content": full_response})

        except anthropic.AuthenticationError:
            print(f"\n{YELLOW}Invalid API key. Delete ~/.config/claude/api_key and try again.{RESET}\n")
            messages.pop()
        except anthropic.RateLimitError:
            print(f"\n{YELLOW}Rate limited. Wait a moment and try again.{RESET}\n")
            messages.pop()
        except Exception as e:
            print(f"\n{YELLOW}Error: {e}{RESET}\n")
            messages.pop()


if __name__ == "__main__":
    main()
