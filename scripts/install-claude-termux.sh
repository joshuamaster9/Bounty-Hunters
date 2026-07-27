#!/data/data/com.termux/files/usr/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$PREFIX/bin/claude-t"
printf '#!/data/data/com.termux/files/usr/bin/bash\nexec python "%s/claude-termux.py" "$@"\n' "$SCRIPT_DIR" > "$BIN"
chmod +x "$BIN"
echo "[+] Installed. Run: claude-t"
