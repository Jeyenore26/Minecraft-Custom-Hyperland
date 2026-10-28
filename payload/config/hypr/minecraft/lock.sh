#!/bin/sh
pgrep -x hyprlock >/dev/null || exec hyprlock -c "$HOME/.config/hypr/minecraft/hyprlock.conf"
