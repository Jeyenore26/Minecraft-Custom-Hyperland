"""Validated, atomic shared hotbar preferences and GTK drag payloads."""
import json,os,tempfile,fcntl,subprocess
from pathlib import Path
import gi
gi.require_version('Gtk','3.0');gi.require_version('Gdk','3.0')
from gi.repository import Gio,GLib,Gdk,Gtk
from inventory_common import ROOT,SHORTCUTS,app_icon,theme
MIME='application/x-minecraft-hotbar-item'
TARGETS=[Gtk.TargetEntry.new(MIME,0,0)]
DEFAULTS=[{'builtin':item[0]} for item in SHORTCUTS]
BUILTINS={item[0]:item for item in SHORTCUTS}

def valid_item(item):
    if not isinstance(item,dict) or len(item)!=1:return False
    if 'builtin' in item:return item['builtin'] in BUILTINS
    name=item.get('app')
    return isinstance(name,str) and len(name)<256 and '/' not in name and name.endswith('.desktop') and Gio.DesktopAppInfo.new(name) is not None

class Store:
    def __init__(self,path=None):
        self.path=Path(path or ROOT/'hotbar-items.json')
    def load(self):
        try:
            items=json.loads(self.path.read_text())
            if not isinstance(items,list) or len(items)!=9:raise ValueError()
            return [item if valid_item(item) else DEFAULTS[i].copy() for i,item in enumerate(items)]
        except (OSError,ValueError):return [i.copy() for i in DEFAULTS]
    def write(self,items):
        if len(items)!=9 or not all(valid_item(i) for i in items):raise ValueError('Invalid hotbar items')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,path=tempfile.mkstemp(prefix='.hotbar-',dir=self.path.parent)
        try:
            with os.fdopen(fd,'w') as f:json.dump(items,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
            os.replace(path,self.path)
        finally:
            if os.path.exists(path):os.unlink(path)
    def drop(self,slot,payload):
        if not isinstance(slot,int) or not 0<=slot<9:raise ValueError('Choose a hotbar slot')
        if isinstance(payload,(str,bytes)):
            if len(payload)>2048:raise ValueError('Invalid drop')
            payload=json.loads(payload)
        if not isinstance(payload,dict) or not valid_item(payload.get('item')):raise ValueError('Drag an installed application')
        with open(str(self.path)+'.lock','w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            items=self.load();source=payload.get('source_slot');item=payload['item']
            if type(source) is int and 0<=source<9 and items[source]==item:
                items[source],items[slot]=items[slot],items[source]
            else:items[slot]=item.copy()
            self.write(items)
        return items
    def restore(self,slot):
        return self.drop(slot,{'item':DEFAULTS[slot]})
    def watch(self,callback):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        monitor=Gio.File.new_for_path(str(self.path.parent)).monitor_directory(Gio.FileMonitorFlags.NONE,None)
        def changed(_,file,other,event):
            if any(f and f.get_basename()==self.path.name for f in (file,other)):callback()
        monitor.connect('changed',changed)
        return monitor

def describe(item,t=None):
    if 'builtin' in item:
        key,label,icon,command=BUILTINS[item['builtin']]
        return key,label,icon,command
    app=Gio.DesktopAppInfo.new(item['app'])
    if not app:return item['app'],'App unavailable','application-x-executable',None
    return item['app'],app.get_display_name(),app_icon(app,t or theme()),app

def launch(action):
    if isinstance(action,list):subprocess.Popen(action)
    elif action:action.launch([],Gdk.Display.get_default().get_app_launch_context())

def payload(item,source=None):
    value={'item':item}
    if source is not None:value['source_slot']=source
    return json.dumps(value).encode()

DRAG_FLAG=Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/f'minecraft-hotbar-drag-{os.getuid()}'
def drag_active(active):
    if active:DRAG_FLAG.write_text(str(os.getpid()))
    else:DRAG_FLAG.unlink(missing_ok=True)
