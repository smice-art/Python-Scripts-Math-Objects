import bpy
import bmesh
import math
from mathutils import Vector

# --- Parameters ---
res_t = 120        
res_theta = 32     
r_tube = 1.0/7.0   

def f_knot(t):
    x = (2 + math.cos(2 * t)) * math.cos(3 * t)
    y = (2 + math.cos(2 * t)) * math.sin(3 * t)
    z = math.sin(4 * t)
    return Vector((x, y, z)) / 4.0

def f_prime(t):
    dt = 0.001
    return (f_knot(t + dt) - f_knot(t - dt)) / (2 * dt)

def f_double_prime(t):
    dt = 0.001
    return (f_prime(t + dt) - f_prime(t - dt)) / (2 * dt)

def inverse_stereographic(v):
    sq_mag = v.length_squared
    denom = 1 + sq_mag
    return [2*v.x/denom, 2*v.y/denom, 2*v.z/denom, (sq_mag - 1)/denom]

def stereographic_projection(v4):
    x, y, z, w = v4
    denom = 1.0 - w
    if abs(denom) < 1e-4: denom = 1e-4
    return Vector((x/denom, y/denom, z/denom))

# --- Generator Function ---
def create_knot_mesh(rotation_angle):
    bm = bmesh.new()
    verts_grid = []

    for i in range(res_t):
        t = (i / res_t) * 2 * math.pi
        pos = f_knot(t)
        df = f_prime(t)
        ddf = f_double_prime(t)
        
        tangent = df.normalized()
        normal = (ddf * df.length_squared - df * df.dot(ddf)).normalized()
        binormal = normal.cross(tangent)
        
        row = []
        for j in range(res_theta):
            theta_val = (j / res_theta) * 2 * math.pi
            tube_point = pos + r_tube * (normal * math.cos(theta_val) + binormal * math.sin(theta_val))
            
            # Lift, Rotate in YW, and Project
            v4 = inverse_stereographic(tube_point)
            
            # YW Rotation
            x, y, z, w = v4
            new_y = y * math.cos(rotation_angle) - w * math.sin(rotation_angle)
            new_w = y * math.sin(rotation_angle) + w * math.cos(rotation_angle)
            
            final_pos = stereographic_projection((x, new_y, z, new_w))
            row.append(bm.verts.new(final_pos))
        verts_grid.append(row)

    for i in range(res_t):
        next_i = (i + 1) % res_t
        for j in range(res_theta):
            next_j = (j + 1) % res_theta
            bm.faces.new((verts_grid[i][j], verts_grid[next_i][j], 
                          verts_grid[next_i][next_j], verts_grid[i][next_j]))
    
    return bm

# --- Main Logic ---
mesh_name = "Knot4D_Animated"
if mesh_name in bpy.data.meshes:
    bpy.data.meshes.remove(bpy.data.meshes[mesh_name])

mesh = bpy.data.meshes.new(mesh_name)
obj = bpy.data.objects.new(mesh_name, mesh)
bpy.context.collection.objects.link(obj)

# Using frame 1 as the initial state
bm_data = create_knot_mesh(0.0)
bm_data.to_mesh(mesh)
bm_data.free()

bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()

# --- THE ANIMATION TRICK: Geometry Nodes Driver ---
# We use a simple GN setup to "drive" the rotation via the timeline
gn_mod = obj.modifiers.new("4D_Driver", 'NODES')
# We won't actually use the nodes to move vertices (too slow with this math), 
# but we can use the "Bake to Shape Keys" trick we used before, 
# OR we can simply re-run the script with a loop.

print("Knot Generated. To animate the 4D morph, would you like me to bake it to Shape Keys?")