#!/bin/sh
exec flock -n "${XDG_RUNTIME_DIR:-/tmp}/minecraft-launcher-$(id -u).lock" /usr/bin/python3 "$HOME/.config/hypr/minecraft/inventory.py"
