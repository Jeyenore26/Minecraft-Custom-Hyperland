#!/bin/bash
set -euo pipefail
mkdir -p "$HOME/Pictures/Screenshots"
region=$(slurp) || exit 0
file="$HOME/Pictures/Screenshots/minecraft-$(date +%Y%m%d-%H%M%S).png"
grim -g "$region" "$file"
wl-copy < "$file"
notify-send 'Map captured' 'Screenshot saved to Pictures/Screenshots and copied.'
