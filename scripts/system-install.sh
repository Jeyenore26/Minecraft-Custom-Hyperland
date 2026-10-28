#!/usr/bin/env bash
set -euo pipefail
[[ $EUID == 0 ]] || { echo 'This helper needs root; use install.sh.' >&2; exit 1; }
repo=$1
source /etc/os-release
[[ $ID == ubuntu && $VERSION_ID == 24.04 && $(dpkg --print-architecture) == amd64 ]] || exit 1
# Save system state before package changes.
backup=$(mktemp -d /var/backups/jeyenore-hyprland-XXXXXXXX)
cp -a /etc/apt/sources.list.d "$backup/"
dpkg-query -W -f='${binary:Package}\t${Version}\n' > "$backup/packages.tsv"
# Install prerequisites from Ubuntu before adding the third-party package source.
apt-get update
apt-get install -y --no-remove ca-certificates gnupg software-properties-common
fingerprint=$(gpg --batch --show-keys --with-colons "$repo/scripts/ppa-key.asc" | awk -F: '$1=="fpr" {print $10; exit}')
[[ $fingerprint == A54D23B62FF3FCC76EFF71E8FDBAAA1CF0CCF48E ]] || { echo 'PPA key fingerprint mismatch' >&2; exit 1; }
if [[ -e /usr/share/wayland-sessions/jeyenore-hyprland.desktop ]]; then cp -a /usr/share/wayland-sessions/jeyenore-hyprland.desktop "$backup/"; fi
add-apt-repository -y -n universe
# Reuse a pre-existing PPA entry to avoid conflicting Signed-By definitions.
if /usr/bin/python3 - <<'PYEXISTING'
from pathlib import Path
import sys
paths = [Path('/etc/apt/sources.list'), *Path('/etc/apt/sources.list.d').glob('*.list'), *Path('/etc/apt/sources.list.d').glob('*.sources')]
for path in paths:
    if not path.exists():
        continue
    text = '\n'.join(line for line in path.read_text().splitlines() if not line.lstrip().startswith('#'))
    if 'Enabled: no' in text:
        continue
    if any(host + '/cppiber/hyprland/ubuntu' in text for host in ('ppa.launchpadcontent.net', 'ppa.launchpad.net')):
        sys.exit(0)
sys.exit(1)
PYEXISTING
then
  echo 'Using existing cppiber Hyprland PPA source.'
else
gpg --batch --yes --dearmor -o /usr/share/keyrings/jeyenore-hyprland.gpg "$repo/scripts/ppa-key.asc"
cat > /etc/apt/sources.list.d/jeyenore-hyprland.sources <<'SOURCE'
Types: deb
URIs: https://ppa.launchpadcontent.net/cppiber/hyprland/ubuntu/
Suites: noble
Components: main
Architectures: amd64
Signed-By: /usr/share/keyrings/jeyenore-hyprland.gpg
SOURCE
fi
apt-get update
# The Lua configuration requires 0.56; fail instead of installing an incompatible release.
version=$(apt-cache madison hyprland | awk '$3 ~ /^0\.56\./ {print $3; exit}')
[[ -n $version ]] || { echo 'No Hyprland 0.56 package available. See docs/DEPENDENCIES.md.' >&2; exit 1; }
packages=("hyprland=$version" waybar wofi hyprlock hypridle swaybg sway-notification-center
  xdg-desktop-portal-hyprland xdg-desktop-portal-gtk policykit-1-gnome
  grim slurp wl-clipboard brightnessctl playerctl pavucontrol network-manager network-manager-gnome
  libnotify-bin fonts-font-awesome fonts-dejavu-core yaru-theme-icon adwaita-icon-theme
  python3 python3-gi python3-cairo python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 gir1.2-nm-1.0
  kitty nautilus firefox zenity gnome-control-center gnome-system-monitor terminator
  pipewire wireplumber util-linux desktop-file-utils fontconfig)
apt-get -s --no-remove install "${packages[@]}" > "$backup/package-plan.txt"
apt-get install -y --no-remove "${packages[@]}"
# Dispatcher resolves the logged-in user's home; no author's username in system files.
install -d /usr/local/bin /usr/share/wayland-sessions
cat > /usr/local/bin/jeyenore-hyprland-session <<'WRAPPER'
#!/bin/sh
exec "$HOME/.local/bin/minecraft-session"
WRAPPER
chmod 755 /usr/local/bin/jeyenore-hyprland-session
cat > /usr/share/wayland-sessions/jeyenore-hyprland.desktop <<'DESKTOP'
[Desktop Entry]
Name=Jeyenore — Minecraft (Hyprland)
Comment=Unofficial Minecraft desktop by Jeyenore
Exec=/usr/local/bin/jeyenore-hyprland-session
TryExec=/usr/bin/Hyprland
Type=Application
DesktopNames=Hyprland
DESKTOP
printf 'System package plan and previous sources saved: %s\n' "$backup"
