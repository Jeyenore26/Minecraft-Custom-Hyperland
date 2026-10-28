#!/usr/bin/python3
"""Per-monitor Minecraft dock. A three-pixel bottom edge reveals it on hover."""
import os,sys,subprocess,fcntl,time
from pathlib import Path
import cairo,gi
gi.require_foreign('cairo')
gi.require_version('Gtk','3.0');gi.require_version('GtkLayerShell','0.1')
from gi.repository import Gtk,Gdk,GLib,GtkLayerShell
from inventory_common import ASSETS,SHORTCUTS,theme,icon_info
from hotbar_store import Store,TARGETS,describe,launch,payload,drag_active,DRAG_FLAG
SCALE=3
WIDTH=184*SCALE
HEIGHT=24*SCALE

class Hotbar:
    def __init__(self,monitor):
        self.monitor=monitor;self.timer=0;self.inside_dock=False;self.inside_trigger=False;self.hover=None;self.visible=False;self.closed=False
        self.sheet=cairo.ImageSurface.create_from_png(str(ASSETS/'widgets.png'))
        self.icon_theme=theme();self.store=Store();self.shortcuts=[];self.icons=[]
        self.drag_over=False;self.external_drag=False;self.dragging=False;self.press=None;self.drag_bytes=None
        self.reload_pins();self.monitor_file=self.store.watch(self.reload_pins)
        self.dock=self.window('minecraft-hotbar',WIDTH,HEIGHT,4)
        self.canvas=Gtk.DrawingArea();self.canvas.set_size_request(WIDTH,HEIGHT)
        self.canvas.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK|Gdk.EventMask.LEAVE_NOTIFY_MASK|Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.BUTTON_PRESS_MASK|Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.canvas.connect('draw',self.draw);self.canvas.connect('enter-notify-event',self.enter_dock)
        self.canvas.connect('leave-notify-event',self.leave_dock);self.canvas.connect('motion-notify-event',self.motion)
        self.canvas.connect('button-press-event',self.click);self.canvas.connect('button-release-event',self.release);self.dock.add(self.canvas)
        self.canvas.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,TARGETS,Gdk.DragAction.COPY|Gdk.DragAction.MOVE)
        self.canvas.drag_dest_set(Gtk.DestDefaults.DROP,TARGETS,Gdk.DragAction.COPY|Gdk.DragAction.MOVE)
        self.canvas.connect('drag-begin',self.drag_begin);self.canvas.connect('drag-data-get',self.drag_data)
        self.canvas.connect('drag-end',self.drag_end);self.canvas.connect('drag-motion',self.drag_motion)
        self.canvas.connect('drag-leave',self.drag_leave);self.canvas.connect('drag-data-received',self.drag_received)
        self.trigger=self.window('minecraft-hotbar-trigger',WIDTH,3,0)
        edge=Gtk.EventBox();edge.set_visible_window(False);edge.set_size_request(WIDTH,3)
        edge.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK|Gdk.EventMask.LEAVE_NOTIFY_MASK)
        edge.connect('enter-notify-event',self.enter_trigger);edge.connect('leave-notify-event',self.leave_trigger)
        edge.drag_dest_set(Gtk.DestDefaults.MOTION,TARGETS,Gdk.DragAction.COPY)
        edge.connect('drag-motion',self.edge_drag)
        edge.connect('drag-leave',lambda *_:self.schedule_hide())
        self.trigger.add(edge);self.trigger.show_all()

    def window(self,name,width,height,bottom):
        win=Gtk.Window(type=Gtk.WindowType.TOPLEVEL);win.set_name(name);win.set_decorated(False)
        win.set_accept_focus(False);win.set_app_paintable(True);win.set_default_size(width,height)
        visual=win.get_screen().get_rgba_visual()
        if visual:win.set_visual(visual)
        GtkLayerShell.init_for_window(win);GtkLayerShell.set_namespace(win,name)
        GtkLayerShell.set_monitor(win,self.monitor);GtkLayerShell.set_layer(win,GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(win,GtkLayerShell.Edge.BOTTOM,True)
        GtkLayerShell.set_margin(win,GtkLayerShell.Edge.BOTTOM,bottom)
        GtkLayerShell.set_keyboard_mode(win,GtkLayerShell.KeyboardMode.NONE)
        GtkLayerShell.set_exclusive_zone(win,0)
        return win

    def cancel_hide(self):
        if self.timer:GLib.source_remove(self.timer);self.timer=0

    def reveal(self):
        self.cancel_hide();self.visible=True;self.dock.show_all()

    def schedule_hide(self):
        self.cancel_hide();self.timer=GLib.timeout_add(350,self.hide_if_outside)

    def hide_if_outside(self):
        self.timer=0
        if not self.inside_dock and not self.inside_trigger and not self.drag_over and not self.external_drag:
            self.visible=False;self.hover=None;self.dock.hide()
        return False

    def enter_trigger(self,*_):self.inside_trigger=True;self.reveal();return False
    def leave_trigger(self,*_):self.inside_trigger=False;self.schedule_hide();return False
    def enter_dock(self,*_):self.inside_dock=True;self.cancel_hide();return False
    def leave_dock(self,*_):self.inside_dock=False;self.hover=None;self.canvas.queue_draw();self.schedule_hide();return False

    def motion(self,_,event):
        index=int((event.x/SCALE-2)//20)
        self.hover=index if 0<=index<9 else None
        self.canvas.set_tooltip_text(self.shortcuts[self.hover][1] if self.hover is not None else None)
        self.canvas.queue_draw();return False

    def paint_sprite(self,cr,sx,sy,w,h,x,y):
        cr.save();cr.rectangle(x,y,w,h);cr.clip();cr.set_source_surface(self.sheet,x-sx,y-sy)
        cr.get_source().set_filter(cairo.FILTER_NEAREST);cr.paint();cr.restore()

    def draw(self,_,cr):
        cr.set_operator(cairo.OPERATOR_SOURCE);cr.set_source_rgba(0,0,0,0);cr.paint();cr.set_operator(cairo.OPERATOR_OVER)
        cr.save();cr.scale(SCALE,SCALE);self.paint_sprite(cr,0,0,182,22,1,1)
        if self.hover is not None:self.paint_sprite(cr,0,22,24,24,self.hover*20,0)
        for i,pix in enumerate(self.icons):
            cr.save();cr.translate(6+20*i,6);cr.scale(1/SCALE,1/SCALE)
            Gdk.cairo_set_source_pixbuf(cr,pix,0,0);cr.paint();cr.restore()
        cr.restore();return False

    def reload_pins(self):
        self.pinned=self.store.load();self.shortcuts=[describe(i,self.icon_theme) for i in self.pinned]
        self.icons=[icon_info(self.icon_theme,i[2],36).load_icon() for i in self.shortcuts]
        if hasattr(self,'canvas'):self.canvas.queue_draw()

    def index_at(self,x):
        i=int((x/SCALE-2)//20)
        return i if 0<=i<9 else None

    def click(self,_,event):
        if event.button==3:
            index=self.index_at(event.x)
            if index is not None:
                menu=Gtk.Menu();item=Gtk.MenuItem(label='Restore default slot')
                item.connect('activate',lambda _:self.store.restore(index));menu.append(item);menu.show_all();menu.popup_at_pointer(event)
            return True
        if event.button!=1:return False
        self.press=(self.index_at(event.x),event.x,event.y);self.dragging=False;return False

    def release(self,_,event):
        press=self.press;self.press=None
        if event.button!=1 or not press or self.dragging:return False
        index,x,y=press
        if index is None or index!=self.index_at(event.x) or abs(event.x-x)+abs(event.y-y)>8:return False
        try:launch(self.shortcuts[index][3])
        except (OSError,GLib.Error) as e:print('Could not launch hotbar item:',e,file=sys.stderr)
        if self.pinned[index].get('builtin')=='capture':
            self.inside_dock=False;self.inside_trigger=False;self.hide_if_outside()
        return True

    def drag_begin(self,_,context):
        index=self.press[0] if self.press else None
        if index is None:Gtk.drag_cancel(context);return
        self.dragging=True;self.drag_bytes=payload(self.pinned[index],index);drag_active(True)
        Gtk.drag_set_icon_pixbuf(context,self.icons[index],18,18)

    def drag_data(self,_,context,selection,info,time):
        if self.drag_bytes:selection.set(selection.get_target(),8,self.drag_bytes)

    def drag_end(self,*_):
        self.dragging=False;self.press=None;self.drag_bytes=None;drag_active(False);self.drag_over=False;self.schedule_hide()

    def edge_drag(self,_,context,x,y,time):
        self.reveal();Gdk.drag_status(context,Gdk.DragAction.COPY,time);return True

    def drag_motion(self,_,context,x,y,time):
        self.drag_over=True;self.cancel_hide();self.hover=self.index_at(x)
        Gdk.drag_status(context,Gdk.DragAction.COPY if self.hover is not None else Gdk.DragAction(0),time)
        self.canvas.queue_draw();return True

    def drag_leave(self,*_):self.drag_over=False;self.hover=None;self.canvas.queue_draw();self.schedule_hide()

    def drag_received(self,_,context,x,y,selection,info,time):
        success=False
        try:
            index=self.index_at(x)
            if index is not None:self.store.drop(index,bytes(selection.get_data()));success=True;self.reload_pins()
        except (ValueError,OSError,TypeError) as e:print('Hotbar drop:',e,file=sys.stderr)
        self.drag_over=False;Gtk.drag_finish(context,success,False,time);self.schedule_hide()

    def destroy(self):
        self.closed=True;self.monitor_file.cancel();self.cancel_hide();self.dock.destroy();self.trigger.destroy()

class DockApp:
    def __init__(self):
        self.bars={};self.display=Gdk.Display.get_default()
        self.display.connect('monitor-added',lambda _,m:self.add(m))
        self.display.connect('monitor-removed',lambda _,m:self.remove(m))
        for i in range(self.display.get_n_monitors()):self.add(self.display.get_monitor(i))
        self.drag_timer=GLib.timeout_add(150,self.sync_drag)
    def sync_drag(self):
        try:active=time.time()-DRAG_FLAG.stat().st_mtime<60
        except OSError:active=False
        for bar in self.bars.values():
            if active!=bar.external_drag:
                bar.external_drag=active
                if active:bar.reveal()
                else:bar.schedule_hide()
        return True
    def add(self,monitor):
        if monitor not in self.bars:self.bars[monitor]=Hotbar(monitor)
    def remove(self,monitor):
        bar=self.bars.pop(monitor,None)
        if bar:bar.destroy()

def init_style():
    css=Gtk.CssProvider();css.load_from_data(b'window#minecraft-hotbar, window#minecraft-hotbar-trigger { background: transparent; border: none; box-shadow: none; } tooltip { background: #1e102e; color: white; border: 2px solid #573183; font-family: Monocraft; font-size: 16px; }')
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__=='__main__':
    lock=open(Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/f'minecraft-hotbar-{os.getuid()}.lock','w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:sys.exit(0)
    GLib.set_prgname('minecraft-hotbar');init_style();app=DockApp();Gtk.main()
