# Recovery and troubleshooting

## Backups and reinstalling

Each deployment saves replaced user files and a manifest in:

```
~/.local/state/jeyenore-hyprland/backups/TIMESTAMP-RANDOM/
```

To undo one deployment, run from the repository, substituting the actual backup directory printed during installation:

```bash
python3 scripts/restore.py "$HOME/.local/state/jeyenore-hyprland/backups/TIMESTAMP-RANDOM"
```

Restore the newest backup first if undoing multiple installations. This restores replaced files and removes files added by that deployment. It will replace later edits to those files, so save changes you want to keep first. An interrupted deployment can be restored using its `journal.jsonl` if the final manifest was not written. Empty directories may remain.

System package installation is separate: user file restoration does not downgrade APT packages, remove the PPA, remove the login entry, or undo user service masks. System source lists, package inventory and the package plan are saved under `/var/backups/jeyenore-hyprland-*`.

## Returning to Ubuntu

Save your work, log out, and choose your previous Ubuntu/GNOME session at login. The themed session wrapper restores the previous GTK/icon/font preferences when it exits normally. It does not change the default login session or bootloader.

The installer masks `waybar.service`, `swaync.service` and `hypridle.service` for your user to avoid automatic duplicate instances outside the themed session. The startup script launches its own configured processes. To allow package services to start normally again:

```bash
systemctl --user unmask waybar.service swaync.service hypridle.service
```

Pre-existing user unit overrides, if present, are saved to the printed `unit-backup-*` directory. Restore any custom override from that directory if needed.

## Diagnosing a component

Logs live in `~/.local/state/minecraft-desktop/`: `wallpaper.log`, `waybar.log`, `hotbar.log`, `animals.log`, `notifications.log`, `idle.log`, `polkit.log`, `network.log`, and `lua-errors.log`.

- No new login entry: full installation must complete; `--config-only` installs no display-manager entry. Log out fully before checking the session selector.
- Black/missing shell: verify the compositor is 0.56.x with `Hyprland --version`, then check the component logs. Do not use an older `.conf` compositor with this Lua configuration.
- Missing `gi`, Cairo or GtkLayerShell: install the Python/GIR packages listed in DEPENDENCIES.md using APT, not a personal virtual environment. Scripts use `/usr/bin/python3`.
- Settings hub opens but a tool fails: verify `pavucontrol`, `gnome-control-center`, `nautilus`, `zenity` and NetworkManager are installed. General settings launches GNOME Control Center with `XDG_CURRENT_DESKTOP=GNOME` for that process. Some GNOME panels govern GNOME only; use the dedicated display button and Hyprland config for compositor settings.
- Wi-Fi cannot connect: NetworkManager must manage the adapter, with working rfkill/radio and polkit. Saved credentials stay in NetworkManager; they are not shipped with the theme.
- Missing dock app: drag an app installed on your computer from the inventory into that slot.
- Brightness keys do nothing: hardware/backlight support and device permissions vary by machine.
- Screen sharing fails: check the Hyprland portal packages, your user D-Bus session, and the application screen-sharing permissions.
- Existing custom `XDG_CONFIG_HOME`: this setup uses `~/.config`; the full installer refuses a nondefault config directory.

Power, suspend, screen sharing, graphics drivers and multiple monitor behavior require checking on the friend's hardware. No installer can reproduce the author's hardware or existing app accounts.
