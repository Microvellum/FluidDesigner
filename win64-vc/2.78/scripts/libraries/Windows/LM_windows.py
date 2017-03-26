"""
Microvellum 
Windows
Stores the logic and product defs for entry doors.
"""

import bpy
import math
import os
from mv import fd_types, utils, unit

WINDOW_FRAMES = os.path.join(os.path.dirname(__file__),"Window Frames")
WINDOW_GLASS = os.path.join(os.path.dirname(__file__),"Window Glass")

MATERIAL_FILE = os.path.join(os.path.dirname(__file__),"materials","materials.blend")

DEFAULT_WIDTH = unit.inch(36.0)
DEFAULT_HEIGHT = unit.inch(36.0)
DEFAULT_DEPTH = unit.inch(8.0)
HEIGHT_ABOVE_FLOOR = unit.inch(40.0)

class Window(fd_types.Assembly):
    library_name = "Windows"
    category_name = ""
    assembly_name = ""
    property_id = "cabinetlib.window_prompts"
    type_assembly = "PRODUCT"
    mirror_z = False
    mirror_y = False
    width = 0
    height = 0
    depth = 0
    
    height_above_floor = 0
    window_frame = ""
    window_divider = ""
    window_blinds = ""
    
    def draw(self):
        self.create_assembly()
        
        self.add_tab(name='Main Options',tab_type='VISIBLE')
        self.add_prompt(name="Array X",prompt_type='QUANTITY',value=1,tab_index=0)
        self.add_prompt(name="Array X Offset",prompt_type='DISTANCE',value=unit.inch(6),tab_index=0)
        
        Width = self.get_var('dim_x','Width')
        Height = self.get_var('dim_z','Height')
        Depth = self.get_var('dim_y','Depth')
        Array_X = self.get_var("Array X")
        Array_X_Offset = self.get_var("Array X Offset")
        
        frame = self.add_assembly(os.path.join(WINDOW_FRAMES,self.window_frame))
        frame.set_name(self.window_frame)
        frame.x_dim('Width',[Width])
        frame.y_dim('Depth',[Depth])
        frame.z_dim('Height',[Height])
        frame.prompt("Array X","Array_X",[Array_X])
        frame.prompt("Array X Offset","Array_X_Offset",[Array_X_Offset])
        frame.assign_material("Glass",MATERIAL_FILE,"Glass")
        frame.assign_material("Frame",MATERIAL_FILE,"White")
        
        if self.window_divider != "":
            if self.window_frame == "Window_Frame_Fixed.blend":
                divider = self.add_assembly(os.path.join(WINDOW_GLASS,self.window_divider))
                divider.set_name(self.window_divider)
                divider.x_loc(value = unit.inch(4.0))
                divider.y_loc(value = unit.inch(3.86))
                divider.z_loc(value = unit.inch(2.75))
                divider.x_dim('Width-INCH(8.0)',[Width])
                divider.z_dim('Height-INCH(6.75)',[Height])
                divider.prompt("Array X","Array_X",[Array_X])
                divider.prompt("Array X Offset","Width+Array_X_Offset",[Array_X_Offset,Width])
                divider.assign_material("Frame",MATERIAL_FILE,"White")
                
            if self.window_frame == "Window_Frame_Hung.blend":
                divider_1 = self.add_assembly(os.path.join(WINDOW_GLASS,self.window_divider))
                divider_1.set_name(self.window_divider + " 1")
                divider_1.x_loc(value = unit.inch(4.0))
                divider_1.y_loc(value = unit.inch(3.86))
                divider_1.z_loc(value = unit.inch(2.75))
                divider_1.x_dim('Width-INCH(8)',[Width])
                divider_1.z_dim('(Height*0.5)-INCH(5)',[Height])
                divider_1.prompt("Array X","Array_X",[Array_X])
                divider_1.prompt("Array X Offset","Width+Array_X_Offset",[Array_X_Offset,Width])                
                divider_1.assign_material("Frame",MATERIAL_FILE,"White")
                
                divider_2 = self.add_assembly(os.path.join(WINDOW_GLASS,self.window_divider))
                divider_2.set_name(self.window_divider + " 2")
                divider_2.x_loc(value = unit.inch(3))
                divider_2.y_loc(value = unit.inch(3))
                divider_2.z_loc('Height*0.5',[Height])
                divider_2.x_dim('Width-INCH(6)',[Width])
                divider_2.z_dim('(Height*0.5)-INCH(3)',[Height])         
                divider_2.prompt("Array X","Array_X",[Array_X])
                divider_2.prompt("Array X Offset","Width+Array_X_Offset",[Array_X_Offset,Width])   
                divider_2.assign_material("Frame",MATERIAL_FILE,"White")                     
            
            if self.window_frame == "Window_Frame_Sliding.blend":
                divider_1 = self.add_assembly(os.path.join(WINDOW_GLASS,self.window_divider))
                divider_1.set_name(self.window_divider + " 1")
                divider_1.x_loc(value = unit.inch(3.5))
                divider_1.y_loc(value = unit.inch(3.86))
                divider_1.z_loc(value = unit.inch(2))
                divider_1.x_dim('(Width*0.5)-INCH(4)',[Width])
                divider_1.z_dim('Height-INCH(5.5)',[Height])
                divider_1.prompt("Array X","Array_X",[Array_X])
                divider_1.prompt("Array X Offset","Width+Array_X_Offset",[Array_X_Offset,Width])    
                divider_1.assign_material("Frame",MATERIAL_FILE,"White")             
                
                divider_2 = self.add_assembly(os.path.join(WINDOW_GLASS,self.window_divider))
                divider_2.set_name(self.window_divider + " 2")
                divider_2.x_loc('(Width*0.5)+INCH(0.75)',[Width])
                divider_2.y_loc(value = unit.inch(3))
                divider_2.z_loc(value = unit.inch(1.5))
                divider_2.x_dim('(Width*0.5)-INCH(3.25)',[Width])
                divider_2.z_dim('Height-INCH(4)',[Height]) 
                divider_2.prompt("Array X","Array_X",[Array_X])
                divider_2.prompt("Array X Offset","Width+Array_X_Offset",[Array_X_Offset,Width]) 
                divider_2.assign_material("Frame",MATERIAL_FILE,"White")  
                
            if self.window_frame == "Window_Frame_Triple.blend":
                divider = self.add_assembly(os.path.join(WINDOW_GLASS,self.window_divider))
                divider.set_name(self.window_divider + " 1")
                divider.x_loc(value = unit.inch(15))
                divider.y_loc(value = unit.inch(3))
                divider.z_loc(value = unit.inch(1.5))
                divider.x_dim('Width-INCH(30)',[Width])
                divider.z_dim('Height-INCH(13.5)',[Height])   
                divider.prompt("Array X","Array_X",[Array_X])
                divider.prompt("Array X Offset","Width+Array_X_Offset",[Array_X_Offset,Width])                                    
                divider.assign_material("Frame",MATERIAL_FILE,"White")

        
class PRODUCT_Window_Fixed(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Fixed Window"
        self.width = DEFAULT_WIDTH
        self.height = DEFAULT_HEIGHT
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Fixed.blend"
        self.window_divider = ""
        self.window_blinds = ""
        
class PRODUCT_Window_Fixed_4_Lites(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Fixed Window 4 Lites" 
        self.width = DEFAULT_WIDTH
        self.height = DEFAULT_HEIGHT
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Fixed.blend"
        self.window_divider = "Window_Divider_4_Lites.blend"
        self.window_blinds = ""        
        
class PRODUCT_Window_Fixed_Marginal_Border(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Fixed Window Marginal Borders" 
        self.width = DEFAULT_WIDTH
        self.height = DEFAULT_HEIGHT
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Fixed.blend"
        self.window_divider = "Window_Divider_Border.blend"
        self.window_blinds = ""          
        
class PRODUCT_Window_Fixed_Georgian(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Fixed Window Georgian" 
        self.width = DEFAULT_WIDTH
        self.height = DEFAULT_HEIGHT
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Fixed.blend"
        self.window_divider = "Window_Divider_Georgian.blend"
        self.window_blinds = ""             
        
class PRODUCT_Window_Hung(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Hung Window"
        self.width = DEFAULT_WIDTH
        self.height = unit.inch(48)
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Hung.blend"
        self.window_divider = ""
        self.window_blinds = ""        
        
class PRODUCT_Window_Hung_4_Lites(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Hung Window 4 Lites"
        self.width = DEFAULT_WIDTH
        self.height = unit.inch(48)
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Hung.blend"
        self.window_divider = "Window_Divider_4_Lites.blend"
        self.window_blinds = ""   
        
class PRODUCT_Window_Hung_Marginal_Border(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Hung Window Marginal Borders"
        self.width = DEFAULT_WIDTH
        self.height = unit.inch(48)
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Hung.blend"
        self.window_divider = "Window_Divider_Border.blend"
        self.window_blinds = ""              
        
class PRODUCT_Window_Hung_Georgian(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Hung Window Georgian"
        self.width = DEFAULT_WIDTH
        self.height = unit.inch(48)
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Hung.blend"
        self.window_divider = "Window_Divider_Georgian.blend"
        self.window_blinds = ""        

class PRODUCT_Window_Sliding(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Sliding Window"
        self.width = unit.inch(64)
        self.height = DEFAULT_HEIGHT
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Sliding.blend"
        self.window_divider = ""
        self.window_blinds = ""  
        
class PRODUCT_Window_Sliding_4_Lites(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Sliding Window 4 Lites"
        self.width = unit.inch(64)
        self.height = DEFAULT_HEIGHT
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Sliding.blend"
        self.window_divider = "Window_Divider_4_Lites.blend"
        self.window_blinds = ""          
        
class PRODUCT_Window_Sliding_Marginal_Border(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Sliding Window Marginal Borders"
        self.width = unit.inch(64)
        self.height = DEFAULT_HEIGHT
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Sliding.blend"
        self.window_divider = "Window_Divider_Border.blend"
        self.window_blinds = ""            
        
class PRODUCT_Window_Sliding_Georgian(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Sliding Window Georgian"
        self.width = unit.inch(64)
        self.height = DEFAULT_HEIGHT
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Sliding.blend"
        self.window_divider = "Window_Divider_Georgian.blend"
        self.window_blinds = ""          

class PRODUCT_Window_Triple(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Triple Window"
        self.width = unit.inch(64)
        self.height = unit.inch(48)
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Triple.blend"
        self.window_divider = ""
        self.window_blinds = "" 
        
class PRODUCT_Window_Triple_4_Lites(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Triple Window 4 Lites"
        self.width = unit.inch(64)
        self.height = unit.inch(48)
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Triple.blend"
        self.window_divider = "Window_Divider_4_Lites.blend"
        self.window_blinds = ""     
        
class PRODUCT_Window_Triple_Marginal_Border(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Triple Window Marginal Borders"
        self.width = unit.inch(64)
        self.height = unit.inch(48)
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Triple.blend"
        self.window_divider = "Window_Divider_Border.blend"
        self.window_blinds = ""    
        
class PRODUCT_Window_Triple_Georgian(Window):
    
    def __init__(self):
        self.category_name = "Windows"
        self.assembly_name = "Triple Window Georgian"
        self.width = unit.inch(64)
        self.height = unit.inch(48)
        self.depth = DEFAULT_DEPTH
        self.height_above_floor = HEIGHT_ABOVE_FLOOR
        
        self.window_frame = "Window_Frame_Triple.blend"
        self.window_divider = "Window_Divider_Georgian.blend"
        self.window_blinds = ""                
        
class PROMPTS_Window_Prompts(bpy.types.Operator):
    bl_idname = "cabinetlib.window_prompts"
    bl_label = "Window Prompts" 
    bl_options = {'UNDO'}
    
    object_name = bpy.props.StringProperty(name="Object Name")
    
    product = None
    
    width = bpy.props.FloatProperty(name="Width",unit='LENGTH',precision=4)
    height = bpy.props.FloatProperty(name="Height",unit='LENGTH',precision=4)
    depth = bpy.props.FloatProperty(name="Depth",unit='LENGTH',precision=4)

    x_loc = bpy.props.FloatProperty(name="X Location",unit='LENGTH',precision=4)

    base_point = bpy.props.EnumProperty(name="Main Tabs",
                                        items=[('LEFT',"Left",'Left'),
                                               ('CENTER',"Center",'Center'),
                                               ('RIGHT',"Right",'Right')],
                                        default = 'LEFT')

    array_x = bpy.props.IntProperty(name="Array X",min=0,)
    
    array_x_offset = bpy.props.FloatProperty(name="Array X Offset",unit='LENGTH',precision=4)
    
    array_x_prompt = None
    
    array_x_offset_prompt = None
    
    start_x = 0
    start_width = 0
    
    @classmethod
    def poll(cls, context):
        return True

    def check(self, context):
        self.product.obj_x.location.x = self.width
        
        if self.base_point == 'LEFT':
            self.product.obj_bp.location.x = self.x_loc
        elif self.base_point == 'CENTER':
            self.product.obj_bp.location.x = self.x_loc - (self.product.obj_x.location.x - self.start_width)/2
        else:
            self.product.obj_bp.location.x = self.x_loc - (self.product.obj_x.location.x - self.start_width)
        
        if self.product.obj_bp.mv.mirror_y:
            self.product.obj_y.location.y = -self.depth
        else:
            self.product.obj_y.location.y = self.depth
         
        if self.product.obj_bp.mv.mirror_z:
            self.product.obj_z.location.z = -self.height
        else:
            self.product.obj_z.location.z = self.height    
            
        if self.array_x_prompt:
            self.array_x_prompt.set_value(self.array_x)
            
        if self.array_x_offset_prompt:
            self.array_x_offset_prompt.set_value(self.array_x_offset)                    
             
        self.product.obj_bp.location = self.product.obj_bp.location
        self.product.obj_bp.location = self.product.obj_bp.location
        
        return True

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self,context,event):
        obj = bpy.data.objects[self.object_name]
        obj_product_bp = utils.get_bp(obj,'PRODUCT')
        self.product = fd_types.Assembly(obj_product_bp)
        if self.product.obj_bp:
            self.depth = math.fabs(self.product.obj_y.location.y)
            self.height = math.fabs(self.product.obj_z.location.z)
            self.width = math.fabs(self.product.obj_x.location.x)
            
            self.start_x = self.product.obj_bp.location.x
            self.x_loc = self.product.obj_bp.location.x
            self.start_width = math.fabs(self.product.obj_x.location.x)
            
            self.array_x_prompt = self.product.get_prompt("Array X")
            self.array_x = self.array_x_prompt.value()
            
            self.array_x_offset_prompt = self.product.get_prompt("Array X Offset")
            self.array_x_offset = self.array_x_offset_prompt.value()          
                
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=480)

    def draw_product_size(self,layout):
        row = layout.row()
        box = row.box()
        col = box.column(align=True)

        row1 = col.row(align=True)
        if self.object_has_driver(self.product.obj_x):
            row1.label('Width: ' + str(unit.meter_to_active_unit(math.fabs(self.product.obj_x.location.x))))
        else:
            row1.label('Width:')
            row1.prop(self,'width',text="")
            row1.prop(self.product.obj_x,'hide',text="")
        
        row1 = col.row(align=True)
        if self.object_has_driver(self.product.obj_z):
            row1.label('Height: ' + str(unit.meter_to_active_unit(math.fabs(self.product.obj_z.location.z))))
        else:
            row1.label('Height:')
            row1.prop(self,'height',text="")
            row1.prop(self.product.obj_z,'hide',text="")
        
        row1 = col.row(align=True)
        if self.object_has_driver(self.product.obj_y):
            row1.label('Depth: ' + str(unit.meter_to_active_unit(math.fabs(self.product.obj_y.location.y))))
        else:
            row1.label('Depth:')
            row1.prop(self,'depth',text="")
            row1.prop(self.product.obj_y,'hide',text="")
            
    def object_has_driver(self,obj):
        if obj.animation_data:
            if len(obj.animation_data.drivers) > 0:
                return True
            
    def draw_product_prompts(self,layout):

        if "Main Options" in self.product.obj_bp.mv.PromptPage.COL_MainTab:
            array_x = self.product.get_prompt("Array X")
            array_x_offset = self.product.get_prompt("Array X Offset")
            
            box = layout.box()
            box.label("Main Options:")
            
            col = box.column()
            row = col.row(align=True)
            row.label("Array X:")
            row.prop(self,'array_x',text="",)   
            row = col.row(align=True)                
            row.label("Array X Offset:")
            row.prop(self, 'array_x_offset',text="")
    
    def draw_product_placment(self,layout):
        box = layout.box()
        col = box.column()
        row = col.row(align=True)
        row.label('Location X:')
        row.prop(self,'x_loc',text="")
        row = col.row(align=True)
        row.label('Location Z:')        
        row.prop(self.product.obj_bp,'location',index=2,text="")

    def draw(self, context):
        layout = self.layout
        if self.product.obj_bp:
            if self.product.obj_bp.name in context.scene.objects:
                box = layout.box()
                
                split = box.split(percentage=.8)
                split.label(self.product.obj_bp.mv.name_object,icon='LATTICE_DATA')
                row = box.row()
                row.label("Set Base Point:")
                row.prop(self,'base_point',expand=True)
                self.draw_product_size(box)
                self.draw_product_placment(box)    
                self.draw_product_prompts(box)    
        
def register():
    bpy.utils.register_class(PROMPTS_Window_Prompts)