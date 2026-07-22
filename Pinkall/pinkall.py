import bpy
import bmesh
import math

# =====================================================
# Mesh builder
# =====================================================
def build_ps_torus(obj):
    p = obj.ps_props

    R0 = p.R0
    r  = p.r
    a1 = p.a1
    a2 = p.a2
    k1 = p.k1
    k2 = p.k2

    u_res = 260
    v_res = 220

    mesh = obj.data
    mesh.clear_geometry()
    bm = bmesh.new()

    verts = []

    for i in range(u_res):
        u = 2 * math.pi * i / u_res
        ring = []

        for j in range(v_res):
            v = 2 * math.pi * j / v_res

            # 2D Willmore-like modulation
            mod = (
                1
                + a1 * math.cos(k1 * u)
                + a2 * math.cos(k2 * v)
            )

            R = R0 * mod
            rr = r * mod

            x = (R + rr * math.cos(v)) * math.cos(u)
            y = (R + rr * math.cos(v)) * math.sin(u)
            z = rr * math.sin(v)

            ring.append(bm.verts.new((x, y, z)))

        verts.append(ring)

    bm.verts.ensure_lookup_table()

    for i in range(u_res):
        for j in range(v_res):
            bm.faces.new((
                verts[i][j],
                verts[(i + 1) % u_res][j],
                verts[(i + 1) % u_res][(j + 1) % v_res],
                verts[i][(j + 1) % v_res]
            ))

    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()


# =====================================================
# Auto update
# =====================================================
def ps_update(self, context):
    obj = context.object
    if obj and obj.type == 'MESH' and hasattr(obj, "ps_props"):
        build_ps_torus(obj)


# =====================================================
# Properties
# =====================================================
class PSTorusProps(bpy.types.PropertyGroup):
    R0: bpy.props.FloatProperty(
        name="Major Radius",
        default=2.0,
        min=0.5,
        update=ps_update
    )

    r: bpy.props.FloatProperty(
        name="Minor Radius",
        default=0.6,
        min=0.1,
        update=ps_update
    )

    a1: bpy.props.FloatProperty(
        name="u-modulation",
        default=0.15,
        min=0.0,
        update=ps_update
    )

    a2: bpy.props.FloatProperty(
        name="v-modulation",
        default=0.12,
        min=0.0,
        update=ps_update
    )

    k1: bpy.props.IntProperty(
        name="u-frequency",
        default=3,
        min=1,
        update=ps_update
    )

    k2: bpy.props.IntProperty(
        name="v-frequency",
        default=8,
        min=1,
        update=ps_update
    )


# =====================================================
# UI Panel
# =====================================================
class PS_PT_panel(bpy.types.Panel):
    bl_label = "Pinkall–Sterling Torus"
    bl_idname = "OBJECT_PT_ps_torus"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if not obj or not hasattr(obj, "ps_props"):
            layout.label(text="Select PS_Torus object")
            return

        p = obj.ps_props
        layout.prop(p, "R0")
        layout.prop(p, "r")
        layout.prop(p, "a1")
        layout.prop(p, "a2")
        layout.prop(p, "k1")
        layout.prop(p, "k2")


# =====================================================
# Register
# =====================================================
def register():
    bpy.utils.register_class(PSTorusProps)
    bpy.utils.register_class(PS_PT_panel)
    bpy.types.Object.ps_props = bpy.props.PointerProperty(type=PSTorusProps)

def unregister():
    bpy.utils.unregister_class(PS_PT_panel)
    bpy.utils.unregister_class(PSTorusProps)
    del bpy.types.Object.ps_props

register()

# =====================================================
# Create object
# =====================================================
mesh = bpy.data.meshes.new("PS_Torus")
obj = bpy.data.objects.new("PS_Torus", mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj

build_ps_torus(obj)
bpy.ops.object.shade_smooth()
