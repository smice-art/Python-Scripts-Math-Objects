"""
Kluchikov Torus Generator
==========================

WHAT THIS IS
------------
This add-on procedurally builds the "Kluchikov Torus" - a torus whose tube
radius is not constant, but is displaced by a 3-strand potential field
("kluchikov_potential"). The field is built from three attractor points
arranged 120 degrees apart around the tube's cross-section, combined with
a slow twist that rotates 8/3 times per revolution around the main ring.
Because the twist rate (8/3) and the 3-fold symmetry of the attractor
points don't divide evenly, the three "lobes" braid around each other as
they travel around the ring - producing a continuous, self-weaving
triple-strand torus instead of a plain donut.

How a vertex position is found:
1. Start from a plain torus surface point (major_r / minor_base_r).
2. Evaluate the potential field at that point.
3. Compare the result to a target iso-value ("contour_target"); the
   difference, scaled by "amplitude", pushes the tube radius in or out.
4. Re-project the point outward with that adjusted radius.

Repeating this on a (res_major x res_minor) grid and stitching the grid
into quads produces the braided tube surface.

WHAT THIS ADD-ON GIVES YOU
---------------------------
- An N-panel tab called "Kluchikov" (open the 3D Viewport sidebar with N)
  with all generation parameters.
- An "Auto Update" toggle: while enabled, dragging any slider regenerates
  the mesh live. While disabled, use the "Generate / Update Torus" button.
- A "Random Metallic Material" button that builds and assigns a shiny,
  randomized metallic material suited to the torus.

Installation: Edit > Preferences > Add-ons > Install..., pick this file,
then enable "Add Mesh: Kluchikov Torus".
"""

bl_info = {
    "name": "Kluchikov Torus",
    "author": "Claudio Claude",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Kluchikov",
    "description": "Generates the procedural 3-strand Kluchikov Torus with live parameter editing",
    "category": "Add Mesh",
}

import bpy
import bmesh
import math
import random

OBJECT_NAME = "Kluchikov_Torus"


# ---------------------------------------------------------------------------
# Core math: the potential field that carves the 3-strand braid
# ---------------------------------------------------------------------------
def kluchikov_potential(x, y, z, major_r):
    """Evaluate the 3-strand braid potential at a 3D point.

    Three attractor points, spaced 120 degrees apart in the twisted local
    frame, each contribute a very sharp (1/64 power) falloff term. Where a
    point sits close to one of the three attractors the potential is low;
    summing and averaging the three terms produces a field whose iso-surface
    traces three braided strands around the ring.
    """
    # Core constants: the three attractor points (triangle at radius ~0.25)
    x1, y1 = 0.125, 0.25 * math.sin(2 * math.pi / 3.0)

    # Toroidal coordinates relative to the ring
    r = math.sqrt(x ** 2 + z ** 2) - major_r
    theta = math.atan2(z, x) + math.pi / 2.0

    # The "Twist" logic (8/3 determines the braiding rhythm)
    t = (8.0 * theta / 3.0)
    x2 = r * math.sin(t) + y * math.cos(t)
    y2 = r * math.cos(t) - y * math.sin(t)

    # The "Triple-Point" potential - three attractor terms = 3-strand braid
    d1 = (x2 + 0.25) ** 2 + y2 ** 2
    d2 = (x2 - x1) ** 2 + (y2 + y1) ** 2
    d3 = (x2 - x1) ** 2 + (y2 - y1) ** 2

    # 1/64 is a very "sharp" root. A small epsilon avoids pow(0, ...) issues.
    p = 0.33 * (pow(max(d1, 1e-8), 1 / 64) +
                pow(max(d2, 1e-8), 1 / 64) +
                pow(max(d3, 1e-8), 1 / 64))

    # Ripple from the secondary term of the original formula
    p += 0.01 * math.sin(5 * theta)
    return p


def build_kluchikov_mesh(bm, settings):
    """Fill a bmesh with the Kluchikov Torus geometry for the given settings."""
    res_major = settings.res_major
    res_minor = settings.res_minor
    amplitude = settings.amplitude
    contour_target = settings.contour_target
    major_r = settings.major_r
    minor_base_r = settings.minor_base_r

    verts_grid = []

    for i in range(res_major):
        theta_m = (i / res_major) * 2 * math.pi
        row = []
        for j in range(res_minor):
            phi_m = (j / res_minor) * 2 * math.pi

            # Test point at the base (undisplaced) torus surface
            test_x = (major_r + minor_base_r * math.cos(phi_m)) * math.cos(theta_m)
            test_z = (major_r + minor_base_r * math.cos(phi_m)) * math.sin(theta_m)
            test_y = minor_base_r * math.sin(phi_m)

            # How far this point is from the "ideal" braid contour
            p_val = kluchikov_potential(test_x, test_y, test_z, major_r)

            # Push the tube radius in/out to trace the braid
            offset = (contour_target - p_val) * amplitude
            r_eff = minor_base_r + offset

            final_x = (major_r + r_eff * math.cos(phi_m)) * math.cos(theta_m)
            final_z = (major_r + r_eff * math.cos(phi_m)) * math.sin(theta_m)
            final_y = r_eff * math.sin(phi_m)

            row.append(bm.verts.new((final_x, final_y, final_z)))
        verts_grid.append(row)

    # Face stitching (wrap around both directions)
    for i in range(res_major):
        ni = (i + 1) % res_major
        for j in range(res_minor):
            nj = (j + 1) % res_minor
            bm.faces.new((verts_grid[i][j], verts_grid[ni][j],
                           verts_grid[ni][nj], verts_grid[i][nj]))


def generate_kluchikov_object(context, settings):
    """Create the Kluchikov Torus object if needed, or rebuild its mesh in place."""
    obj = bpy.data.objects.get(OBJECT_NAME)

    if obj is None or obj.type != 'MESH':
        mesh = bpy.data.meshes.new(OBJECT_NAME)
        obj = bpy.data.objects.new(OBJECT_NAME, mesh)
        context.collection.objects.link(obj)
    else:
        mesh = obj.data

    bm = bmesh.new()
    build_kluchikov_mesh(bm, settings)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    context.view_layer.objects.active = obj
    obj.select_set(True)

    # Shade smooth
    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj


# ---------------------------------------------------------------------------
# Property group (lives on the Scene, drives the N-panel)
# ---------------------------------------------------------------------------
def _on_param_update(self, context):
    """Called whenever a slider changes; regenerates the mesh if Auto Update is on."""
    if self.auto_update:
        generate_kluchikov_object(context, self)


class KluchikovSettings(bpy.types.PropertyGroup):
    auto_update: bpy.props.BoolProperty(
        name="Auto Update",
        description="Regenerate the torus live whenever a parameter changes",
        default=False,
    )
    res_major: bpy.props.IntProperty(
        name="Ring Segments",
        description="Segments around the main ring",
        default=200, min=3, max=512,
        update=_on_param_update,
    )
    res_minor: bpy.props.IntProperty(
        name="Tube Segments",
        description="Segments around the tube cross-section",
        default=80, min=3, max=256,
        update=_on_param_update,
    )
    amplitude: bpy.props.FloatProperty(
        name="Amplitude",
        description="How strongly the braid potential displaces the tube radius",
        default=5.5, min=0.0, max=30.0,
        update=_on_param_update,
    )
    contour_target: bpy.props.FloatProperty(
        name="Contour Target",
        description="Target iso-value of the potential field that the surface follows",
        default=0.945, min=0.0, max=3.0,
        update=_on_param_update,
    )
    major_r: bpy.props.FloatProperty(
        name="Major Radius",
        description="Radius of the main ring",
        default=1.5, min=0.05, max=20.0,
        update=_on_param_update,
    )
    minor_base_r: bpy.props.FloatProperty(
        name="Tube Radius",
        description="Base radius of the tube before braid displacement",
        default=0.35, min=0.01, max=10.0,
        update=_on_param_update,
    )


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------
class OBJECT_OT_kluchikov_generate(bpy.types.Operator):
    bl_idname = "object.kluchikov_generate"
    bl_label = "Generate / Update Torus"
    bl_description = "Build (or rebuild) the Kluchikov Torus with the current parameters"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.kluchikov_settings
        generate_kluchikov_object(context, settings)
        return {'FINISHED'}


class OBJECT_OT_kluchikov_random_material(bpy.types.Operator):
    bl_idname = "object.kluchikov_random_material"
    bl_label = "Random Metallic Material"
    bl_description = "Generate and assign a random shiny metallic material to the torus"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.data.objects.get(OBJECT_NAME)
        if obj is None:
            self.report({'WARNING'}, "No Kluchikov Torus found - generate it first")
            return {'CANCELLED'}

        mat = bpy.data.materials.new(name="Kluchikov_Metal")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")

        if bsdf is not None:
            # Randomized but metal-plausible color: keep saturation/value in
            # a range that reads as polished metal (steel, gold, copper,
            # gunmetal, brass...) rather than a flat cartoon hue.
            hue = random.random()
            sat = random.uniform(0.15, 0.65)
            val = random.uniform(0.55, 0.95)
            r, g, b = _hsv_to_rgb(hue, sat, val)

            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
            bsdf.inputs["Metallic"].default_value = 1.0
            bsdf.inputs["Roughness"].default_value = random.uniform(0.03, 0.25)

            # Slight per-material coat variation if available (Blender 4.x)
            if "Coat Weight" in bsdf.inputs:
                bsdf.inputs["Coat Weight"].default_value = random.uniform(0.0, 0.3)

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

        self.report({'INFO'}, f"Assigned new metallic material: {mat.name}")
        return {'FINISHED'}


def _hsv_to_rgb(h, s, v):
    import colorsys
    return colorsys.hsv_to_rgb(h, s, v)


# ---------------------------------------------------------------------------
# N-panel
# ---------------------------------------------------------------------------
class VIEW3D_PT_kluchikov_panel(bpy.types.Panel):
    bl_label = "Kluchikov Torus"
    bl_idname = "VIEW3D_PT_kluchikov_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Kluchikov"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kluchikov_settings

        col = layout.column(align=True)
        col.label(text="Resolution")
        col.prop(settings, "res_major")
        col.prop(settings, "res_minor")

        col = layout.column(align=True)
        col.label(text="Braid Shape")
        col.prop(settings, "amplitude")
        col.prop(settings, "contour_target")

        col = layout.column(align=True)
        col.label(text="Torus Size")
        col.prop(settings, "major_r")
        col.prop(settings, "minor_base_r")

        layout.separator()
        layout.prop(settings, "auto_update", toggle=True)

        row = layout.row()
        row.scale_y = 1.4
        row.operator("object.kluchikov_generate", icon='MESH_TORUS')

        layout.separator()
        row = layout.row()
        row.scale_y = 1.4
        row.operator("object.kluchikov_random_material", icon='MATERIAL')


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
classes = (
    KluchikovSettings,
    OBJECT_OT_kluchikov_generate,
    OBJECT_OT_kluchikov_random_material,
    VIEW3D_PT_kluchikov_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.kluchikov_settings = bpy.props.PointerProperty(type=KluchikovSettings)


def unregister():
    del bpy.types.Scene.kluchikov_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()