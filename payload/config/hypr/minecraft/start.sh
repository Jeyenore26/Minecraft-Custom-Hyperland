#!/bin/bash
set -u
base="$HOME/.config/hypr/minecraft"
state="$HOME/.local/state/minecraft-desktop"
mkdir -p "$state"
dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE HYPRLAND_INSTANCE_SIGNATURE
"$base/winter-wallpaper.py" > "$state/wallpaper.log" 2>&1 &
/usr/bin/python3 "$base/waybar-session.py" >> "$state/waybar.log" 2>&1 &
"$base/hotbar.py" > "$state/hotbar.log" 2>&1 &
/usr/bin/python3 "$base/desktop-animals.py" >> "$state/animals.log" 2>&1 &
swaync -c "$base/swaync.json" -s "$base/swaync.css" > "$state/notifications.log" 2>&1 &
hypridle -c "$base/hypridle.conf" > "$state/idle.log" 2>&1 &
/usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1 > "$state/polkit.log" 2>&1 &
GDK_BACKEND=x11 nm-applet --no-indicator > "$state/network.log" 2>&1 &
if [[ ! -f "$state/welcomed" ]]; then
 "$base/guide.py" &
 touch "$state/welcomed"
fi
