#!/usr/bin/python3
"""Minecraft Wi-Fi panel. Preview by default; --live enables NetworkManager."""
import argparse
import subprocess
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('NM', '1.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, NM, Pango

AP_SECURITY = getattr(NM, '80211ApSecurityFlags')
AP_FLAGS = getattr(NM, '80211ApFlags')

ROOT = Path(__file__).resolve().parent
ASSETS = Path.home() / '.local/share/minecraft-desktop/vanilla/recipe-items'


def label(text, style=None):
    widget = Gtk.Label(label=text, xalign=0)
    if style:
        widget.get_style_context().add_class(style)
    return widget


class Signal(Gtk.Box):
    def __init__(self, strength, connected=False):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        self.set_size_request(48, 36)
        self.set_valign(Gtk.Align.CENTER)
        for i in range(4):
            bar = Gtk.Box()
            bar.set_size_request(8, (i + 1) * 6)
            bar.set_valign(Gtk.Align.END)
            bar.get_style_context().add_class('signal-lit' if strength > i * 25 else 'signal-dim')
            self.pack_start(bar, False, False, 0)


class Wifi(Gtk.Window):
    def __init__(self, live=False, screenshot=None):
        super().__init__(title='Wi-Fi settings' if live else 'Wi-Fi design preview')
        self.live, self.screenshot = live, screenshot
        self.client = NM.Client.new(None) if live else None
        self.busy = False
        self.devices = []
        self.set_wmclass('minecraft-wifi', 'minecraft-wifi')
        self.set_default_size(760, 640)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.connect('destroy', Gtk.main_quit)
        self.connect('key-press-event', self.key)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.set_name('inventory')
        self.add(root)
        header = Gtk.Box(spacing=14)
        header.set_border_width(22)
        icon = Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(str(ASSETS / 'compass.png'), 16, 16, True).scale_simple(48,48,GdkPixbuf.InterpType.NEAREST))
        header.pack_start(icon, False, False, 0)
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        titles.pack_start(label('Wi-Fi settings', 'title'), False, False, 0)
        titles.pack_start(label('Find a network. Join your world.', 'subtitle'), False, False, 0)
        header.pack_start(titles, True, True, 0)
        close = Gtk.Button(label='X')
        close.get_style_context().add_class('close')
        close.connect('clicked', lambda *_: self.destroy())
        header.pack_start(close, False, False, 0)
        root.pack_start(header, False, False, 0)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(24); content.set_margin_end(24); content.set_margin_bottom(22)
        root.pack_start(content, True, True, 0)
        toolbar = Gtk.Box(spacing=10)
        toolbar.pack_start(label('Wireless networks', 'section'), True, True, 0)
        self.toggle = Gtk.Button(label='Wi-Fi: ON')
        self.toggle.connect('clicked', self.toggle_wifi)
        toolbar.pack_end(self.toggle, False, False, 0)
        content.pack_start(toolbar, False, False, 0)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(310)
        scroll.get_style_context().add_class('network-well')
        self.rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.rows.set_border_width(8)
        scroll.add(self.rows)
        content.pack_start(scroll, True, True, 0)
        self.status = label('Choose a network to connect.' if live else 'Preview mode - sample networks; controls do not change Wi-Fi.', 'hint')
        self.status.set_line_wrap(True)
        self.status.set_max_width_chars(66)
        content.pack_start(self.status, False, False, 0)
        buttons = Gtk.Box(spacing=12)
        self.refresh_button = Gtk.Button(label='Refresh')
        self.refresh_button.connect('clicked', self.scan)
        advanced = Gtk.Button(label='Saved networks...')
        advanced.connect('clicked', self.advanced)
        done = Gtk.Button(label='Done')
        done.connect('clicked', lambda *_: self.destroy())
        for b in (self.refresh_button, advanced, done):
            buttons.pack_start(b, True, True, 0)
        content.pack_start(buttons, False, False, 0)
        self.populate()
        self.show_all()
        if live:
            GLib.timeout_add_seconds(5, self.refresh)
        if screenshot:
            GLib.timeout_add(500, self.capture)

    def key(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True

    def capture(self):
        w, h = self.get_size()
        pixbuf = Gdk.pixbuf_get_from_window(self.get_window(), 0, 0, w, h)
        pixbuf.savev(str(self.screenshot), 'png', [], [])
        self.destroy()
        return False

    def refresh(self):
        if not self.busy:
            self.populate()
        return True

    def populate(self):
        for child in self.rows.get_children():
            child.destroy()
        if not self.live:
            networks = [('Home network', 94, True, 'WPA2', None, None),
                        ('Crafting room', 76, False, 'WPA2', None, None),
                        ('Village guest', 51, False, 'Open', None, None)]
        else:
            self.devices = [d for d in self.client.get_devices() if isinstance(d, NM.DeviceWifi)]
            enabled = self.client.wireless_get_enabled()
            self.toggle.set_label('Wi-Fi: ON' if enabled else 'Wi-Fi: OFF')
            self.toggle.set_sensitive(self.client.wireless_hardware_get_enabled() and not self.busy)
            networks = []
            for dev in self.devices:
                active = dev.get_active_access_point()
                for ap in dev.get_access_points():
                    ssid = ap.get_ssid()
                    if not ssid:
                        continue
                    name = NM.utils_ssid_to_utf8(ssid.get_data())
                    flags = ap.get_rsn_flags() | ap.get_wpa_flags()
                    if flags & AP_SECURITY.KEY_MGMT_802_1X:
                        security = 'Enterprise'
                    elif flags & AP_SECURITY.KEY_MGMT_SAE:
                        security = 'WPA3'
                    elif flags:
                        security = 'WPA2'
                    elif ap.get_flags() & AP_FLAGS.PRIVACY:
                        security = 'Legacy'
                    else:
                        security = 'Open'
                    networks.append((name, ap.get_strength(), ap == active, security, dev, ap))
            unique = {}
            for item in sorted(networks, key=lambda n: (not n[2], -n[1])):
                unique.setdefault((item[0], item[3]), item)
            networks = list(unique.values()) if enabled else []
            if not networks:
                message = 'No Wi-Fi adapter found.' if not self.devices else ('Wi-Fi is off.' if not enabled else 'No networks found. Try Refresh.')
                self.rows.pack_start(label(message, 'empty'), True, True, 30)
        for network in networks:
            name, strength, connected, security, dev, ap = network
            row = Gtk.Box(spacing=16)
            row.get_style_context().add_class('network')
            if connected:
                row.get_style_context().add_class('connected')
            row.pack_start(Signal(strength, connected), False, False, 0)
            texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            title = label(name, 'ssid')
            title.set_ellipsize(Pango.EllipsizeMode.END)
            title.set_max_width_chars(28)
            texts.pack_start(title, False, False, 0)
            subtitle = f'Connected  /  {strength}%' if connected else f'{security}  /  Signal {strength}%'
            texts.pack_start(label(subtitle, 'connected-text' if connected else 'network-detail'), False, False, 0)
            row.pack_start(texts, True, True, 0)
            button = Gtk.Button(label='Disconnect' if connected else 'Connect')
            button.set_sensitive(not self.busy)
            button.connect('clicked', self.connect_network, network)
            row.pack_end(button, False, False, 0)
            self.rows.pack_start(row, False, False, 0)
        self.rows.show_all()

    def preview_message(self):
        self.status.set_text('Preview only - your current connection stays unchanged.')

    def advanced(self, *_):
        if self.live:
            subprocess.Popen(['nm-connection-editor'])
        else:
            self.preview_message()

    def toggle_wifi(self, *_):
        if not self.live:
            self.preview_message(); return
        self.client.wireless_set_enabled(not self.client.wireless_get_enabled())
        GLib.timeout_add(600, lambda: (self.populate(), False)[1])

    def scan(self, *_):
        if not self.live:
            self.preview_message(); return
        self.status.set_text('Searching for nearby networks...')
        for dev in self.devices:
            dev.request_scan_async(None, self.scanned, None)

    def scanned(self, dev, result, data):
        try:
            dev.request_scan_finish(result)
            self.status.set_text('Network list refreshed.')
        except GLib.Error as error:
            self.status.set_text(error.message)
        self.populate()

    def password(self, name):
        dialog = Gtk.Dialog(title='Connect to ' + name, transient_for=self, modal=True)
        dialog.set_border_width(20)
        dialog.add_buttons('Cancel', Gtk.ResponseType.CANCEL, 'Connect', Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        box = dialog.get_content_area(); box.set_spacing(12)
        box.pack_start(label('Password for ' + name), False, False, 0)
        entry = Gtk.Entry(); entry.set_visibility(False); entry.set_activates_default(True)
        box.pack_start(entry, False, False, 0)
        show = Gtk.CheckButton(label='Show password')
        show.connect('toggled', lambda w: entry.set_visibility(w.get_active()))
        box.pack_start(show, False, False, 0)
        dialog.show_all(); entry.grab_focus()
        response = dialog.run()
        secret = entry.get_text() if response == Gtk.ResponseType.OK else None
        entry.set_text(''); dialog.destroy()
        return secret

    def connect_network(self, button, network):
        if not self.live:
            self.preview_message(); return
        name, strength, connected, security, dev, ap = network
        if connected:
            self.busy = True
            dev.disconnect_async(None, self.finished, 'disconnect')
        else:
            existing = next((c for c in dev.get_available_connections() if ap.connection_valid(c)), None)
            if existing:
                self.busy = True
                self.client.activate_connection_async(existing, dev, ap.get_path(), None, self.finished, 'activate')
            elif security in ('Enterprise', 'Legacy'):
                self.status.set_text('Use Saved networks to configure this network’s security.')
                self.advanced(); return
            else:
                secret = None
                if security != 'Open':
                    secret = self.password(name)
                    if secret is None:
                        return
                    if security == 'WPA2' and not (8 <= len(secret) <= 63 or (len(secret) == 64 and all(c in '0123456789abcdefABCDEF' for c in secret))):
                        self.status.set_text('WPA2 passwords need 8-63 characters or 64 hex digits.'); return
                    if not secret:
                        self.status.set_text('Enter a password to connect.'); return
                connection = NM.SimpleConnection.new()
                general = NM.SettingConnection.new()
                general.set_property('id', name)
                general.set_property('type', '802-11-wireless')
                general.set_property('uuid', NM.utils_uuid_generate())
                general.set_property('autoconnect', True)
                connection.add_setting(general)
                wireless = NM.SettingWireless.new()
                wireless.set_property('ssid', ap.get_ssid())
                wireless.set_property('mode', 'infrastructure')
                connection.add_setting(wireless)
                if secret is not None:
                    setting = NM.SettingWirelessSecurity.new()
                    setting.set_property('key-mgmt', 'sae' if security == 'WPA3' else 'wpa-psk')
                    setting.set_property('psk', secret)
                    connection.add_setting(setting)
                self.busy = True
                self.client.add_and_activate_connection_async(connection, dev, ap.get_path(), None, self.finished, 'add')
        self.status.set_text('Disconnecting...' if connected else 'Connecting to ' + name + '...')
        self.populate()

    def finished(self, obj, result, action):
        try:
            if action == 'disconnect':
                obj.disconnect_finish(result)
                self.status.set_text('Disconnected.')
            else:
                active = obj.activate_connection_finish(result) if action == 'activate' else obj.add_and_activate_connection_finish(result)
                active.connect('state-changed', self.connection_state)
                self.status.set_text('Waiting for the connection...')
        except GLib.Error as error:
            self.status.set_text(error.message)
        self.busy = False
        self.populate()

    def connection_state(self, active, state, reason):
        if state == NM.ActiveConnectionState.ACTIVATED:
            self.status.set_text('Connected to ' + active.get_id() + '.')
        elif state == NM.ActiveConnectionState.DEACTIVATED:
            self.status.set_text('Connection ended. Check the password or edit Saved networks.')
        self.populate()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--screenshot', type=Path)
    args = parser.parse_args()
    GLib.set_prgname('minecraft-wifi')
    Gtk.init([])
    css = Gtk.CssProvider(); css.load_from_path(str(ROOT / 'wifi.css'))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    window = Wifi(args.live, args.screenshot)
    Gtk.main()


if __name__ == '__main__':
    main()
