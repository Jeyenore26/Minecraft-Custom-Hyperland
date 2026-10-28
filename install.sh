#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mode=${1:-install}
case "$mode" in
  --help|-h) printf '%s\n' 'Usage: bash install.sh [--dry-run|--config-only]' 'Default: install Ubuntu 24.04 amd64 dependencies, theme, and login session.' '--config-only: deploy user files only; dependencies must already be installed.' '--dry-run: preview user file deployment without changing anything.'; exit 0 ;;
  --dry-run) exec /usr/bin/python3 "$repo/scripts/deploy.py" --dry-run ;;
  --config-only|install) ;;
  *) printf 'Unknown argument: %s\n' "$mode" >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo 'Too many arguments' >&2; exit 2; }
[[ $EUID != 0 ]] || { echo 'Run as your normal desktop user, without sudo. The installer requests sudo when needed.' >&2; exit 1; }
[[ -z ${XDG_CONFIG_HOME:-} || $XDG_CONFIG_HOME == "$HOME/.config" ]] || { echo 'This desktop currently requires the default ~/.config location.' >&2; exit 1; }
if [[ $mode == install ]]; then
  source /etc/os-release
  [[ $ID == ubuntu && $VERSION_ID == 24.04 && $(dpkg --print-architecture) == amd64 ]] || { echo 'Full installation supports Ubuntu 24.04 amd64. Use --config-only with compatible dependencies elsewhere.' >&2; exit 1; }
  command -v sudo >/dev/null
  sudo bash "$repo/scripts/system-install.sh" "$repo"
fi
/usr/bin/python3 "$repo/scripts/deploy.py"
fc-cache -f "$HOME/.local/share/fonts/minecraft"
if command -v update-desktop-database >/dev/null; then update-desktop-database "$HOME/.local/share/applications"; fi
if [[ $mode == install ]]; then
  # Package units otherwise start duplicate panels even outside the themed session.
  for unit in waybar.service swaync.service hypridle.service; do
    if systemctl --user cat "$unit" >/dev/null 2>&1; then
      unit_dir="$HOME/.config/systemd/user"
      mkdir -p "$unit_dir"
      if [[ -e $unit_dir/$unit || -L $unit_dir/$unit ]]; then
        unit_backup=$(mktemp -d "$HOME/.local/state/jeyenore-hyprland/unit-backup-XXXXXXXX")
        cp -a "$unit_dir/$unit" "$unit_backup/$unit"
        rm -- "$unit_dir/$unit"
        printf 'Previous unit override saved: %s\n' "$unit_backup/$unit"
      fi
      systemctl --user mask "$unit"
    fi
  done
fi
printf '\n%s\n' 'Installation complete. Save your work, log out, and choose “Jeyenore — Minecraft (Hyprland)” at login.' 'Settings: click Settings in the top bar, find Jeyenore System Settings in the launcher, or press Super+comma.'
