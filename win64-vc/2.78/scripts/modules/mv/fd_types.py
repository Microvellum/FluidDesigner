'''
Created on Jul 25, 2016

@author: Andrew
'''
import bpy
import bmesh
import math
from bpy_extras import object_utils
from . import unit
from . import utils
import xml.etree.ElementTree as ET

class Assembly():
    """
    Assemblies are collections of objects that work together to create parametric assets. 
    Assemblies can have any number of mesh objects, curves, and empties, but there is a specific structure that is required for Assemblies. 
    Assemblies all have a base point which is typically a mesh object that is made up of a single vertex. Every object in an assembly is parented to this object. 
    The three other objects that are required are empties that control the X, Y, and Z dimension of the assembly.

    ##package_name
    The python package the assembly is stored in. \n
    - Type: String
            
    ##module_name
    The python module the assembly is stored in. \n
    - Type: String
    
    ##library_name
    The library folder name to save assembly to. \n
    - Type: String
            
    ##category_name
    The category folder name to save assembly to. \n
    - Type: String
    
    ##assembly_name
    The assembly name. \n
    - Type: String        
    
    ##property_id
    The Prompt Page Operator ID. This is the bl_id property. \n
    - Type: String
    
    ##plan_draw_id
    The Operator ID that should be called when updating a prebuilt assembly. This is the bl_id property. \n
    - Type: String
    
    ##update_id
    The Operator ID that should be called when dropping this assembly into the scene. This is the bl_id property. \n
    - Type: String
    
    ##drop_id
    The Operator ID that should be called when dropping this assembly into the scene. This is the bl_id property \n
    - Type: String
    
    ##prompts
    The list of prompts to overwrite when creating this assembly (key = prompt name, value = prompt value). \n
    - Type: Dictionary
    
    ##obj_bp
    Base point of the assembly. \n
    - Type: bpy.types.Object
    
    ##obj_x
    X dimension of the assembly. \n
    - Type: bpy.types.Object
    
    ##obj_y
    Y dimension of the assembly. \n
    - Type: bpy.types.Object
    
    ##obj_z
    Z dimension of the assembly. \n
    - Type: bpy.types.Object
    
    ##type_assembly
    Determines if the library assembly is an insert or a product. \n
    - Type: enum_string("PRODUCT", "INSERT") 
    
    ##placement_type
    Used for drag and drop from placement. \n
    - Type: enum_string("","Corner")
    
    ##mirror_z
    Determines if the z dimension is mirrored. \n
    - Type: Bool
    
    ##mirror_y
    Determines if the y dimension is mirrored. Typically used for all cabinets. \n
    - Type: Bool
    
    ##width
    The default x dimension of the assembly. \n
    - Type: Float
    
    ##height
    The default z dimension of the assembly. \n
    - Type: Float
    
    ##depth
    The default y dimension of the assembly. \n
    - Type: Float
    
    ##height_above_floor
    The default z location of the assembly. \n
    - Type: Float
    """
    
    package_name = ""
    module_name = ""    
    library_name = ""
    category_name = ""
    assembly_name = ""    

    property_id = ""
    plan_draw_id = ""
    update_id = ""    
    drop_id = ""        
    
    prompts = {}
    
    obj_bp = None
    obj_x = None
    obj_y = None
    obj_z = None
    
    type_assembly = "PRODUCT"
    placement_type = ""    
    mirror_z = False
    mirror_y = True
    width = 0
    height = 0
    depth = 0
    height_above_floor = 0
    
    def __init__(self,obj_bp=None):
        """ 
        Assembly Constructor. If you want to create an instance of
        an existing Assembly then pass in the base point of the assembly 
        in the obj_bp parameter
        
        **Parameters:**
        
        * **obj_bp** (bpy.types.object, (optional))
        
        **Returns:** None
        """
        if obj_bp:
            self.obj_bp = obj_bp
            for child in obj_bp.children:
                if child.mv.type == 'VPDIMX':
                    self.obj_x = child
                if child.mv.type == 'VPDIMY':
                    self.obj_y = child
                if child.mv.type == 'VPDIMZ':
                    self.obj_z = child
                if self.obj_bp and self.obj_x and self.obj_y and self.obj_z:
                    break

    def create_assembly(self):
        """ 
        This creates the basic structure for an assembly.
        This must be called first when creating an assembly from a script.
        """
        bpy.ops.object.select_all(action='DESELECT')
        obj_parent = utils.create_single_vertex("New Assembly")
        obj_parent.location = (0,0,0)
        obj_parent.mv.type = 'BPASSEMBLY'
        
#         verts = [(0, 0, 0)]
#         mesh = bpy.data.meshes.new("Base Point")
#         bm = bmesh.new()
#         for v_co in verts:
#             bm.verts.new(v_co)
#         bm.to_mesh(mesh)
#         mesh.update()
#         obj_base = object_utils.object_data_add(bpy.context,mesh)
#         obj_parent = obj_base.object
#         obj_parent.location = (0,0,0)
#         obj_parent.mv.type = 'BPASSEMBLY'
#         obj_parent.mv.name_object = 'New Assembly'

        bpy.ops.object.empty_add()
        obj_x = bpy.context.active_object
        obj_x.name = "VPDIMX"
        obj_x.location = (0,0,0)
        obj_x.mv.type = 'VPDIMX'
        obj_x.lock_location[1] = True
        obj_x.lock_location[2] = True
        obj_x.parent = obj_parent

        bpy.ops.object.empty_add()
        obj_y = bpy.context.active_object
        obj_y.name = "VPDIMY"
        obj_y.location = (0,0,0)
        obj_y.mv.type = 'VPDIMY'
        obj_y.lock_location[0] = True
        obj_y.lock_location[2] = True
        obj_y.parent = obj_parent

        bpy.ops.object.empty_add()
        obj_z = bpy.context.active_object
        obj_z.name = "VPDIMZ"
        obj_z.location = (0,0,0)
        obj_z.mv.type = 'VPDIMZ'
        obj_z.lock_location[0] = True
        obj_z.lock_location[1] = True
        obj_z.parent = obj_parent
        
        self.obj_bp = obj_parent
        self.obj_x = obj_x
        self.obj_y = obj_y
        self.obj_z = obj_z
        
        obj_x.location.x = unit.inch(10)
        obj_y.location.y = unit.inch(10)
        obj_z.location.z = unit.inch(10)
        
        self.set_object_names()
    
    def build_cage(self):
        """ 
        This builds the cage object which is a cube that visually represents volume of the assembly.
        """
        if self.obj_bp and self.obj_x and self.obj_y and self.obj_z:
            size = (self.obj_x.location.x, self.obj_y.location.y, self.obj_z.location.z)
            obj_cage = utils.create_cube_mesh('CAGE',size)
            obj_cage.mv.name_object = 'CAGE'
            obj_cage.location = (0,0,0)
            obj_cage.parent = self.obj_bp
            obj_cage.mv.type = 'CAGE'

            utils.create_vertex_group_for_hooks(obj_cage,[2,3,6,7],'X Dimension')
            utils.create_vertex_group_for_hooks(obj_cage,[1,2,5,6],'Y Dimension')
            utils.create_vertex_group_for_hooks(obj_cage,[4,5,6,7],'Z Dimension')
            utils.hook_vertex_group_to_object(obj_cage,'X Dimension',self.obj_x)
            utils.hook_vertex_group_to_object(obj_cage,'Y Dimension',self.obj_y)
            utils.hook_vertex_group_to_object(obj_cage,'Z Dimension',self.obj_z)
            
            obj_cage.draw_type = 'WIRE'
            obj_cage.hide_select = True
            obj_cage.hide_render = True
            obj_cage.lock_location = (True,True,True)
            obj_cage.lock_rotation = (True,True,True)
            obj_cage.cycles_visibility.camera = False
            obj_cage.cycles_visibility.diffuse = False
            obj_cage.cycles_visibility.glossy = False
            obj_cage.cycles_visibility.transmission = False
            obj_cage.cycles_visibility.shadow = False
            return obj_cage

    def add_empty(self):
        """ 
        Creates an empty and returns it as an Assembly_Object
        
        **Returns:** fd_types.Assembly_Object
        """
        bpy.ops.object.empty_add()
        obj_empty = bpy.context.active_object
        obj_empty.parent = self.obj_bp
        empty = Assembly_Object(obj_empty)
        return empty

    def add_opening(self):
        """ 
        Creates and adds an empty opening to this assembly and returns it as an Assembly.
                               
        **Returns:** fd_types.Assembly
        """
        opening = Assembly()
        opening.create_assembly()
        opening.obj_bp.parent = self.obj_bp
        opening.obj_bp.mv.type_group = 'OPENING'
        opening.obj_bp.mv.name_object = "Opening"
        return opening

    def get_cage(self):
        """ 
        This gets the cage for an assembly. If the cage cannot be found
        then a new one is create and returned by the function.
        """
        for child in self.obj_bp.children:
            if child.mv.type == 'CAGE':
                return child
        return self.build_cage()

    def get_var(self,data_path,var_name="",transform_space='WORLD_SPACE',transform_type='LOC_X'):
        """ 
        Returns a variable which can be used in python expressions.
        
        **Parameters:**
        
        * **data_path** (string, (never None)) - Data_path the data path to retrieve the variable from there are reserved names that can be used.
          * 'dim_x' = X Dimension of the Assembly
          * 'dim_y' = Y Dimension of the Assembly
          * 'dim_z' = Z Dimension of the Assembly
          * 'loc_x' = X Location of the Assembly
          * 'loc_y' = Y Location of the Assembly
          * 'loc_z' = Z Location of the Assembly
          * 'rot_x' = X Rotation of the Assembly
          * 'rot_y' = Y Rotation of the Assembly
          * 'rot_z' = Z Rotation of the Assembly
          * 'world_loc_x' = X Location of the Assembly in world space
          * 'world_loc_y' = Y Location of the Assembly in world space
          * 'world_loc_z' = Z Location of the Assembly in world space
        
        * **var_name** (string, (Optional)) - The variable name to use for the returned variable. 
                                              If an empty string is passed in then the data_path is used as the variable name. 
                                              All spaces are replaced with the underscore charcter.
        
        * **transform_space** (ENUM in ('WORLD_SPACE','TRANSFORM_SPACE','LOCAL_SPACE')) - TODO: DELETE, THIS IS BEING PASSED IN THE DATAPATH.
        
        * **transform_type** (ENUM in ()) - TODO: REMOVE PARAMETER. THIS IS BEING PASSED IN THE DATAPATH.
        
        **Returns:** fd_types.Variable
        """
        
        if var_name == "":
            var_name = data_path.replace(" ","_")
        if data_path == 'dim_x':
            return Variable(self.obj_x,'location.x',var_name)
        elif data_path == 'dim_y':
            return Variable(self.obj_y,'location.y',var_name)
        elif data_path == 'dim_z':
            return Variable(self.obj_z,'location.z',var_name)
        elif data_path == 'loc_x':
            return Variable(self.obj_bp,'location.x',var_name)
        elif data_path == 'loc_y':
            return Variable(self.obj_bp,'location.y',var_name)
        elif data_path == 'loc_z':
            return Variable(self.obj_bp,'location.z',var_name)
        elif data_path == 'world_loc_x':
            return Variable(self.obj_bp,'matrix_world[0][3]',var_name,var_type='TRANSFORMS',transform_space=transform_space,transform_type=transform_type)
        elif data_path == 'world_loc_y':
            return Variable(self.obj_bp,'matrix_world[1][3]',var_name,var_type='TRANSFORMS',transform_space=transform_space,transform_type=transform_type)
        elif data_path == 'world_loc_z':
            return Variable(self.obj_bp,'matrix_world[2][3]',var_name,var_type='TRANSFORMS',transform_space=transform_space,transform_type=transform_type)
        elif data_path == 'rot_x':
            return Variable(self.obj_bp,'rotation_euler.x',var_name)
        elif data_path == 'rot_y':
            return Variable(self.obj_bp,'rotation_euler.y',var_name)
        elif data_path == 'rot_z':
            return Variable(self.obj_bp,'rotation_euler.z',var_name)
        else:
            prompt_path = self.get_prompt_data_path(data_path)
            if prompt_path:
                return Variable(self.obj_bp,prompt_path,var_name)
            else:
                return Variable(self.obj_bp,data_path,var_name)
        
    def get_prompt_data_path(self,prompt_name):
        for prompt in self.obj_bp.mv.PromptPage.COL_Prompt:
            if prompt.name == prompt_name:
                if prompt.Type == 'NUMBER':
                    return 'mv.PromptPage.COL_Prompt["' + prompt_name + '"].NumberValue'
                if prompt.Type == 'QUANTITY':
                    return 'mv.PromptPage.COL_Prompt["' + prompt_name + '"].QuantityValue'
                if prompt.Type == 'COMBOBOX':
                    return 'mv.PromptPage.COL_Prompt["' + prompt_name + '"].EnumIndex'
                if prompt.Type == 'CHECKBOX':
                    return 'mv.PromptPage.COL_Prompt["' + prompt_name + '"].CheckBoxValue'
                if prompt.Type == 'TEXT':
                    return 'mv.PromptPage.COL_Prompt["' + prompt_name + '"].TextValue'
                if prompt.Type == 'DISTANCE':
                    return 'mv.PromptPage.COL_Prompt["' + prompt_name + '"].DistanceValue'
                if prompt.Type == 'ANGLE':
                    return 'mv.PromptPage.COL_Prompt["' + prompt_name + '"].AngleValue'
                if prompt.Type == 'PERCENTAGE':
                    return 'mv.PromptPage.COL_Prompt["' + prompt_name + '"].PercentageValue'
                if prompt.Type == 'PRICE':
                    return 'mv.PromptPage.COL_Prompt["' + prompt_name + '"].PriceValue'
        
    def set_material_pointers(self,material_pointer_name,slot_name=""):
        """ 
        Sets every material slot for every mesh to the material_pointer_name.
             
        **Parameters:**
                           
        * **material_pointer_name** (string, (never None)) - Name of the material pointer to assign.
                                           
        * **slot_name** (string, (optional)) - If not "" then the material_pointer_name will be assigned to the slot.
            
        **Returns:** None                                     
        """
        for slot in self.obj_bp.cabinetlib.material_slots:
            if slot_name == "":
                slot.pointer_name = material_pointer_name
            elif slot_name == slot.name:
                slot.pointer_name = material_pointer_name
        for child in self.obj_bp.children:
            if child.type == 'MESH':
                for slot in child.cabinetlib.material_slots:
                    if slot_name == "":
                        slot.pointer_name = material_pointer_name
                    elif slot_name == slot.name:
                        slot.pointer_name = material_pointer_name     
        
    def delete_cage(self):
        list_obj_cage = []
        for child in self.obj_bp.children:
            if child.mv.type == 'CAGE':
                list_obj_cage.append(child)
                
        utils.delete_obj_list(list_obj_cage)

    def replace(self,assembly):
        utils.copy_drivers(self.obj_bp,assembly.obj_bp)
        utils.copy_drivers(self.obj_x,assembly.obj_x)
        utils.copy_drivers(self.obj_y,assembly.obj_y)
        utils.copy_drivers(self.obj_z,assembly.obj_z)
        obj_list = []
        obj_list.append(self.obj_bp)
        for child in self.obj_bp.children:
            obj_list.append(child)
        utils.delete_obj_list(obj_list)

    def set_object_names(self):
        group_name = self.obj_bp.mv.name_object
        self.obj_bp.name = self.obj_bp.mv.type + "." + self.obj_bp.mv.name_object
        for child in self.obj_bp.children:
            if child.mv.type != 'NONE':
                if child.mv.name_object != "":
                    child.name = child.mv.type + "." + group_name + "." + child.mv.name_object
                else:
                    child.name = child.mv.type + "." + group_name
            else:
                if child.mv.name_object != "":
                    child.name = child.type + "." + group_name + "." + child.mv.name_object
                else:
                    child.name = child.type + "." + group_name

    def add_tab(self,name="",tab_type='VISIBLE',calc_type="XDIM"):
        tab = self.obj_bp.mv.PromptPage.COL_MainTab.add()
        tab.name = name
        tab.type = tab_type
        if tab_type == 'CALCULATOR':
            tab.calculator_type = calc_type

    def number_of_visible_prompt_tabs(self):
        number_of_tabs = 0
        for tab in self.obj_bp.mv.PromptPage.COL_MainTab:
            if tab.type == 'VISIBLE':
                number_of_tabs += 1
        return number_of_tabs

    def get_prompt_tabs(self):
        return self.obj_bp.mv.PromptPage.COL_MainTab

    def get_prompt(self,prompt_name):
        if prompt_name in self.obj_bp.mv.PromptPage.COL_Prompt:
            return self.obj_bp.mv.PromptPage.COL_Prompt[prompt_name]

    def add_prompt(self,name="",prompt_type='DISTANCE',value=False,lock=False,tab_index=0,items=[],columns=1,equal=False,export=False):
        prompt = self.obj_bp.mv.PromptPage.COL_Prompt.add()
        prompt.name = name
        prompt.Type = prompt_type
        prompt.lock_value = lock
        prompt.TabIndex = tab_index
        prompt.equal = equal # Only for calculators
        prompt.export = export
        if prompt.Type == 'NUMBER':
            prompt.NumberValue = value
        if prompt.Type == 'QUANTITY':
            prompt.QuantityValue = value
        if prompt.Type == 'COMBOBOX':
            prompt.EnumIndex = value
            for combo_box_item in items:
                enum_item = prompt.COL_EnumItem.add()
                enum_item.name = combo_box_item
            prompt.columns =  columns
        if prompt.Type == 'CHECKBOX':
            prompt.CheckBoxValue = value
        if prompt.Type == 'TEXT':
            prompt.TextValue = value
        if prompt.Type == 'DISTANCE':
            prompt.DistanceValue = value
        if prompt.Type == 'ANGLE':
            prompt.AngleValue = value
        if prompt.Type == 'PERCENTAGE':
            prompt.PercentageValue = value
        if prompt.Type == 'PRICE':
            prompt.PriceValue = value

    def calc_width(self):
        """ 
        Calculates the width of the group based on the rotation. 
        Used to determine collisions for rotated groups.
        """
        return math.cos(self.obj_bp.rotation_euler.z) * self.obj_x.location.x
    
    def calc_depth(self):
        """ 
        Calculates the depth of the group based on the rotation. 
        Used to determine collisions for rotated groups.
        """
        #TODO: This not correct
        if self.obj_bp.rotation_euler.z < 0:
            return math.fabs(self.obj_x.location.x)
        else:
            return math.fabs(self.obj_y.location.y)
    
    def calc_x(self):
        """ 
        Calculates the x location of the group based on the rotation. 
        Used to determine collisions for rotated groups.
        """
        return math.sin(self.obj_bp.rotation_euler.z) * self.obj_y.location.y

    def refresh_hook_modifiers(self):
        for child in self.obj_bp.children:
            if child.type == 'MESH':
                bpy.ops.fd_object.apply_hook_modifiers(object_name=child.name)
                bpy.ops.fd_assembly.connect_meshes_to_hooks_in_assembly(object_name=child.name)

    def has_height_collision(self,group):
        """ 
        Determines if this group will collide in the z with the group that is passed in.
        
        **Parameters:**
                           
        * **group** (bpy.types.Group, (never None)) - Name of the group to test against.
            
        **Returns:** Bool          
        """

        if self.obj_bp.matrix_world[2][3] > self.obj_z.matrix_world[2][3]:
            grp1_z_1 = self.obj_z.matrix_world[2][3]
            grp1_z_2 = self.obj_bp.matrix_world[2][3]
        else:
            grp1_z_1 = self.obj_bp.matrix_world[2][3]
            grp1_z_2 = self.obj_z.matrix_world[2][3]
        
        if group.obj_bp.matrix_world[2][3] > group.obj_z.matrix_world[2][3]:
            grp2_z_1 = group.obj_z.matrix_world[2][3]
            grp2_z_2 = group.obj_bp.matrix_world[2][3]
        else:
            grp2_z_1 = group.obj_bp.matrix_world[2][3]
            grp2_z_2 = group.obj_z.matrix_world[2][3]
    
        if grp1_z_1 >= grp2_z_1 and grp1_z_1 <= grp2_z_2:
            return True
            
        if grp1_z_2 >= grp2_z_1 and grp1_z_2 <= grp2_z_2:
            return True
    
        if grp2_z_1 >= grp1_z_1 and grp2_z_1 <= grp1_z_2:
            return True
            
        if grp2_z_2 >= grp1_z_1 and grp2_z_2 <= grp1_z_2:
            return True

    def has_width_collision(self,group):
        """ 
        Determines if this group will collide in the x with the group that is passed in.
        
        **Parameters:**
                           
        * **group** (bpy.types.Group, (never None)) - Name of the group to test against.
            
        **Returns:** Bool          
        """        
        
        grp1_x_1 = self.obj_bp.matrix_world[0][3]
        grp1_x_2 = self.obj_x.matrix_world[0][3]

        grp2_x_1 = group.obj_bp.matrix_world[0][3]
        grp2_x_2 = group.obj_x.matrix_world[0][3]
        
        if grp1_x_1 >= grp2_x_1 and grp1_x_1 <= grp2_x_2:
            return True
            
        if grp1_x_1 <= grp2_x_1 and grp1_x_2 >= grp2_x_1:
            return True

    def get_adjacent_assembly(self,direction='LEFT'):
        """ 
        Returns an adjacent assembly to this assembly on the same Wall in the direction given.
        
        **Parameters:**
                           
        * **direction** (Enum in ['LEFT', 'RIGHT', 'ABOVE', 'BELOW'], (never None)) - Direction to check.
            
        **Returns:** fd_types.Assembly          
        """        
        
        if self.obj_bp.parent:
            wall = Wall(self.obj_bp.parent)
        list_obj_bp = wall.get_wall_groups()
        list_obj_left_bp = []
        list_obj_right_bp = []
        
        list_obj_bp_z = wall.get_wall_groups(loc_sort='Z')
        list_obj_above_bp = []
        list_obj_below_bp = []
        
        for index, obj_bp in enumerate(list_obj_bp):
            if obj_bp.name == self.obj_bp.name:
                list_obj_left_bp = list_obj_bp[:index]
                list_obj_right_bp = list_obj_bp[index + 1:]
                break
            
        for index, obj_bp in enumerate(list_obj_bp_z):
            if obj_bp.name == self.obj_bp.name:
                list_obj_above_bp = list_obj_bp_z[index + 1:]
                list_obj_below_bp = list_obj_bp_z[:index]
            
        if direction == 'LEFT':
            list_obj_left_bp.reverse()
            for obj_bp in list_obj_left_bp:
                prev_group = Assembly(obj_bp)
                if self.has_height_collision(prev_group):
                    return Assembly(obj_bp)
             
            # CHECK NEXT WALL
    #         if math.radians(wall.obj_bp.rotation_euler.z) < 0:
#             left_wall =  wall.get_connected_wall('LEFT')
#             if left_wall:
#                 rotation_difference = wall.obj_bp.rotation_euler.z - left_wall.obj_bp.rotation_euler.z
#                 if rotation_difference < 0:
#                     list_obj_bp = left_wall.get_wall_groups()
#                     for obj in list_obj_bp:
#                         prev_group = Assembly(obj)
#                         product_x = obj.location.x
#                         product_width = prev_group.calc_width()
#                         x_dist = left_wall.obj_x.location.x  - (product_x + product_width)
#                         product_depth = math.fabs(self.obj_y.location.y)
#                         if x_dist <= product_depth:
#                             if self.has_height_collision(prev_group):
#                                 return prev_group.calc_depth()
         
        if direction == 'RIGHT':
            for obj_bp in list_obj_right_bp:
                next_group = Assembly(obj_bp)
                if self.has_height_collision(next_group):
                    return Assembly(obj_bp)
     
#             # CHECK NEXT WALL
#             right_wall =  wall.get_connected_wall('RIGHT')
#             if right_wall:
#                 rotation_difference = wall.obj_bp.rotation_euler.z - right_wall.obj_bp.rotation_euler.z
#                 if rotation_difference > 0:
#                     list_obj_bp = right_wall.get_wall_groups()
#                     for obj in list_obj_bp:
#                         next_group = Assembly(obj)
#                         product_x = obj.location.x
#                         product_width = next_group.calc_width()
#                         product_depth = math.fabs(self.obj_y.location.y)
#                         if product_x <= product_depth:
#                             if self.has_height_collision(next_group):
#                                 wall_length = wall.obj_x.location.x
#                                 product_depth = next_group.calc_depth()
#                                 return wall_length - product_depth
#     
#             return wall.obj_x.location.x

        if direction == 'ABOVE':
            for obj_bp in list_obj_above_bp:
                above_group = Assembly(obj_bp)
                if self.has_width_collision(above_group):
                    return Assembly(obj_bp)
        
        if direction == 'BELOW':
            for obj_bp in list_obj_below_bp:
                below_group = Assembly(obj_bp)
                if self.has_width_collision(below_group):
                    return Assembly(obj_bp)

    def get_next_wall(self,placement):
        """ 
        This gets the next LEFT or RIGHT wall that this product is connected to. 
        This is used for placing product on corner cabinets that are in corners.
        
        **Parameters:**
                           
        * **placement** (Enum in ['LEFT', 'RIGHT'], (never None)) - Direction to check for next wall.
            
        **Returns:** fd_types.Wall         
        """
        
        if self.obj_bp.parent:
            wall = Wall(self.obj_bp.parent)
            
            if placement == 'LEFT':
                # Check if base the closer than 1" to the left side 
                if self.obj_bp.location.x < unit.inch(1):
                    left_wall = wall.get_connected_wall('LEFT')
                    if left_wall:
                        rotation_difference = wall.obj_bp.rotation_euler.z - left_wall.obj_bp.rotation_euler.z
                        if rotation_difference < 0:
                            return left_wall
    
            if placement == 'RIGHT':
                # Check if base the closer than 1" to the right side 
                if (wall.obj_x.location.x - self.obj_bp.location.x) < unit.inch(1):
                    right_wall = wall.get_connected_wall('RIGHT')
                    if right_wall:
                        rotation_difference = wall.obj_bp.rotation_euler.z - right_wall.obj_bp.rotation_euler.z
                        if rotation_difference > 0:
                            return right_wall

    def get_collision_location(self,direction='LEFT'):
        if self.obj_bp.parent:
            wall = Wall(self.obj_bp.parent)
        list_obj_bp = wall.get_wall_groups()
        list_obj_left_bp = []
        list_obj_right_bp = []
        for index, obj_bp in enumerate(list_obj_bp):
            if obj_bp.name == self.obj_bp.name:
                list_obj_left_bp = list_obj_bp[:index]
                list_obj_right_bp = list_obj_bp[index + 1:]
                break
        if direction == 'LEFT':
            list_obj_left_bp.reverse()
            for obj_bp in list_obj_left_bp:
                prev_group = Assembly(obj_bp)
                if self.has_height_collision(prev_group):
                    return obj_bp.location.x + prev_group.calc_width()
            
            # CHECK NEXT WALL
            left_wall =  wall.get_connected_wall('LEFT')
            if left_wall:
                rotation_difference = math.degrees(wall.obj_bp.rotation_euler.z) - math.degrees(left_wall.obj_bp.rotation_euler.z)
                if rotation_difference < 0 or rotation_difference > 180:
                    list_obj_bp = left_wall.get_wall_groups()
                    for obj in list_obj_bp:
                        prev_group = Assembly(obj)
                        product_x = obj.location.x
                        product_width = prev_group.calc_width()
                        x_dist = left_wall.obj_x.location.x  - (product_x + product_width)
                        product_depth = math.fabs(self.obj_y.location.y)
                        if x_dist <= product_depth:
                            if self.has_height_collision(prev_group):
                                return prev_group.calc_depth()
            return 0
        
        if direction == 'RIGHT':
            for obj_bp in list_obj_right_bp:
                next_group = Assembly(obj_bp)
                if self.has_height_collision(next_group):
                    return obj_bp.location.x - next_group.calc_x()
    
            # CHECK NEXT WALL
            right_wall =  wall.get_connected_wall('RIGHT')
            if right_wall:
                rotation_difference = math.degrees(wall.obj_bp.rotation_euler.z) - math.degrees(right_wall.obj_bp.rotation_euler.z)
                if rotation_difference > 0 or rotation_difference < -180:
                    list_obj_bp = right_wall.get_wall_groups()
                    for obj in list_obj_bp:
                        next_group = Assembly(obj)
                        product_x = obj.location.x
                        product_width = next_group.calc_width()
                        product_depth = math.fabs(self.obj_y.location.y)
                        if product_x <= product_depth:
                            if self.has_height_collision(next_group):
                                wall_length = wall.obj_x.location.x
                                product_depth = next_group.calc_depth()
                                return wall_length - product_depth
    
            return wall.obj_x.location.x

    def set_name(self,name):
        self.obj_bp.mv.name = name
        self.obj_bp.mv.name_object = name

    def set_prompts(self,dict_prompts):
        for key in dict_prompts:
            if key in self.obj_bp.mv.PromptPage.COL_Prompt:
                prompt = self.obj_bp.mv.PromptPage.COL_Prompt[key]
                if prompt.Type == 'NUMBER':
                    prompt.NumberValue = dict_prompts[key]
                if prompt.Type == 'QUANTITY':
                    prompt.QuantityValue = dict_prompts[key]
                if prompt.Type == 'COMBOBOX':
                    prompt.EnumIndex = dict_prompts[key]
                if prompt.Type == 'CHECKBOX':
                    prompt.CheckBoxValue = dict_prompts[key]
                if prompt.Type == 'TEXT':
                    prompt.TextValue = dict_prompts[key]
                if prompt.Type == 'DISTANCE':
                    prompt.DistanceValue = dict_prompts[key]
                if prompt.Type == 'ANGLE':
                    prompt.AngleValue = dict_prompts[key]
                if prompt.Type == 'PERCENTAGE':
                    prompt.PercentageValue = dict_prompts[key]
                if prompt.Type == 'PRICE':
                    prompt.PriceValue = dict_prompts[key]

    def x_loc(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj_bp.location.x = value
        else:
            driver = self.obj_bp.driver_add('location',0)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def y_loc(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj_bp.location.y = value
        else:
            driver = self.obj_bp.driver_add('location',1)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def z_loc(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj_bp.location.z = value
        else:
            driver = self.obj_bp.driver_add('location',2)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def x_rot(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj_bp.rotation_euler.x = math.radians(value)
        else:
            driver = self.obj_bp.driver_add('rotation_euler',0)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def y_rot(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj_bp.rotation_euler.y = math.radians(value)
        else:
            driver = self.obj_bp.driver_add('rotation_euler',1)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
                
    def z_rot(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj_bp.rotation_euler.z = math.radians(value)
        else:
            driver = self.obj_bp.driver_add('rotation_euler',2)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def x_dim(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj_x.location.x = value
        else:
            driver = self.obj_x.driver_add('location',0)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def y_dim(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj_y.location.y = value
        else:
            driver = self.obj_y.driver_add('location',1)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
                          
    def z_dim(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj_z.location.z = value
        else:
            driver = self.obj_z.driver_add('location',2)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
    
    def calculator_deduction(self,expression,driver_vars):
        for tab in self.obj_bp.mv.PromptPage.COL_MainTab:
            if tab.type == 'CALCULATOR':
                data_path = 'mv.PromptPage.COL_MainTab["' + tab.name + '"].calculator_deduction'
                driver = self.obj_bp.driver_add(data_path)
                utils.add_variables_to_driver(driver,driver_vars)
                driver.driver.expression = expression

    def add_assembly(self,file_path):
        """
        Adds an assembly to this assembly and returns it as a fd_types.Part.
        
        **Parameters:**
        
        * **file_path** (String, (never None)) - The folder location to the assembly to add.
        
        **Returns:** fd_types.Part
        """
        with bpy.data.libraries.load(file_path, False, False) as (data_from, data_to):
            for group in data_from.groups:
                data_to.groups = [group]
                break

        for grp in data_to.groups:
            """
            THIS IS A HACK 
            In Blender 2.78a if an object has a reference to a shape key
            the object is not appended it is linked. If an object is linked 
            it can cause errors trying to link duplicate objects into the scene. If a 
            library is found on an object we make objects local. 
            Unfortunetly we have to make 'ALL' local becuase selected objects doens't work
            when the linked object has hide_select turned on. 
            """
            for obj in grp.objects:
                if obj.library:
                    bpy.ops.object.make_local(type='ALL')      
            """
            END HACK
            """
            part = Part(utils.get_assembly_bp(grp.objects[0]))
            part.obj_bp.parent = self.obj_bp
            utils.link_objects_to_scene(part.obj_bp,bpy.context.scene)

            bpy.data.groups.remove(grp,do_unlink=True)
            return part

    def add_object(self,file_path):
        """ 
        Adds an object to this assembly and returns it as a fd_types.Assembly_Object.
        
        **Parameters:**
        
        * **file_path** (tuple[string], (never None)) - The folder location to the object to add, split into strings.
                                                        i.e ("Library Name","Category Name","Object Name")
        
        **Returns:** fd_types.Assembly_Object
        """
        with bpy.data.libraries.load(file_path, False, False) as (data_from, data_to):
            for ob in data_from.objects:
                data_to.objects = [ob]
                break
            
        for obj in data_to.objects:
            utils.link_objects_to_scene(obj,bpy.context.scene)
            obj.parent = self.obj_bp
            obj.select = False
            ass_obj = Assembly_Object(obj)
            return ass_obj

    def prompt(self,prompt_name,expression="",driver_vars=[],value=0):
        if expression == "":
            if prompt_name in self.obj_bp.mv.PromptPage.COL_Prompt:
                prompt = self.obj_bp.mv.PromptPage.COL_Prompt[prompt_name]
                prompt.set_value(value)
        else:
            driver = None
            for prompt in self.obj_bp.mv.PromptPage.COL_Prompt:
                if prompt.name == prompt_name:
                    if prompt.Type == 'NUMBER':
                        data_path = 'mv.PromptPage.COL_Prompt["' + prompt.name + '"].NumberValue'
                        driver = self.obj_bp.driver_add(data_path)
                    if prompt.Type == 'QUANTITY':
                        data_path = 'mv.PromptPage.COL_Prompt["' + prompt.name + '"].QuantityValue'
                        driver = self.obj_bp.driver_add(data_path)
                    if prompt.Type == 'COMBOBOX':
                        data_path = 'mv.PromptPage.COL_Prompt["' + prompt.name + '"].EnumIndex'
                        driver = self.obj_bp.driver_add(data_path)
                    if prompt.Type == 'CHECKBOX':
                        data_path = 'mv.PromptPage.COL_Prompt["' + prompt.name + '"].CheckBoxValue'
                        driver = self.obj_bp.driver_add(data_path)
                    if prompt.Type == 'DISTANCE':
                        data_path = 'mv.PromptPage.COL_Prompt["' + prompt.name + '"].DistanceValue'
                        driver = self.obj_bp.driver_add(data_path)
                    if prompt.Type == 'ANGLE':
                        data_path = 'mv.PromptPage.COL_Prompt["' + prompt.name + '"].AngleValue'
                        driver = self.obj_bp.driver_add(data_path)
                    if prompt.Type == 'PERCENTAGE':
                        data_path = 'mv.PromptPage.COL_Prompt["' + prompt.name + '"].PercentageValue'
                        driver = self.obj_bp.driver_add(data_path)
                    if prompt.Type == 'PRICE':
                        data_path = 'mv.PromptPage.COL_Prompt["' + prompt.name + '"].PriceValue'
                        driver = self.obj_bp.driver_add(data_path)
                    break
            if driver:
                utils.add_variables_to_driver(driver,driver_vars)
                driver.driver.expression = expression
            else:
                print("Error: '" + prompt_name + "' not found while setting expression '" + expression + "'")

    def draw_properties(self,layout):
        ui = bpy.context.scene.mv.ui
        col = layout.column(align=True)
        box = col.box()
        row = box.row(align=True)
        row.prop_enum(ui, "group_tabs", 'INFO', icon='INFO', text="") 
        row.prop_enum(ui, "group_tabs", 'PROMPTS', icon='SETTINGS', text="")    
        row.prop_enum(ui, "group_tabs", 'OBJECTS', icon='GROUP', text="")
        row.prop_enum(ui, "group_tabs", 'DRIVERS', icon='AUTO', text="")
        row.separator()
        row.operator('fd_assembly.delete_selected_assembly',text="",icon='X').object_name = self.obj_bp.name
        if ui.group_tabs == 'INFO':
            box = col.box()
            self.draw_transform(box)
            box.prop(self.obj_bp.mv,'comment')
        if ui.group_tabs == 'PROMPTS':
            box = col.box()
            self.obj_bp.mv.PromptPage.draw_prompt_page(box,allow_edit=True)
        if ui.group_tabs == 'OBJECTS':
            box = col.box()
            self.draw_objects(box)
        if ui.group_tabs == 'DRIVERS':
            box = col.box()
            self.draw_drivers(box)
    
    def draw_transform(self,layout,show_prompts=False):
        row = layout.row()
        row.operator('fd_assembly.rename_assembly',text=self.obj_bp.mv.name_object,icon='GROUP').object_name = self.obj_bp.name
        if show_prompts and self.number_of_visible_prompt_tabs() > 0:
            if self.number_of_visible_prompt_tabs() == 1:
                for index, tab in enumerate(self.obj_bp.mv.PromptPage.COL_MainTab):
                    if tab.type in {'VISIBLE','CALCULATOR'}:
                        props = row.operator("fd_prompts.show_object_prompts",icon='SETTINGS',text="")
                        props.object_bp_name = self.obj_bp.name
                        props.tab_name = tab.name
                        props.index = index
            else:
                row.menu('MENU_active_group_options',text="",icon='SETTINGS')

        row = layout.row(align=True)
        row.label('Width:')
        row.prop(self.obj_x,"lock_location",index=0,text='')
        if self.obj_x.lock_location[0]:
            row.label(str(round(unit.meter_to_active_unit(self.obj_x.location.x),4)))
        else:
            row.prop(self.obj_x,"location",index=0,text="")
            row.prop(self.obj_x,'hide',text="")
        
        row = layout.row(align=True)
        row.label('Depth:')
        row.prop(self.obj_y,"lock_location",index=1,text='')
        if self.obj_y.lock_location[1]:
            row.label(str(round(unit.meter_to_active_unit(self.obj_y.location.y),4)))
        else:
            row.prop(self.obj_y,"location",index=1,text="")
            row.prop(self.obj_y,'hide',text="")
        
        row = layout.row(align=True)
        row.label('Height:')
        row.prop(self.obj_z,"lock_location",index=2,text='')
        if self.obj_z.lock_location[2]:
            row.label(str(round(unit.meter_to_active_unit(self.obj_z.location.z),4)))
        else:
            row.prop(self.obj_z,"location",index=2,text="")
            row.prop(self.obj_z,'hide',text="")
        
        col1 = layout.row()
        if self.obj_bp:
            col2 = col1.split()
            col = col2.column(align=True)
            col.label('Location:')
            
            if self.obj_bp.lock_location[0]:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_location",index=0,text="")
                row.label(str(round(unit.meter_to_active_unit(self.obj_bp.location.x),4)))
            else:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_location",index=0,text="")
                row.prop(self.obj_bp,"location",index=0,text="X")
                
            if self.obj_bp.lock_location[1]:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_location",index=1,text="")
                row.label(str(round(unit.meter_to_active_unit(self.obj_bp.location.y),4)))
            else:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_location",index=1,text="")
                row.prop(self.obj_bp,"location",index=1,text="Y")
                
            if self.obj_bp.lock_location[2]:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_location",index=2,text="")
                row.label(str(round(unit.meter_to_active_unit(self.obj_bp.location.z),4)))
            else:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_location",index=2,text="")
                row.prop(self.obj_bp,"location",index=2,text="Z")
                
            col2 = col1.split()
            col = col2.column(align=True)
            col.label('Rotation:')
            
            if self.obj_bp.lock_rotation[0]:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_rotation",index=0,text="")
                row.label(str(round(math.degrees(self.obj_bp.rotation_euler.x),4)))
            else:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_rotation",index=0,text="")
                row.prop(self.obj_bp,"rotation_euler",index=0,text="X")
                
            if self.obj_bp.lock_rotation[1]:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_rotation",index=1,text="")
                row.label(str(round(math.degrees(self.obj_bp.rotation_euler.y),4)))
            else:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_rotation",index=1,text="")
                row.prop(self.obj_bp,"rotation_euler",index=1,text="Y")
                
            if self.obj_bp.lock_rotation[2]:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_rotation",index=2,text="")
                row.label(str(round(math.degrees(self.obj_bp.rotation_euler.z),4)))
            else:
                row = col.row(align=True)
                row.prop(self.obj_bp,"lock_rotation",index=2,text="")
                row.prop(self.obj_bp,"rotation_euler",index=2,text="Z")
                
    def draw_objects(self,layout):
        scene = bpy.context.scene
        row = layout.row()
        row.prop(self.obj_bp.cabinetlib,'type_mesh')
        row = layout.row()
        row.operator('fd_assembly.load_active_assembly_objects',text="Load Child Objects",icon='FILE_REFRESH').object_name = self.obj_bp.name
        row.menu('MENU_add_assembly_object',text="",icon='ZOOMIN')
        if self.obj_bp.name == scene.mv.active_object_name:
            col = layout.column(align=True)
            col.template_list("FD_UL_objects", " ", scene.mv, "children_objects", scene.mv, "active_object_index")
            if scene.mv.active_object_index <= len(scene.mv.children_objects) + 1:
                box = col.box()
                obj = bpy.data.objects[scene.mv.children_objects[scene.mv.active_object_index].name]
                box.prop(obj.mv,'name_object')
                if obj.type == 'MESH':
                    box.prop(obj.mv,'use_as_bool_obj')
                box.prop(obj.mv,'use_as_mesh_hook')
            
    def draw_drivers(self,layout):
        ui = bpy.context.scene.mv.ui
        row = layout.row(align=True)
        row.operator('fd_driver.turn_on_driver',text="",icon='QUIT').object_name = self.obj_bp.name
        row.prop(ui,'group_driver_tabs',text='')
        box = layout.box()
        
        if ui.group_driver_tabs == 'LOC_X':
            box.prop(self.obj_bp,'location',index=0,text="Location X")
            driver = utils.get_driver(self.obj_bp,'location',0)
            if driver:
                utils.draw_driver_expression(box,driver)
                utils.draw_add_variable_operators(layout,self.obj_bp.name,'location',0)
                utils.draw_driver_variables(layout,driver,self.obj_bp.name)
    
        if ui.group_driver_tabs == 'LOC_Y':
            box.prop(self.obj_bp,'location',index=1,text="Location Y")
            driver = utils.get_driver(self.obj_bp,'location',1)
            if driver:
                utils.draw_driver_expression(box,driver)
                utils.draw_add_variable_operators(layout,self.obj_bp.name,'location',1)
                utils.draw_driver_variables(layout,driver,self.obj_bp.name)
                
        if ui.group_driver_tabs == 'LOC_Z':
            box.prop(self.obj_bp,'location',index=2,text="Location Z")
            driver = utils.get_driver(self.obj_bp,'location',2)
            if driver:
                utils.draw_driver_expression(box,driver)
                utils.draw_add_variable_operators(layout,self.obj_bp.name,'location',2)
                utils.draw_driver_variables(layout,driver,self.obj_bp.name)
                
        if ui.group_driver_tabs == 'ROT_X':
            box.prop(self.obj_bp,'rotation_euler',index=0,text="Rotation X")
            driver = utils.get_driver(self.obj_bp,'rotation_euler',0)
            if driver:
                utils.draw_driver_expression(box,driver)
                utils.draw_add_variable_operators(layout,self.obj_bp.name,'rotation_euler',0)
                utils.draw_driver_variables(layout,driver,self.obj_bp.name)
                
        if ui.group_driver_tabs == 'ROT_Y':
            box.prop(self.obj_bp,'rotation_euler',index=1,text="Rotation Y")
            driver = utils.get_driver(self.obj_bp,'rotation_euler',1)
            if driver:
                utils.draw_driver_expression(box,driver)
                utils.draw_add_variable_operators(layout,self.obj_bp.name,'rotation_euler',1)
                utils.draw_driver_variables(layout,driver,self.obj_bp.name)
    
        if ui.group_driver_tabs == 'ROT_Z':
            box.prop(self.obj_bp,'rotation_euler',index=2,text="Rotation Z")
            driver = utils.get_driver(self.obj_bp,'rotation_euler',2)
            if driver:
                utils.draw_driver_expression(box,driver)
                utils.draw_add_variable_operators(layout,self.obj_bp.name,'rotation_euler',2)
                utils.draw_driver_variables(layout,driver,self.obj_bp.name)
    
        if ui.group_driver_tabs == 'DIM_X':
            box.prop(self.obj_x,'location',index=0,text="Dimension X")
            driver = utils.get_driver(self.obj_x,'location',0)
            if driver:
                utils.draw_driver_expression(box,driver)
                utils.draw_add_variable_operators(layout,self.obj_x.name,'location',0)
                utils.draw_driver_variables(layout,driver,self.obj_x.name)
    
        if ui.group_driver_tabs == 'DIM_Y':
            box.prop(self.obj_y,'location',index=1,text="Dimension Y")
            driver = utils.get_driver(self.obj_y,'location',1)
            if driver:
                utils.draw_driver_expression(box,driver)
                utils.draw_add_variable_operators(layout,self.obj_y.name,'location',1)
                utils.draw_driver_variables(layout,driver,self.obj_y.name)
                        
        if ui.group_driver_tabs == 'DIM_Z':
            box.prop(self.obj_z,'location',index=2,text="Dimension Z")
            driver = utils.get_driver(self.obj_z,'location',2)
            if driver:
                utils.draw_driver_expression(box,driver)
                utils.draw_add_variable_operators(layout,self.obj_z.name,'location',2)
                utils.draw_driver_variables(layout,driver,self.obj_z.name)
                
        if ui.group_driver_tabs == 'PROMPTS':
            if len(self.obj_bp.mv.PromptPage.COL_Prompt) < 1:
                box.label('No Prompts')
            else:
                box.template_list("FD_UL_promptitems"," ", self.obj_bp.mv.PromptPage, "COL_Prompt", self.obj_bp.mv.PromptPage, "PromptIndex",rows=5,type='DEFAULT')
                prompt = self.obj_bp.mv.PromptPage.COL_Prompt[self.obj_bp.mv.PromptPage.PromptIndex]
                
                if prompt.Type == 'DISTANCE':
                    driver = utils.get_driver(self.obj_bp,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].DistanceValue',0)
                    if driver:
                        box.operator('fd_driver.turn_off_driver').object_name = self.obj_bp.name
                        utils.draw_driver_expression(box,driver)
                        utils.draw_add_variable_operators(layout,self.obj_bp.name,'mv.PromptPage.COL_Prompt["' +  prompt.name + '"].DistanceValue',0)
                        utils.draw_driver_variables(layout,driver,self.obj_bp.name)
                        
                if prompt.Type == 'ANGLE':
                    driver = utils.get_driver(self.obj_bp,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].AngleValue',0)
                    if driver:
                        box.operator('fd_driver.turn_off_driver').object_name = self.obj_bp.name
                        utils.draw_driver_expression(box,driver)
                        utils.draw_add_variable_operators(layout,self.obj_bp.name,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].AngleValue',0)
                        utils.draw_driver_variables(layout,driver,self.obj_bp.name)
                        
                if prompt.Type == 'PRICE':
                    driver = utils.get_driver(self.obj_bp,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].PriceValue',0)
                    if driver:
                        box.operator('fd_driver.turn_off_driver').object_name = self.obj_bp.name
                        utils.draw_driver_expression(box,driver)
                        utils.draw_add_variable_operators(layout,self.obj_bp.name,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].PriceValue',0)
                        utils.draw_driver_variables(layout,driver,self.obj_bp.name)
                        
                if prompt.Type == 'PERCENTAGE':
                    driver = utils.get_driver(self.obj_bp,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].PercentageValue',0)
                    if driver:
                        box.operator('fd_driver.turn_off_driver').object_name = self.obj_bp.name
                        utils.draw_driver_expression(box,driver)
                        utils.draw_add_variable_operators(layout,self.obj_bp.name,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].PercentageValue',0)
                        utils.draw_driver_variables(layout,driver,self.obj_bp.name)
                
                if prompt.Type == 'NUMBER':
                    driver = utils.get_driver(self.obj_bp,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].NumberValue',0)
                    if driver:
                        box.operator('fd_driver.turn_off_driver').object_name = self.obj_bp.name
                        utils.draw_driver_expression(box,driver)
                        utils.draw_add_variable_operators(layout,self.obj_bp.name,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].NumberValue',0)
                        utils.draw_driver_variables(layout,driver,self.obj_bp.name)
                        
                if prompt.Type == 'QUANTITY':
                    driver = utils.get_driver(self.obj_bp,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].QuantityValue',0)
                    if driver:
                        box.operator('fd_driver.turn_off_driver').object_name = self.obj_bp.name
                        utils.draw_driver_expression(box,driver)
                        utils.draw_add_variable_operators(layout,self.obj_bp.name,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].QuantityValue',0)
                        utils.draw_driver_variables(layout,driver,self.obj_bp.name)
    
                if prompt.Type == 'COMBOBOX':
                    driver = utils.get_driver(self.obj_bp,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].EnumIndex',0)
                    if driver:
                        box.operator('fd_driver.turn_off_driver').object_name = self.obj_bp.name
                        utils.draw_driver_expression(box,driver)
                        utils.draw_add_variable_operators(layout,self.obj_bp.name,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].EnumIndex',0)
                        utils.draw_driver_variables(layout,driver,self.obj_bp.name)
    
                if prompt.Type == 'CHECKBOX':
                    driver = utils.get_driver(self.obj_bp,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].CheckBoxValue',0)
                    if driver:
                        box.operator('fd_driver.turn_off_driver').object_name = self.obj_bp.name
                        utils.draw_driver_expression(box,driver)
                        utils.draw_add_variable_operators(layout,self.obj_bp.name,'mv.PromptPage.COL_Prompt["' + prompt.name + '"].CheckBoxValue',0)
                        utils.draw_driver_variables(layout,driver,self.obj_bp.name)

    def update(self,obj_bp=None):
        """ 
        Sets the specification group, placement_type, mirror_z, mirror_y, name, product_id,
        height_above_floor, runs the calculators, and sets prompts based on the prompt dictionary property.
        
        **Parameters:**
        
        * **obj_bp** (bpy.types.object, (optional)) - An assembly base point.
        
        **Returns:** None
        """
        if obj_bp:
            self.obj_bp = obj_bp
        for child in self.obj_bp.children:
            if child.mv.type == 'VPDIMX':
                self.obj_x = child
            if child.mv.type == 'VPDIMY':
                self.obj_y = child
            if child.mv.type == 'VPDIMZ':
                self.obj_z = child
                
        default_spec_group = bpy.context.scene.mv.spec_groups[bpy.context.scene.mv.spec_group_index]
        bpy.ops.fd_material.change_product_spec_group(object_name=self.obj_bp.name,spec_group_name=default_spec_group.name)
        if self.assembly_name == "":
            self.set_name(utils.get_product_class_name(self.__class__.__name__))
        else:
            self.set_name(self.assembly_name)
        
        self.obj_bp.mv.type_group = self.type_assembly
        self.obj_bp.mv.placement_type = self.placement_type
        self.obj_bp.mv.mirror_z = self.mirror_z
        self.obj_bp.mv.mirror_y = self.mirror_y
        self.obj_bp.mv.package_name = self.package_name
        self.obj_bp.mv.module_name = self.module_name
        self.obj_bp.mv.class_name = self.__class__.__name__
        self.obj_bp.mv.plan_draw_id = self.plan_draw_id
        self.obj_bp.mv.update_id = self.update_id
        self.obj_bp.mv.drop_id = self.drop_id
        utils.set_property_id(self.obj_bp,self.property_id)
        self.x_dim(value = self.width)
        self.y_dim(value = -self.depth if self.mirror_y else self.depth)
        self.z_dim(value = -self.height if self.mirror_z else self.height)
        self.z_loc(value = self.height_above_floor)
        utils.run_calculators(self.obj_bp)
        self.set_prompts(self.prompts)

class Part(Assembly):
    """
    Part Assembly.
    """
    
    
    def assign_material(self,slot_name,material_path,material_name):
        """
        Sets the every material slot for every mesh that matches the slot_name to the material_pointer_name.
        
        **Parameters:**
        
        * **slot_name** (string, (never None)) - Name of the mv.material_slot to assign material to.
        
        * **material_path** (string, (never None)) - File path to retrieve material from.
        
        * **material_name** (string, (never None)) - Material name.
        
        ***Returns:*** None
        """
        material = None
        
        if material_name in bpy.data.materials:
            material = bpy.data.materials[material_name]
        else:
            with bpy.data.libraries.load(material_path, False, False) as (data_from, data_to):
                for mat in data_from.materials:
                    if mat == material_name:
                        data_to.materials = [mat]
                        break
                    
            for mat in data_to.materials:
                material = mat
            
        for child in self.obj_bp.children:
            for index, slot in enumerate(child.cabinetlib.material_slots):
                if slot.name == slot_name:
                    slot.material_path = material_path
                    slot.item_name = material_name
                    child.material_slots[index].material = material
    
    def material(self,material_pointer_name):
        """ 
        Sets every material slot for every mesh to the material_pointer_name.
        
        **Parameters:**
        
        * **material_pointer_name** (string, (never None)) - Name of the material pointer to assign.
        
        **Returns:** None
        """
        for slot in self.obj_bp.cabinetlib.material_slots:
            slot.pointer_name = material_pointer_name
        for child in self.obj_bp.children:
            if child.type == 'MESH':
                for slot in child.cabinetlib.material_slots:
                    slot.pointer_name = material_pointer_name

    def cutpart(self,cutpart_name):
        """ 
        Assigns every mesh cut part to the cutpart_name.
        
        **Parameters:**
        
        * **cutpart_name** (string, (never None)) - Name of the material pointer to assign.
        
        **Returns:** None
        """
        for child in self.obj_bp.children:
            if child.type == 'MESH' and child.cabinetlib.type_mesh == 'CUTPART':
                child.cabinetlib.cutpart_name = cutpart_name

    def solid_stock(self,solid_stock_name):
        """ 
        Assigns the every mesh solid stock to the solid_stock_name.
        
        **Parameters:**
        
        * **solid_stock_name** (string, (never None)) - Solid stock name to assign to obj.
        
        **Returns:** None
        """        

        for child in self.obj_bp.children:
            if child.type == 'MESH' and child.cabinetlib.type_mesh == 'SOLIDSTOCK':
                child.mv.solid_stock = solid_stock_name

    def edgebanding(self,edgebanding_name,w1=False,l1=False,w2=False,l2=False):
        """ 
        Assigns every mesh cut part to the edgebanding_name.
        
        **Parameters:**
        
        * **edgebanding_name** (string, (never None)) - Name of the edgepart pointer to assign.
        
        * **w1** (bool, (optional, default=False)) - Determines if to edgeband width 1 of the part.
        
        * **w2** (bool, (optional, default=False)) - Determines if to edgeband width 2 of the part.
        
        * **l1** (bool, (optional, default=False)) - Determines if to edgeband length 1 of the part.
        
        * **l2** (bool, (optional, default=False)) - Determines if to edgeband length 2 of the part.
        
        **Returns:** None
        """         

        for child in self.obj_bp.children:
            if child.type == 'MESH' and child.cabinetlib.type_mesh == 'EDGEBANDING':
                child.cabinetlib.edgepart_name = edgebanding_name
            if child.type == 'MESH' and child.cabinetlib.type_mesh == 'CUTPART':
                child.cabinetlib.edgepart_name = edgebanding_name
                if w1:
                    child.mv.edge_w1 = edgebanding_name
                if l1:
                    child.mv.edge_l1 = edgebanding_name
                if w2:
                    child.mv.edge_w2 = edgebanding_name
                if l2:
                    child.mv.edge_l2 = edgebanding_name
                 
    def add_machine_token(self,machining_name,machining_type,machining_face,machining_edge="1"):
        """ Returns:tuple(bpy.types.Object,properties.Machining_Token) - adds a machine token
                                                                         to the first cutpart mesh
                           
            machining_name:string - name of the machining token
                                      
            machining_name:string - type of machining token to add
            
            machining_face:string - face to add the machining token to
            
            machining_edge:string - edge to add the machining token to
        """
        for child in self.obj_bp.children:
            if child.cabinetlib.type_mesh == 'CUTPART':
                token = child.mv.mp.add_machine_token(machining_name ,machining_type,machining_face,machining_edge)
                return child, token
                 
    def get_cutparts(self):
        """ Returns:list of bpy.types.Object - gets all mesh objects that are assigned as cutparts.
        """
        cutparts = []
        for child in self.obj_bp.children:
            if child.type == 'MESH' and child.cabinetlib.type_mesh == 'CUTPART':
                cutparts.append(child)
        return cutparts
    
    def machine_token(self,obj,token,token_property,expression,driver_vars,index=None):
        """ Returns:None - sets a driver for a machine token that is passed in.
        """
        data_path = ""
        for m_token in obj.mv.mp.machine_tokens:
            if m_token == token:
                if index:
                    data_path = 'mv.mp.machine_tokens.["' + token.name + '"].' + token_property + '[' + str(index) + ']'
                else:
                    data_path = 'mv.mp.machine_tokens.["' + token.name + '"].' + token_property
                obj.driver_add(data_path)
                 
        if data_path != "":
            for var in driver_vars:
                if obj.animation_data:
                    for DR in obj.animation_data.drivers:
                        if data_path in DR.data_path:
                            new_var = DR.driver.variables.new()
                            new_var.name = var.var_name
                            new_var.targets[0].data_path = var.data_path
                            new_var.targets[0].id = var.obj
                            DR.driver.expression = expression
                            break
        else:
            print("Error: '" + token.name + "' not found while setting expression '" + expression + "'")

class Wall(Assembly):
    """
    Wall Assembly.
    """
    
    def __init__(self,obj_bp=None):
        if obj_bp:
            self.obj_bp = obj_bp
            for child in obj_bp.children:
                if child.mv.type == 'VPDIMX':
                    self.obj_x = child
                if child.mv.type == 'VPDIMY':
                    self.obj_y = child
                if child.mv.type == 'VPDIMZ':
                    self.obj_z = child
                if self.obj_bp and self.obj_x and self.obj_y and self.obj_z:
                    break

    def create_wall(self):
        self.create_assembly()
        self.obj_bp.mv.type = 'BPWALL'
        self.obj_bp.mv.name_object = 'Wall'
        self.set_object_names()

    def build_wall_mesh(self):
        self.obj_bp.mv.name = "BPWALL.Wall"
        obj_mesh = self.build_cage()
        obj_mesh.mv.is_wall_mesh = True
        obj_mesh.mv.name = 'Wall Mesh'
        obj_mesh.name = "Wall Mesh"
        obj_mesh.mv.type = 'NONE'
        obj_mesh.draw_type = 'TEXTURED'
        obj_mesh.hide_render = False
        obj_mesh.hide_select = False
        obj_mesh.cycles_visibility.camera = True
        obj_mesh.cycles_visibility.diffuse = True
        obj_mesh.cycles_visibility.glossy = True
        obj_mesh.cycles_visibility.transmission = True
        obj_mesh.cycles_visibility.shadow = True
        return obj_mesh
        
    def get_wall_mesh(self):
        for child in self.obj_bp.children:
            if child.type == 'MESH' and child.mv.type == 'NONE' and len(child.data.vertices) != 1:
                return child
    
    #NOT BEING USED DELETE
    def create_wall_group(self):
        wall_group = bpy.data.groups.new(self.obj_bp.name)
        return self.group_children(wall_group,self.obj_bp)
    
    #NOT BEING USED DELETE
    def group_children(self,grp,obj):
        grp.objects.link(obj)   
        for child in obj.children:
            if len(child.children) > 0:
                self.group_children(grp,child)
            else:
                
                if not child.mv.is_wall_mesh:
                    grp.objects.link(child)   
        return grp
        
    def get_wall_groups(self, loc_sort='X'):
        """ This returns a sorted list of all of the groups base points
            parented to the wall
        """
        list_obj_bp = []
        for child in self.obj_bp.children:
            if child.mv.type == 'BPASSEMBLY':
                list_obj_bp.append(child)
        if loc_sort == 'X':
            list_obj_bp.sort(key=lambda obj: obj.location.x, reverse=False)
        if loc_sort == 'Y':
            list_obj_bp.sort(key=lambda obj: obj.location.y, reverse=False)            
        if loc_sort == 'Z':
            list_obj_bp.sort(key=lambda obj: obj.location.z, reverse=False)
        return list_obj_bp
        
    def get_connected_wall(self,direction):
        if direction == 'LEFT':
            for con in self.obj_bp.constraints:
                if con.type == 'COPY_LOCATION':
                    if con.target:
                        return Wall(con.target.parent)
    
        if direction == 'RIGHT':
            for obj in bpy.context.visible_objects:
                if obj.mv.type == 'BPWALL':
                    next_wall = Wall(obj)
                    for con in next_wall.obj_bp.constraints:
                        if con.type == 'COPY_LOCATION':
                            if con.target == self.obj_x:
                                return next_wall
                            
class Assembly_Object():
    
    obj = None
    
    def __init__(self,obj):
        self.obj = obj

    def set_name(self,name):
        self.obj.mv.name = name
        self.obj.mv.name_object = name

    def get_var(self,data_path,var_name="",transform_space='WORLD_SPACE',transform_type='LOC_X'):
        """ This returns a variable which can be used in python expressions
            arg1: data_path the data path to retrieve the variable from there are 
                  reserved names that can be used.
                  dim_x = X Dimension of the Assembly
                  dim_y = Y Dimension of the Assembly
                  dim_z = Z Dimension of the Assembly
                  loc_x = X Location of the Assembly
                  loc_y = Y Location of the Assembly
                  loc_z = Z Location of the Assembly
                  rot_x = X Rotation of the Assembly
                  rot_y = Y Rotation of the Assembly
                  rot_z = Z Rotation of the Assembly
                  world_loc_x = X Location of the Assembly in world space
                  world_loc_y = Y Location of the Assembly in world space
                  world_loc_z = Z Location of the Assembly in world space
            arg2: var_name the variable name to use for the returned variable. If 
                  an empty string is passed in then the data_path is used as the
                  variable name. all spaces are replaced with the underscore charcter
            arg3: (TODO: THIS IS ONLY USED BECAUSE WE CANNOT USE 'matrix_world[X][X]' in data_path) transform_space ENUM in ('WORLD_SPACE','TRANSFORM_SPACE','LOCAL_SPACE')
                  only used if calculating world space
            arg4: (TODO: THIS IS ONLY USED BECAUSE WE CANNOT USE 'matrix_world[X][X]' in data_path)
        """
        if var_name == "":
            var_name = data_path.replace(" ","_")
        if data_path == 'dim_x':
            return Variable(self.obj,'dimensions.x',var_name)
        elif data_path == 'dim_y':
            return Variable(self.obj,'dimensions.y',var_name)
        elif data_path == 'dim_z':
            return Variable(self.obj,'dimensions.z',var_name)
        elif data_path == 'loc_x':
            return Variable(self.obj,'location.x',var_name)
        elif data_path == 'loc_y':
            return Variable(self.obj,'location.y',var_name)
        elif data_path == 'loc_z':
            return Variable(self.obj,'location.z',var_name)
        elif data_path == 'world_loc_x':
            return Variable(self.obj,'matrix_world[0][3]',var_name,var_type='TRANSFORMS',transform_space=transform_space,transform_type=transform_type)
        elif data_path == 'world_loc_y':
            return Variable(self.obj,'matrix_world[1][3]',var_name,var_type='TRANSFORMS',transform_space=transform_space,transform_type=transform_type)
        elif data_path == 'world_loc_z':
            return Variable(self.obj,'matrix_world[2][3]',var_name,var_type='TRANSFORMS',transform_space=transform_space,transform_type=transform_type)
        elif data_path == 'rot_x':
            return Variable(self.obj,'rotation_euler.x',var_name)
        elif data_path == 'rot_y':
            return Variable(self.obj,'rotation_euler.y',var_name)
        elif data_path == 'rot_z':
            return Variable(self.obj,'rotation_euler.z',var_name)
        else:
            print("Prompt Variable not available on Assembly_Object")

    def x_loc(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj.location.x = value
        else:
            driver = self.obj.driver_add('location',0)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def y_loc(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj.location.y = value
        else:
            driver = self.obj.driver_add('location',1)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def z_loc(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj.location.z = value
        else:
            driver = self.obj.driver_add('location',2)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
            
    def x_rot(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj.rotation_euler.x = math.radians(value)
        else:
            driver = self.obj.driver_add('rotation_euler',0)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def y_rot(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj.rotation_euler.y = math.radians(value)
        else:
            driver = self.obj.driver_add('rotation_euler',1)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
                
    def z_rot(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj.rotation_euler.z = math.radians(value)
        else:
            driver = self.obj.driver_add('rotation_euler',2)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
            
    def x_dim(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj.location.x = value
        else:
            driver = self.obj.driver_add('dimensions',0)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def y_dim(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj.location.y = value
        else:
            driver = self.obj.driver_add('dimensions',1)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression

    def z_dim(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.obj.location.z = value
        else:
            driver = self.obj.driver_add('dimensions',2)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
            
    def hide(self,expression="",driver_vars=[],value=False):
        if expression == "":
            self.obj.hide = value
            self.obj.hide_render = value
        else:
            driver = self.obj.driver_add('hide')
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
            
            driver = self.obj.driver_add('hide_render')
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
            
    def material(self,material_pointer_name):
        for slot in self.obj.cabinetlib.material_slots:
            slot.pointer_name = material_pointer_name

    def assign_material(self,slot_name,material_path,material_name):
        """ Returns:None - sets the every material slot that matches the slot_name
                           to the material_pointer_name

            slot_name:string - name of the mv.material_slot to assign material to
          
            material_path:string - file path to retrieve material from
            
            material_name:string - material name to retrieve from the file specified in the material path
        """
        material = None
        
        if material_name in bpy.data.materials:
            material = bpy.data.materials[material_name]
        else:
            with bpy.data.libraries.load(material_path, False, False) as (data_from, data_to):
                for mat in data_from.materials:
                    if mat == material_name:
                        data_to.materials = [mat]
                        break
                    
            for mat in data_to.materials:
                material = mat

        for index, slot in enumerate(self.obj.cabinetlib.material_slots):
            if slot.name == slot_name:
                slot.material_path = material_path
                slot.item_name = material_name
                self.obj.material_slots[index].material = material

class Material_Pointer():
    
    name = ""
    library_name = ""
    category_name = ""
    item_name = ""
    
    def __init__(self,library_path):
        self.library_name = library_path[0]
        self.item_name = library_path[-1]
        if len(library_path) > 2:
            self.category_name = library_path[1]


class Cutpart_Pointer():
    
    name = ""
    thickness = 0.0
    core = ""
    top = ""
    bottom = ""
    mv_pointer_name = ""
    
    def __init__(self,thickness,core,top,bottom,mv_pointer_name = ""):
        self.thickness = thickness
        self.core = core
        self.top = top
        self.bottom = bottom
        self.mv_pointer_name = mv_pointer_name


class Edgepart_Pointer():
    
    name = ""
    thickness = 0.0
    material = ""
    mv_pointer_name = ""
    
    def __init__(self,thickness,material,mv_pointer_name = ""):
        self.thickness = thickness
        self.material = material
        self.mv_pointer_name = mv_pointer_name

class Variable():
    
    var_name = ""
    obj = None
    data_path = ""
    var_type = ""
    transform_space = 'WORLD_SPACE'
    transform_type = 'LOC_X'
    
    def __init__(self,obj,data_path,var_name,var_type='SINGLE_PROP',transform_space='WORLD_SPACE',transform_type='LOC_X'):
        self.obj = obj
        self.data_path = data_path
        self.var_name = var_name
        self.var_type = var_type
        if var_type == 'TRANSFORMS':
            self.transform_space = transform_space
            self.transform_type = transform_type

class Dimension():
    
    anchor = None
    end_point = None
    label = ""   
    opengl_dim = None
    
    def __init__(self):
        scene = bpy.context.scene
        self.draw()
 
        self.opengl_dim = self.anchor.mv.opengl_dim
        self.opengl_dim.glpointa = 0
        self.opengl_dim.glpointb = 0  
        self.opengl_dim.gl_label = scene.mv.opengl_dim.gl_label
        self.opengl_dim.gl_font_size = scene.mv.opengl_dim.gl_font_size     
    
    def draw(self):
        context = bpy.context
        bpy.ops.object.add(type='EMPTY')
        self.anchor = context.object
        self.anchor.location = (0,0,0)
        self.anchor.mv.type = 'VISDIM_A'
        self.anchor.mv.name_object = "Anchor"
        self.anchor.hide = True
        
        bpy.ops.object.add(type='EMPTY')
        self.end_point = context.object
        self.end_point.location = (0,0,0)
        self.end_point.mv.type = 'VISDIM_B'
        self.end_point.mv.name_object = "End Point"
        self.end_point.parent = self.anchor
        self.end_point.hide = True
    
    def parent(self, obj_bp):
        self.anchor.parent = obj_bp
    
    def start_x(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.anchor.location.x = value
        else:
            driver = self.anchor.driver_add('location',0)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression        
    
    def start_y(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.anchor.location.y = value
        else:
            driver = self.anchor.driver_add('location',1)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression 
    
    def start_z(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.anchor.location.z = value
        else:
            driver = self.anchor.driver_add('location',2)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression 
    
    def end_x(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.end_point.location.x = value
        else:
            driver = self.end_point.driver_add('location',0)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression 
    
    def end_y(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.end_point.location.y = value
        else:
            driver = self.end_point.driver_add('location',1)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression 
    
    def end_z(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.end_point.location.z = value
        else:
            driver = self.end_point.driver_add('location',2)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression 
    
    def hide(self,expression="",driver_vars=[],value=True):
        if expression == "":
            self.opengl_dim.hide = value
        else:
            driver = self.anchor.driver_add('mv.opengl_dim.hide')
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression 
            
    def set_color(self,expression="",driver_vars=[],value=0):  
        if expression == "":
            self.opengl_dim.gl_color = value
        else:
            driver = self.anchor.driver_add('mv.opengl_dim.gl_color')
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression                      
            
    def set_label(self, text, new_line=False):
        if new_line:
            self.opengl_dim.gl_label = " | " + text
        else:
            self.opengl_dim.gl_label = text
    
    def set_text_offset_x(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.opengl_dim.gl_text_x = value
        else:
            driver = self.anchor.driver_add('cabinetlib.opengl_dim.gl_text_x')
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression 
    
    def set_text_offset_y(self,expression="",driver_vars=[],value=0):
        if expression == "":
            self.opengl_dim.gl_text_y = value
        else:
            driver = self.anchor.driver_add('cabinetlib.opengl_dim.gl_text_y')
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression            
    
class MV_XML():
    
    tree = None
    
    def __init__(self):
        pass
    
    def create_tree(self):
        root = ET.Element('Root',{'Application':'Microvellum','ApplicationVersion':'7.0'})
        self.tree = ET.ElementTree(root)
        return root
    
    def add_element(self,root,elm_name,attrib_name=""):
        if attrib_name == "":
            elm = ET.Element(elm_name)
        else:
            elm = ET.Element(elm_name,{'Name':attrib_name})
        root.append(elm)
        return elm
    
    def add_element_with_text(self,root,elm_name,text):
        field = ET.Element(elm_name)
        field.text = text
        root.append(field)
    
    def format_xml_file(self,path):
        """ This makes the xml file readable as a txt doc.
            For some reason the xml.toprettyxml() function
            adds extra blank lines. This makes the xml file
            unreadable. This function just removes
            all of the blank lines.
            arg1: path to xml file
        """
        from xml.dom.minidom import parse
        
        xml = parse(path)
        pretty_xml = xml.toprettyxml()
        
        file = open(path,'w')
        file.write(pretty_xml)
        file.close()
        
        cleaned_lines = []
        with open(path,"r") as f:
            lines = f.readlines()
            for l in lines:
                l.strip()
                if "<" in l:
                    cleaned_lines.append(l)
            
        with open (path,"w") as f:
            f.writelines(cleaned_lines)
    
    def write(self,path):
        with open(path, 'w',encoding='utf-8') as file:
            self.tree.write(file,encoding='unicode')
            
#         self.format_xml_file(path)

class Prompts_Interface(bpy.types.Operator):
    
    def get_product(self):
        obj = bpy.data.objects[self.object_name]
        obj_product_bp = utils.get_bp(obj,'PRODUCT')
        product = Assembly(obj_product_bp)
        self.depth = math.fabs(product.obj_y.location.y)
        self.height = math.fabs(product.obj_z.location.z)
        self.width = math.fabs(product.obj_x.location.x)   
        return product
    
    def draw_product_size(self,layout):
        box = layout.box()
        row = box.row()
        
        col = row.column(align=True)
        row1 = col.row(align=True)
        if utils.object_has_driver(self.product.obj_x):
            row1.label('Width: ' + str(unit.meter_to_active_unit(math.fabs(self.product.obj_x.location.x))))
        else:
            row1.label('Width:')
            row1.prop(self,'width',text="")
            row1.prop(self.product.obj_x,'hide',text="")
        
        row1 = col.row(align=True)
        if utils.object_has_driver(self.product.obj_z):
            row1.label('Height: ' + str(unit.meter_to_active_unit(math.fabs(self.product.obj_z.location.z))))
        else:
            row1.label('Height:')
            row1.prop(self,'height',text="")
            row1.prop(self.product.obj_z,'hide',text="")
        
        row1 = col.row(align=True)
        if utils.object_has_driver(self.product.obj_y):
            row1.label('Depth: ' + str(unit.meter_to_active_unit(math.fabs(self.product.obj_y.location.y))))
        else:
            row1.label('Depth:')
            row1.prop(self,'depth',text="")
            row1.prop(self.product.obj_y,'hide',text="")
            
        col = row.column(align=True)
        col.label("Location X:")
        col.label("Location Y:")
        col.label("Location Z:")
        
        col = row.column(align=True)
        col.prop(self.product.obj_bp,'location',text="")
        
        row = box.row()
        row.label('Rotation Z:')
        row.prop(self.product.obj_bp,'rotation_euler',index=2,text="")    
    
    def update_product_size(self):
        self.product.obj_x.location.x = self.width
        
        if self.product.obj_bp.mv.mirror_y:
            self.product.obj_y.location.y = -self.depth
        else:
            self.product.obj_y.location.y = self.depth
        
        if self.product.obj_bp.mv.mirror_z:
            self.product.obj_z.location.z = -self.height
        else:
            self.product.obj_z.location.z = self.height
            
        utils.run_calculators(self.product.obj_bp)
