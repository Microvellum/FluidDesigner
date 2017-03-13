"""
Microvellum 
Appliances 
Stores all of the Logic, Product, and Insert Class definitions for appliances
"""

import os
from mv import fd_types, unit
from . import appliance_properties
from . import cabinet_countertops

MATERIAL_FILE = os.path.join(os.path.dirname(__file__),"materials","materials.blend")

def get_file_name(path):
    file_name = os.path.basename(path)
    return os.path.splitext(file_name)[0]

class Parametric_Wall_Appliance(fd_types.Assembly):
    
    library_name = appliance_properties.LIBRARY_FOLDER_NAME
    type_assembly = "PRODUCT"
    
    """ Path to blend file that contains a group of the appliance """
    appliance_path = ""
    
    """ Set to True if you want to add a countertop to this appliance """
    add_countertop = False
    
    def draw(self):
        self.create_assembly()
        dim_x = self.get_var("dim_x")
        dim_z = self.get_var("dim_z")
        dim_y = self.get_var("dim_y")
        assembly = self.add_assembly(file_path = self.appliance_path)
        assembly.set_name(get_file_name(self.appliance_path))
        assembly.x_dim('dim_x',[dim_x])
        assembly.y_dim('dim_y',[dim_y])
        assembly.z_dim('dim_z',[dim_z])
        assembly.assign_material("Chrome",MATERIAL_FILE,"Chrome")
        assembly.assign_material("Stainless Steel",MATERIAL_FILE,"Stainless Steel")
        assembly.assign_material("Black Anodized Metal",MATERIAL_FILE,"Black Anodized Metal")
        
        if self.add_countertop:
            self.add_tab(name="Counter Top Options",tab_type='VISIBLE')
            self.add_prompt(name="Countertop Overhang Front",prompt_type='DISTANCE',value=unit.inch(1),tab_index=0)
            self.add_prompt(name="Countertop Overhang Back",prompt_type='DISTANCE',value=unit.inch(0),tab_index=0)
            self.add_prompt(name="Countertop Overhang Left",prompt_type='DISTANCE',value=unit.inch(0),tab_index=0)
            self.add_prompt(name="Countertop Overhang Right",prompt_type='DISTANCE',value=unit.inch(0),tab_index=0)
            Countertop_Overhang_Front = self.get_var('Countertop Overhang Front')
            Countertop_Overhang_Left = self.get_var('Countertop Overhang Left')
            Countertop_Overhang_Right = self.get_var('Countertop Overhang Right')
            Countertop_Overhang_Back = self.get_var('Countertop Overhang Back')
 
            ctop = cabinet_countertops.Straight_Countertop()
            ctop.draw()
            ctop.obj_bp.mv.type_group = 'INSERT'
            ctop.obj_bp.parent = self.obj_bp
            ctop.x_loc('-Countertop_Overhang_Left',[Countertop_Overhang_Left])
            ctop.y_loc('Countertop_Overhang_Back',[Countertop_Overhang_Back])
            ctop.z_loc('dim_z',[dim_z])
            ctop.x_rot(value = 0)
            ctop.y_rot(value = 0)
            ctop.z_rot(value = 0)
            ctop.x_dim('dim_x+Countertop_Overhang_Left+Countertop_Overhang_Right',[dim_x,Countertop_Overhang_Left,Countertop_Overhang_Right])
            ctop.y_dim('dim_y-Countertop_Overhang_Front-Countertop_Overhang_Back',[dim_y,Countertop_Overhang_Front,Countertop_Overhang_Back])
            ctop.z_dim(value = unit.inch(4))        
        
class Static_Wall_Appliance(fd_types.Assembly):
    
    library_name = appliance_properties.LIBRARY_FOLDER_NAME
    type_assembly = "PRODUCT"
    
    """ Path to blend file that contains a group of the appliance """
    appliance_path = ""
    
    """ Set to True if you want to add a countertop to this appliance """
    add_countertop = False
    
    def draw(self):
        self.create_assembly()
        assembly = self.add_assembly(file_path = self.appliance_path)
        assembly.set_name(get_file_name(self.appliance_path))
        self.width = assembly.obj_x.location.x
        self.height = assembly.obj_z.location.z
        self.depth = assembly.obj_y.location.y
        assembly.assign_material("Chrome",MATERIAL_FILE,"Chrome")
        assembly.assign_material("Stainless Steel",MATERIAL_FILE,"Stainless Steel")
        assembly.assign_material("Black Anodized Metal",MATERIAL_FILE,"Black Anodized Metal")
        
        dim_x = self.get_var("dim_x")
        dim_z = self.get_var("dim_z")
        dim_y = self.get_var("dim_y")        
        
        if self.add_countertop:
            self.add_tab(name="Counter Top Options",tab_type='VISIBLE')
            self.add_prompt(name="Countertop Overhang Front",prompt_type='DISTANCE',value=unit.inch(1),tab_index=0)
            self.add_prompt(name="Countertop Overhang Back",prompt_type='DISTANCE',value=unit.inch(0),tab_index=0)
            self.add_prompt(name="Countertop Overhang Left",prompt_type='DISTANCE',value=unit.inch(0),tab_index=0)
            self.add_prompt(name="Countertop Overhang Right",prompt_type='DISTANCE',value=unit.inch(0),tab_index=0)
            Countertop_Overhang_Front = self.get_var('Countertop Overhang Front')
            Countertop_Overhang_Left = self.get_var('Countertop Overhang Left')
            Countertop_Overhang_Right = self.get_var('Countertop Overhang Right')
            Countertop_Overhang_Back = self.get_var('Countertop Overhang Back')
 
            ctop = cabinet_countertops.PRODUCT_Straight_Countertop()
            ctop.draw()
            ctop.obj_bp.mv.type_group = 'INSERT'
            ctop.obj_bp.parent = self.obj_bp
            ctop.x_loc('-Countertop_Overhang_Left',[Countertop_Overhang_Left])
            ctop.y_loc('Countertop_Overhang_Back',[Countertop_Overhang_Back])
            ctop.z_loc('dim_z',[dim_z])
            ctop.x_rot(value = 0)
            ctop.y_rot(value = 0)
            ctop.z_rot(value = 0)
            ctop.x_dim('dim_x+Countertop_Overhang_Left+Countertop_Overhang_Right',[dim_x,Countertop_Overhang_Left,Countertop_Overhang_Right])
            ctop.y_dim('dim_y-Countertop_Overhang_Front-Countertop_Overhang_Back',[dim_y,Countertop_Overhang_Front,Countertop_Overhang_Back])
            ctop.z_dim(value = unit.inch(4))               
        
class Countertop_Appliance(fd_types.Assembly):
    
    library_name = appliance_properties.LIBRARY_FOLDER_NAME
    type_assembly = "NONE"
    
    """ Path to blend file that contains a group of the appliance """
    appliance_path = ""
    drop_id = appliance_properties.LIBRARY_NAME_SPACE + ".place_countertop_appliance"

    def draw(self):
        self.create_assembly()
        assembly = self.add_assembly(file_path = self.appliance_path)
        assembly.set_name(get_file_name(self.appliance_path))
        self.width = assembly.obj_x.location.x
        self.height = assembly.obj_z.location.z
        self.depth = assembly.obj_y.location.y
        assembly.assign_material("Chrome",MATERIAL_FILE,"Chrome")
        assembly.assign_material("Stainless Steel",MATERIAL_FILE,"Stainless Steel")
        assembly.assign_material("Black Anodized Metal",MATERIAL_FILE,"Black Anodized Metal")        

class Object_Appliance(fd_types.Assembly):
    
    library_name = appliance_properties.LIBRARY_FOLDER_NAME
    type_assembly = "NONE"
    drop_id = appliance_properties.LIBRARY_NAME_SPACE + ".place_appliance_object"
    
    """ Path to blend file that contains a group of the appliance """
    appliance_path = ""

    def draw(self):
        self.create_assembly()
        ass_obj = self.add_object(file_path = self.appliance_path)
        ass_obj.set_name(get_file_name(self.appliance_path))
        self.obj_x.empty_draw_size = unit.inch(1)
        self.obj_y.empty_draw_size = unit.inch(1)
        self.obj_z.empty_draw_size = unit.inch(1)      
        