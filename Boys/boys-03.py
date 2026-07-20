import bpy
import bmesh
import math
import cmath

# --- Parameters ---
arms =  3          # 3 = Classic, 4 = Square, 5 = Pentagonal
resolution_r = 140
resolution_theta = 200
# For n=4, the "singularity" is right at r=1. 
# We stop at 0.85 to see the structure without the "blow-up".
max_r = 0.85 if arms > 3 else 1.0 

def get_boys_coords(r, theta, n):
    z = cmath.rect(r, theta)
    
    # The Bryant Polynomial
    a = z**(2*n) + math.sqrt(5) * (z**n) - 1
    
    # Avoid division by zero
    if abs(a) < 1e-4: return None
    
    # Parametric components
    try:
        m1 = (z * (z**(n+1) - 1) / a).imag
        m2 = (z * (z**(n+1) + 1) / a).real
        m3 = ((2/3) * (z**(2*n) + 1) / a).imag + 0.5
        
        m_vec = [m1, m2, m3]
        dot_product = sum(comp**2 for comp in m_vec)
        
        if dot_product < 1e-4: return (0, 0, 0)
        
        # The Inversion
        return (m_vec[0]/dot_product, m_vec[1]/dot_product, m_vec[2]/dot_product)
    except OverflowError:
        return None

# --- Mesh Generation ---
mesh = bpy.data.meshes.new(f"BoysSurface_{arms}Arms")
obj = bpy.data.objects.new(mesh.name, mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()

verts_grid = []
for i in range(resolution_r + 1):
    r = (i / resolution_r) * max_r
    row = []
    for j in range(resolution_theta):
        theta = (j / resolution_theta) * 2 * math.pi
        pos = get_boys_coords(r, theta, arms)
        
        if pos is not None:
            row.append(bm.verts.new(pos))
        else:
            row.append(None) # Marker for failed math
    verts_grid.append(row)

# Stitch faces only where we have valid vertices
for i in range(resolution_r):
    for j in range(resolution_theta):
        jp1 = (j + 1) % resolution_theta
        v1, v2, v3, v4 = verts_grid[i][j], verts_grid[i+1][j], verts_grid[i+1][jp1], verts_grid[i][jp1]
        
        if all([v1, v2, v3, v4]):
            bm.faces.new((v1, v2, v3, v4))

# Normalize size so it doesn't appear 1000m wide
bm.to_mesh(mesh)
bm.free()

# Final Auto-Scale to keep it in view
obj.scale = (1.0, 1.0, 1.0)
max_dim = max(obj.dimensions)
if max_dim > 10:
    s = 5.0 / max_dim
    obj.scale = (s, s, s)