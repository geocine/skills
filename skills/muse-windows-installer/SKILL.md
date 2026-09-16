---
name: muse-windows-installer
description: Install and update Meta Muse on Windows through Git Bash, adapting the upstream Bash launcher when it lacks Windows artifact support and verifying the native executable.
---

# Muse Windows Installer

Use this skill when the user asks to install, update, repair, or verify the Meta Muse CLI on Windows from Git Bash. The target is a native Windows executable, not a Linux binary under WSL.

## Portable package

All reusable files are inside this skill directory:

- [`scripts/update-muse.sh`](scripts/update-muse.sh) — fetches the latest upstream scripts, selects a Windows-safe launcher, and performs install/update.
- [`scripts/install-muse.sh`](scripts/install-muse.sh) — known-good Bash bootstrap installer.
- [`scripts/muse-launcher.sh`](scripts/muse-launcher.sh) — known-good Windows-compatible launcher fallback.

Run commands relative to this directory or invoke the scripts by their absolute path at runtime. Do not add references to a developer's workspace, home directory, or another machine's filesystem to this skill.

## Install and update modes

- **Install:** use `bash scripts/update-muse.sh install` when Muse is missing, broken, or not Windows-compatible.
- **Update:** use `bash scripts/update-muse.sh update` when Muse is already installed. The helper fetches the latest upstream launcher, preserves the Windows fallback when upstream is still Unix-only, and then runs the bootstrap so the latest stable Windows binary is downloaded and verified.
- **Auto:** use `bash scripts/update-muse.sh auto` when the caller has not specified a mode. It updates an existing installation and installs when the active launcher or binary is missing.

The installed command belongs in Git Bash's `$HOME/.local/bin/muse`. The versioned native binary must end in `.exe`.

## Upstream sources and safety

Fetch these sources with Git Bash `curl` before executing anything:

- `https://dev.meta.ai/install.sh`
- `https://api.meta.ai/muse-launcher.sh`

Do not use `curl ... | bash`. Validate staged Bash files with `bash -n`, and do not replace a working launcher until the candidate is syntactically valid. Preserve the launcher's release-manifest size and SHA-256 checks. Never substitute a Linux artifact when Windows metadata is unavailable.

PowerShell's `curl.exe` can fail with a Schannel credential error in some environments; use the `curl` and `bash` supplied by Git for Windows.

## Windows compatibility invariants

If the latest upstream launcher lacks Windows support, use the bundled launcher fallback or patch a staged copy with all of these behaviors:

1. Treat `MINGW*`, `MSYS*`, `CYGWIN*`, and `Windows_NT*` from `uname -s` as Windows.
2. Map `x86_64`/`amd64` to `x86_windows`; map `arm64`/`aarch64` to `aarch64_windows`.
3. Use `.exe` for the temporary artifact, versioned target, and active-binary path.
4. Open device-login URLs with `cmd.exe /c start "" "$url"` when available.
5. Do not let a Unix-only upstream launcher overwrite the Windows-compatible launcher during self-update. Skip launcher self-update on Windows, or accept a replacement only after checking equivalent Windows platform and `.exe` handling. Keep binary updates enabled.

The helper determines whether the fetched launcher is Windows-aware. If not, it uses `scripts/muse-launcher.sh`, while still allowing that launcher to fetch the latest stable binary.

## Manual verification

After either operation, run:

```bash
command -v muse
MUSE_NO_AUTO_UPDATE=1 muse --version
ls -l "$HOME/.local/bin"/muse "$HOME/.local/bin"/muse-bin-*.exe
```

A successful operation resolves `muse` from `$HOME/.local/bin`, reports a version, and leaves a versioned `.exe`. If the user-profile directory is inaccessible only because of the execution sandbox, retry the verification with the required approval; do not relocate the install to Linux or WSL.

If a new Git Bash session does not inherit the path, suggest reopening Git Bash or running `export PATH="$HOME/.local/bin:$PATH"`.

If the upstream launcher structure changes and the Windows compatibility check or patch cannot be applied confidently, stop and report the mismatch rather than guessing.
