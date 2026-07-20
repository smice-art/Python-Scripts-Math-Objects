import bpy
import bmesh
import math

# --- Parameters ---
res_x = 40        # Resolution from center to edge of petal
res_theta = 600   # Resolution around the spiral (higher = smoother petals)
x_max = 1.0
theta_min = -2 * math.pi
theta_max = 15 * math.pi

def get_rose_coords(x, theta):
    # phi: controls the opening of the flower as it spirals
    phi = (math.pi / 2) * math.exp(-theta / (8 * math.pi))
    
    # X: controls the "wavy" petal shape (the 3.6 determines petal count/frequency)
    petal_wave = (5/4) * (1 - ((3.6 * theta) % (2 * math.pi)) / math.pi)**2 - 1/4
    X = 1 - 0.5 * (petal_wave**2)
    
    # y: the vertical "bend" of the petal surface
    y = 1.95653 * (x**2) * (1.27689 * x - 1)**2 * math.sin(phi)
    
    # r: the radial distance from the Z-axis
    r = X * (x * math.sin(phi) + y * math.cos(phi))
    
    # Final 3D mapping
    pos_x = r * math.sin(theta)
    pos_y = r * math.cos(theta)
    pos_z = X * (x * math.cos(phi) - y * math.sin(phi))
    
    return (pos_x, pos_y, pos_z)

# --- Mesh Generation ---
mesh = bpy.data.meshes.new("MathematicalRose")
obj = bpy.data.objects.new("MathematicalRose", mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()

# Create the grid of vertices
verts_grid = []
for i in range(res_x + 1):
    x_val = (i / res_x) * x_max
    row = []
    for j in range(res_theta + 1):
        theta_val = theta_min + (j / res_theta) * (theta_max - theta_min)
        pos = get_rose_coords(x_val, theta_val)
        row.append(bm.verts.new(pos))
    verts_grid.append(row)

# Stitch the grid into faces
for i in range(res_x):
    for j in range(res_theta):
        v1 = verts_grid[i][j]
        v2 = verts_grid[i+1][j]
        v3 = verts_grid[i+1][j+1]
        v4 = verts_grid[i][j+1]
        bm.faces.new((v1, v2, v3, v4))

bm.to_mesh(mesh)
bm.free()

# Final Touch: Smoothing
bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()