import bpy
import bmesh
import math
from mathutils import Matrix, Vector

# --- Resolution ---
# Number of real sub-steps generated for every original spiral step.
# 1 = original mesh (coarse/faceted). 2-4 = noticeably smoother tube,
# since it actually adds real rings/edges along the spiral rather than
# relying on a subdivision modifier (which can't smooth this mesh - see
# the weld step below for why).
RESOLUTION = 12

# --- Constants & Parameters ---
n = 16 #6
t2 = math.pi / 5
t1 = t2 / 2 #2
alpha = math.acos(-math.sqrt(5.0) / 5)
dz = math.sin(t1)**2 * math.tan(alpha / 2)
z_val = ((1 + math.sqrt(5)) / 2) * math.tan(alpha / 2) / 2 + dz # GoldenRatio = (1+sqrt(5))/2

scale = (math.cos(t1) - math.sqrt(3.0 * (1 - math.cos(t2)) / 2)) / (2 * math.cos(t2) - 1)
# Rotation Matrix R
angle_r = math.acos(math.cos(t1) + dz**2 * (scale - 1)**2 / (2 * scale))

def get_Rz(t):
    return Matrix(((math.cos(t), -math.sin(t), 0), (math.sin(t), math.cos(t), 0), (0, 0, 1)))

def get_Ry(t):
    return Matrix(((math.cos(t), 0, math.sin(t)), (0, 1, 0), (-math.sin(t), 0, math.cos(t))))

R_mat = scale * get_Rz(angle_r)

# Fine-grained version of R_mat: applying this RESOLUTION times lands
# exactly where one R_mat step would, since R_mat is a similarity
# transform (uniform scale + rotation about Z) and both scale and angle
# split evenly. This is what actually increases vertex/edge count along
# the spiral without changing the overall shape or endpoints.
scale_fine = scale ** (1.0 / RESOLUTION)
angle_r_fine = angle_r / RESOLUTION
R_mat_fine = scale_fine * get_Rz(angle_r_fine)
n_steps = n * RESOLUTION

# --- Geometry Generation ---
all_verts = []
all_faces = []

def add_set(base_verts, base_faces):
    offset = len(all_verts)
    all_verts.extend([Vector(v) for v in base_verts])
    for f in base_faces:
        all_faces.append([i + offset for i in f])

# 1. Generate core verts and faces (The "verts0" loop)
verts_strip = []
v0 = [Vector((math.cos(i * t2), math.sin(i * t2), (2 * (i % 2) - 1) * dz)) for i in range(10)]

for _ in range(n_steps + 1):
    verts_strip.extend([Vector((0, 0, z_val)) + v for v in v0])
    v0 = [R_mat_fine @ v for v in v0]

# Generate the faces for the strip
# Quads instead of two triangles per cell - the diagonal split was what
# created the "double pattern"/crosshatching you were seeing across the
# surface. Blender/Subsurf/shading all handle quads fine natively.
strip_faces = []
for i in range(n_steps):
    for j in range(10):
        v1, v2 = j, (j + 1) % 10
        v3, v4 = j + 10, (j + 1) % 10 + 10
        strip_faces.append([10*i + v1, 10*i + v2, 10*i + v4, 10*i + v3])

# 2. Assemble the final scene (The "Show" logic)
# Original strip
add_set(verts_strip, strip_faces)

# Rotated copies
for t in [i * 2 * t2 for i in range(1, 6)]:
    # Transformation 1: Rz[t + t2] . Ry[Pi - alpha]
    m1 = get_Rz(t + t2) @ get_Ry(math.pi - alpha)
    add_set([m1 @ v for v in verts_strip], strip_faces)

    # Transformation 2: Rz[t] . Ry[alpha] . Rz[t2]
    m2 = get_Rz(t) @ get_Ry(alpha) @ get_Rz(t2)
    add_set([m2 @ v for v in verts_strip], strip_faces)

# Mirror copy (Ry[Pi])
m_mirror = get_Ry(math.pi)
add_set([m_mirror @ v for v in verts_strip], strip_faces)

# --- Create Mesh in Blender ---
mesh = bpy.data.meshes.new("ComplexPolyStructure")
obj = bpy.data.objects.new("ComplexPolyStructure", mesh)
bpy.context.collection.objects.link(obj)

mesh.from_pydata(all_verts, [], all_faces)
mesh.update()

# --- Weld seams ---
# Each add_set() call above creates its own disconnected block of
# vertices, even where two copies meet at the exact same 3D point (that
# mismatch is why a Subdivision Surface modifier pulled the copies apart
# earlier - each island had free boundary edges with nothing holding
# them together). Merging by distance welds those coincident verts into
# shared ones, turning the mesh into one connected manifold.
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(mesh)
bm.free()
mesh.update()

for poly in mesh.polygons:
    poly.use_smooth = False
