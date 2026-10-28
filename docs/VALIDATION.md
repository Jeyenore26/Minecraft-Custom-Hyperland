# Validation

Checked on the author's Ubuntu 24.04 amd64 machine with Hyprland 0.56.2. The packaging checks were performed on 2026-10-28.

| Check | Result |
| --- | --- |
| Isolated deployment to a different home, including a space and apostrophe | Passed |
| Actual `install.sh --config-only` entry point in a temporary home | Passed |
| Dry run leaves the target untouched | Passed |
| Reinstallation preserves overwritten edits in a new backup | Passed |
| Restoring both the newest and original backup | Passed |
| Rendered Waybar settings command executes with correct path quoting | Passed |
| Settings launcher passes `desktop-file-validate` | Passed |
| Python parsing, JSON parsing and Bash syntax | Passed |
| Bundled theme symlinks resolve within the payload | Passed |
| Entire 42-package main dependency list resolves using `apt-get -s --no-remove install` | Passed using this machine's configured repository metadata |
| Bundled PPA signing key fingerprint | Matches expected fingerprint |
| `Hyprland --verify-config` on packaged and installed Lua files | Passed |
| Settings window startup under an isolated Xvfb display | Passed; GTK emits a harmless deprecated `set_wmclass` notice |
| Live compositor reload and themed Waybar restart | Passed |

The checks cover installation logic and dependency resolution, not a full fresh-machine system install. The root package installer was inspected and syntax-checked; it was not run to reinstall the author's system. APT availability and repository versions can change. First login, lock authentication, suspend/resume, GPU compatibility, Wi-Fi hardware, multiple monitors and screen sharing must be checked on the recipient's machine.

To repeat the deployment integration check without changing your real configuration:

```bash
python3 tests/test_install.py
```

It creates a temporary home, copies the whole payload twice, validates deployment and restoration, then deletes the temporary directory. Allow approximately 1.5 GB of temporary free disk space. It needs Python 3, `desktop-file-validate`, and a POSIX filesystem with symlink support. It does not invoke sudo or install packages.

To preview your deployment:

```bash
bash install.sh --dry-run
```
