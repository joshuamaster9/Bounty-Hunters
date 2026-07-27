#!/data/data/com.termux/files/usr/bin/python
"""Sovereign Claude CLI for Termux — runs with local models, no API keys."""

import json
import os
import readline
import ssl
import sys
import urllib.request
import urllib.error
from pathlib import Path

LOCAL_ENDPOINTS = [
    "http://127.0.0.1:11434",  # Ollama
    "http://127.0.0.1:8080",   # llama.cpp
    "http://127.0.0.1:1234",   # LM Studio
    "http://127.0.0.1:5000",   # text-generation-webui
]

GREEN = "\033[1;32m"
CYAN = "\033[1;36m"
YELLOW = "\033[1;33m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[1;31m"


def detect_server():
    """Find a running local model server."""
    custom = os.environ.get("LOCAL_MODEL_URL")
    if custom:
        return custom.rstrip("/"), "custom"

    for url in LOCAL_ENDPOINTS:
        try:
            urllib.request.urlopen(url, timeout=2)
            if ":11434" in url:
                return url, "ollama"
            elif ":8080" in url:
                return url, "llama.cpp"
            elif ":1234" in url:
                return url, "lm-studio"
            elif ":5000" in url:
                return url, "text-gen-webui"
            return url, "openai-compat"
        except Exception:
            continue
    return None, None


def get_ollama_model(base_url):
    """Get the first available Ollama model."""
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/tags", timeout=5)
        data = json.loads(resp.read())
        models = data.get("models", [])
        if models:
            return models[0]["name"]
    except Exception:
        pass
    return None


def chat_ollama(base_url, model, messages):
    """Stream chat via Ollama API."""
    body = json.dumps({
        "model": model,
        "messages": messages,
        "stream": True,
    }).encode()

    req = urllib.request.Request(
        f"{base_url}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )

    full_text = ""
    with urllib.request.urlopen(req, timeout=120) as resp:
        for line in resp:
            try:
                chunk = json.loads(line)
                text = chunk.get("message", {}).get("content", "")
                if text:
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    full_text += text
                if chunk.get("done"):
                    break
            except json.JSONDecodeError:
                continue
    return full_text


def chat_openai_compat(base_url, model, messages):
    """Stream chat via OpenAI-compatible API (llama.cpp, LM Studio, etc.)."""
    body = json.dumps({
        "model": model,
        "messages": messages,
        "stream": True,
    }).encode()

    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )

    full_text = ""
    with urllib.request.urlopen(req, timeout=120) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                text = chunk["choices"][0].get("delta", {}).get("content", "")
                if text:
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    full_text += text
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
    return full_text


def install_ollama():
    """Guide user to install Ollama on Termux."""
    print(f"""
{YELLOW}No local model server found.{RESET}

Set up Ollama in Termux:

  {GREEN}pkg install ollama{RESET}
  {GREEN}ollama serve &{RESET}
  {GREEN}ollama pull qwen3:1.7b{RESET}    # small, fast on phones
  {GREEN}claude-t{RESET}                   # then run this again

Or if you have a model server on another port:

  {GREEN}LOCAL_MODEL_URL=http://127.0.0.1:PORT claude-t{RESET}
""")


def print_banner(server_type, model, base_url):
    port = base_url.split(":")[-1].split("/")[0] if base_url else "?"
    print(f"""
{CYAN}╭───────────────────────────────────────────╮
│  Claude Termux  {DIM}(soberano — no API keys){CYAN}  │
│                                           │
│  server: {server_type:<33s}│
│  model:  {model[:33]:<33s}│
│  port:   {port:<33s}│
╰───────────────────────────────────────────╯{RESET}
{DIM}  /quit  exit    /clear  reset conversation
  /model <name>  change model
  /models        list available models{RESET}
""")


def list_models(base_url, server_type):
    if server_type == "ollama":
        try:
            resp = urllib.request.urlopen(f"{base_url}/api/tags", timeout=5)
            data = json.loads(resp.read())
            models = data.get("models", [])
            if models:
                print(f"{DIM}Available models:{RESET}")
                for m in models:
                    size = m.get("size", 0) / (1024**3)
                    print(f"  {m['name']:<30s} {size:.1f} GB")
            else:
                print(f"{YELLOW}No models pulled yet. Run: ollama pull qwen3:1.7b{RESET}")
        except Exception as e:
            print(f"{YELLOW}Could not list models: {e}{RESET}")
    else:
        try:
            resp = urllib.request.urlopen(f"{base_url}/v1/models", timeout=5)
            data = json.loads(resp.read())
            models = data.get("data", [])
            print(f"{DIM}Available models:{RESET}")
            for m in models:
                print(f"  {m.get('id', '?')}")
        except Exception:
            print(f"{YELLOW}Could not list models from this server.{RESET}")


def main():
    base_url, server_type = detect_server()

    if not base_url:
        install_ollama()
        sys.exit(1)

    if server_type == "ollama":
        model = os.environ.get("LOCAL_MODEL", get_ollama_model(base_url))
        if not model:
            print(f"{YELLOW}Ollama running but no models pulled.{RESET}")
            print(f"Run: {GREEN}ollama pull qwen3:1.7b{RESET}")
            sys.exit(1)
        chat_fn = chat_ollama
    else:
        model = os.environ.get("LOCAL_MODEL", "default")
        chat_fn = chat_openai_compat

    messages = [{"role": "system", "content": f"You are a helpful coding assistant. Working directory: {os.getcwd()}"}]
    print_banner(server_type, model, base_url)

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
            messages = [messages[0]]
            print(f"{DIM}Conversation cleared.{RESET}")
            continue
        if user_input == "/models":
            list_models(base_url, server_type)
            continue
        if user_input.startswith("/model"):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1:
                model = parts[1]
                print(f"{DIM}Model set to: {model}{RESET}")
            else:
                print(f"{DIM}Current model: {model}{RESET}")
            continue

        messages.append({"role": "user", "content": user_input})
        sys.stdout.write(f"\n{BOLD}")
        sys.stdout.flush()

        try:
            result = chat_fn(base_url, model, messages)
            sys.stdout.write(f"{RESET}\n\n")
            if result:
                messages.append({"role": "assistant", "content": result})
            else:
                messages.pop()
        except Exception as e:
            sys.stdout.write(f"{RESET}\n")
            print(f"{YELLOW}Error: {e}{RESET}\n")
            messages.pop()


if __name__ == "__main__":
    main()
