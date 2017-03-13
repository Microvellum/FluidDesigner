"""
This is the template for a custom properties and a panel UI
"""

import bpy
from mv import fd_types

class PANEL_Panel_Interface(bpy.types.Panel):
    """Panel to Store all of the Cabinet Options"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Panel Inteface"
    bl_category = "Fluid Designer"
    
    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='BLANK1')    
    
    def draw(self, context):
        props = context.scene.my_custom_properties
        props.draw(self.layout)   

class PROPERTIES_Custom_Properties(bpy.types.PropertyGroup):
    float_property = bpy.props.FloatProperty(name="Float Property",
                                             description="This is a float number property",
                                             default=unit.inch(1.5),
                                             unit='LENGTH')

    integer_property = bpy.props.IntProperty(name="Integer Property",
                                             description="This is an integer number property",
                                             default=1)

    boolean_property = bpy.props.BoolProperty(name="Boolean Property",
                                              description="This is a boolean or checkbox property",
                                              default=True)
    
    enumerator_property = bpy.props.EnumProperty(name="Enumerator Property",
                                                 items=[('OPTION1',"Option 1","This is help text for option 1"),
                                                        ('OPTION2',"Option 2","This is help text for option 2"),
                                                        ('OPTION3',"Option 3","This is help text for option 3")],
                                                 description="This is a enumerator or combobox property",
                                                 default='OPTION1')

    string_property = bpy.props.StringProperty(name="String Property",
                                               description="This is a string or text property",
                                               default="This is Text")

    def draw(self,layout):
        layout.prop(self,"float_property")
        layout.prop(self,"integer_property")
        layout.prop(self,"boolean_property")
        layout.prop(self,"enumerator_property")
        layout.prop(self,"string_property")
        
bpy.utils.register_class(PANEL_Panel_Interface)
bpy.utils.register_class(PROPERTIES_Custom_Properties)    
bpy.types.Scene.my_custom_properties = bpy.props.PointerProperty(type = PROPERTIES_Custom_Properties)    
     