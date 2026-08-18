#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DASHBOARD_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

OS=$(uname -s 2>/dev/null || printf unknown)
ARCH=$(uname -m 2>/dev/null || printf unknown)

case "$OS:$ARCH" in
  Darwin:arm64|Darwin:aarch64)
    TARGET="darwin-aarch64"
    ;;
  Darwin:x86_64|Darwin:amd64)
    TARGET="darwin-x86_64"
    ;;
  Linux:x86_64|Linux:amd64)
    TARGET="linux-x86_64"
    ;;
  Linux:aarch64|Linux:arm64)
    TARGET="linux-aarch64"
    ;;
  *)
    TARGET="unsupported"
    ;;
esac

BINARY="$DASHBOARD_DIR/bin/$TARGET/axiom-dashboard"
if [ -x "$BINARY" ]; then
  exec "$BINARY" "$@"
fi

if command -v cargo >/dev/null 2>&1; then
  exec cargo run --quiet --release --manifest-path "$DASHBOARD_DIR/Cargo.toml" -- "$@"
fi

cat >&2 <<MESSAGE
Axiom Dashboard binary was not found for $OS/$ARCH.
Expected: $BINARY

This source package can be built with:
  cargo build --release --manifest-path "$DASHBOARD_DIR/Cargo.toml"

Then copy the produced axiom-dashboard executable into:
  $DASHBOARD_DIR/bin/$TARGET/

Official release packages include prebuilt supported binaries.
MESSAGE
exit 1
