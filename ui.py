import bpy
import numpy as np
from . import logic

global_curve_node_mapping = {}
global_current_cumshot_obj = None

def myNodeTree():
    if 'TestCurveData' not in bpy.data.node_groups:
        ng = bpy.data.node_groups.new('TestCurveData', 'ShaderNodeTree')
        ng.fake_user = True
    return bpy.data.node_groups['TestCurveData'].nodes

# Velocity curve editor
def CurveData_add(curve_name):  
    global global_curve_node_mapping
    if curve_name not in global_curve_node_mapping:
        cn = myNodeTree().new('ShaderNodeRGBCurve')
        global_curve_node_mapping[curve_name] = cn.name

    curve = myNodeTree()[global_curve_node_mapping[curve_name]]
    return curve

class Cumshot_add(bpy.types.Operator):
    bl_idname = 'cs.add_cumshot'
    bl_label = 'Add Cumshot'
    bl_options = {"REGISTER", "UNDO"}
 
    def execute(self, context):
        global global_current_cumshot_obj
        selected_object_str = context.scene.selected_object
        if selected_object_str != "":
            selected_object = bpy.data.objects[selected_object_str]
            global_current_cumshot_obj = logic.create_cumshot(context, selected_object, myNodeTree()[global_curve_node_mapping["Velocity"]].mapping)
            if context.scene.remesh_modifier:
                remesh_modifier_selected(self,context)
        return {"FINISHED"}
    
class  CS_PT_MainPanel(bpy.types.Panel):
    bl_label = "Baking Settings"
    bl_category = "Cumshotter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    velocity_curve = None
    #bl_options = {"DEFAULT_CLOSED"}

    def __init__(self):
        self.set_velocity_curve_defaults()

    def draw(self, context):

        layout = self.layout
        layout.label(text="Select emitter")

        scene = context.scene
        layout.prop_search(scene, "selected_object", scene, "objects", icon='OBJECT_DATA', text='Object')
        layout.prop(scene, "start_frame")
        layout.prop(scene, "thickness")        
        layout.prop(scene, "velocity")
        layout.label(text="Velocity Curve")
        layout.template_curve_mapping(self.velocity_curve, "mapping")
        #self.invokeFunction(layout, "resetEndPoints", text = "Reset End Points")
        layout.prop(scene, "length")   
        layout.prop(scene, "physics_resolution") 
        layout.prop(scene, "spline_resolution")           
        layout.prop(scene, "randomness")            
        layout.operator("cs.add_cumshot", icon='MESH_CUBE', text="Bake Cumshot")

    def set_velocity_curve_defaults(self): 

        if self.velocity_curve is None:
            self.velocity_curve = CurveData_add('Velocity')

            # Set default curve
            curve_mapping = myNodeTree()[global_curve_node_mapping["Velocity"]].mapping

            curve_mapping.curves[3].points[0].location = (0,0.35)
            curve_mapping.curves[3].points[1].location = (1,0)
            curve_mapping.curves[3].points.new(0.05, 0.40)
            curve_mapping.curves[3].points.new(0.25, 0.35)
            curve_mapping.curves[3].points.new(0.5, 0.1)


class CS_PT_VisualSettingsPanel(bpy.types.Panel):
    bl_label = "Visual Settings"
    bl_category = "Cumshotter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    #bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
           
        layout.prop(scene, "remesh_modifier")                
        layout.prop(scene, "remesh_modifier_effect")                


def remesh_modifier_selected(self, context):
    global global_current_cumshot_obj

    if context.scene.remesh_modifier and global_current_cumshot_obj is not None:

        mod = global_current_cumshot_obj.modifiers.get("Remesh")
        if mod is None:
            # add a solidify modifier on active object
            mod = global_current_cumshot_obj.modifiers.new("Remesh", 'REMESH')
            mod.use_smooth_shade = True
            mod.voxel_size = np.interp(context.scene.remesh_modifier_effect, (0, 1), (0.02, 0.1))

    else:
            global_current_cumshot_obj.modifiers.remove(global_current_cumshot_obj.modifiers.get("Remesh"))

def remesh_modifier_effect_changed(self, context):
    global global_current_cumshot_obj

    mod = global_current_cumshot_obj.modifiers.get("Remesh")
    if mod is not None:
        val  = np.interp(context.scene.remesh_modifier_effect, (0, 1), (0.02, 0.1))
        print("setting voxel size", val)
        mod.voxel_size = val

def randomness_changed(self, context):
    pass

def register():  
    print("REGISTER")
    bpy.utils.register_class(CS_PT_MainPanel)
    bpy.utils.register_class(CS_PT_VisualSettingsPanel)    
    bpy.utils.register_class(Cumshot_add)

    # Properties
    bpy.types.Scene.start_frame = bpy.props.IntProperty(
        name="Start Frame",
        min=0
    )
    bpy.types.Scene.velocity = bpy.props.IntProperty(
        name="Velocity",
        default=20,
        min=0
    )
    bpy.types.Scene.length = bpy.props.IntProperty(
        name="Volume",
        default=1,        
        min=1
    )
    bpy.types.Scene.physics_resolution = bpy.props.IntProperty(
        name="Physics Resolution",
        default=40,
        min=0
    )
    bpy.types.Scene.spline_resolution = bpy.props.IntProperty(
        name="Spline Resolution",
        default=20,
        min=0
    )    
    bpy.types.Scene.thickness = bpy.props.FloatProperty(
        name="Cum Thickness",
        default=0.15,
        min=0.0
    )
    bpy.types.Scene.slowdown = bpy.props.FloatProperty(
        name="Cum Flow",
        default=0.95,
        min=0.0,
        max=1.0
    )
    bpy.types.Scene.randomness = bpy.props.FloatProperty(
        name="Randomness",
        default=0,
        min=0,
        max=1,
        update=randomness_changed
    )   
    bpy.types.Scene.remesh_modifier = bpy.props.BoolProperty(
        name="Grainy Look",
        default=False,
        update=remesh_modifier_selected
    )        
    bpy.types.Scene.remesh_modifier_effect = bpy.props.FloatProperty(
        name="Grainy Effect",
        default=1,
        min=0,
        max=1,
        update=remesh_modifier_effect_changed
    )
            
    bpy.types.Scene.selected_object = bpy.props.StringProperty(name="Emitter Object")

def unregister():
    bpy.utils.unregister_class(CS_PT_MainPanel)
    bpy.utils.unregister_class(CS_PT_VisualSettingsPanel)
    bpy.utils.unregister_class(Cumshot_add)