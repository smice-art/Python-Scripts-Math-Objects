import bpy
import math
from mathutils import Vector
import numpy as np

# Define a property group with automatic update
class BianchiPinkallProperties(bpy.types.PropertyGroup):
    def update_surface(self, context):
        create_surface(context)

    valminu: bpy.props.FloatProperty(name="U Min", default=0, min=-10, max=math.pi*2, update=update_surface)
    valmaxu: bpy.props.FloatProperty(name="U Max", default=math.pi*2, min=0, max=math.pi*4, update=update_surface)
    valminv: bpy.props.FloatProperty(name="V Min", default=0, min=-10, max=math.pi*2, update=update_surface)
    valmaxv: bpy.props.FloatProperty(name="V Max", default=math.pi*2, min=0, max=math.pi*4, update=update_surface)
    resolutionu: bpy.props.IntProperty(name="Resolution U", default=150, min=10, max=500, update=update_surface)
    resolutionv: bpy.props.IntProperty(name="Resolution V", default=150, min=10, max=500, update=update_surface)
    a: bpy.props.FloatProperty(name="a", default=0.93, min=0, max=2, update=update_surface)
    n: bpy.props.FloatProperty(name="n", default=3, min=1, max=10, update=update_surface)
    b: bpy.props.FloatProperty(name="b", default=0.36, min=0, max=2, update=update_surface)
    c: bpy.props.FloatProperty(name="c", default=0, min=0, max=2, update=update_surface)
    d: bpy.props.FloatProperty(name="d", default=0, min=0, max=2, update=update_surface)
    k: bpy.props.FloatProperty(name="k", default=15, min=1, max=30, update=update_surface)

# Generate the surface based on parameters
def create_surface(context):
    props = context.scene.bianchi_pinkall_props

    # Extract properties
    valminu = props.valminu
    valmaxu = props.valmaxu
    valminv = props.valminv
    valmaxv = props.valmaxv
    resolutionu = props.resolutionu
    resolutionv = props.resolutionv
    a = props.a
    n = props.n
    b = props.b
    c = props.c
    d = props.d
    k = props.k

    pasu = (valmaxu - valminu) / resolutionu
    pasv = (valmaxv - valminv) / resolutionv

    # Create vertices and faces
    vertices = []
    faces = []
    for ui, varu in enumerate(np.arange(valminu, valmaxu, pasu)):
        for vi, varv in enumerate(np.arange(valminv, valmaxv, pasv)):
            gamma = a + b * math.sin(2 * n * varv)
            x = math.cos(varu + varv) * math.cos(gamma)
            y = math.sin(varu + varv) * math.cos(gamma)
            z = math.cos(varu - varv) * math.sin(gamma)
            w = math.sin(varu - varv) * math.sin(gamma)
            r = math.acos(w) / math.pi / math.sqrt(1 - w * w)
            vertices.append((x * r, y * r, z * r))

            if ui < resolutionu - 1 and vi < resolutionv - 1:
                idx = ui * resolutionv + vi
                faces.append((idx, idx + 1, idx + resolutionv + 1, idx + resolutionv))

    # Create or update the mesh
    mesh = bpy.data.meshes.get("SurfaceBianchiPinkallMesh")
    if mesh is None:
        mesh = bpy.data.meshes.new("SurfaceBianchiPinkallMesh")

    obj = bpy.data.objects.get("SurfaceBianchiPinkall")
    if obj is None:
        obj = bpy.data.objects.new("SurfaceBianchiPinkall", mesh)
        bpy.context.collection.objects.link(obj)

    # Update mesh
    mesh.clear_geometry()
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

# N-Panel for UI
class BIANCHI_PT_Panel(bpy.types.Panel):
    bl_label = "Bianchi-Pinkall Torus"
    bl_idname = "BIANCHI_PT_Panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Bianchi Torus"

    def draw(self, context):
        layout = self.layout
        props = context.scene.bianchi_pinkall_props

        layout.prop(props, "valminu")
        layout.prop(props, "valmaxu")
        layout.prop(props, "valminv")
        layout.prop(props, "valmaxv")
        layout.prop(props, "resolutionu")
        layout.prop(props, "resolutionv")
        layout.prop(props, "a")
        layout.prop(props, "n")
        layout.prop(props, "b")
       

# Register classes
def register():
    bpy.utils.register_class(BianchiPinkallProperties)
    bpy.types.Scene.bianchi_pinkall_props = bpy.props.PointerProperty(type=BianchiPinkallProperties)

    bpy.utils.register_class(BIANCHI_PT_Panel)

def unregister():
    bpy.utils.unregister_class(BianchiPinkallProperties)
    del bpy.types.Scene.bianchi_pinkall_props

    bpy.utils.unregister_class(BIANCHI_PT_Panel)

if __name__ == "__main__":
    register()
