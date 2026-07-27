#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

info()  { printf '\033[1;32m[+]\033[0m %s\n' "$1"; }
warn()  { printf '\033[1;33m[!]\033[0m %s\n' "$1"; }

info "Installing proot-distro..."
pkg update -y && pkg install -y proot-distro

if ! proot-distro list 2>/dev/null | grep -q "ubuntu.*installed"; then
    info "Installing Ubuntu..."
    proot-distro install ubuntu
else
    info "Ubuntu already installed."
fi

info "Setting up Claude Code inside Ubuntu..."
proot-distro login ubuntu -- bash -c '
set -e
apt update -y
apt install -y curl git
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt install -y nodejs
npm install -g @anthropic-ai/claude-code
echo ""
echo "[+] Claude Code installed!"
claude --version
'

info "Creating launcher..."
cat > "$PREFIX/bin/claude" << 'LAUNCHER'
#!/data/data/com.termux/files/usr/bin/bash
proot-distro login ubuntu -- claude "$@"
LAUNCHER
chmod +x "$PREFIX/bin/claude"

info "Done! Just type: claude"
