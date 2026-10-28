#!/usr/bin/python3
"""Settings entry point for the Jeyenore desktop."""
import os
from pathlib import Path
import subprocess
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

ROOT = Path(__file__).resolve().parent
GLib.set_prgname('minecraft-settings')


def main():
    Gtk.init([])
    win = Gtk.Window(title='Jeyenore • System settings')
    win.set_wmclass('minecraft-settings', 'minecraft-settings')
    win.set_default_size(480, 540)
    win.set_border_width(24)
    css = Gtk.CssProvider()
    css.load_from_data(b'''
window { background: #142229; color: #e3dfc6; }
* { font-family: Monocraft, monospace; font-size: 15px; }
.title { font-family: Minecraft; font-size: 32px; color: #b7dc9f; }
button { background: #2b4638; color: #f0e7c8; border: 2px solid #71846c;
         border-radius: 0; padding: 12px; }
button:hover { background: #3d5e44; }
''')
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    win.add(box)
    title = Gtk.Label(label='SYSTEM SETTINGS')
    title.get_style_context().add_class('title')
    box.pack_start(title, False, False, 12)

    def launch(_, command, gnome=False):
        env = os.environ.copy()
        if gnome:
            env['XDG_CURRENT_DESKTOP'] = 'GNOME'
        try:
            subprocess.Popen(command, env=env)
        except OSError as error:
            dialog = Gtk.MessageDialog(transient_for=win, modal=True,
                message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.CLOSE,
                text='Could not open settings')
            dialog.format_secondary_text(str(error))
            dialog.run()
            dialog.destroy()

    choices = [
        ('Displays • mirror / extend', ['/usr/bin/python3', str(ROOT / 'display-menu.py')], False),
        ('Wi-Fi', ['/usr/bin/python3', str(ROOT / 'wifi/wifi.py'), '--live'], False),
        ('Saved network connections', ['nm-connection-editor'], False),
        ('Sound • volume / devices', ['pavucontrol'], False),
        ('System settings • GNOME', ['gnome-control-center'], True),
        ('Edit desktop configuration', ['nautilus', str(ROOT.parent)], False),
        ('Keyboard shortcut guide', ['/usr/bin/python3', str(ROOT / 'guide.py')], False),
    ]
    for text, command, gnome in choices:
        button = Gtk.Button(label=text)
        button.connect('clicked', launch, command, gnome)
        box.pack_start(button, False, False, 0)
    win.connect('key-press-event', lambda _, event: (win.destroy() or True) if event.keyval == Gdk.KEY_Escape else False)
    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
