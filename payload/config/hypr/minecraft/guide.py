#!/usr/bin/python3
import gi,subprocess
from pathlib import Path
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gdk,GLib
GLib.set_prgname("minecraft-guide")
P=Path.home()/'.config/hypr/minecraft'
Gtk.init([])
win=Gtk.Window(title='Shortcuts • Ancient City');win.set_wmclass('minecraft-guide','minecraft-guide');win.set_default_size(740,660);win.set_border_width(24)
css=Gtk.CssProvider();css.load_from_data(b'''
window { background: #142229; color: #e3dfc6; }
* { font-family: Monocraft; font-size: 14px; }
.title { font-family: Minecraft; font-size: 40px; color: #b7dc9f; }
.subtitle { color: #d8b67e; font-size: 14px; }
.key { color: #a5d590; }
notebook, notebook header, notebook stack { background: #142229; }
notebook tab { padding: 10px 12px; color: #e3dfc6; }
notebook tab:checked { background: #2b4638; }
button { background: #2b4638; color: #f0e7c8; border: 2px solid #71846c; border-radius: 0; padding: 12px; }
button:hover { background: #3d5e44; }
''');Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=14);win.add(box)
def label(text,style=None):
 w=Gtk.Label(label=text);w.set_xalign(0)
 if style:w.get_style_context().add_class(style)
 box.pack_start(w,False,False,0)
label('SHORTCUTS','title');label('Super = Windows key · Open this guide with Super + H','subtitle')
notebook=Gtk.Notebook();box.pack_start(notebook,True,True,0)
def page(title,description,shortcuts):
 content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=16)
 content.set_border_width(16)
 intro=Gtk.Label(label=description);intro.set_xalign(0);intro.set_line_wrap(True)
 content.pack_start(intro,False,False,0)
 grid=Gtk.Grid(column_spacing=20,row_spacing=14)
 for i,(key,action) in enumerate(shortcuts):
  a=Gtk.Label(label=key);a.set_xalign(0);a.set_yalign(0);a.get_style_context().add_class('key')
  b=Gtk.Label(label=action);b.set_xalign(0);b.set_yalign(0);b.set_line_wrap(True);b.set_max_width_chars(34);b.set_hexpand(True)
  grid.attach(a,0,i,1,1);grid.attach(b,1,i,1,1)
 content.pack_start(grid,False,False,0)
 scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);scroll.add(content)
 notebook.append_page(scroll,Gtk.Label(label=title))
page('Desktop','Move the whole app window between your screens. Hold Super while dragging anywhere inside the window.',[
 ('Super + Shift + Left','Move window to the left screen'),
 ('Super + Shift + Right','Move window to the right screen'),
 ('Super + left drag','Move window; drag across the screen edge'),
 ('Super + right drag','Resize window'),
 ('Super + arrow keys','Focus a neighbouring window'),
 ('Super + Tab','Search and switch between open windows'),
 ('Super + Q','Close current window'),
 ('Super + V','Toggle floating window'),
 ('Super + F','Toggle fullscreen for current window'),
 ('Super + N','Open / close notifications'),
 ('Super + comma','Open system settings'),
 ('Super + P','Display options: duplicate, extend, single screen'),
 ('Super + Enter','Open Minecraft Kitty terminal'),
 ('Super + E / B','Open files / browser'),
 ('Super + 1–9','Switch workspace'),
 ('Super + Shift + 1–9','Move window to a workspace'),
 ('Super + Shift + S','Take a screenshot'),
 ('Super + L','Lock screen'),
 ('Super + Escape','Open power menu'),
 ('Alt + Shift','Switch English / Arabic'),
 ('Ctrl + W','Close browser tab'),
])
page('Inventory','Search opens automatically. Drag apps onto the bottom row or the desktop dock to pin them.',[
 ('Super + Space / R','Open inventory'),
 ('Escape / click outside','Close inventory'),
 ('/ or Ctrl + F','Open search from the grid'),
 ('Enter','Launch first search result / selected app'),
 ('Down (in search)','Move focus to the app grid'),
 ('Arrow keys','Select an app in the grid'),
 ('Scroll / Page Up / Down','Browse app pages'),
])
page('Terminator','These shortcuts apply to Terminator. Closing the last pane also closes its tab.',[
 ('Ctrl + Shift + D','Split left / right'),
 ('Ctrl + Shift + E','Split top / bottom'),
 ('Ctrl + Shift + arrows','Focus another pane'),
 ('Ctrl + Shift + Alt + arrows','Resize pane'),
 ('Ctrl + Shift + Z','Maximize / restore pane'),
 ('Ctrl + Shift + W','Close current pane'),
 ('Ctrl + Shift + Q','Close entire terminal window'),
 ('Ctrl + Shift + T','New tab'),
 ('Ctrl + Page Down / Up','Next / previous tab'),
 ('Ctrl + Shift + C / V','Copy / paste'),
])
page('Minecraft Kitty','The terminal opened with Super + Enter uses these shortcuts.',[
 ('Ctrl + Shift + Enter','Add a terminal pane'),
 ('Ctrl + Shift + L','Cycle pane layouts'),
 ('Ctrl + Shift + W','Close current pane'),
 ('Ctrl + Shift + Q','Close entire tab'),
 ('Ctrl + Shift + T','New tab'),
 ('Ctrl + Tab','Next tab'),
 ('Ctrl + Shift + Tab','Previous tab'),
 ('Ctrl + Shift + C / V','Copy / paste'),
])
row=Gtk.Box(spacing=12)
for text,cmd in [('Inventory',[str(P/'launcher.sh')]),('Terminal',['/usr/bin/kitty','--config',str(P/'kitty.conf')])]:
 b=Gtk.Button(label=text);b.connect('clicked',lambda _,c=cmd:subprocess.Popen(c));row.pack_start(b,True,True,0)
b=Gtk.Button(label='Close');b.connect('clicked',lambda _:win.destroy());row.pack_start(b,True,True,0);box.pack_start(row,False,False,0)
win.connect('key-press-event',lambda _,event: (win.destroy() or True) if event.keyval==Gdk.KEY_Escape else False)
win.connect('destroy',Gtk.main_quit);win.show_all();Gtk.main()
