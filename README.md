# Minecraft-Custom-Hyperland · Jeyenore

An unofficial Minecraft-inspired desktop by **Jeyenore**, packaged from my working Ubuntu setup. Includes the snow wallpaper, wandering animals, top status bar, inventory app launcher, draggable nine-slot dock, XP clock, notification styling, village lock screen, GTK theme, icon themes and pixel fonts.

## Install

Full installation targets **Ubuntu 24.04 LTS, amd64**, with internet access and sudo. The configuration uses **Hyprland 0.56.x Lua**; older `.conf` releases and future incompatible releases are not supported. Keep an existing desktop session available for your first login.

Clone the repository, then run the installer:

```bash
git clone https://github.com/Jeyenore26/Minecraft-Custom-Hyperland.git
cd Minecraft-Custom-Hyperland
bash install.sh
```

Or use GitHub's **Code → Download ZIP**, extract it, open a terminal in the extracted folder, and run this one file:

```bash
bash install.sh
```

The installer installs dependencies through APT, adds the [cppiber Hyprland PPA](https://github.com/cpiber/hyprland-ppa), installs all user files with your own home path, and registers **Jeyenore — Minecraft (Hyprland)** at the login screen. APT is instructed to refuse package removals. It asks for your sudo password for system packages and the login entry; run the script as your normal user.

Save your work, log out, select the new session using your login screen's session selector, and sign in. The shortcut guide opens on first login.

```bash
bash install.sh --dry-run      # Preview file deployment; makes no changes
bash install.sh --config-only  # User files only; compatible packages must already exist
```

`--dry-run` does not validate network/package availability. `--config-only` does not register a system login session. For manual startup with compatible dependencies already installed, run `~/.local/bin/minecraft-session` from a TTY after logging out of your other graphical session.

## Daily use

**Jeyenore** at the top left opens the inventory. **Settings** opens the graphical settings hub. It provides display arrangement, Wi-Fi, saved networks, sound devices, GNOME system settings, the configuration folder, and the keyboard guide. It is also available as **Jeyenore System Settings** in the app launcher.

| Shortcut | Action |
| --- | --- |
| Super + comma | System settings |
| Super + H | Shortcut guide |
| Super + Space / R | Inventory and app search |
| Super + Enter | Kitty terminal |
| Super + E / B | Files / Firefox |
| Super + Tab | Search open windows |
| Super + 1–9 | Switch workspace |
| Super + Shift + 1–9 | Move window to workspace |
| Super + arrows | Focus a window |
| Super + left / right mouse drag | Move / resize a window |
| Super + Shift + Left / Right | Move window between monitors |
| Super + Q / V / F | Close / float / fullscreen |
| Super + P | Display mirror / extend options |
| Super + N | Notifications |
| Super + L | Lock |
| Super + Escape | Power menu |
| Super + Shift + S / Print | Capture a region to Pictures/Screenshots and clipboard |
| Super + Shift + R | Reload compositor settings |
| Alt + Shift | Switch English / Arabic |

Super means the Windows/logo key. Move to the bottom edge to reveal the dock. Drag installed apps from the inventory onto dock slots to pin them. The repository preserves my pins; unavailable apps fall back to built-in desktop actions. Your friend's installed apps are discovered automatically; Chrome, Discord, OBS, developer tools, accounts, and application data are not copied or automatically installed.

## Customize and maintain

- [Where to edit](docs/CUSTOMIZATION.md): colors, name, wallpaper, keybinds, dock, lock, display and keyboard.
- [Dependencies and libraries](docs/DEPENDENCIES.md): every package group and Python library.
- [Recovery and troubleshooting](docs/RECOVERY.md): backups, restore, login issues and logs.
- [Asset credits](docs/ASSETS.md): third-party origins and licensing notes.
- [Validation](docs/VALIDATION.md): checks run and what still requires a real login.

Changes made directly to installed files take effect according to the customization guide. Re-running the installer replaces shipped files and backs up the previous versions; preserve your edits in `payload/` if maintaining your own fork.

## Repository

[github.com/Jeyenore26/Minecraft-Custom-Hyperland](https://github.com/Jeyenore26/Minecraft-Custom-Hyperland)

The asset payload includes both current and alternate lock animation frames, so the folder is approximately 480 MB. No logs, local backups, browser profiles, Wi-Fi credentials, or compiled Python dependencies are included. Minecraft assets and fonts retain their respective ownership; see the asset credits before redistributing them.
