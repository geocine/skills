---
name: cargo-fork-optimize
description: Move a Rust project onto the huacnlee/cargo fork to save disk space and build time (shared deps across projects and git worktrees, small target dirs, automatic GC). Use when the user runs it in a Rust project directory, asks to "optimize cargo", "save space on Rust builds", "use the cargo fork", or when starting work on any Rust project on this machine. Also covers installing or repairing the fork itself.
---

# Cargo fork optimize

## Goal

The user runs this skill inside a Rust project directory. The project must end up building
with the huacnlee/cargo fork (https://huacnlee.github.io/cargo/), using as little disk as
possible, with nothing broken. Report the space freed and the build result.

Every Rust project on this machine should be moved over, one directory at a time.

## What the fork does (why)

- Replaces `~/.cargo/bin/cargo.exe`. The original rustup proxy is kept as `cargo.rustup.exe`.
- Intermediate files go to `~/.cargo/targets/<project>-<hash>/`. Final binaries still land
  in `./target` (scripts that read `target/release/x.exe` keep working).
- Registry and git dependencies build once in `~/.cargo/targets/shared-deps/`. They are reused
  by every project and worktree with the same version, features and profile.
- Workspace crates are keyed by content, so git worktrees of one commit share builds.
- GC: unused units are dropped after 1 day, and shared deps after 7 days (capped at 50 GiB).
- Dev builds keep less debug info. A `debug` setting in your profile still wins.
- It **ignores** `CARGO_TARGET_DIR`, `--target-dir`, `build.target-dir` and `build.build-dir`,
  with a warning. `cargo +<toolchain>` and `rust-toolchain.toml` still work: rustc still
  comes from the toolchain. Cargo itself is the fork's version.
- It auto-updates at most once a day (log: `~/.cargo/.fork-update.log`).
  `CARGO_FORK_AUTO_UPDATE=0` turns this off.

## Steps

1. **Fork installed?** Run `cargo --version`. It must mention `huacnlee/cargo`. If not:
   - Download https://huacnlee.github.io/cargo/install.ps1 to a scratch folder.
   - Read it.
   - Run it with `powershell -NoProfile -ExecutionPolicy Bypass -File <path>`.
   - No cargo/rustc process may be running at the time (Windows can't replace a running exe).
   - After `rustup self update`, run the script again (rustup puts its proxy back).
   - Undo: the same script with `-Uninstall`.

   If it is installed, check it is current: compare the version in `cargo --version` with the
   newest tag on https://github.com/huacnlee/cargo/releases (the landing page shows no
   version), and read the last line of `~/.cargo/.fork-update.log`. If it is behind, run the
   install script again as above.
2. **Find what fights the fork** in the project, and in `~/.cargo/config.toml`:
   - `target-dir` / `build-dir` in `.cargo/config.toml` or `config`;
   - `CARGO_TARGET_DIR` in scripts (`*.ps1`, `*.sh`, `justfile`, `Makefile`, CI files, `.envrc`);
   - `--target-dir` flags;
   - anything that calls the toolchain's own cargo directly and so skips the fork:
     `~/.rustup/toolchains/<ver>-…/bin/cargo.exe` or `cargo.rustup` in scripts, agent
     briefs, the project's memory notes or CLAUDE.md. A "build with stock cargo" rule left
     over from an old failure keeps every worktree building its own full target.
   For each one, say what you found. Then remove it, or leave it if it's needed for CI on
   other machines (stock cargo there). Explain the choice. Never break a CI path that runs
   on stock cargo: a setting the fork merely warns about can stay for CI.
3. **Old build folders** (the space to reclaim):
   - `./target` from before the move;
   - old custom target dirs that step 2 found (e.g. a scratchpad `*-target` folder);
   - `target` folders in this project's git worktrees.
   Measure them with `du -sh`. For each worktree, also check whether its branch is merged
   into the main branch (`git rev-list --count HEAD..<branch>` is 0) and whether it has
   uncommitted changes (`git -C <wt> status --porcelain`). A merged, clean worktree can be
   removed whole (`git worktree remove`, then `git worktree prune`), not only its `target`;
   the branch stays. **Ask the user before deleting.** List paths, sizes and merged/clean
   state, then delete only what they approve.

   The fork's first build in a project also garbage-collects the old `./target` on its own
   (sinag: 3.4 GB to 658 MB, "Cleaned 83 stale build units"), so measure again after step 4
   before offering to delete `./target` by hand. Never delete `~/.cargo/registry` or `~/.cargo/targets`
   (the fork manages that one).
4. **Build** the project the way it is normally built: read its README, justfile or scripts
   for the toolchain (`cargo +1.95.0 …`), features and env vars it needs (e.g. `ZIG`,
   `LIBCLANG_PATH`). Run `cargo build`, plus `--release` if that is what the project ships.
   Run `cargo test` if it is cheap. If the build fails, find out whether the fork is the
   cause: build once with `cargo.rustup` (the original proxy) and compare. Report it plainly.
   A full workspace test run can take a quarter of an hour: run it in the background at
   below-normal priority and wait for the notification.
   Once it passes, update any note or brief from step 2 that said to use stock cargo.
5. **Report:**
   - space freed;
   - the size of `~/.cargo/targets` now;
   - build time;
   - which settings changed;
   - anything left for the user.

## Watch out

- **Known Windows failure** (fork 0.102.0-9, 2026-11-08): herdr-app fails in `gpui-shell`
  with "can't find crate for `gpui`" (and ~67 more), even with `CARGO_SHARED_DEPS=0` and
  `CARGO_SHARE_WORKSPACE_UNITS=0`. Stock cargo builds it fine. If a project fails like
  this, build it with the toolchain's own cargo
  (`~/.rustup/toolchains/<ver>-x86_64-pc-windows-msvc/bin/cargo.exe`, plus
  `RUSTUP_TOOLCHAIN=<ver>`). Then report that the fork doesn't fit this project, and leave
  the project's settings as they were.
  0.103.0-1 (16 Nov) fixes "check sees two copies of a path crate below a shared
  dependency" (PR #11), which may be this failure: try herdr-app once more on 0.103.0-1 or
  later before falling back.
- **Known good:** sinag (24 Nov 2026, 0.103.0-1): the workspace build took
  4 min 18 s and `cargo test --workspace` passed. Removing its seven merged worktrees freed
  about 53 GB, and `~/.cargo/targets` went from 12 GB to 20 GB.

- Build scripts and crates that read `CARGO_MANIFEST_DIR` still build per worktree. That is
  expected.
- Windows is the fork's least-tested platform. If something looks wrong, check it with
  `cargo.rustup` before blaming the project.
- With `-Zremap-cwd-prefix=.`, start a debugger from the workspace root.
- Don't commit changes for the user unless they ask. Follow their git rules.
