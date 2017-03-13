"""
This is the template for a custom prompt UI

To assign this to an assembly set the property_id of the Assembly class
To the bl_idname of the Prompt_Inteface class

"""
import bpy
from mv import fd_types

class PROMPTS_Prompts_Template(fd_types.Prompts_Interface):
    bl_idname = "prompt.template"
    bl_label = "Prompt Template"
    bl_options = {'UNDO'}
    
    object_name = bpy.props.StringProperty(name="Object Name",
                                           description="Stores the Base Point Object Name \
                                           so the object can be retrieved from the database.")
    
    width = bpy.props.FloatProperty(name="Width",unit='LENGTH',precision=4)
    height = bpy.props.FloatProperty(name="Height",unit='LENGTH',precision=4)
    depth = bpy.props.FloatProperty(name="Depth",unit='LENGTH',precision=4)    
    
    product = None

    def check(self, context):
        """ This is called everytime a change is made in the UI """
        self.update_product_size()
        return True

    def execute(self, context):
        """ This is called when the OK button is clicked """
        self.update_product_size()
        return {'FINISHED'}

    def invoke(self,context,event):
        """ This is called before the interface is displayed """
        self.product = self.get_product()
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(500))
        
    def draw(self, context):
        """ This is where you draw the interface """
        layout = self.layout
        layout.label(self.product.obj_bp.mv.name_object)
        self.draw_product_size(layout)
        col = layout.column(align=True)
        
        prompt = self.product.get_prompt("Prompt Name")
        col.prop(prompt,prompt.prompt_type,text=prompt.name)            

bpy.utils.register_class(PROMPTS_Prompts_Template)