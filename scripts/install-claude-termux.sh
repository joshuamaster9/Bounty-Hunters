#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

info() { printf '\033[1;32m[+]\033[0m %s\n' "$1"; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN_DIR="$PREFIX/bin"

info "Installing anthropic SDK..."
pip install anthropic

info "Creating claude-t command..."
cat > "$BIN_DIR/claude-t" << LAUNCHER
#!/data/data/com.termux/files/usr/bin/bash
exec python "$SCRIPT_DIR/claude-termux.py" "\$@"
LAUNCHER
chmod +x "$BIN_DIR/claude-t"

info "Done! Run 'claude-t' from anywhere."
