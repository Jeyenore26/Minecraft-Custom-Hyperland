#!/usr/bin/python3
"""Minecraft recipe-book launcher, persistent inventory, and animated book toggle."""
import math,sys,subprocess,signal,json
from pathlib import Path
import cairo,gi
gi.require_foreign('cairo')
gi.require_version('Gtk','3.0')
from gi.repository import Gtk,Gdk,Gio,GLib
from inventory_common import ROOT,ASSETS,SHORTCUTS,theme,icon_info,app_icon,ordered_apps
from steve import Steve
from inventory_shelf import Shelf
from hotbar_store import Store,TARGETS,describe,payload,drag_active
SCALE=3
PAGE_SIZE=20
BROWSER_X=36
WINDOW_WIDTH=400
WINDOW_HEIGHT=184
GLASS_OPACITY=.90
BOOK_DURATION=320000
MAIN_X=202
MAIN_CLOSED_X=103
RECIPE_ICONS=['black_bundle','bundle','chest_minecart','flint_and_steel','mace',
 'name_tag','shears','acacia_planks','dark_oak_log','amethyst_block',
 'andesite','bricks','red_nether_bricks','chiseled_copper','polished_blackstone_bricks',
 'nether_bricks','chiseled_polished_blackstone','quartz_block_side','chiseled_red_sandstone','jack_o_lantern']
BLOCK_ICONS=set(RECIPE_ICONS[7:])
CATEGORIES=[('All apps',None),('Tools',{'Development','System','Utility'}),
 ('Building',{'Development','Graphics','Science','Education'}),
 ('Media',{'AudioVideo','Audio','Video','Game','Graphics'}),
 ('Connections',{'Network','Settings'})]

def applications():
    return ordered_apps()

def rectangle(cr,x,y,w,h,color):
    cr.set_source_rgb(*[int(color[i:i+2],16)/255 for i in (0,2,4)])
    cr.rectangle(x,y,w,h);cr.fill()

def slot(cr,x,y,width=16):
    rectangle(cr,x-1,y-1,width+2,18,'8b8b8b')
    rectangle(cr,x-1,y-1,width+1,1,'373737');rectangle(cr,x-1,y,1,16,'373737')
    rectangle(cr,x,y+16,width+1,1,'ffffff');rectangle(cr,x+width,y,1,16,'ffffff')

class Inventory(Gtk.Window):
    def __init__(self):
        super().__init__(title='Inventory')
        self.set_resizable(True)
        self.set_default_size(WINDOW_WIDTH*SCALE,WINDOW_HEIGHT*SCALE)
        self.fullscreen()
        visual=self.get_screen().get_rgba_visual()
        if visual:self.set_visual(visual)
        self.book_open=True;self.book_progress=1.;self.book_callback=0;self.category=0;self.pinned_only=False
        self.launching=False;self.page=0;self.selected=0;self.hover=None;self.yaw=.12;self.pitch=0;self.target_yaw=.12;self.target_pitch=0;self.look_callback=0;self.look_time=0
        self.icon_theme=theme();self.icons={};self.pixel_icons={};self.search_snapshot=None;self.apps=applications();self.all_apps=ordered_apps(True);self.filtered=self.all_apps[:]
        self.store=Store();self.pinned=self.store.load();self.shortcuts=[describe(i,self.icon_theme) for i in self.pinned]
        self.press=None;self.dragging=False;self.drag_bytes=None;self.drop_slot=None
        self.monitor=self.store.watch(self.reload_pins)
        self.shelf=Shelf();self.shelf_items=self.shelf.load();self.shelf_monitor=self.shelf.watch(self.reload_shelf)
        self.steve=Steve(ASSETS/'steve.png')
        self.art={name:cairo.ImageSurface.create_from_png(str(ASSETS/name)) for name in ['empty_helmet.png','empty_chestplate.png','empty_leggings.png','empty_boots.png','empty_shield.png','knowledge_book.png']}
        for path in (ASSETS/'recipe-items').glob('*.png'):
            self.art[path.stem]=cairo.ImageSurface.create_from_png(str(path))
        self.app_sprites={app.get_id():('app',app_icon(app,self.icon_theme)) for app in self.all_apps}
        css=Gtk.CssProvider();css.load_from_path(str(ROOT/'inventory.css'))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.canvas=Gtk.DrawingArea();self.canvas.set_size_request(WINDOW_WIDTH*SCALE,WINDOW_HEIGHT*SCALE);self.canvas.set_can_focus(True)
        self.canvas.add_events(Gdk.EventMask.POINTER_MOTION_MASK|Gdk.EventMask.BUTTON_PRESS_MASK|Gdk.EventMask.BUTTON_RELEASE_MASK|Gdk.EventMask.LEAVE_NOTIFY_MASK|Gdk.EventMask.SCROLL_MASK|Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.canvas.connect('draw',self.draw);self.canvas.connect('motion-notify-event',self.motion)
        self.canvas.connect('button-press-event',self.click);self.canvas.connect('button-release-event',self.release);self.canvas.connect('leave-notify-event',self.leave)
        self.canvas.connect('scroll-event',self.scroll)
        layout=Gtk.Fixed();self.layout=layout;layout.put(self.canvas,0,0)
        layout.set_halign(Gtk.Align.CENTER);layout.set_valign(Gtk.Align.CENTER)
        layout.set_size_request(WINDOW_WIDTH*SCALE,WINDOW_HEIGHT*SCALE)
        # One fullscreen surface lets Hyprland blur the whole active display.
        # The inventory retains its original size and centered hit coordinates.
        overlay=Gtk.Overlay();self.backdrop=Gtk.DrawingArea()
        self.backdrop.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.backdrop.connect('draw',self.draw_backdrop)
        self.backdrop.connect('button-press-event',self.backdrop_click)
        overlay.add(self.backdrop);overlay.add_overlay(layout);self.add(overlay)
        self.canvas.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,TARGETS,Gdk.DragAction.COPY|Gdk.DragAction.MOVE)
        self.canvas.drag_dest_set(Gtk.DestDefaults.DROP,TARGETS,Gdk.DragAction.COPY|Gdk.DragAction.MOVE)
        self.canvas.connect('drag-begin',self.drag_begin)
        self.canvas.connect('drag-data-get',self.drag_data)
        self.canvas.connect('drag-end',self.drag_end)
        self.canvas.connect('drag-motion',self.drag_motion)
        self.canvas.connect('drag-leave',self.drag_leave)
        self.canvas.connect('drag-data-received',self.drag_received)
        self.search=Gtk.Entry()
        self.search.set_name('browser-search')
        self.search.set_opacity(GLASS_OPACITY)
        self.search.connect_after('draw',self.draw_search_hint)
        self.search.set_size_request(90*SCALE,15*SCALE)
        self.search.connect('changed',self.filter_items);self.search.connect('activate',self.launch_first)
        self.search.connect('key-press-event',self.search_key)
        layout.put(self.search,64*SCALE,15*SCALE)
        self.connect('key-press-event',self.key)
        self.connect('destroy',self.cleanup)
        self.outside_click_source=GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGUSR1,self.outside_click)
        self.reveal_start=GLib.get_monotonic_time();self.reveal_callback=0;self.opening=True
        self.show_all();self.start_reveal(True)
        GLib.idle_add(self.open_search)

    def draw_backdrop(self,_,cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0,0,0,0);cr.paint()
        return False

    def backdrop_click(self,*_):
        if not self.dragging and not self.launching:self.destroy()
        return True

    def start_reveal(self,opening=False):
        self.opening=opening;self.reveal_start=GLib.get_monotonic_time()
        settings=Gtk.Settings.get_default()
        if not settings.get_property('gtk-enable-animations'):
            self.reveal_start-=1000000;self.canvas.queue_draw();return
        if not self.reveal_callback:self.reveal_callback=self.canvas.add_tick_callback(self.reveal_tick)
        self.canvas.queue_draw()

    def item_alpha(self,row):
        elapsed=(GLib.get_monotonic_time()-self.reveal_start)/1000
        delay=row*(28 if self.opening else 12)
        progress=max(0,min(1,(elapsed-delay)/150))
        return 1-(1-progress)**3

    def reveal_tick(self,_,clock):
        self.canvas.queue_draw()
        if GLib.get_monotonic_time()-self.reveal_start>=400000:
            self.reveal_callback=0;return False
        return True

    def filter_items(self,*_):
        words=self.search.get_text().casefold().split()
        categories=CATEGORIES[self.category][1]
        pinned={p.get('app') for p in self.pinned if 'app' in p}
        builtin_execs={describe(p,self.icon_theme)[3][0].split('/')[-1] for p in self.pinned if 'builtin' in p}
        self.filtered=[]
        for app in self.all_apps:
            text=' '.join([app.get_display_name(),app.get_description() or '',app.get_executable() or '']).casefold()
            cats=set((app.get_categories() or '').split(';'))
            if not all(w in text for w in words):continue
            if categories and not categories.intersection(cats):continue
            if self.pinned_only and app.get_id() not in pinned and (app.get_executable() or '').split('/')[-1] not in builtin_execs:continue
            self.filtered.append(app)
        self.page=0;self.selected=self.browser_start() if self.filtered and self.book_open else 0;self.hover=None;self.start_reveal(False)

    def change_page(self,step):
        if not self.book_open:return
        self.page=max(0,min(max(0,(len(self.filtered)-1)//PAGE_SIZE),self.page+step));self.selected=self.browser_start() if self.filtered else 0;self.hover=None;self.start_reveal(False)

    @staticmethod
    def smooth(value):
        t=max(0.,min(1.,value))
        return t*t*t*(t*(t*6-15)+10)

    def main_x(self):
        # Finish moving the inventory before revealing the book. Closing reverses
        # the same path, so neither panel crosses visible search content.
        progress=self.smooth(self.book_progress/.64)
        return round((MAIN_CLOSED_X+(MAIN_X-MAIN_CLOSED_X)*progress)*SCALE)/SCALE

    def browser_alpha(self):return self.smooth((self.book_progress-.64)/.36)

    def entries(self):
        result=[];mx=self.main_x()
        for i,item in enumerate(self.shelf_items):
            if item:
                _,label,icon,action=describe(item,self.icon_theme)
                sprite=self.app_sprites.get(item.get('app'),('app',icon))
                result.append((mx+8+20*(i%9),94+20*(i//9),label,sprite,action))
        for i,item in enumerate(self.shortcuts):
            sprite=self.app_sprites.get(self.pinned[i].get('app'),('app',item[2]))
            result.append((mx+8+20*i,158,item[1],sprite,item[3]))
        result.append((mx+114,70,'Hide search · Green book' if self.book_open else 'Show search · /','knowledge_book','search'))
        if self.book_open:result.extend(self.recipe_entries())
        return result

    def recipe_entries(self):
        return [(49+28*(i%5),37+28*(i//5),app.get_display_name(),self.app_sprites[app.get_id()],app)
                for i,app in enumerate(self.filtered[self.page*PAGE_SIZE:(self.page+1)*PAGE_SIZE])]

    def draw_search_hint(self,widget,cr):
        if not widget.get_text():
            cr.save();cr.select_font_face('Monocraft',cairo.FONT_SLANT_ITALIC);cr.set_font_size(24)
            cr.set_source_rgb(.8,.8,.8);cr.move_to(9,31);cr.show_text('Search...');cr.restore()
        return False

    def shelf_count(self):return sum(item is not None for item in self.shelf_items)

    def browser_start(self):return self.shelf_count()+len(self.shortcuts)+1

    def entry_size(self,index):
        return 24 if index>=self.browser_start() else 20 if index==self.browser_start()-1 else 18

    def capture_search(self):
        # Animate a single Cairo scene instead of reallocating a GTK entry on
        # every frame. The real, fully editable entry returns at the endpoint.
        if self.search.get_visible():
            self.search_snapshot=cairo.ImageSurface(cairo.FORMAT_ARGB32,self.search.get_allocated_width(),self.search.get_allocated_height())
            self.search.set_opacity(1.)
            self.search.draw(cairo.Context(self.search_snapshot))
            self.search.set_opacity(GLASS_OPACITY)

    def toggle_book(self):
        self.capture_search()
        self.book_open=not self.book_open
        self.book_from=self.book_progress;self.book_to=1. if self.book_open else 0.
        self.book_duration=max(1,BOOK_DURATION*abs(self.book_to-self.book_from))
        self.book_time=self.canvas.get_frame_clock().get_frame_time()
        self.hover=None;self.selected=self.browser_start()-1
        self.search.hide();self.canvas.grab_focus()
        settings=Gtk.Settings.get_default()
        if not settings.get_property('gtk-enable-animations'):
            if self.book_callback:self.canvas.remove_tick_callback(self.book_callback);self.book_callback=0
            self.book_progress=self.book_to;self.finish_book();return
        if not self.book_callback:self.book_callback=self.canvas.add_tick_callback(self.book_tick)
        self.canvas.queue_draw()

    def book_tick(self,_,clock):
        t=min(1.,max(0.,(clock.get_frame_time()-self.book_time)/self.book_duration))
        self.book_progress=self.book_from+(self.book_to-self.book_from)*t
        self.canvas.queue_draw()
        if t>=1:
            self.book_callback=0;self.finish_book();return False
        return True

    def finish_book(self):
        self.search.set_opacity(GLASS_OPACITY)
        if self.book_open:self.search.show();self.search.grab_focus()
        else:self.search.hide()
        self.canvas.queue_draw()

    def pixbuf(self,icon):
        key=icon if isinstance(icon,str) else icon.to_string() if icon else 'missing'
        if key not in self.icons:self.icons[key]=icon_info(self.icon_theme,icon,33).load_icon()
        return self.icons[key]

    def sprite(self,cr,name,x,y,size=16):
        art=self.art[name];cr.save();cr.translate(x,y);cr.scale(size/art.get_width(),size/art.get_height())
        cr.set_source_surface(art,0,0);cr.get_source().set_filter(cairo.FILTER_NEAREST);cr.paint();cr.restore()

    def panel(self,cr,x,y,w,h):
        rectangle(cr,x+2,y+2,w,h,'080d11')
        rectangle(cr,x,y,w,h,'202930')
        # Subtle cool glass sheen, bounded by Minecraft's stepped bevel.
        sheen=cairo.LinearGradient(0,y,0,y+h)
        sheen.add_color_stop_rgba(0,.65,.78,.86,.10)
        sheen.add_color_stop_rgba(.32,.4,.5,.6,.025)
        sheen.add_color_stop_rgba(1,0,0,0,.08)
        cr.set_source(sheen);cr.rectangle(x+2,y+2,w-4,h-4);cr.fill()
        rectangle(cr,x+2,y,w-4,1,'71818b');rectangle(cr,x,y+2,1,h-4,'63737d')
        rectangle(cr,x+2,y+1,w-4,1,'46545e');rectangle(cr,x+1,y+2,1,h-4,'46545e')
        rectangle(cr,x+2,y+h-2,w-2,2,'0b1116');rectangle(cr,x+w-2,y+2,2,h-4,'0b1116')
        rectangle(cr,x+w-3,y+3,1,h-6,'34404a');rectangle(cr,x+3,y+h-3,w-6,1,'34404a')

    def well(self,cr,x,y,w=18,h=18):
        rectangle(cr,x,y,w,h,'162027')
        rectangle(cr,x,y,w-1,1,'080e13');rectangle(cr,x,y,1,h-1,'080e13')
        rectangle(cr,x+1,y+h-1,w-1,1,'46545f');rectangle(cr,x+w-1,y+1,1,h-1,'46545f')

    def text(self,cr,text,x,y,size=8,color='d6e2e4'):
        cr.select_font_face('Monocraft');cr.set_font_size(size)
        cr.set_source_rgb(*[int(color[i:i+2],16)/255 for i in (0,2,4)])
        cr.move_to(x,y);cr.show_text(text)

    def arrow(self,cr,x,y,direction,enabled=True):
        cr.save();cr.translate(x,y)
        if direction<0:cr.translate(10,0);cr.scale(-1,1)
        cr.move_to(1,0);cr.line_to(11,9);cr.line_to(1,18);cr.close_path()
        cr.set_source_rgb(0,0,0);cr.set_line_width(2);cr.stroke_preserve()
        cr.set_source_rgb(*((.78,.78,.78) if enabled else (.38,.38,.38)));cr.fill()
        if enabled:
            cr.set_source_rgb(1,1,1);cr.set_line_width(1);cr.move_to(2,2);cr.line_to(9,9);cr.stroke()
        cr.restore()

    def cube(self,cr,name,x,y,size):
        # Three textured faces, sampled nearest-neighbor like Minecraft's GUI items.
        top={'quartz_block_side':'quartz_block_top','crafting_table_front':'crafting_table_top','spruce_log':'spruce_log_top','dark_oak_log':'dark_oak_log_top','chiseled_red_sandstone':'chiseled_red_sandstone_top','carved_pumpkin':'pumpkin_top','jack_o_lantern':'pumpkin_top'}.get(name,name)
        side={'crafting_table_front':'crafting_table_side','carved_pumpkin':'pumpkin_side','jack_o_lantern':'pumpkin_side'}.get(name,name)
        cr.save();cr.translate(x,y);cr.scale(size/16,size/16)
        for texture,matrix,shade in [(top,cairo.Matrix(.5,.25,-.5,.25,8,0),0),
                                    (side,cairo.Matrix(.5,.25,0,.65,0,4),.16),
                                    (name,cairo.Matrix(.5,-.25,0,.65,8,8),.32)]:
            cr.save();cr.transform(matrix)
            art=self.art.get(texture,self.art.get('cut_copper'))
            cr.rectangle(0,0,16,16);cr.clip();cr.set_source_surface(art)
            cr.get_source().set_filter(cairo.FILTER_NEAREST);cr.paint()
            cr.set_source_rgba(0,0,0,shade);cr.paint();cr.restore()
        cr.restore()

    def pixel_icon(self,icon):
        key=icon if isinstance(icon,str) else icon.to_string() if icon else 'missing'
        if key not in self.pixel_icons:
            # Render the installed app's icon on the same 16x16 grid as a
            # Minecraft item. Hard alpha edges and a compact palette retain
            # brand colors without smooth vector edges in the final UI.
            info=icon_info(self.icon_theme,icon,16)
            try:pixbuf=info.load_icon()
            except GLib.Error:pixbuf=icon_info(self.icon_theme,'application-x-executable',16).load_icon()
            from gi.repository import GdkPixbuf
            pixbuf=pixbuf.scale_simple(16,16,GdkPixbuf.InterpType.BILINEAR)
            pixels=pixbuf.get_pixels();stride=pixbuf.get_rowstride();channels=pixbuf.get_n_channels()
            surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,16,16);ctx=cairo.Context(surface)
            ctx.set_antialias(cairo.ANTIALIAS_NONE)
            for y in range(16):
                for x in range(16):
                    offset=y*stride+x*channels
                    if channels==4 and pixels[offset+3]<110:continue
                    rgb=[min(255,round(pixels[offset+c]/32)*32)/255 for c in range(3)]
                    ctx.set_source_rgb(*rgb);ctx.rectangle(x,y,1,1);ctx.fill()
            self.pixel_icons[key]=surface
        return self.pixel_icons[key]

    def item(self,cr,name,x,y,size=18):
        if isinstance(name,tuple):
            art=self.pixel_icon(name[1]);cr.save();cr.translate(x,y);cr.scale(size/16,size/16)
            cr.set_source_surface(art);cr.get_source().set_filter(cairo.FILTER_NEAREST);cr.paint();cr.restore()
        elif name in BLOCK_ICONS:self.cube(cr,name,x,y,size)
        elif name in self.art:self.sprite(cr,name,x,y,size)
        else:self.sprite(cr,'knowledge_book.png',x,y,size)

    def draw_browser(self,cr):
        # Recipe categories sit behind the book's raised stone border.
        for index,(label,_) in enumerate(CATEGORIES):
            y=5+30*index
            self.panel(cr,1 if self.category==index else 3,y,39 if self.category==index else 35,27)
            if self.category==index:rectangle(cr,36,y+3,4,21,'28333b')
            if index==0:self.item(cr,'compass',10,y+6,18)
            elif index==1:
                self.item(cr,'iron_axe',8,y+6,18);self.item(cr,'golden_sword',16,y+4,18)
            elif index==2:self.cube(cr,'bricks',12,y+5,18)
            elif index==3:
                self.item(cr,'lava_bucket',7,y+5,18);self.item(cr,'apple',18,y+8,17)
            else:self.item(cr,'redstone',11,y+6,18)
        self.panel(cr,37,2,159,180)
        rectangle(cr,43,8,147,168,'46545f');rectangle(cr,43,8,146,167,'080e13');rectangle(cr,44,9,145,166,'111a20')
        # Magnifying glass, drawn on the pixel grid.
        rectangle(cr,49,23,2,5,'9d6035');rectangle(cr,48,27,2,2,'9d6035')
        rectangle(cr,51,16,7,7,'294f59');rectangle(cr,52,15,5,9,'4a94a8')
        rectangle(cr,51,17,7,5,'4a94a8');rectangle(cr,53,16,3,2,'e8faff')
        rectangle(cr,52,18,4,3,'7ed9e8')
        self.panel(cr,159,14,29,18)
        self.cube(cr,'crafting_table_front',173,17,12)
        color='48a24b' if self.pinned_only else 'b44135'
        if self.pinned_only:
            for i in range(4):rectangle(cr,161+i,23+i,2,2,color)
            for i in range(6):rectangle(cr,164+i,26-i,2,2,color)
        else:
            for i in range(7):
                rectangle(cr,161+i,20+i,2,2,color);rectangle(cr,167-i,20+i,2,2,color)
        for row in range(4):
            for col in range(5):
                x,y=48+28*col,36+28*row
                rectangle(cr,x,y,27,27,'0a1015');rectangle(cr,x+1,y+1,25,25,'3b4b55')
                rectangle(cr,x+2,y+2,23,23,'25323b')
                rectangle(cr,x+2,y+2,22,1,'566671');rectangle(cr,x+2,y+2,1,22,'566671')
                rectangle(cr,x+3,y+24,22,1,'111b22');rectangle(cr,x+24,y+3,1,22,'111b22')
        pages=max(1,math.ceil(len(self.filtered)/PAGE_SIZE));label=f'{self.page+1}/{pages}'
        self.text(cr,label,117-len(label)*3.9/2,167,10,'ffffff')
        if self.page>0:self.arrow(cr,83,156,-1)
        if self.page+1<pages:self.arrow(cr,141,156,1)
        if not self.filtered:
            rectangle(cr,48,36,139,111,'111a20')
            self.text(cr,'No apps found',56,87,7,'ffffff')
        for i,entry in enumerate(self.recipe_entries()):
            x,y,label,icon,action=entry;idx=self.browser_start()+i
            alpha=self.item_alpha(i//5)
            cr.save();cr.push_group()
            if idx==self.hover or (self.canvas.has_focus() and idx==self.selected):
                rectangle(cr,x,y,24,24,'40594c')
            self.item(cr,icon,x+3,y+3,18)
            cr.pop_group_to_source();cr.paint_with_alpha(alpha);cr.restore()

    def draw(self,_,cr):
        cr.save();cr.set_operator(cairo.OPERATOR_SOURCE);cr.set_source_rgba(0,0,0,0);cr.paint();cr.set_operator(cairo.OPERATOR_OVER)
        cr.scale(SCALE,SCALE);cr.set_antialias(cairo.ANTIALIAS_NONE)
        alpha=self.browser_alpha()
        if alpha>0:
            cr.save();cr.push_group();self.draw_browser(cr)
            if self.book_callback and self.search_snapshot:
                cr.save();cr.translate(64,15);cr.scale(1/SCALE,1/SCALE)
                cr.set_source_surface(self.search_snapshot);cr.paint();cr.restore()
            cr.pop_group_to_source();cr.paint_with_alpha(GLASS_OPACITY*alpha);cr.restore()
        cr.push_group()
        mx=self.main_x();self.panel(cr,mx,2,194,180)
        for y,name in zip([8,28,48,68],['helmet','chestplate','leggings','boots']):
            self.well(cr,mx+8,y,20,20);self.sprite(cr,'empty_'+name+'.png',mx+10,y+2,16)
        rectangle(cr,mx+28,8,56,80,'0c151b')
        rectangle(cr,mx+28,8,56,1,'080e13');rectangle(cr,mx+83,8,1,80,'46545f');rectangle(cr,mx+28,87,56,1,'46545f')
        cr.save();cr.rectangle(mx+29,9,53,77);cr.clip();self.steve.render(cr,mx+56,83,2.,self.yaw,self.pitch);cr.restore()
        self.well(cr,mx+84,68,20,20);self.sprite(cr,'empty_shield.png',mx+86,70,16)
        self.text(cr,'Crafting',mx+108,14,10)
        for y in (20,40):
            for x in (108,128):self.well(cr,mx+x,y,20,20)
        self.well(cr,mx+170,31,20,20)
        rectangle(cr,mx+150,39,10,5,'71818b')
        for i in range(7):rectangle(cr,mx+160+i,34+i,1,15-2*i,'71818b')
        self.panel(cr,mx+114,70,21,19)
        for row in range(3):
            for col in range(9):self.well(cr,mx+8+20*col,94+20*row,20,20)
        for col in range(9):self.well(cr,mx+8+20*col,158,20,20)
        for i,(x,y,label,icon,action) in enumerate(self.entries()[:self.browser_start()]):
            if i==self.hover or (self.canvas.has_focus() and i==self.selected):
                cr.set_source_rgba(1,1,1,.24);cr.rectangle(x+1,y+1,18,18);cr.fill()
            self.item(cr,icon,x+2,y+2,16)
        if self.drop_slot is not None:
            cr.set_source_rgb(.65,.9,.4);cr.set_line_width(1)
            if isinstance(self.drop_slot,tuple):
                n=self.drop_slot[1];cr.rectangle(mx+8+20*(n%9),94+20*(n//9),20,20)
            else:cr.rectangle(mx+8+20*self.drop_slot,158,20,20)
            cr.stroke()
        cr.pop_group_to_source();cr.paint_with_alpha(GLASS_OPACITY)
        cr.restore();return False

    def hit(self,x,y):
        return next((i for i,(sx,sy,*_) in enumerate(self.entries()) if sx<=x<sx+self.entry_size(i) and sy<=y<sy+self.entry_size(i)),None)

    def motion(self,_,event):
        x,y=event.x/SCALE,event.y/SCALE
        self.target_yaw=.56*math.tanh((x-self.main_x()-56)/95)
        self.target_pitch=.26*math.tanh((y-35)/100)
        if not self.look_callback:
            self.look_time=0;self.look_callback=self.canvas.add_tick_callback(self.look_tick)
        self.hover=self.hit(x,y)
        label=self.entries()[self.hover][2] if self.hover is not None else None
        if self.book_open and x<38 and 5<=y<152:
            category=int((y-5)//30)
            if category<len(CATEGORIES):label=CATEGORIES[category][0]
        elif self.book_open and 159<=x<188 and 14<=y<32:label='Show all apps' if self.pinned_only else 'Show pinned apps'
        target=self.target_slot(event.x,event.y)
        if isinstance(target,tuple):
            label=(label+' · Right-click to remove') if label else 'Drag an app into this slot'
        self.canvas.set_tooltip_text(label)
        self.canvas.queue_draw();return False

    def look_tick(self,_,clock):
        now=clock.get_frame_time()
        dt=min(.05,(now-self.look_time)/1000000) if self.look_time else 1/60
        self.look_time=now
        blend=1-math.exp(-dt/.075)
        self.yaw+=(self.target_yaw-self.yaw)*blend
        self.pitch+=(self.target_pitch-self.pitch)*blend
        self.canvas.queue_draw()
        if abs(self.yaw-self.target_yaw)+abs(self.pitch-self.target_pitch)<.001:
            self.yaw=self.target_yaw;self.pitch=self.target_pitch;self.look_callback=0;return False
        return True

    def leave(self,*_):self.hover=None;self.canvas.queue_draw()

    def reload_shelf(self):
        self.shelf_items=self.shelf.load()
        self.selected=min(self.selected,len(self.entries())-1);self.hover=None
        self.canvas.queue_draw()

    def reload_pins(self):
        self.pinned=self.store.load();self.shortcuts=[describe(i,self.icon_theme) for i in self.pinned]
        if hasattr(self,'search'):self.filter_items()
        elif hasattr(self,'canvas'):self.canvas.queue_draw()

    def cleanup(self,*_):
        if self.outside_click_source:GLib.source_remove(self.outside_click_source)
        for name in ('book_callback','look_callback','reveal_callback'):
            callback=getattr(self,name,0)
            if callback:self.canvas.remove_tick_callback(callback)
        self.monitor.cancel();self.shelf_monitor.cancel()
        if self.dragging:drag_active(False)
        if Gtk.main_level():Gtk.main_quit()

    def outside_click(self):
        # Hyprland forwards button presses without consuming the original click.
        # GDK identifies the inventory and its attached browser as one window.
        pointer=self.get_display().get_default_seat().get_pointer()
        window,_,_=pointer.get_window_at_position()
        if window is None and not self.dragging and not self.launching:
            self.outside_click_source=0;self.destroy()
            return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    def click(self,_,event):
        x,y=event.x/SCALE,event.y/SCALE
        in_inventory=self.main_x()<=x<self.main_x()+196 and 0<=y<184
        in_book=self.browser_alpha()>0 and 0<=x<198 and 0<=y<184
        if not in_inventory and not in_book:return self.backdrop_click()
        if event.button==3:
            slot=self.target_slot(event.x,event.y)
            if isinstance(slot,tuple):self.shelf.clear(slot[1]);self.reload_shelf();return True
            return False
        if event.button!=1:return False
        self.press=(self.hit(event.x/SCALE,event.y/SCALE),event.x,event.y)
        self.dragging=False
        self.canvas.grab_focus()
        if self.press[0] is not None:self.selected=self.press[0]
        self.canvas.queue_draw()
        return False

    def release(self,_,event):
        press=self.press;self.press=None
        if event.button!=1 or not press or self.dragging:return False
        i,x,y=press
        if abs(event.x-x)+abs(event.y-y)>8:return True
        x,y=event.x/SCALE,event.y/SCALE
        if i is not None and i==self.hit(x,y) and self.entries()[i][4]=='search':
            self.toggle_book();return True
        if self.book_callback:return True
        if self.book_open:
            if x<38 and 5<=y<152:
                category=int((y-5)//30)
                if category<len(CATEGORIES):self.category=category;self.filter_items()
                return True
            if 159<=x<188 and 14<=y<32:self.pinned_only=not self.pinned_only;self.filter_items();return True
            if 154<=y<176:
                if 80<=x<98:self.change_page(-1);return True
                if 138<=x<156:self.change_page(1);return True
        if i is not None and i==self.hit(x,y):self.activate(self.entries()[i][4])
        return True

    def drag_begin(self,_,context):
        i=self.press[0] if self.press else None
        count=self.shelf_count()
        if self.book_callback or i is None or self.entries()[i][4]=='search':
            Gtk.drag_cancel(context);return
        if i<count:
            slots=[n for n,item in enumerate(self.shelf_items) if item]
            n=slots[i];self.drag_bytes=json.dumps({'item':self.shelf_items[n],'inventory_slot':n}).encode()
        elif count<=i<count+len(self.pinned):self.drag_bytes=payload(self.pinned[i-count],i-count)
        else:self.drag_bytes=payload({'app':self.entries()[i][4].get_id()})
        self.dragging=True;drag_active(True)
        action=self.entries()[i][4]
        icon=app_icon(action,self.icon_theme) if not isinstance(action,list) else describe(self.shelf_items[slots[i]],self.icon_theme)[2] if i<count else self.shortcuts[i-count][2]
        art=self.pixel_icon(icon)
        from gi.repository import GdkPixbuf
        drag_icon=Gdk.pixbuf_get_from_surface(art,0,0,16,16).scale_simple(48,48,GdkPixbuf.InterpType.NEAREST)
        Gtk.drag_set_icon_pixbuf(context,drag_icon,24,24)

    def drag_data(self,_,context,selection,info,time):
        if self.drag_bytes:selection.set(selection.get_target(),8,self.drag_bytes)

    def drag_end(self,*_):
        self.press=None;self.dragging=False;self.drag_bytes=None;drag_active(False)
        self.drop_slot=None;self.canvas.queue_draw()

    def target_slot(self,x,y):
        x,y=x/SCALE,y/SCALE
        mx=self.main_x()
        if 94<=y<154 and mx+8<=x<mx+188:return ('shelf',int((y-94)/20)*9+int((x-mx-8)/20))
        if 158<=y<178 and mx+8<=x<mx+188:return max(0,min(8,int((x-mx-8)/20)))
        return None

    def drag_motion(self,_,context,x,y,time):
        self.drop_slot=self.target_slot(x,y)
        Gdk.drag_status(context,Gdk.DragAction.COPY if self.drop_slot is not None else Gdk.DragAction(0),time)
        self.canvas.queue_draw();return True

    def drag_leave(self,*_):self.drop_slot=None;self.canvas.queue_draw()

    def drag_received(self,_,context,x,y,selection,info,time):
        success=False
        try:
            slot=self.target_slot(x,y)
            if isinstance(slot,tuple):self.shelf.drop(slot[1],bytes(selection.get_data()));success=True;self.reload_shelf()
            elif slot is not None:self.store.drop(slot,bytes(selection.get_data()));success=True;self.reload_pins()
        except (ValueError,OSError,TypeError) as e:print('Hotbar drop:',e,file=sys.stderr)
        self.drop_slot=None;Gtk.drag_finish(context,success,False,time);self.canvas.queue_draw()

    def scroll(self,_,event):
        if not self.book_open or event.x/SCALE>=MAIN_X:return False
        if event.direction==Gdk.ScrollDirection.DOWN:self.change_page(1)
        elif event.direction==Gdk.ScrollDirection.UP:self.change_page(-1)
        return True

    def open_search(self):
        if not self.book_open:self.toggle_book()
        elif not self.book_callback:self.search.grab_focus()
        return False

    def activate(self,action):
        if action=='search':self.toggle_book();return
        if isinstance(action,list) and action==SHORTCUTS[0][3]:self.open_search();return
        if self.launching:return
        self.launching=True
        try:
            if isinstance(action,list):
                subprocess.Popen(action)
                self.destroy()
            else:
                context=Gdk.Display.get_default().get_app_launch_context()
                # Keep the GTK loop alive until D-Bus activation completes.
                # Exiting after launch() can discard the activation request.
                action.launch_uris_async([],context,None,self.launch_finished,None)
                self.hide()
        except (GLib.Error,OSError) as e:
            self.launch_failed(e)

    def launch_finished(self,action,result,*_):
        try:
            action.launch_uris_finish(result)
        except GLib.Error as e:
            self.launch_failed(e)
            return
        self.destroy()

    def launch_failed(self,error):
        self.launching=False
        self.present()
        dialog=Gtk.MessageDialog(transient_for=self,modal=True,message_type=Gtk.MessageType.ERROR,buttons=Gtk.ButtonsType.CLOSE,text='Could not open app')
        dialog.format_secondary_text(str(error));dialog.run();dialog.destroy()

    def launch_first(self,*_):
        apps=self.filtered[self.page*PAGE_SIZE:(self.page+1)*PAGE_SIZE]
        if apps:self.activate(apps[0])

    def search_key(self,_,event):
        if event.keyval==Gdk.KEY_Escape:self.destroy();return True
        if event.keyval==Gdk.KEY_Page_Down:self.change_page(1);return True
        if event.keyval==Gdk.KEY_Page_Up:self.change_page(-1);return True
        if event.keyval==Gdk.KEY_Down:
            self.canvas.grab_focus();self.selected=min(self.browser_start(),len(self.entries())-1);self.canvas.queue_draw();return True
        return False

    def key(self,_,event):
        k=event.keyval
        if self.search.has_focus():return False
        if k==Gdk.KEY_Escape:self.destroy();return True
        if k==Gdk.KEY_slash or (k==Gdk.KEY_f and event.state&Gdk.ModifierType.CONTROL_MASK):self.open_search();return True
        if k==Gdk.KEY_Page_Down:self.change_page(1);return True
        if k==Gdk.KEY_Page_Up:self.change_page(-1);return True
        columns=5 if self.selected>=self.browser_start() else 9
        delta={Gdk.KEY_Left:-1,Gdk.KEY_Right:1,Gdk.KEY_Up:-columns,Gdk.KEY_Down:columns}.get(k)
        if delta is not None:self.selected=max(0,min(len(self.entries())-1,self.selected+delta));self.canvas.queue_draw();return True
        if k in (Gdk.KEY_Return,Gdk.KEY_KP_Enter):self.activate(self.entries()[self.selected][4]);return True
        return False

if __name__=='__main__':
    GLib.set_prgname('minecraft-inventory')
    if '--check' in sys.argv:print(f'{len(applications())} installed apps')
    else:Inventory();Gtk.main()
