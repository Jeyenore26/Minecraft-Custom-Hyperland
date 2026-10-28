#!/usr/bin/python3
"""Occasional, click-through vanilla Minecraft animals; idle between visits."""
import fcntl
import math
import os
from pathlib import Path
import random
import signal
import time

from hotbar import Gtk, Gdk, GLib, GtkLayerShell, cairo

from animal_models import frame, WIDTH, HEIGHT, FRAMES

SPECIES = ('fox', 'rabbit', 'pig')


class Visitor(Gtk.Window):
    def __init__(self, monitor, finished):
        super().__init__()
        self.monitor, self.finished = monitor, finished
        self.species = random.choice(SPECIES)
        self.direction = random.choice((-1, 1))
        self.speed = random.uniform(100, 155)
        print(f'Visit: {self.species}, direction={self.direction}, speed={self.speed:.0f}', flush=True)
        self.width = monitor.get_geometry().width
        self.distance = 0.0
        self.last_time = time.monotonic()
        self.start = self.last_time
        self.pause_at = random.uniform(.3, .65) * self.width
        self.pause_until = 0
        self.paused_once = False
        self.set_name('minecraft-wandering-animal')
        self.set_decorated(False)
        self.set_accept_focus(False)
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, 'minecraft-wandering-animal')
        GtkLayerShell.set_monitor(self, monitor)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        GtkLayerShell.set_exclusive_zone(self, 0)
        for edge in (GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT, GtkLayerShell.Edge.BOTTOM):
            GtkLayerShell.set_anchor(self, edge, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.BOTTOM, random.randint(18, 90))
        self.area = Gtk.DrawingArea()
        self.area.set_size_request(-1, HEIGHT)
        self.area.connect('draw', self.draw)
        self.add(self.area)
        # Store the empty input region on the widget so GTK preserves it when
        # realizing, mapping or resizing the window. A Gdk.Window-only change
        # in a realize handler gets overwritten with the default full region.
        self.input_shape_combine_region(cairo.Region())
        self.connect('map', self.click_through)
        self.connect('destroy', self.cleanup)
        self.show_all()
        self.timer = GLib.timeout_add(33, self.step)

    def click_through(self, *_):
        # A remap can create a new Wayland surface; send its empty region again.
        self.input_shape_combine_region(cairo.Region())

    def step(self):
        now = time.monotonic()
        dt = min(now - self.last_time, .1)
        self.last_time = now
        if not self.paused_once and self.distance >= self.pause_at:
            self.paused_once = True
            self.pause_until = now + random.uniform(.7, 1.8)
        if now >= self.pause_until:
            self.distance += dt * self.speed
        if self.distance > self.width + WIDTH:
            self.timer = 0
            self.destroy()
            return False
        self.area.queue_draw()
        return True

    def draw(self, _, cr):
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        x = self.distance - WIDTH if self.direction > 0 else self.width - self.distance
        moving = self.last_time >= self.pause_until
        # Distance drives the gait, so changing speed never makes the feet skate.
        index = int(self.distance / 90 * FRAMES) % FRAMES if moving else 0
        sprite = frame(self.species, index, self.direction, moving)
        cr.set_source_surface(sprite, round(x), 0)
        cr.paint()
        return False

    def cleanup(self, *_):
        if getattr(self, 'timer', 0):
            GLib.source_remove(self.timer)
            self.timer = 0
        self.finished()


class Animals:
    def __init__(self):
        self.visitor = None
        self.timer = 0
        self.display = Gdk.Display.get_default()
        self.display.connect('monitor-removed', self.monitor_removed)
        self.schedule(8)

    def schedule(self, delay=None):
        self.timer = GLib.timeout_add_seconds(delay or random.randint(90, 240), self.visit)

    def visit(self):
        self.timer = 0
        count = self.display.get_n_monitors()
        if count:
            self.visitor = Visitor(self.display.get_monitor(random.randrange(count)), self.finished)
        else:
            self.schedule()
        return False

    def finished(self):
        self.visitor = None
        self.schedule()

    def monitor_removed(self, _, monitor):
        if self.visitor and self.visitor.monitor == monitor:
            self.visitor.destroy()

    def summon(self):
        if self.visitor is None:
            if self.timer:
                GLib.source_remove(self.timer)
            self.visit()
        return True


def main():
    lock = open(Path(os.environ['XDG_RUNTIME_DIR']) / 'minecraft-animals.lock', 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return
    css = Gtk.CssProvider()
    css.load_from_data(b'window#minecraft-wandering-animal { background: transparent; border: none; box-shadow: none; }')
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    app = Animals()
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGUSR1, app.summon)
    for sig in (signal.SIGTERM, signal.SIGINT):
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, sig, lambda: (Gtk.main_quit(), False)[1])
    Gtk.main()


if __name__ == '__main__':
    main()
