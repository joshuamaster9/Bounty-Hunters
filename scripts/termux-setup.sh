#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

REPO_URL="https://github.com/joshuamaster9/Bounty-Hunters.git"
INSTALL_DIR="$HOME/Bounty-Hunters"

info()  { printf '\033[1;32m[+]\033[0m %s\n' "$1"; }
warn()  { printf '\033[1;33m[!]\033[0m %s\n' "$1"; }
error() { printf '\033[1;31m[-]\033[0m %s\n' "$1"; }

if [ ! -d "/data/data/com.termux" ]; then
    error "This script must be run inside Termux."
    exit 1
fi

FAILED_PKGS=""

install_pkg() {
    local label="$1"; shift
    info "Installing $label..."
    if ! pkg install -y "$@"; then
        for p in "$@"; do
            FAILED_PKGS="$FAILED_PKGS $p"
        done
        warn "Some packages in '$label' failed — continuing anyway."
    fi
}

info "Updating Termux package lists..."
pkg update -y && pkg upgrade -y

install_pkg "core tools"        git openssh curl wget
install_pkg "Python"            python python-pip
install_pkg "Node.js"           nodejs-lts
install_pkg "C/C++ toolchain"   clang make openssl openssl-tool
install_pkg "Go"                golang
install_pkg "Rust"              rust
install_pkg "utilities"         jq nmap termux-api

info "Setting up storage access..."
if [ ! -d "$HOME/storage" ]; then
    termux-setup-storage || warn "Storage setup skipped — run 'termux-setup-storage' manually if needed."
fi

info "Configuring Git..."
if ! git config --global user.name > /dev/null 2>&1; then
    read -rp "Git username: " git_user
    git config --global user.name "$git_user"
fi
if ! git config --global user.email > /dev/null 2>&1; then
    read -rp "Git email: " git_email
    git config --global user.email "$git_email"
fi

if [ -d "$INSTALL_DIR" ]; then
    warn "Repository already exists at $INSTALL_DIR — pulling latest..."
    git -C "$INSTALL_DIR" pull origin main || warn "Pull failed — you may need to resolve conflicts."
else
    info "Cloning Bounty-Hunters..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

info "Installing Python dependencies..."
pip install --upgrade pip
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    pip install -r "$INSTALL_DIR/requirements.txt"
fi

info "Running verification checks..."
echo ""
printf '%-14s %s\n' "Component" "Version"
printf '%-14s %s\n' "---------" "-------"
printf '%-14s %s\n' "git"     "$(git --version 2>/dev/null | cut -d' ' -f3 || echo 'not found')"
printf '%-14s %s\n' "python"  "$(python --version 2>/dev/null | cut -d' ' -f2 || echo 'not found')"
printf '%-14s %s\n' "node"    "$(node --version 2>/dev/null || echo 'not found')"
printf '%-14s %s\n' "clang"   "$(clang --version 2>/dev/null | head -1 | sed 's/.*version //' | cut -d' ' -f1 || echo 'not found')"
printf '%-14s %s\n' "go"      "$(go version 2>/dev/null | cut -d' ' -f3 | sed 's/go//' || echo 'not found')"
printf '%-14s %s\n' "rustc"   "$(rustc --version 2>/dev/null | cut -d' ' -f2 || echo 'not found')"
printf '%-14s %s\n' "openssl" "$(openssl version 2>/dev/null | cut -d' ' -f2 || echo 'not found')"
echo ""

if [ -n "$FAILED_PKGS" ]; then
    warn "These packages failed to install:$FAILED_PKGS"
    warn "Try installing them manually: pkg install <name>"
fi

info "Setup complete!"
info "Project location: $INSTALL_DIR"
echo ""
echo "Quick start:"
echo "  cd $INSTALL_DIR"
echo "  python python/tls_handshake.py        # Python TLS module"
echo "  node javascript/tls_handshake_client.js # JS TLS client"
echo "  cd go && go build ./...                # Build Go module"
echo "  cd rust && rustc tls_session.rs        # Build Rust module"
echo "  cd c && clang -lssl -lcrypto tls_cert_validator.c -o validator  # Build C module"
