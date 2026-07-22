import bpy
import bmesh
import math

# ==============================
# Parameters (feel free to tweak)
# ==============================
R0 = 1.9        # Base major radius
r = 0.5         # Minor radius
a = 0.55        # Lobe amplitude
u_res = 256     # Resolution around torus
v_res = 164      # Resolution of tube

name = "Willmore_Torus_4_Lobed"

# ==============================
# Mesh generation
# ==============================
mesh = bpy.data.meshes.new(name)
obj = bpy.data.objects.new(name, mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()

verts = []
for i in range(u_res):
    phi = 2 * math.pi * i / u_res
    R = R0 + a * math.cos(4 * phi)

    ring = []
    for j in range(v_res):
        theta = 2 * math.pi * j / v_res

        x = (R + r * math.cos(theta)) * math.cos(phi)
        y = (R + r * math.cos(theta)) * math.sin(phi)
        z = r * math.sin(theta)

        ring.append(bm.verts.new((x, y, z)))

    verts.append(ring)

bm.verts.ensure_lookup_table()

# ==============================
# Faces
# ==============================
for i in range(u_res):
    for j in range(v_res):
        v1 = verts[i][j]
        v2 = verts[(i + 1) % u_res][j]
        v3 = verts[(i + 1) % u_res][(j + 1) % v_res]
        v4 = verts[i][(j + 1) % v_res]

        bm.faces.new((v1, v2, v3, v4))

# ==============================
# Finish
# ==============================
bm.normal_update()
bm.to_mesh(mesh)
bm.free()

# Shade smooth
bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()

# Optional subdivision modifier
sub = obj.modifiers.new("Subdivision", type='SUBSURF')
sub.levels = 2
sub.render_levels = 3
