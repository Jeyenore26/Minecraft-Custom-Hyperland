# Dependencies and libraries

The full installer supports Ubuntu 24.04 amd64 and uses the [cppiber Hyprland PPA](https://github.com/cpiber/hyprland-ppa). The bundled signing key is checked against fingerprint `A54D23B62FF3FCC76EFF71E8FDBAAA1CF0CCF48E` before it is installed into APT's keyring. The PPA supplies newer compositor dependencies and may upgrade shared libraries. Exact versions and the simulated APT plan are recorded under `/var/backups/jeyenore-hyprland-*` during installation.

The source machine runs **Hyprland 0.56.2-1ppa2**. The installer selects an available **0.56.x** package and stops if none is available. It does not silently switch this Lua configuration to another configuration format. Other package versions follow the enabled Ubuntu/PPA repositories; this is a theme distribution, not an immutable OS image. Review compatibility before upgrading the compositor to a new major/minor series.

| Packages | Used for |
| --- | --- |
| `hyprland` | Wayland compositor, Lua configuration, `hyprctl`, `start-hyprland` |
| `waybar` | Top status bar and tray |
| `wofi` | Window search and display option menus |
| `hyprlock`, `hypridle` | Authentication lock and idle handling |
| `swaybg` | Available wallpaper utility / alternate configurations |
| `sway-notification-center`, `libnotify-bin` | Notifications, control center, `notify-send` |
| `xdg-desktop-portal-hyprland`, `xdg-desktop-portal-gtk` | Screen sharing portal and file chooser |
| `policykit-1-gnome` | Graphical privilege authentication agent |
| `grim`, `slurp`, `wl-clipboard` | Region screenshots and clipboard |
| `brightnessctl`, `playerctl` | Brightness and media keys |
| `pipewire`, `wireplumber`, `pavucontrol` | Audio service, `wpctl`, volume/device GUI |
| `network-manager`, `network-manager-gnome`, `gir1.2-nm-1.0` | NetworkManager, applet, connection editor, Wi-Fi API |
| `python3`, `python3-gi`, `python3-cairo`, `python3-gi-cairo` | Python runtime, GObject introspection, Cairo drawing and GTK/Cairo integration |
| `gir1.2-gtk-3.0`, `gir1.2-gtklayershell-0.1` | GTK3 windows and Wayland layer surfaces |
| `kitty`, `terminator` | Primary terminal and additional terminal described in guide |
| `nautilus`, `firefox` | Files and browser actions; Firefox may install through Ubuntu's Snap integration |
| `zenity`, `gnome-control-center`, `gnome-system-monitor` | Dialogs, general system settings, CPU/RAM click actions |
| `fonts-font-awesome`, `fonts-dejavu-core`, `fontconfig` | Symbol/text fallbacks and font cache |
| `yaru-theme-icon`, `adwaita-icon-theme` | Icon fallbacks referenced by shell styling |
| `util-linux`, `desktop-file-utils` | `flock` launcher lock, desktop entry database |
| `ca-certificates`, `gnupg`, `software-properties-common` | HTTPS trust, signing key validation, Ubuntu universe repository |

Python imports `gi.repository` modules **Gtk 3, Gdk, Gio, GLib, GdkPixbuf, Pango, GtkLayerShell 0.1 and NM 1.0**, plus **cairo**. Everything else is Python's standard library. No pip, npm, virtual environment or binary Python wheels are required. The source machine's extracted `.deb` Python fallback is deliberately replaced with distribution packages.

Hyprland's APT dependencies supply Aquamarine, Hyprutils, Hyprgraphics, Hyprcursor, Hyprlang, Wayland, graphics/input libraries and other linked dependencies. APT resolves these; they are not vendored in this repository.

For another distribution, install compatible equivalents yourself, then use `bash install.sh --config-only`. The session wrapper currently expects `/usr/bin/start-hyprland`, and the startup script uses Ubuntu's polkit agent path. Port those paths and register your display manager session manually. Non-Ubuntu installation has not been verified.
