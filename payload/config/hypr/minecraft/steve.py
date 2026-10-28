"""Orthographic, skin-textured cuboids for the inventory player preview."""
import math
import cairo

class Steve:
    def __init__(self, path):
        self.skin = cairo.ImageSurface.create_from_png(str(path))
        self.data = self.skin.get_data()
        self.stride = self.skin.get_stride()

    def render(self, cr, cx, feet, scale, yaw=0.15, pitch=0):
        # Head and torso share a neck pivot; keep the preview within a natural gaze.
        yaw = max(-.58, min(.58, yaw))
        pitch = max(-.28, min(.28, pitch))
        faces = []
        def rotate(p, angle, tilt=0):
            x,y,z=p
            y,z=y*math.cos(tilt)-z*math.sin(tilt),y*math.sin(tilt)+z*math.cos(tilt)
            return (x*math.cos(angle)+z*math.sin(angle),y,-x*math.sin(angle)+z*math.cos(angle))
        def cuboid(center, size, uv, head=False):
            w,h,d=size; x,y,z=center
            # top-left, top-right, bottom-right, bottom-left as seen from each face
            parts=[([(-w/2,h/2,d/2),(w/2,h/2,d/2),(w/2,-h/2,d/2),(-w/2,-h/2,d/2)],(uv[0]+d,uv[1]+d,w,h),1),
                   ([(w/2,h/2,-d/2),(-w/2,h/2,-d/2),(-w/2,-h/2,-d/2),(w/2,-h/2,-d/2)],(uv[0]+2*d+w,uv[1]+d,w,h),.72),
                   ([(-w/2,h/2,-d/2),(-w/2,h/2,d/2),(-w/2,-h/2,d/2),(-w/2,-h/2,-d/2)],(uv[0],uv[1]+d,d,h),.80),
                   ([(w/2,h/2,d/2),(w/2,h/2,-d/2),(w/2,-h/2,-d/2),(w/2,-h/2,d/2)],(uv[0]+d+w,uv[1]+d,d,h),.86),
                   ([(-w/2,h/2,-d/2),(w/2,h/2,-d/2),(w/2,h/2,d/2),(-w/2,h/2,d/2)],(uv[0]+d,uv[1],w,d),1.05),
                   ([(-w/2,-h/2,d/2),(w/2,-h/2,d/2),(w/2,-h/2,-d/2),(-w/2,-h/2,-d/2)],(uv[0]+d+w,uv[1],w,d),.6)]
            for corners,tex,light in parts:
                points=[]
                for p in corners:
                    if head:
                        # Move the bottom-center to the origin before turning.
                        p=rotate((p[0],p[1]+h/2,p[2]),yaw*.75,pitch)
                        p=(p[0]+x,p[1]+y-h/2,p[2]+z)
                    else:
                        p=(p[0]+x,p[1]+y,p[2]+z)
                    points.append(rotate(p,yaw*.25,.035))
                # Only camera-facing surfaces; screen y is reversed.
                a,b,c=points[:3]
                nz=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                if nz>=0:continue
                faces.append((sum(p[2] for p in points)/4,points,tex,light))
        cuboid((-2,6,0),(4,12,4),(0,16))
        cuboid((2,6,0),(4,12,4),(16,48))
        cuboid((0,18,0),(8,12,4),(16,16))
        cuboid((-6,18,0),(4,12,4),(40,16))
        cuboid((6,18,0),(4,12,4),(32,48))
        cuboid((0,28,0),(8,8,8),(0,0),True)
        cr.save();cr.set_antialias(cairo.ANTIALIAS_NONE)
        for _,points,(u,v,w,h),light in sorted(faces,key=lambda f:f[0]):
            a,b,_,d=points
            def pos(s,t):
                return (cx+(a[0]+(b[0]-a[0])*s+(d[0]-a[0])*t)*scale,
                        feet-(a[1]+(b[1]-a[1])*s+(d[1]-a[1])*t)*scale)
            for row in range(h):
                for col in range(w):
                    i=(v+row)*self.stride+(u+col)*4
                    blue,green,red,alpha=self.data[i:i+4]
                    if not alpha:continue
                    cr.set_source_rgb(min(1,red/255*light),min(1,green/255*light),min(1,blue/255*light))
                    ps=[pos(col/w,row/h),pos((col+1)/w,row/h),pos((col+1)/w,(row+1)/h),pos(col/w,(row+1)/h)]
                    cr.move_to(*ps[0])
                    for point in ps[1:]:cr.line_to(*point)
                    cr.close_path();cr.fill()
        cr.restore()
