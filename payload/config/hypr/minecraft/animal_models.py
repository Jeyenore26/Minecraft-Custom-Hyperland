"""Render Mojang's vanilla Bedrock cuboids, box UVs and bone pivots with Cairo.

Asset versions and upstream URLs are recorded beside the original JSON/PNGs.
Legacy bind_pose_rotation bakes each bone's mesh; animated rotations propagate
to children. Texture sampling is nearest-neighbor, never smoothed pixel art.
"""
import json
import math
from functools import lru_cache
from pathlib import Path
import cairo

ASSETS = Path.home() / '.local/share/minecraft-desktop/animals'
WIDTH, HEIGHT, FRAMES = 160, 128, 32


def rotate(point, pivot, angles):
    x, y, z = (point[i] - pivot[i] for i in range(3))
    ax, ay, az = (math.radians(a) for a in angles)
    # Bedrock's X/Y rotations use the opposite handedness to screen coordinates.
    y, z = y*math.cos(ax) + z*math.sin(ax), -y*math.sin(ax) + z*math.cos(ax)
    x, z = x*math.cos(ay) - z*math.sin(ay), x*math.sin(ay) + z*math.cos(ay)
    x, y = x*math.cos(az) - y*math.sin(az), x*math.sin(az) + y*math.cos(az)
    return x+pivot[0], y+pivot[1], z+pivot[2]


def cube_faces(cube):
    x, y, z = cube['origin']
    w, h, d = cube['size']
    X, Y, Z = x+w, y+h, z+d
    u, v = cube['uv']
    # Each quad is outward-wound, with corners TL, TR, BR, BL in texture space.
    return [
        ([(x,Y,z),(X,Y,z),(X,y,z),(x,y,z)], (u+d,v+d,w,h)),
        ([(X,Y,Z),(x,Y,Z),(x,y,Z),(X,y,Z)], (u+2*d+w,v+d,w,h)),
        ([(X,Y,z),(X,Y,Z),(X,y,Z),(X,y,z)], (u,v+d,d,h)),
        ([(x,Y,Z),(x,Y,z),(x,y,z),(x,y,Z)], (u+d+w,v+d,d,h)),
        ([(x,Y,Z),(X,Y,Z),(X,Y,z),(x,Y,z)], (u+d,v,w,d)),
        ([(x,y,z),(X,y,z),(X,y,Z),(x,y,Z)], (u+d+w,v,w,d)),
    ]


class AnimalModel:
    def __init__(self, species):
        self.species = species
        data = json.loads((ASSETS / f'{species}.geo.json').read_text())
        geometry = next(value for key, value in data.items() if key.startswith('geometry.'))
        self.bones = {b['name']: b for b in geometry['bones'] if b['name'] != 'head_sleeping'}
        texture = 'white' if species == 'rabbit' else species
        self.texture = cairo.ImageSurface.create_from_png(str(ASSETS / f'{texture}.png'))
        assert self.texture.get_width() == geometry['texturewidth']
        assert self.texture.get_height() == geometry['textureheight']

    def pose(self, phase, moving):
        rotations = {}
        if self.species in ('fox', 'pig'):
            # Vanilla animation.quadruped.walk: diagonal leg pairs, +/-80 degrees.
            stride = math.cos(phase) * 80 if moving else 0
            for i, sign in enumerate((1, -1, -1, 1)):
                rotations[f'leg{i}'] = (stride*sign, 0, 0)
        else:
            jump = max(0, math.sin(phase)) if moving else 0
            for name, bone in self.bones.items():
                lower = name.lower()
                target = None
                if lower.startswith('frontleg'):
                    target = -40*jump - 11
                elif lower.startswith('haunch'):
                    target = 50*jump - 21
                elif lower.startswith('rearfoot'):
                    target = 50*jump
                if target is not None:
                    rotations[name] = (target - bone.get('bind_pose_rotation', [0,0,0])[0], 0, 0)
        return rotations

    def render(self, cr, phase, facing=1, moving=True):
        rotations = self.pose(phase, moving)
        yaw = -1.05 if facing > 0 else 1.05
        pitch = .20
        scale = 4 if self.species != 'rabbit' else 3.2
        hop = max(0, math.sin(phase))*7 if self.species == 'rabbit' and moving else 0

        def transform(point, bone):
            p = rotate(point, bone['pivot'], bone.get('bind_pose_rotation', [0,0,0]))
            current = bone
            while current:
                p = rotate(p, current['pivot'], rotations.get(current['name'], [0,0,0]))
                current = self.bones.get(current.get('parent'))
            x, y, z = p
            x, z = x*math.cos(yaw)+z*math.sin(yaw), -x*math.sin(yaw)+z*math.cos(yaw)
            y, z = y*math.cos(pitch)+z*math.sin(pitch), z*math.cos(pitch)-y*math.sin(pitch)
            return WIDTH/2+x*scale, HEIGHT-24-y*scale-hop, z

        faces = []
        for bone in self.bones.values():
            for cube in bone.get('cubes', []):
                for corners, uv in cube_faces(cube):
                    points = [transform(p, bone) for p in corners]
                    a, b, c, _ = points
                    cross = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                    if cross <= .001:
                        continue
                    # Soft directional face lighting keeps the actual texture colors.
                    ab = [(b[i]-a[i])/(scale if i < 2 else 1) for i in range(3)]
                    ac = [(c[i]-a[i])/(scale if i < 2 else 1) for i in range(3)]
                    normal = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
                    length = math.sqrt(sum(n*n for n in normal))
                    light = .73 + .27*abs(normal[1])/length
                    faces.append((sum(p[2] for p in points)/4, points, uv, light, bone.get('mirror', False)))

        cr.save()
        cr.translate(WIDTH/2, HEIGHT-20)
        cr.scale(35 if self.species != 'rabbit' else 22, 6)
        cr.arc(0, 0, 1, 0, math.tau)
        cr.set_source_rgba(0, 0, 0, .12)
        cr.fill()
        cr.restore()
        for _, points, (u,v,w,h), light, mirror in sorted(faces, key=lambda f:f[0], reverse=True):
            a, b, _, d = points
            cr.save()
            cr.set_antialias(cairo.ANTIALIAS_NONE)
            cr.transform(cairo.Matrix((b[0]-a[0])/w, (b[1]-a[1])/w,
                                      (d[0]-a[0])/h, (d[1]-a[1])/h, a[0], a[1]))
            cr.rectangle(0, 0, w, h)
            cr.clip()
            if mirror:
                cr.translate(w, 0)
                cr.scale(-1, 1)
            cr.set_source_surface(self.texture, -u, -v)
            cr.get_source().set_filter(cairo.FILTER_NEAREST)
            cr.paint()
            cr.set_source_rgba(0, 0, 0, 1-light)
            cr.paint()
            cr.restore()


@lru_cache(maxsize=3)
def model(species):
    return AnimalModel(species)


@lru_cache(maxsize=200)
def frame(species, index, facing=1, moving=True):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    model(species).render(cairo.Context(surface), math.tau*index/FRAMES, facing, moving)
    return surface
