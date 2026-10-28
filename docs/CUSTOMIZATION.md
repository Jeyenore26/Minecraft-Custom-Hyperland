# Where to edit

The repository's `payload/` contains the source files. Installation maps its folders into your home directory. `@HOME@` in source files is an installer placeholder: use a real path when editing an installed file. The installer quotes Waybar commands and substitutes your home directory automatically.

| Installed path | Purpose |
| --- | --- |
| `~/.config/hypr/minecraft.lua` | Hyprland window rules, animations, monitor defaults, keyboard layouts, keybindings, startup |
| `~/.config/hypr/minecraft/waybar.json` | Top-left name, top-bar buttons, metrics and click commands |
| `~/.config/hypr/minecraft/waybar.css` | Top-bar colors, spacing, fonts and XP clock graphics |
| `~/.config/hypr/minecraft/settings.py` | Graphical settings hub and its buttons |
| `~/.config/hypr/minecraft/guide.py` | On-screen shortcut guide |
| `~/.config/hypr/minecraft/start.sh` | Desktop programs started on login |
| `~/.config/hypr/minecraft/winter-wallpaper.py` | Animated snow overlay and wallpaper path |
| `~/.local/share/minecraft-desktop/frozen-river.png` | Current wallpaper image |
| `~/.config/hypr/minecraft/desktop-animals.py` | Wandering animal behavior |
| `~/.config/hypr/minecraft/animal_models.py` | Cairo animal renderer |
| `~/.config/hypr/minecraft/hotbar.py` | Dock drawing and hover reveal |
| `~/.config/hypr/minecraft/hotbar-items.json` | Nine pinned dock slots; normally edited by dragging apps |
| `~/.config/hypr/minecraft/inventory-items.json` | Inventory shelf items |
| `~/.config/hypr/minecraft/inventory.py`, `inventory.css` | App launcher layout, search and styling |
| `~/.config/hypr/minecraft/inventory_common.py` | Built-in actions, app sorting and Tela icon selection |
| `~/.config/hypr/minecraft/kitty.conf` | Terminal colors, fonts and pane shortcuts |
| `~/.config/hypr/minecraft/swaync.json`, `swaync.css` | Notification content, styling and achievement panel |
| `~/.config/hypr/minecraft/hyprlock.conf` | Current lock image, password box and labels |
| `~/.config/hypr/minecraft/hypridle.conf` | Lock after 600 seconds, screen off after 900 seconds |
| `~/.config/hypr/minecraft/wifi/` | Graphical NetworkManager Wi-Fi interface |
| `~/.themes/Minecraft-DeepSlate/` | GTK 3/4 appearance |
| `~/.icons/Minecraft-Pixel/` | Minecraft icon theme |
| `~/.local/share/icons/Tela*` | Application icons used by inventory |
| `~/.local/share/fonts/minecraft/` | Minecraft and Monocraft fonts |
| `~/.local/bin/minecraft-session` | Session environment and GTK preference restoration |

## Common changes

**Name:** edit `custom/realm.format` in `waybar.json`. It ships as `Jeyenore`; clicking it opens the inventory.

**Keyboard:** change `kb_layout = "us,eg"` and `kb_options` in `minecraft.lua`. Super keybindings are `cmd(...)` or `hl.bind(...)` calls in that file. GNOME's keyboard and display panels manage GNOME settings; use the Hyprland config and the hub's Displays button for this session.

**Monitor:** the default uses each monitor's preferred mode, automatic positioning and scale 1. `Super+P` gives temporary mirror/extend choices. For persistent layout or scaling, edit the `hl.monitor(...)` declarations in `minecraft.lua`.

**Browser:** Firefox is the default built-in action and `Super+B` binding. Change both `minecraft.lua` and the browser command in `inventory_common.py` to select another installed browser.

**Wallpaper:** replace `frozen-river.png` with a PNG or change the `IMAGE` path in `winter-wallpaper.py`. The snow effect is drawn by Python/Cairo.

**Lock screen:** `lock.sh` currently runs Hyprlock with the static village image in `hyprlock.conf`. The alternate `animated-lock.py` and `lock-village-3d/` frames are included, but are not selected by default. Keep Hyprlock as the authentication component.

**Pins:** drag apps onto the dock. If an app from the author's pins is absent, its slot uses a built-in fallback. Delete `hotbar-items.json` to restore the nine built-in actions; delete `inventory-items.json` to reset the shelf.

## Apply edits

`Super+Shift+R` reloads compositor rules and keybindings. Close and reopen the inventory, guide, or settings hub after editing them. To reload notifications, run `swaync-client -R -rs`. For Waybar, dock, wallpaper, GTK themes or startup script changes, save your work and log out and back in; this restarts all session components together.

The desktop hub's **Edit desktop configuration** button opens the folder in Files. Open a text configuration file with your preferred editor from there.
