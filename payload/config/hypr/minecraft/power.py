#!/usr/bin/python3
import gi,subprocess
from pathlib import Path
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gdk,GLib
GLib.set_prgname("minecraft-pause")
Gtk.init([]);win=Gtk.Window(title='World paused');win.set_wmclass('minecraft-pause','minecraft-pause');win.set_default_size(440,520);win.set_border_width(28)
css=Gtk.CssProvider();css.load_from_data(b'window { background: #142229; color: #e3dfc6; } * { font-family: Monocraft; font-size: 21px; } button { background: #2b4038; color: #e3dfc6; border: 3px solid #75846c; border-radius: 0; padding: 14px; } button:hover { background: #426249; } .title { font-family: Minecraft; font-size: 36px; color: #b7dc9f; }');Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);win.add(box);title=Gtk.Label(label='World paused');title.get_style_context().add_class('title');box.pack_start(title,False,False,16)
def act(_,name,cmd,confirm):
 if confirm:
  d=Gtk.MessageDialog(transient_for=win,modal=True,message_type=Gtk.MessageType.QUESTION,buttons=Gtk.ButtonsType.OK_CANCEL,text=name+'?');d.format_secondary_text('Save your work before continuing.');response=d.run();d.destroy()
  if response!=Gtk.ResponseType.OK:return
 if cmd:subprocess.Popen(cmd)
 win.destroy()
for name,cmd,confirm in [('Back to world',None,False),('Lock world',[str(Path.home()/'.config/hypr/minecraft/lock.sh')],False),('Sleep',['systemctl','suspend'],False),('Log out',['hyprctl','dispatch','hl.dsp.exit()'],True),('Restart',['systemctl','reboot'],True),('Power off',['systemctl','poweroff'],True)]:
 b=Gtk.Button(label=name);b.connect('clicked',act,name,cmd,confirm);box.pack_start(b,True,True,0)
win.connect('destroy',Gtk.main_quit);win.show_all();Gtk.main()
