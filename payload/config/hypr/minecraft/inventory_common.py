from pathlib import Path
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gio
ROOT=Path(__file__).resolve().parent
ASSETS=Path.home()/'.local/share/minecraft-desktop/vanilla'
SHORTCUTS=[
 ('inventory','Applications','view-app-grid',[str(ROOT/'launcher.sh')]),
 ('terminal','Terminal','kitty',['kitty','--config',str(ROOT/'kitty.conf')]),
 ('files','Files','org.gnome.Nautilus',['nautilus','--new-window']),
 ('browser','Firefox','firefox',['firefox']),
 ('capture','Screenshot','org.gnome.Screenshot',[str(ROOT/'screenshot.sh')]),
 ('audio','Sound','multimedia-volume-control',['pavucontrol']),
 ('notifications','Notifications','preferences-system-notifications',['swaync-client','-t']),
 ('lock','Lock','system-lock-screen',[str(ROOT/'lock.sh')]),
 ('pause','Power','system-shutdown',[str(ROOT/'power.py')])]
def theme():
 t=Gtk.IconTheme.new();t.set_custom_theme('Tela');return t
def icon_info(t,icon,size=48):
 if isinstance(icon,str):icon=Gio.ThemedIcon.new(icon)
 found=t.lookup_by_gicon(icon,size,Gtk.IconLookupFlags.FORCE_SIZE) if icon else None
 return found or t.lookup_icon('application-x-executable',size,Gtk.IconLookupFlags.FORCE_SIZE)

# Prefer one coherent icon family while retaining genuine brand icons as fallback.
APP_ICON_NAMES={
 'firefox_firefox.desktop':'firefox','firefox.desktop':'firefox',
 'google-chrome.desktop':'google-chrome','kitty.desktop':'kitty',
 'discord_discord.desktop':'discord','spotify_spotify.desktop':'spotify',
 'figma-linux_figma-linux.desktop':'figma','postman_postman.desktop':'postman',
 'dev.zed.Zed.desktop':'zed','terminator.desktop':'terminator',
 'snap-store_snap-store.desktop':'software-store',
 'firmware-updater_firmware-updater.desktop':'firmware-manager',
 'idle.desktop':'python','idle-python3.12.desktop':'python',
 'minecraft-field-guide.desktop':'help-browser',
}
def app_icon(app,icon_theme):
    name=APP_ICON_NAMES.get(app.get_id(),(app.get_id() or '').removesuffix('.desktop'))
    if name and icon_theme.has_icon(name):return Gio.ThemedIcon.new(name)
    return app.get_icon()

# Stable rows: daily apps, development, then media/utilities. Remaining tools follow.
PREFERRED_APPS=[
 'org.gnome.Nautilus.desktop','firefox.desktop','google-chrome.desktop',
 'kitty.desktop','code.desktop','discord_discord.desktop','spotify_spotify.desktop',
 'figma-linux_figma-linux.desktop','org.gnome.TextEditor.desktop',
 'dev.zed.Zed.desktop','t3-code.desktop','postman_postman.desktop','mongodb-compass.desktop',
 'tableplus.desktop','designer-qt5.desktop','assistant-qt5.desktop','linguist-qt5.desktop','idle.desktop',
 'com.obsproject.Studio.desktop','mpv.desktop','org.gnome.eog.desktop','org.gnome.Evince.desktop',
 'org.gnome.Calculator.desktop','org.gnome.clocks.desktop','org.gnome.Characters.desktop',
 'org.gnome.font-viewer.desktop','terminator.desktop',
]
def ordered_apps(include_duplicates=False):
    apps=[a for a in Gio.AppInfo.get_all() if a.should_show()]
    ids={a.get_id() for a in apps}
    aliases={'firefox_firefox.desktop':'firefox.desktop','idle-python3.12.desktop':'idle.desktop'}
    if not include_duplicates:apps=[a for a in apps if aliases.get(a.get_id()) not in ids]
    rank={name:i for i,name in enumerate(PREFERRED_APPS)}
    return sorted(apps,key=lambda a:(rank.get(a.get_id(),999),a.get_display_name().casefold()))
