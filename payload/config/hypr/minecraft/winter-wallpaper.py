#!/usr/bin/python3
"""Cold Minecraft wallpaper with gently drifting pixel snow and a cached background."""
import math,random,time,os,fcntl
from pathlib import Path
from hotbar import Gtk,Gdk,GLib,GtkLayerShell,cairo
IMAGE=Path.home()/'.local/share/minecraft-desktop/frozen-river.png'
CACHE={}

class Winter(Gtk.Window):
    def __init__(self,monitor,index=0):
        super().__init__()
        self.monitor=monitor;self.start=time.monotonic();self.frame_time=0;self.last=[]
        self.set_name('minecraft-winter');self.set_decorated(False);self.set_accept_focus(False);self.set_app_paintable(True)
        GtkLayerShell.init_for_window(self);GtkLayerShell.set_namespace(self,'minecraft-winter-wallpaper')
        GtkLayerShell.set_layer(self,GtkLayerShell.Layer.BACKGROUND);GtkLayerShell.set_monitor(self,monitor)
        GtkLayerShell.set_keyboard_mode(self,GtkLayerShell.KeyboardMode.NONE);GtkLayerShell.set_exclusive_zone(self,-1)
        for edge in (GtkLayerShell.Edge.TOP,GtkLayerShell.Edge.BOTTOM,GtkLayerShell.Edge.LEFT,GtkLayerShell.Edge.RIGHT):GtkLayerShell.set_anchor(self,edge,True)
        self.area=Gtk.DrawingArea();self.area.connect('draw',self.draw);self.add(self.area)
        self.connect('realize',self.pass_through)
        self.area.connect('size-allocate',self.resize)
        r=random.Random(3701+index)
        self.flakes=[(r.random(),r.random(),r.uniform(10,28),r.uniform(1,3),r.uniform(.2,.65),r.uniform(0,math.tau)) for _ in range(110)]
        self.bg=None;self.width=1;self.height=1
        self.show_all();self.tick=self.area.add_tick_callback(self.animate)

    def pass_through(self,*_):self.get_window().input_shape_combine_region(cairo.Region(),0,0)

    def resize(self,_,alloc):
        if (alloc.width,alloc.height)==(self.width,self.height) and self.bg:return
        self.width,self.height=max(1,alloc.width),max(1,alloc.height)
        key=(self.width,self.height)
        if key not in CACHE:
            source=cairo.ImageSurface.create_from_png(str(IMAGE))
            target=cairo.ImageSurface(cairo.FORMAT_RGB24,*key);cr=cairo.Context(target)
            scale=max(self.width/source.get_width(),self.height/source.get_height())
            cr.translate((self.width-source.get_width()*scale)/2,(self.height-source.get_height()*scale)/2)
            cr.scale(scale,scale);cr.set_source_surface(source,0,0);cr.get_source().set_filter(cairo.FILTER_BILINEAR);cr.paint()
            CACHE[key]=target
        self.bg=CACHE[key];self.last=[]

    def positions(self,t):
        return [((x*self.width+10*math.sin(t*.3+phase)+t*(3+size))%(self.width+10)-5,
                 (y*self.height+t*speed)%(self.height+10)-5,size,alpha)
                for x,y,speed,size,alpha,phase in self.flakes]

    def animate(self,_,clock):
        now=clock.get_frame_time()
        if now-self.frame_time<66666:return True  # 15 fps; frame callbacks stop when the surface is not visible.
        self.frame_time=now
        current=self.positions(time.monotonic()-self.start)
        self.area.queue_draw()
        self.last=current
        return True

    def draw(self,_,cr):
        if not self.bg:return False
        cr.set_source_surface(self.bg,0,0);cr.paint()
        cr.set_antialias(cairo.ANTIALIAS_NONE)
        for x,y,size,alpha in self.positions(time.monotonic()-self.start):
            cr.set_source_rgba(.84,.93,1,alpha);cr.rectangle(round(x),round(y),round(size),round(size));cr.fill()
        return False

class Wallpaper:
    def __init__(self):
        self.windows={};d=Gdk.Display.get_default()
        d.connect('monitor-added',lambda _,m:self.add(m));d.connect('monitor-removed',lambda _,m:self.remove(m))
        for i in range(d.get_n_monitors()):self.add(d.get_monitor(i))
    def add(self,monitor):
        if monitor not in self.windows:self.windows[monitor]=Winter(monitor,len(self.windows))
    def remove(self,monitor):
        w=self.windows.pop(monitor,None)
        if w:w.destroy()

if __name__=='__main__':
    lock=open(Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/f'minecraft-winter-{os.getuid()}.lock','w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit(0)
    css=Gtk.CssProvider();css.load_from_data(b'window#minecraft-winter { background: #112139; border: none; box-shadow: none; }')
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    app=Wallpaper();Gtk.main()
