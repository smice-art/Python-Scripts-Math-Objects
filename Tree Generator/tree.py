import bpy
import bmesh
import math
import mathutils

# --- SETTINGS ---
ITERATIONS = 5      
BRANCH_ANGLE = math.pi / 4  
REDUCTION = 0.6     
TRI_BRANCH = [0, 2*math.pi/3, 4*math.pi/3] 

# --- Setup Single Mesh ---
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# We create ONE mesh and ONE bmesh to hold everything
main_mesh = bpy.data.meshes.new("FractalTreeMesh")
main_obj = bpy.data.objects.new("FractalTree", main_mesh)
bpy.context.collection.objects.link(main_obj)

# Global BMesh to collect all branches
tree_bm = bmesh.new()

def add_branch_to_bmesh(p1, p2, radius, iteration):
    direction = p2 - p1
    length = direction.length
    if length < 0.0001: return

    # Create a temporary bmesh for this single branch
    temp_bm = bmesh.new()
    bmesh.ops.create_cone(
        temp_bm, 
        cap_ends=True, 
        segments=8, 
        radius1=radius, 
        radius2=radius * 0.7, 
        depth=length
    )
    
    # Align and move
    up = mathutils.Vector((0, 0, 1))
    rot = up.rotation_difference(direction.normalized())
    trans_matrix = mathutils.Matrix.Translation(p1 + direction/2)
    rot_matrix = rot.to_matrix().to_4x4()
    
    temp_bm.transform(trans_matrix @ rot_matrix)
    
    # Merge this branch into the main tree bmesh
    temp_bm.to_mesh(main_mesh) # Optional: Write directly to mesh to save memory
    tree_bm.from_mesh(main_mesh) 
    # Actually, simpler: 
    bmesh.ops.insert_mesh(tree_bm, mesh=temp_bm)
    temp_bm.free()

def grow_tree(p1, rotation_matrix, iteration):
    if iteration == 0:
        return
    
    # Calculate p2
    z_axis = mathutils.Vector((0, 0, 1))
    step = (rotation_matrix @ z_axis)
    p2 = p1 + step
    
    # Mathematica thickness logic: 0.07 * r
    radius = 0.07 * step.length
    
    # Create the branch inside our global bmesh
    # (Directly using bmesh ops is 100x faster than 3000 objects)
    direction = p2 - p1
    length = direction.length
    
    up = mathutils.Vector((0, 0, 1))
    rot = up.rotation_difference(direction.normalized())
    
    # Create the geometry directly in the main tree_bm
    # This avoids the "3000 objects" overhead entirely
    matrix = mathutils.Matrix.Translation(p1 + direction/2) @ rot.to_matrix().to_4x4()
    
    bmesh.ops.create_cone(
        tree_bm, 
        cap_ends=True, 
        segments=6, 
        radius1=radius, 
        radius2=radius * 0.6, 
        depth=length,
        matrix=matrix
    )
    
    # Branch out
    for theta in TRI_BRANCH:
        mat_rot_z = mathutils.Matrix.Rotation(theta, 3, 'Z')
        mat_rot_y = mathutils.Matrix.Rotation(-BRANCH_ANGLE, 3, 'Y')
        new_rotation = rotation_matrix @ mat_rot_z @ mat_rot_y
        grow_tree(p2, new_rotation * REDUCTION, iteration - 1)

# --- Run ---
grow_tree(mathutils.Vector((0, 0, 0)), mathutils.Matrix.Identity(3), ITERATIONS)

# Finalize the mesh
tree_bm.to_mesh(main_mesh)
tree_bm.free()

# Add a single material for the whole tree
mat = bpy.data.materials.new(name="TreeMaterial")
mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.2, 0.5, 0.1, 1)
main_obj.data.materials.append(mat)

# Smooth it out
bpy.context.view_layer.objects.active = main_obj
bpy.ops.object.shade_smooth()

print("Tree built as a single object. No more crashes!")