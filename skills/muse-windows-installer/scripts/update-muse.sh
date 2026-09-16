#!/usr/bin/env bash
set -euo pipefail

mode="${1:-auto}"
case "$mode" in
  install|update|auto) ;;
  *)
    printf 'usage: %s [install|update|auto]\n' "${0##*/}" >&2
    exit 2
    ;;
esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
known_good_installer="$script_dir/install-muse.sh"
known_good_launcher="$script_dir/muse-launcher.sh"
work=""

cleanup() {
  [[ -z "$work" ]] || rm -rf -- "$work"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

die() {
  printf 'muse-windows-installer: %s\n' "$*" >&2
  exit 1
}

for required_command in bash curl grep mktemp uname; do
  command -v "$required_command" >/dev/null 2>&1 || \
    die "required command not found: $required_command"
done

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*|Windows_NT*) ;;
  *) die "run this skill from Git Bash on Windows" ;;
esac

[[ -r "$known_good_installer" ]] || die "bundled installer is missing"
[[ -r "$known_good_launcher" ]] || die "bundled launcher is missing"

if [[ "$mode" == update ]] && ! command -v muse >/dev/null 2>&1; then
  printf 'Muse is not currently installed; performing an install.\n' >&2
  mode=install
elif [[ "$mode" == auto ]]; then
  if command -v muse >/dev/null 2>&1; then
    mode=update
  else
    mode=install
  fi
fi

work="$(mktemp -d "${TMPDIR:-/tmp}/muse-windows-installer.XXXXXX")"
upstream_installer="$work/install.sh"
upstream_launcher="$work/upstream-muse-launcher.sh"
selected_launcher="$work/muse-launcher.sh"
selected_installer="$work/install-muse.sh"

curl \
  --fail \
  --silent \
  --show-error \
  --location \
  --max-redirs 3 \
  --proto '=https' \
  --proto-redir '=https' \
  --tlsv1.2 \
  --output "$upstream_installer" \
  https://dev.meta.ai/install.sh

curl \
  --fail \
  --silent \
  --show-error \
  --location \
  --max-redirs 3 \
  --proto '=https' \
  --proto-redir '=https' \
  --tlsv1.2 \
  --output "$upstream_launcher" \
  https://api.meta.ai/muse-launcher.sh

bash -n "$upstream_installer" || die "latest upstream installer is invalid"
bash -n "$upstream_launcher" || die "latest upstream launcher is invalid"

# The current upstream launcher only handles Darwin/Linux. Use it when it
# advertises both Windows platform keys and Windows executable handling;
# otherwise retain the bundled tested fallback.
if grep -Eq 'MINGW|MSYS|CYGWIN|Windows_NT' "$upstream_launcher" && \
    grep -Eq 'x86_windows|aarch64_windows' "$upstream_launcher" && \
    grep -Eq '\.exe|binary_suffix' "$upstream_launcher"; then
  cp -- "$upstream_launcher" "$selected_launcher"
  launcher_source="latest upstream launcher"
else
  cp -- "$known_good_launcher" "$selected_launcher"
  launcher_source="bundled Windows-compatible launcher"
fi

bash -n "$selected_launcher" || die "selected launcher is invalid"

# Use a newer upstream installer only when it supports injecting the selected
# launcher. Otherwise keep the bundled installer, which has that override.
if grep -q 'MUSE_LAUNCHER_FILE' "$upstream_installer"; then
  cp -- "$upstream_installer" "$selected_installer"
  installer_source="latest upstream installer"
else
  cp -- "$known_good_installer" "$selected_installer"
  installer_source="bundled installer"
fi

bash -n "$selected_installer" || die "selected installer is invalid"

printf 'Muse %s using %s and %s.\n' \
  "$mode" "$launcher_source" "$installer_source" >&2

# The bundled installer accepts MUSE_LAUNCHER_FILE and installs the selected
# launcher beside the native binary. Its launcher then fetches the latest
# stable release and verifies the artifact before replacing an older version.
MUSE_LAUNCHER_FILE="$selected_launcher" \
  bash "$selected_installer"

command -v muse >/dev/null 2>&1 || die "muse is not on PATH after installation"
MUSE_NO_AUTO_UPDATE=1 muse --version
