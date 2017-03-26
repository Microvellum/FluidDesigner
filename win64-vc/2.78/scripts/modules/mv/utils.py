'''
Utility Functions
'''

import bpy
import bmesh
import inspect
import math
import os
import mathutils
import sys
import bgl
import blf
from bpy_extras import view3d_utils, object_utils
from . import unit
import bpy_extras.image_utils as img_utils
import time
from decimal import *

LIBRARY_PATH_FILENAME = "fd_paths.xml"

#-------OBJECT FUNCTIONS

def create_cube_mesh(name,size):
    
    verts = [(0.0, 0.0, 0.0),
             (0.0, size[1], 0.0),
             (size[0], size[1], 0.0),
             (size[0], 0.0, 0.0),
             (0.0, 0.0, size[2]),
             (0.0, size[1], size[2]),
             (size[0], size[1], size[2]),
             (size[0], 0.0, size[2]),
             ]

    faces = [(0, 1, 2, 3),
             (4, 7, 6, 5),
             (0, 4, 5, 1),
             (1, 5, 6, 2),
             (2, 6, 7, 3),
             (4, 0, 3, 7),
            ]
    
    return create_object_from_verts_and_faces(verts,faces,name)

def create_floor_mesh(name,size):
    
    verts = [(0.0, 0.0, 0.0),
             (0.0, size[1], 0.0),
             (size[0], size[1], 0.0),
             (size[0], 0.0, 0.0),
            ]

    faces = [(0, 1, 2, 3),
            ]

    return create_object_from_verts_and_faces(verts,faces,name)

def create_single_vertex(name):
    
    verts = [(0, 0, 0)]
    
    return create_object_from_verts_and_faces(verts,[],name)

def create_object_from_verts_and_faces(verts,faces,name):
    """ Creates an object from Verties and Faces
        arg1: Verts List of tuples [(float,float,float)]
        arg2: Faces List of ints
        arg3: name of object
    """
    mesh = bpy.data.meshes.new(name)
    
    bm = bmesh.new()

    for v_co in verts:
        bm.verts.new(v_co)
    
    for f_idx in faces:
        bm.verts.ensure_lookup_table()
        bm.faces.new([bm.verts[i] for i in f_idx])
    
    bm.to_mesh(mesh)
    
    mesh.update()
    
    obj_new = bpy.data.objects.new(mesh.name, mesh)
    
    bpy.context.scene.objects.link(obj_new)
    return obj_new

def hook_vertex_group_to_object(obj_mesh,vertex_group,obj_hook):
    """ This function adds a hook modifier to the verties 
        in the vertex_group to the obj_hook
    """
    bpy.ops.object.select_all(action = 'DESELECT')
    obj_hook.hide = False
    obj_hook.hide_select = False
    obj_hook.select = True
    obj_mesh.hide = False
    obj_mesh.hide_select = False
    if vertex_group in obj_mesh.vertex_groups:
        vgroup = obj_mesh.vertex_groups[vertex_group]
        obj_mesh.vertex_groups.active_index = vgroup.index
        bpy.context.scene.objects.active = obj_mesh
        bpy.ops.fd_object.toggle_edit_mode(object_name=obj_mesh.name)
        bpy.ops.mesh.select_all(action = 'DESELECT')
        bpy.ops.object.vertex_group_select()
        if obj_mesh.data.total_vert_sel > 0:
            bpy.ops.object.hook_add_selob()
        bpy.ops.mesh.select_all(action = 'DESELECT')
        bpy.ops.fd_object.toggle_edit_mode(object_name=obj_mesh.name)

def delete_obj_list(obj_list):
    """ This function deletes every object in the list
    """
    bpy.ops.object.select_all(action='DESELECT')
    for obj in obj_list:
        if obj.animation_data:
            for driver in obj.animation_data.drivers:
                if driver.data_path in {'hide','hide_select'}: # THESE DRIVERS MUST BE REMOVED TO DELETE OBJECTS
                    obj.driver_remove(driver.data_path) 
        
        obj.parent = None
        obj.hide_select = False
        obj.hide = False
        obj.select = True
        
        if obj.name in bpy.context.scene.objects:
            bpy.context.scene.objects.unlink(obj)

#   I HAVE HAD PROBLEMS WITH THIS CRASHING BLENDER
#   HOPEFULLY THE do_unlink PARAMETER WORKS
    for obj in obj_list:
        bpy.data.objects.remove(obj,do_unlink=True)
        
def delete_object_and_children(obj_bp):
    """ Deletes a object and all it's children
    """
    obj_list = []
    obj_list.append(obj_bp)
    for child in obj_bp.children:
        if len(child.children) > 0:
            delete_object_and_children(child)
        else:
            obj_list.append(child)
    delete_obj_list(obj_list)

def link_objects_to_scene(obj_bp,scene):
    """ This Function links an object and all of it's children
        to the scene
    """
    obj_bp.draw_type = 'WIRE' #THIS IS NEEDED FOR DRAG AND DROP
    obj_bp.select = False
    scene.objects.link(obj_bp)
    if obj_bp.type == 'EMPTY':
        obj_bp.hide = True
    for child in obj_bp.children:
        link_objects_to_scene(child,scene)

def create_vertex_group_for_hooks(obj_mesh,vert_list,vgroupname):
    """ Adds a new vertex group to a mesh. If the group already exists
        Then no group is added. The second parameter allows you to assign
        verts to the vertex group.
        Arg1: bpy.data.Object | Mesh Object to operate on
        Arg2: [] of int | vertext indexs to assign to group
        Arg3: string | vertex group name
    """
    if vgroupname not in obj_mesh.vertex_groups:
        obj_mesh.vertex_groups.new(name=vgroupname)
        
    vgroup = obj_mesh.vertex_groups[vgroupname]
    vgroup.add(vert_list,1,'ADD')

def set_object_name(obj):
    """ This function sets the name of an object to make the outliner easier to navigate
    """
    counter = str(obj.mv.item_number)
    if obj.mv.type in {'VPDIMX','VPDIMY','VPDIMZ'}:
        obj.name = counter + '.' + obj.mv.type + '.' + obj.parent.mv.name_object if obj.parent else obj.mv.name_object
    elif obj.mv.type == 'BPASSEMBLY':
        if obj.mv.type_group in {'PRODUCT','INSERT','OPENING'}:
            obj.name = counter + '.' + obj.mv.type_group + '.' + obj.mv.name_object   
        else:
            obj.name = counter + '.BPASSEMBLY.' + obj.mv.name_object   
    elif obj.cabinetlib.type_mesh != 'NONE':
        obj.name = counter + '.' + obj.cabinetlib.type_mesh + '.' + obj.parent.mv.name_object + '.' + obj.mv.name_object
    elif obj.mv.type in {'VISDIM_A','VISDIM_B'}:
        obj.name = counter + '.DIMENSION.' + obj.parent.mv.name_object + '.' + obj.mv.name_object
    else:
        obj.name = counter + '.' + obj.type + '.' + obj.mv.name_object

def assign_materials_from_pointers(obj):
    library = bpy.context.scene.mv
    spec_group = library.spec_groups[obj.cabinetlib.spec_group_index]
    #ASSIGN POINTERS TO MESH BASED ON MESH TYPE
    if obj.cabinetlib.type_mesh == 'CUTPART':
        
        if spec_group:
            if obj.cabinetlib.cutpart_name in spec_group.cutparts:
                cutpart = spec_group.cutparts[obj.cabinetlib.cutpart_name]
                for index, slot in enumerate(obj.cabinetlib.material_slots):
                    if slot.name == 'Core':
                        slot.pointer_name = cutpart.core
                    elif slot.name in {'Top','Exterior'}:
                        slot.pointer_name = cutpart.top
                    elif slot.name in {'Bottom','Interior'}:
                        slot.pointer_name = cutpart.bottom
                    else:
                        if obj.cabinetlib.edgepart_name in spec_group.edgeparts:
                            edgepart = spec_group.edgeparts[obj.cabinetlib.edgepart_name]
                            slot.pointer_name = edgepart.material

                    if slot.pointer_name in spec_group.materials:
                        material_pointer = spec_group.materials[slot.pointer_name]
                        slot.library_name = material_pointer.library_name
                        slot.category_name = material_pointer.category_name
                        slot.item_name = material_pointer.item_name

    elif obj.cabinetlib.type_mesh == 'EDGEBANDING':
        obj.show_bounds = False
        if spec_group:
            if obj.cabinetlib.edgepart_name in spec_group.edgeparts:
                edgepart = spec_group.edgeparts[obj.cabinetlib.edgepart_name]
                for index, slot in enumerate(obj.cabinetlib.material_slots):
                    slot.pointer_name = edgepart.material

                    if slot.pointer_name in spec_group.materials:
                        material_pointer = spec_group.materials[slot.pointer_name]
                        slot.library_name = material_pointer.library_name
                        slot.category_name = material_pointer.category_name
                        slot.item_name = material_pointer.item_name

    elif obj.cabinetlib.type_mesh == 'MACHINING':
        # MAKE A SIMPLE BLACK MATERIAL FOR MACHINING
        for slot in obj.cabinetlib.material_slots:
            slot.library_name = "Plastics"
            slot.category_name = "Melamine"
            slot.item_name = "Gloss Black Plastic"
            
    else:
        if spec_group:
            for index, slot in enumerate(obj.cabinetlib.material_slots):
                if slot.pointer_name in spec_group.materials:
                    material_pointer = spec_group.materials[slot.pointer_name]
                    slot.library_name = material_pointer.library_name
                    slot.category_name = material_pointer.category_name
                    slot.item_name = material_pointer.item_name

    #RETRIEVE MATERIAL FROM CATEGORY NAME AND ITEM NAME AND ASSIGN TO SLOT
    for index, slot in enumerate(obj.cabinetlib.material_slots):
        material = get_material((slot.library_name,slot.category_name),slot.item_name)
        if material:
            obj.material_slots[index].material = material
        else:
            print("MATERIAL NOT FOUND",slot.library_name,slot.category_name,slot.item_name,obj.mv.name_object)

    #MAKE SURE OBJECT IS TEXTURED
    if obj.mv.type == 'CAGE':
        obj.draw_type = 'WIRE'
    else:
        obj.draw_type = 'TEXTURED'

def get_child_objects(obj,obj_list=None):
    """ Returns: List of Objects
        Par1: obj - Object to collect all of the children from
        Par2: list - List of Objects to store all of the objects in
    """
    if not obj_list:
        obj_list = []
    if obj not in obj_list:
        obj_list.append(obj)
    for child in obj.children:
        obj_list.append(child)
        get_child_objects(child,obj_list)
    return obj_list

def get_selection_point(context, event, ray_max=10000.0,objects=None,floor=None):
    """Gets the point to place an object based on selection"""
    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y
 
    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    ray_target = ray_origin + view_vector
 
    def visible_objects_and_duplis():
        """Loop over (object, matrix) pairs (mesh only)"""
 
        for obj in context.visible_objects:
             
            if objects:
                if obj in objects:
                    yield (obj, obj.matrix_world.copy())
             
            else:
                if floor is not None and obj == floor:
                    yield (obj, obj.matrix_world.copy())
                     
                if obj.draw_type != 'WIRE':
                    if obj.type == 'MESH':
                        if obj.mv.type not in {'BPASSEMBLY','BPWALL'}:
                            yield (obj, obj.matrix_world.copy())
         
                    if obj.dupli_type != 'NONE':
                        obj.dupli_list_create(scene)
                        for dob in obj.dupli_list:
                            obj_dupli = dob.object
                            if obj_dupli.type == 'MESH':
                                yield (obj_dupli, dob.matrix.copy())
 
            obj.dupli_list_clear()
 
    def obj_ray_cast(obj, matrix):
        """Wrapper for ray casting that moves the ray into object space"""
        try:
            # get the ray relative to the object
            matrix_inv = matrix.inverted()
            ray_origin_obj = matrix_inv * ray_origin
            ray_target_obj = matrix_inv * ray_target
            ray_direction_obj = ray_target_obj - ray_origin_obj
     
            # cast the ray
            success, location, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj)
     
            if success:
                return location, normal, face_index
            else:
                return None, None, None
        except:
            print("ERROR IN obj_ray_cast",obj)
            return None, None, None
             
    best_length_squared = ray_max * ray_max
    best_obj = None
    best_hit = scene.cursor_location
    for obj, matrix in visible_objects_and_duplis():
        if obj.type == 'MESH':
            if obj.data:
                hit, normal, face_index = obj_ray_cast(obj, matrix)
                if hit is not None:
                    hit_world = matrix * hit
                    length_squared = (hit_world - ray_origin).length_squared
                    if length_squared < best_length_squared:
                        best_hit = hit_world
                        best_length_squared = length_squared
                        best_obj = obj
                        
    return best_hit, best_obj

def get_material_name(obj):
    if obj.cabinetlib.type_mesh in {'CUTPART','EDGEBANDING'}:
        thickness = str(round(unit.meter_to_active_unit(get_part_thickness(obj)),4))
        core = ""
        exterior = ""
        interior = ""
        for mv_slot in obj.cabinetlib.material_slots:
            if mv_slot.name == 'Core':
                core = mv_slot.item_name
            if mv_slot.name in {'Top','Exterior'}:
                exterior = mv_slot.item_name
            if mv_slot.name in {'Bottom','Interior'}:
                interior = mv_slot.item_name
    
        return format_material_name(thickness,core,exterior,interior)
    
    if obj.cabinetlib.type_mesh == 'BUYOUT':
        # THIS IS NEEDED FOR THE DOOR BUILDER LIBRARY
        # BECAUSE THE DOOR ASSEMBLY BP IS MARKED AS BUYOUT
        if obj.mv.type == 'BPASSEMBLY':
            return obj.mv.name_object
        if obj.parent:
            return obj.parent.mv.name_object
        else:
            return  obj.mv.name_object
    
    if obj.cabinetlib.type_mesh == 'SOLIDSTOCK':
        return obj.mv.solid_stock
#         thickness = str(round(unit.meter_to_active_unit(get_part_thickness(obj)),4))
#         return thickness + " " + obj.mv.solid_stock

def get_part_thickness(obj):
    if obj.cabinetlib.type_mesh == 'CUTPART':
        spec_group = bpy.context.scene.mv.spec_groups[obj.cabinetlib.spec_group_index]
        if obj.cabinetlib.cutpart_name in spec_group.cutparts:
            return spec_group.cutparts[obj.cabinetlib.cutpart_name].thickness
        else:
            if obj.parent:
                for child in obj.parent.children:
                    if child.mv.type == 'VPDIMZ':
                        return math.fabs(child.location.z)
                    
    if obj.cabinetlib.type_mesh in {'SOLIDSTOCK','BUYOUT'}:
        if obj.parent:
            for child in obj.parent.children:
                if child.mv.type == 'VPDIMZ':
                    return math.fabs(child.location.z)
                
    if obj.cabinetlib.type_mesh == 'EDGEBANDING':
        for mod in obj.modifiers:
            if mod.type == 'SOLIDIFY':
                return mod.thickness

def format_material_name(thickness,core,exterior,interior):
    if core == exterior:
        exterior = "-"
    
    if core == interior:
        interior = "-"
        
    return thickness + " " + core + " [" + exterior + "] [" + interior + "]"

def connect_objects_location(anchor_obj,obj):
    """ This function adds a copy location constraint to the obj
        add sets the target to the anchor_obj
    """
    constraint = obj.constraints.new('COPY_LOCATION')
    constraint.target = anchor_obj
    constraint.use_x = True
    constraint.use_y = True
    constraint.use_z = True

def apply_hook_modifiers(obj):
    """ This function applies all of the hook modifers on an object
    """
    obj.hide = False
    obj.select = True
    bpy.context.scene.objects.active = obj
    for mod in obj.modifiers:
        if mod.type == 'HOOK':
            bpy.ops.object.modifier_apply(modifier=mod.name)

def get_edgebanding_name_from_pointer_name(pointer_name,spec_group):
    if pointer_name in spec_group.edgeparts:
        pointer = spec_group.edgeparts[pointer_name]
        thickness = str(round(unit.meter_to_active_unit(pointer.thickness),4))
        material = spec_group.materials[pointer.material].item_name
        if thickness + " " + material not in bpy.context.scene.cabinetlib.edgebanding:
            mat = bpy.context.scene.cabinetlib.edgebanding.add()
            mat.thickness = pointer.thickness
            mat.name = thickness + " " + material
        return thickness + " " + material
    else:
        return ""

def get_material_name_from_pointer(pointer,spec_group):
    thickness = str(round(unit.meter_to_active_unit(pointer.thickness),4))
    if pointer.core in spec_group.materials:
        core_material = spec_group.materials[pointer.core].item_name
    else:
        core_material = "NA"
    if pointer.top in spec_group.materials:
        top_material = spec_group.materials[pointer.top].item_name
    else:
        top_material = "NA"
    if pointer.bottom in spec_group.materials:
        bottom_material = spec_group.materials[pointer.bottom].item_name
    else:
        bottom_material = "NA"
    return format_material_name(thickness,core_material,top_material,bottom_material)

def object_has_driver(obj):
    """ If the object has driver this function will return True otherwise False
    """
    if obj.animation_data:
        if len(obj.animation_data.drivers) > 0:
            return True

#-------LIBRARY FUNCTIONS

def get_library_dir(lib_type = ""):
    if lib_type == 'assemblies':
        if os.path.exists(bpy.context.window_manager.mv.assembly_library_path):
            return bpy.context.window_manager.mv.assembly_library_path
    if lib_type == 'objects':
        if os.path.exists(bpy.context.window_manager.mv.object_library_path):
            return bpy.context.window_manager.mv.object_library_path
    if lib_type == 'materials':
        if os.path.exists(bpy.context.window_manager.mv.material_library_path):
            return bpy.context.window_manager.mv.material_library_path
    if lib_type == 'worlds':
        if os.path.exists(bpy.context.window_manager.mv.world_library_path):
            return bpy.context.window_manager.mv.world_library_path
        
    # If no path is set get default path
    root_path = os.path.join(os.path.dirname(bpy.app.binary_path),"data")
    if lib_type == "":
        return root_path
    else:
        return os.path.join(root_path,lib_type)

def get_material(folders,material_name):
    if material_name in bpy.data.materials:
        return bpy.data.materials[material_name]
    
    #Make sure no folders are blank
    for folder in folders:
        if folder == "":
            return None
    
    search_directory = get_library_dir("materials")
    for folder in folders:
        search_directory = os.path.join(search_directory,folder)

    if os.path.isdir(search_directory):
        files = os.listdir(search_directory)
        possible_files = []
        # Add the blend file with the same name to the list first so it is searched first
        if material_name + ".blend" in files:
            possible_files.append(os.path.join(search_directory,material_name + ".blend"))
          
        for file in files:
            blendname, ext = os.path.splitext(file)
            if ext == ".blend":
                possible_files.append(os.path.join(search_directory,file))
                  
        for file in possible_files:
            with bpy.data.libraries.load(file, False, False) as (data_from, data_to):
                for mat in data_from.materials:
                    if mat == material_name:
                        data_to.materials = [mat]
                        break
      
            for mat in data_to.materials:
                return mat

def get_library_scripts_dir(context):
    """ Returns: List of Strings (FolderPath) 
    Gets all of the directories to the fluid designer library packages
    """
    b_version = str(bpy.app.version[0]) + "." + str(bpy.app.version[1])
    
    paths = []
    paths.append(os.path.join(os.path.dirname(bpy.app.binary_path),b_version,"scripts","libraries"))
    if os.path.exists(context.window_manager.mv.library_module_path):
        paths.append(context.window_manager.mv.library_module_path)

    return paths

def get_library_packages(context, only_external=False):
    """ Returns: List (of Strings) 
    Adds FD Library Packages to PYTHON Path, and Returns list of package folder names.
    """    
    packages = []
    
    paths = get_library_scripts_dir(context)
        
    #LOAD EXTERIAL LIBRARIES
    for package in context.window_manager.mv.library_packages:
        if os.path.exists(package.lib_path) and package.enabled:
            files = os.listdir(package.lib_path)
            for file in files:
                if file == '__init__.py':
                    path, folder_name = os.path.split(os.path.normpath(package.lib_path))
                    sys.path.append(path)
                    mod = __import__(folder_name)
                    packages.append(folder_name)
                    break
                        
    #LOAD LIBRARIES FROM MODULE PATH
    if not only_external:                      
        for path in paths:
            dirs = os.listdir(path)
            for folder in dirs:
                if os.path.isdir(os.path.join(path,folder)) and not folder.startswith("X_"):
                    files = os.listdir(os.path.join(path,folder))
                    for file in files:
                        if file == '__init__.py':
                            sys.path.append(path)
                            mod = __import__(folder)
                            packages.append(folder)
                            break

    return packages

def get_library_path_file():
    """ Returns the path to the file that stores all of the library paths.
    """
    path = os.path.join(bpy.utils.user_resource('SCRIPTS'), "fluid_designer")

    if not os.path.exists(path):
        os.makedirs(path)
        
    return os.path.join(path,LIBRARY_PATH_FILENAME)

def get_product_class(context,library_name,category_name,product_name):
    """ Returns: Object (Product Class)
    Gets the Product Class Base on active product library name
    """
    lib = context.window_manager.cabinetlib.lib_products[context.scene.mv.product_library_name]
    pkg = __import__(lib.package_name)
    
    for modname, modobj in inspect.getmembers(pkg):
        for name, obj in inspect.getmembers(modobj):
            if "PRODUCT_" in name and inspect.isclass(obj):
                product = obj()
                if product.assembly_name == "":
                    product.assembly_name = get_product_class_name(name)
                if product.library_name == library_name and product.category_name == category_name and product.assembly_name == product_name:
                    product.package_name = lib.package_name
                    product.module_name = modname
                    return product

def get_insert_class(context,library_name,category_name,insert_name):
    """ Returns: Object (Product Class)
    Gets the Product Class Base on active product library name
    """
    lib = context.window_manager.cabinetlib.lib_inserts[context.scene.mv.insert_library_name]
    pkg = __import__(lib.package_name)
    
    for modname, modobj in inspect.getmembers(pkg):
        for name, obj in inspect.getmembers(modobj):
            if "INSERT_" in name and inspect.isclass(obj):
                insert = obj()
                if insert.assembly_name == "":
                    insert.assembly_name = get_insert_class_name(name)                
                if insert.library_name == library_name and insert.category_name == category_name and insert.assembly_name == insert_name:
                    insert.package_name = lib.package_name
                    insert.module_name = modname
                    return insert

def get_group(path):
    with bpy.data.libraries.load(path, False, False) as (data_from, data_to):
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
        obj_bp = get_assembly_bp(grp.objects[0])
        link_objects_to_scene(obj_bp,bpy.context.scene)
        bpy.data.groups.remove(grp,do_unlink=True)
        return obj_bp

def get_object(path):
    if os.path.exists(path): # LOOK FOR FILE NAME AND GET OBJECT
        with bpy.data.libraries.load(path, False, False) as (data_from, data_to):
            for obj in data_from.objects:
                data_to.objects = [obj]
                break
        for obj in data_to.objects:
            link_objects_to_scene(obj,bpy.context.scene)
            return obj
    else: # LOOK IN EVERY BLEND FILE IN THE SAME DIRECTORY FOR AN OBJECT NAME == FILE NAME
        directory_path = os.path.dirname(path)
        object_name, ext = os.path.splitext(os.path.basename(path))
        for file in os.listdir(directory_path):
            file_name, file_ext = os.path.splitext(file)
            if file_ext == '.blend':
                print("Searching: " + os.path.join(directory_path,file) + " for " + object_name) #PRINT STATEMENT FOR DEBUG. THIS COULD BE SLOWER IF SEARCHING MANY FILES!
                with bpy.data.libraries.load(os.path.join(directory_path,file), False, False) as (data_from_1, data_to_1):
                    for obj in data_from_1.objects:
                        if obj == object_name:
                            data_to_1.objects = [obj]
                            break
                        
                for obj in data_to_1.objects:
                    link_objects_to_scene(obj,bpy.context.scene)
                    return obj

def get_wall_bp(obj):
    """ This will get the wall base point from the passed in object
    """
    if obj:
        if obj.mv.type == 'BPWALL':
            return obj
        else:
            if obj.parent:
                return get_wall_bp(obj.parent)

def get_product_class_name(class_name):
    name = class_name.replace("PRODUCT_","")
    return name.replace("_"," ")

def get_insert_class_name(class_name):
    name = class_name.replace("INSERT_","")
    return name.replace("_"," ")

def set_wireframe(obj,make_wire=True):
    obj.show_x_ray = make_wire
    if make_wire:
        obj.draw_type = 'WIRE'
    else:
        obj.draw_type = 'TEXTURED'
        assign_materials_from_pointers(obj)
    for child in obj.children:
        set_wireframe(child, make_wire)

#-------MATH FUNCTIONS
def calc_distance(point1,point2):
    """ This gets the distance between two points (X,Y,Z)
    """
    return math.sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2 + (point1[2]-point2[2])**2) 

def get_curve_length(obj_curve):
    """ This gets a curve objects length. This currently only 
        calculates straight segments.
    """
    length = 0
    
    if obj_curve.type == 'CURVE':
        
        for spline in obj_curve.data.splines:
            for index, point in enumerate(spline.bezier_points):
                if len(spline.bezier_points) > index + 1:
                    length += calc_distance(point.co, spline.bezier_points[index+1].co)
                    
    return length

#-------ENUM FUNCTIONS

def create_image_preview_collection():
    col = bpy.utils.previews.new()
    col.my_previews_dir = ""
    col.my_previews = ()
    return col

def get_image_enum_previews(path,key,force_reload=False):
    """ Returns: ImagePreviewCollection
        Par1: path - The path to collect the images from
        Par2: key - The dictionary key the previews will be stored in
    """
    enum_items = []
    if len(key.my_previews) > 0:
        return key.my_previews
    
    if path and os.path.exists(path):
        image_paths = []
        for fn in os.listdir(path):
            if fn.lower().endswith(".png"):
                image_paths.append(fn)

        for i, name in enumerate(image_paths):
            filepath = os.path.join(path, name)
            thumb = key.load(filepath, filepath, 'IMAGE',force_reload)
            filename, ext = os.path.splitext(name)
            enum_items.append((filename, filename, filename, thumb.icon_id, i))
    
    key.my_previews = enum_items
    key.my_previews_dir = path
    return key.my_previews

def get_folder_enum_previews(path,key):
    """ Returns: ImagePreviewCollection
        Par1: path - The path to collect the folders from
        Par2: key - The dictionary key the previews will be stored in
    """
    enum_items = []
    if len(key.my_previews) > 0:
        return key.my_previews
    
    if path and os.path.exists(path):
        folders = []
        for fn in os.listdir(path):
            if os.path.isdir(os.path.join(path,fn)):
                folders.append(fn)

        for i, name in enumerate(folders):
            filepath = os.path.join(path, name)
            thumb = key.load(filepath, "", 'IMAGE')
            filename, ext = os.path.splitext(name)
            enum_items.append((filename, filename, filename, thumb.icon_id, i))
    
    key.my_previews = enum_items
    key.my_previews_dir = path
    return key.my_previews

#-------ASSEMBLY FUNCTIONS

def get_bp(obj,group_type):
    if obj:
        if obj.mv.type_group == group_type and obj.mv.type == 'BPASSEMBLY':
            return obj
        else:
            if obj.parent:
                return get_bp(obj.parent,group_type)
            
def get_assembly_bp(obj):
    """ This will get the group base point from the passed in object
    """
    if obj:
        if obj.mv.type == 'BPASSEMBLY':
            return obj
        else:
            if obj.parent:
                return get_assembly_bp(obj.parent)

def get_parent_assembly_bp(obj):
    """ This will get the top level group base point from the passed in object
    """
    if obj:
        if obj.parent:
            if obj.parent.mv.type == 'BPASSEMBLY':
                return get_parent_assembly_bp(obj.parent)
            else:
                if obj.parent.mv.type == 'BPWALL' and obj.mv.type == 'BPASSEMBLY':
                    return obj
        else:
            if obj.mv.type == 'BPASSEMBLY':
                return obj
            
def run_calculators(obj_bp):
    """ Runs all calculators for an assembly and all it's children assemblies
    """
    for index, page in enumerate(obj_bp.mv.PromptPage.COL_MainTab):
        if page.type == 'CALCULATOR':
            bpy.ops.fd_prompts.run_calculator(tab_index=index,data_name=obj_bp.name)
    for child in obj_bp.children:
        if child.mv.type == 'BPASSEMBLY':
            run_calculators(child)

def set_property_id(obj,property_id):
    """ Returns:None - sets all of the property_id values for the assembly
                       and all of its children.
    """
    obj.mv.property_id = property_id
    for child in obj.children:
        set_property_id(child,property_id)

def get_insert_bp_list(obj_bp,insert_list):
    for child in obj_bp.children:
        if child.mv.type == 'BPASSEMBLY' and child.mv.type_group == 'INSERT':
            insert_list.append(child)
            get_insert_bp_list(child,insert_list)

    if len(insert_list) > 0:
        insert_list.sort(key=lambda obj: obj.location.z, reverse=True)
    return insert_list

def init_objects(obj_bp):
    """ This Function is used to init all of the objects in a smart group
            -Sets the names of the children
            -Hides all of the empties
            -Deletes the cage objects
            -Sets the materials
    """
    obj_cages = []
    set_object_name(obj_bp)
    for child in obj_bp.children:
        set_object_name(child)

        if child.type == 'EMPTY':
            child.hide = True
            
        if child.mv.type == 'CAGE':
            obj_cages.append(child)
            
        if child.type == 'MESH':
            assign_materials_from_pointers(child)

        if child.mv.type == 'VISDIM_A':
            child.hide = True
            for dim_child in child.children:
                dim_child.hide = True

        if child.mv.type == 'BPASSEMBLY':
            init_objects(child)
            child.hide = True
         
        if child.mv.use_as_bool_obj:
            child.draw_type = 'WIRE'
         
    if len(obj_cages) > 0:
        delete_obj_list(obj_cages)

def save_assembly(assembly,path):
    for obj in bpy.data.objects:
        obj.hide = False
#         obj.hide_select = False
        obj.select = True
        for slot in obj.material_slots:
            slot.material = None
      
    bpy.ops.group.create(name = assembly.assembly_name)

    for mat in bpy.data.materials:
        mat.user_clear()
        bpy.data.materials.remove(mat)
        
    for image in bpy.data.images:
        image.user_clear()
        bpy.data.images.remove(image)    

    bpy.ops.fd_material.clear_spec_group()
    path = os.path.join(path,assembly.category_name)
    if not os.path.exists(path): os.makedirs(path)
    assembly.set_name(assembly.assembly_name)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(path,assembly.assembly_name + ".blend"))

def render_assembly(assembly,path):
    
    area = math.fabs(assembly.obj_x.location.x) + math.fabs(assembly.obj_y.location.y) + math.fabs(assembly.obj_z.location.z)
    
    if area == 0:
        # This is used for products that have a base point at the center (faucets)
        # It would be better to develop a way to create a cube that boarders
        # all of the objects and not look to the assembly size.
        rendering_space = unit.inch(0)
    else:
        rendering_space = unit.inch(5)
  
    render_box = create_cube_mesh("Render Box",(assembly.obj_x.location.x + rendering_space,
                                                assembly.obj_y.location.y - rendering_space,
                                                assembly.obj_z.location.z + rendering_space))
    
    render_box.location.x = assembly.obj_bp.location.x - (rendering_space/2)
    render_box.location.y = assembly.obj_bp.location.y + (rendering_space/2)
    render_box.location.z = assembly.obj_bp.location.z - (rendering_space/2)
     
    render_box.select = True
    
    for child in get_child_objects(assembly.obj_bp):
        child.select = True
    
    bpy.ops.view3d.camera_to_view_selected()
    delete_obj_list([render_box])
    
    init_objects(assembly.obj_bp)
    
    render = bpy.context.scene.render
    render.use_file_extension = True
    render.filepath = path
    bpy.ops.render.render(write_still=True)

def replace_assembly(old_assembly,new_assembly):
    ''' replace the old_assembly with the new_assembly
    '''
    new_assembly.obj_bp.mv.name_object = old_assembly.obj_bp.mv.name_object
    new_assembly.obj_bp.parent = old_assembly.obj_bp.parent
    new_assembly.obj_bp.location = old_assembly.obj_bp.location
    new_assembly.obj_bp.rotation_euler = old_assembly.obj_bp.rotation_euler    
    
    copy_drivers(old_assembly.obj_bp,new_assembly.obj_bp)
    copy_prompt_drivers(old_assembly.obj_bp,new_assembly.obj_bp)
    copy_drivers(old_assembly.obj_x,new_assembly.obj_x)
    copy_drivers(old_assembly.obj_y,new_assembly.obj_y)
    copy_drivers(old_assembly.obj_z,new_assembly.obj_z)
    # Go though all siblings and check if the assembly 
    # is being referenced in any other drivers. 
    search_obj = old_assembly.obj_bp.parent if old_assembly.obj_bp.parent else None
    if search_obj:
        for obj in search_obj.children:
            if obj.animation_data:
                for driver in obj.animation_data.drivers:
                    for var in driver.driver.variables:
                        for target in var.targets:
                            if target.id.name == old_assembly.obj_bp.name:
                                target.id = new_assembly.obj_bp
                            if target.id.name == old_assembly.obj_x.name:
                                target.id = new_assembly.obj_x
                            if target.id.name == old_assembly.obj_y.name:
                                target.id = new_assembly.obj_y
                            if target.id.name == old_assembly.obj_z.name:
                                target.id = new_assembly.obj_z

#-------INTERFACE FUNCTIONS

def get_prop_dialog_width(width):
    """ This function returns the width of a property dialog box in pixels
        This is needed to fix scaling issues with 4k monitors
        TODO: test if this works on the linux and apple OS
    """
    import ctypes
    screen_resolution_width = ctypes.windll.user32.GetSystemMetrics(0)
    if screen_resolution_width > 3000: # There is probably a beter way to check if the monitor is 4K
        return width * 2
    else:
        return width

def get_file_browser_path(context):
    for area in context.screen.areas:
        if area.type == 'FILE_BROWSER':
            for space in area.spaces:
                if space.type == 'FILE_BROWSER':
                    params = space.params
                    return params.directory

def update_file_browser_space(context,path):
    """ This function refreshes the file browser space
        with the path that is passed in
    """
    for area in context.screen.areas:
        if area.type == 'FILE_BROWSER':
            for space in area.spaces:
                if space.type == 'FILE_BROWSER':
                    params = space.params
                    params.directory = path
                    if not context.screen.show_fullscreen:
                        params.use_filter = True
                        params.display_type = 'THUMBNAIL'
                        params.use_filter_movie = False
                        params.use_filter_script = False
                        params.use_filter_sound = False
                        params.use_filter_text = False
                        params.use_filter_font = False
                        params.use_filter_folder = False
                        params.use_filter_blender = False
                        params.use_filter_image = True
    bpy.ops.file.next() #REFRESH FILEBROWSER INTERFACE

def get_selected_file_from_file_browser(context):
    #THIS IS USED BY THE CABINET LIBRARY
    window = context.window
    for area in window.screen.areas:
        if area.type == 'FILE_BROWSER':
            for space in area.spaces:
                if space.type == 'FILE_BROWSER':
                    return os.path.join(space.params.directory,space.params.filename)

def draw_object_info(layout,obj):
    box = layout.box()
    row = box.row()
    row.prop(obj,'name')
    if obj.type in {'MESH','CURVE','LATTICE','TEXT'}:
        row.operator('fd_object.toggle_edit_mode',text="",icon='EDITMODE_HLT').object_name = obj.name
    
    has_hook_modifier = False
    for mod in obj.modifiers:
        if mod.type == 'HOOK':
            has_hook_modifier =  True
    
    has_shape_keys = False
    if obj.type == 'MESH':
        if obj.data.shape_keys:
            if len(obj.data.shape_keys.key_blocks) > 0:
                has_shape_keys = True
    
    if has_hook_modifier or has_shape_keys:
        row = box.row()
        col = row.column(align=True)
        col.label("Dimension")
        col.label("X: " + str(round(unit.meter_to_active_unit(obj.dimensions.x),4)))
        col.label("Y: " + str(round(unit.meter_to_active_unit(obj.dimensions.y),4)))
        col.label("Z: " + str(round(unit.meter_to_active_unit(obj.dimensions.z),4)))
        col = row.column(align=True)
        col.label("Location")
        col.label("X: " + str(round(unit.meter_to_active_unit(obj.location.x),4)))
        col.label("Y: " + str(round(unit.meter_to_active_unit(obj.location.y),4)))
        col.label("Z: " + str(round(unit.meter_to_active_unit(obj.location.z),4)))
        col = row.column(align=True)
        col.label("Rotation")
        col.label("X: " + str(round(math.degrees(obj.rotation_euler.x),4)))
        col.label("Y: " + str(round(math.degrees(obj.rotation_euler.y),4)))
        col.label("Z: " + str(round(math.degrees(obj.rotation_euler.z),4)))
        if has_hook_modifier:
            box.operator("fd_object.apply_hook_modifiers",icon='HOOK').object_name = obj.name
        if has_shape_keys:
            box.operator("fd_object.apply_shape_keys",icon='SHAPEKEY_DATA').object_name = obj.name
    else:
        if obj.type not in {'EMPTY','CAMERA','LAMP'}:
            box.label('Dimensions:')
            col = box.column(align=True)
            #X
            row = col.row(align=True)
            row.prop(obj,"lock_scale",index=0,text="")
            if obj.lock_scale[0]:
                row.label("X: " + str(round(unit.meter_to_active_unit(obj.dimensions.x),4)))
            else:
                row.prop(obj,"dimensions",index=0,text="X")
            #Y
            row = col.row(align=True)
            row.prop(obj,"lock_scale",index=1,text="")
            if obj.lock_scale[1]:
                row.label("Y: " + str(round(unit.meter_to_active_unit(obj.dimensions.y),4)))
            else:
                row.prop(obj,"dimensions",index=1,text="Y")
            #Z
            row = col.row(align=True)
            row.prop(obj,"lock_scale",index=2,text="")
            if obj.lock_scale[2]:
                row.label("Z: " + str(round(unit.meter_to_active_unit(obj.dimensions.z),4)))
            else:
                row.prop(obj,"dimensions",index=2,text="Z")
                
        col1 = box.row()
        if obj:
            col2 = col1.split()
            col = col2.column(align=True)
            col.label('Location:')
            #X
            row = col.row(align=True)
            row.prop(obj,"lock_location",index=0,text="")
            if obj.lock_location[0]:
                row.label("X: " + str(round(unit.meter_to_active_unit(obj.location.x),4)))
            else:
                row.prop(obj,"location",index=0,text="X")
            #Y    
            row = col.row(align=True)
            row.prop(obj,"lock_location",index=1,text="")
            if obj.lock_location[1]:
                row.label("Y: " + str(round(unit.meter_to_active_unit(obj.location.y),4)))
            else:
                row.prop(obj,"location",index=1,text="Y")
            #Z    
            row = col.row(align=True)
            row.prop(obj,"lock_location",index=2,text="")
            if obj.lock_location[2]:
                row.label("Z: " + str(round(unit.meter_to_active_unit(obj.location.z),4)))
            else:
                row.prop(obj,"location",index=2,text="Z")
                
            col2 = col1.split()
            col = col2.column(align=True)
            col.label('Rotation:')
            #X
            row = col.row(align=True)
            row.prop(obj,"lock_rotation",index=0,text="")
            if obj.lock_rotation[0]:
                row.label("X: " + str(round(math.degrees(obj.rotation_euler.x),4)))
            else:
                row.prop(obj,"rotation_euler",index=0,text="X")
            #Y    
            row = col.row(align=True)
            row.prop(obj,"lock_rotation",index=1,text="")
            if obj.lock_rotation[1]:
                row.label("Y: " + str(round(math.degrees(obj.rotation_euler.y),4)))
            else:
                row.prop(obj,"rotation_euler",index=1,text="Y")
            #Z    
            row = col.row(align=True)
            row.prop(obj,"lock_rotation",index=2,text="")
            if obj.lock_rotation[2]:
                row.label("Y: " + str(round(math.degrees(obj.rotation_euler.z),4)))
            else:
                row.prop(obj,"rotation_euler",index=2,text="Z")
                
    row = box.row()
    row.prop(obj.mv,'comment')

def draw_object_data(layout,obj):
    
    if obj.type == 'MESH':
        obj_bp = get_assembly_bp(obj)
        obj_wall_bp = get_wall_bp(obj)
        box = layout.box()
        row = box.row()
        row.label("Vertex Groups:")
        row.operator("object.vertex_group_add", icon='ZOOMIN', text="")
        row.operator("object.vertex_group_remove", icon='ZOOMOUT', text="").all = False
        box.template_list("FD_UL_vgroups", "", obj, "vertex_groups", obj.vertex_groups, "active_index", rows=3)
        if len(obj.vertex_groups) > 0:
            if obj.mode == 'EDIT':
                row = box.row()
                sub = row.row(align=True)
                sub.operator("object.vertex_group_assign", text="Assign")
                sub.operator("object.vertex_group_remove_from", text="Remove")
    
                sub = row.row(align=True)
                
                sub.operator("fd_object.vertex_group_select", text="Select").object_name = obj.name
                sub.separator()
                sub.operator("fd_object.clear_vertex_groups", text="Clear All").object_name = obj.name
#                 sub.operator("object.vertex_group_select", text="Select")
#                 sub.operator("object.vertex_group_deselect", text="Deselect")
            else:
                group = obj.vertex_groups.active
                if obj_bp or obj_wall_bp:
                    box.operator("fd_assembly.connect_meshes_to_hooks_in_assembly",text="Connect Hooks",icon='HOOK').object_name = obj.name
                else:
                    box.prop(group,'name')

        key = obj.data.shape_keys
        kb = obj.active_shape_key
        
        box = layout.box()
        row = box.row()
        row.label("Shape Keys:")
        row.operator("object.shape_key_add", icon='ZOOMIN', text="").from_mix = False
        row.operator("object.shape_key_remove", icon='ZOOMOUT', text="").all = False
        box.template_list("MESH_UL_shape_keys", "", key, "key_blocks", obj, "active_shape_key_index", rows=3)
        if kb and obj.active_shape_key_index != 0:
            box.prop(kb,'name')
            if obj.mode != 'EDIT':
                row = box.row()
                row.prop(kb, "value")
        
    if obj.type == 'EMPTY':
        box = layout.box()
        box.label("Empty Data",icon='FONT_DATA')
        box.prop(obj,'empty_draw_type',text='Draw Type')
        box.prop(obj,'empty_draw_size')
        
    if obj.type == 'CURVE':
        box = layout.box()
        box.label("Curve Data",icon='CURVE_DATA')
        curve = obj.data
        box.prop(curve,"dimensions")
        box.prop(curve,"bevel_object")
        box.prop(curve,"bevel_depth")
        box.prop(curve,"extrude")
        box.prop(curve,"use_fill_caps")
        box.prop(curve.splines[0],"use_cyclic_u")         
    
    if obj.type == 'FONT':
        text = obj.data
        box = layout.box()
        row = box.row()
        row.label("Font Data:")
        if obj.mode == 'OBJECT':
            row.operator("fd_object.toggle_edit_mode",text="Edit Text",icon='OUTLINER_DATA_FONT').object_name = obj.name
        else:
            row.operator("fd_object.toggle_edit_mode",text="Exit Edit Mode",icon='OUTLINER_DATA_FONT').object_name = obj.name
        row = box.row()
        row.template_ID(text, "font", open="font.open", unlink="font.unlink")
        row = box.row()
        row.label("Text Size:")
        row.prop(text,"size",text="")
        row = box.row()
        row.prop(text,"align")
        
        box = layout.box()
        row = box.row()
        row.label("3D Font:")
        row = box.row()
        row.prop(text,"extrude")
        row = box.row()
        row.prop(text,"bevel_depth")
        
    if obj.type == 'LAMP':
        box = layout.box()
        lamp = obj.data
        clamp = lamp.cycles
        cscene = bpy.context.scene.cycles  
        
        emissionNode = None
        mathNode = None
        
        if "Emission" in lamp.node_tree.nodes:
            emissionNode = lamp.node_tree.nodes["Emission"]
        if "Math" in lamp.node_tree.nodes:
            mathNode = lamp.node_tree.nodes["Math"]

        type_box = box.box()
        type_box.label("Lamp Type:")     
        row = type_box.row()
        row.prop(lamp, "type", expand=True)
        
        if lamp.type in {'POINT', 'SUN', 'SPOT'}:
            type_box.prop(lamp, "shadow_soft_size", text="Shadow Size")
        elif lamp.type == 'AREA':
            type_box.prop(lamp, "shape", text="")
            sub = type_box.column(align=True)

            if lamp.shape == 'SQUARE':
                sub.prop(lamp, "size")
            elif lamp.shape == 'RECTANGLE':
                sub.prop(lamp, "size", text="Size X")
                sub.prop(lamp, "size_y", text="Size Y")

        if cscene.progressive == 'BRANCHED_PATH':
            type_box.prop(clamp, "samples")

        if lamp.type == 'HEMI':
            type_box.label(text="Not supported, interpreted as sun lamp")         

        options_box = box.box()
        options_box.label("Lamp Options:")
        if emissionNode:
            row = options_box.row()
            split = row.split(percentage=0.3)
            split.label("Lamp Color:")
            split.prop(emissionNode.inputs[0],"default_value",text="")  
            
        row = options_box.row()
        split = row.split(percentage=0.3)
        split.label("Lamp Strength:")            
        if mathNode:   
            split.prop(mathNode.inputs[0],"default_value",text="") 
        else:          
            split.prop(emissionNode.inputs[1], "default_value",text="")
            
        row = options_box.row()        
        split = row.split(percentage=0.4)     
        split.prop(clamp, "cast_shadow",text="Cast Shadows")
        split.prop(clamp, "use_multiple_importance_sampling")
            
    if obj.type == 'CAMERA':
        box = layout.box()
        cam = obj.data
        ccam = cam.cycles
        scene = bpy.context.scene
        rd = scene.render
        
        box.label("Camera Options:")           
        cam_opt_box_1 = box.box()
        row = cam_opt_box_1.row(align=True)
        row.label(text="Render Size:",icon='STICKY_UVS_VERT')        
        row.prop(rd, "resolution_x", text="X")
        row.prop(rd, "resolution_y", text="Y")
        cam_opt_box_1.prop(cam, "type", expand=False, text="Camera Type")
        split = cam_opt_box_1.split()
        col = split.column()
        if cam.type == 'PERSP':
            row = col.row()
            if cam.lens_unit == 'MILLIMETERS':
                row.prop(cam, "lens")
            elif cam.lens_unit == 'FOV':
                row.prop(cam, "angle")
            row.prop(cam, "lens_unit", text="")

        if cam.type == 'ORTHO':
            col.prop(cam, "ortho_scale")

        if cam.type == 'PANO':
            engine = bpy.context.scene.render.engine
            if engine == 'CYCLES':
                ccam = cam.cycles
                col.prop(ccam, "panorama_type", text="Panorama Type")
                if ccam.panorama_type == 'FISHEYE_EQUIDISTANT':
                    col.prop(ccam, "fisheye_fov")
                elif ccam.panorama_type == 'FISHEYE_EQUISOLID':
                    row = col.row()
                    row.prop(ccam, "fisheye_lens", text="Lens")
                    row.prop(ccam, "fisheye_fov")
            elif engine == 'BLENDER_RENDER':
                row = col.row()
                if cam.lens_unit == 'MILLIMETERS':
                    row.prop(cam, "lens")
                elif cam.lens_unit == 'FOV':
                    row.prop(cam, "angle")
                row.prop(cam, "lens_unit", text="")
        
        row = cam_opt_box_1.row()
#         row.menu("CAMERA_MT_presets", text=bpy.types.CAMERA_MT_presets.bl_label)         
        row.prop_menu_enum(cam, "show_guide")            
        row = cam_opt_box_1.row()
        split = row.split()
        col = split.column()
        col.prop(cam, "clip_start", text="Clipping Start")
        col.prop(cam, "clip_end", text="Clipping End")      
        col = row.column()         
        col.prop(bpy.context.scene.cycles,"film_transparent",text="Transparent Film")   
        
        box.label(text="Depth of Field:")
        dof_box = box.box()
        row = dof_box.row()
        row.label("Focus:")
        row = dof_box.row(align=True)
        row.prop(cam, "dof_object", text="")
        col = row.column()
        sub = col.row()
        sub.active = cam.dof_object is None
        sub.prop(cam, "dof_distance", text="Distance")

#-------DRIVER FUNCTIONS
    
def get_driver(obj,data_path,array_index):
    if obj.animation_data:
        for DR in obj.animation_data.drivers:
            if DR.data_path == data_path and DR.array_index == array_index:
                return DR    
    
def copy_drivers(obj,obj_target):
    """ This Function copies all drivers from obj
        To obj_target. This doesn't include prompt drivers
    """
    if obj.animation_data:
        for driver in obj.animation_data.drivers:
            if 'mv.PromptPage' not in driver.data_path:
                newdriver = None
                try:
                    newdriver = obj_target.driver_add(driver.data_path,driver.array_index)
                except Exception:
                    try:
                        newdriver = obj_target.driver_add(driver.data_path)
                    except Exception:
                        print("Unable to Copy Prompt Driver", driver.data_path)
                if newdriver:
                    newdriver.driver.expression = driver.driver.expression
                    newdriver.driver.type = driver.driver.type
                    for var in driver.driver.variables:
                        if var.name not in newdriver.driver.variables:
                            newvar = newdriver.driver.variables.new()
                            newvar.name = var.name
                            newvar.type = var.type
                            for index, target in enumerate(var.targets):
                                newtarget = newvar.targets[index]
                                if target.id is obj:
                                    newtarget.id = obj_target #CHECK SELF REFERENCE FOR PROMPTS
                                else:
                                    newtarget.id = target.id
                                newtarget.transform_space = target.transform_space
                                newtarget.transform_type = target.transform_type
                                newtarget.data_path = target.data_path

def copy_prompt_drivers(obj,obj_target):
    """ This Function copies all drivers that are 
        assigned to prompts from obj to obj_target.
    """
    if obj.animation_data:
        for driver in obj.animation_data.drivers:
            if 'mv.PromptPage' in driver.data_path:
                for prompt in obj_target.mv.PromptPage.COL_Prompt:
                    newdriver = None
                    if prompt.name in driver.data_path:
                        newdriver = None
                        try:
                            newdriver = obj_target.driver_add(driver.data_path,driver.array_index)
                        except Exception:
                            try:
                                newdriver = obj_target.driver_add(driver.data_path)
                            except Exception:
                                print("Unable to Copy Prompt Driver", driver.data_path)
                    if newdriver:
                        newdriver.driver.expression = driver.driver.expression
                        newdriver.driver.type = driver.driver.type
                        for var in driver.driver.variables:
                            if var.name not in newdriver.driver.variables:
                                newvar = newdriver.driver.variables.new()
                                newvar.name = var.name
                                newvar.type = var.type
                                for index, target in enumerate(var.targets):
                                    newtarget = newvar.targets[index]
                                    if target.id is obj:
                                        newtarget.id = obj_target #CHECK SELF REFERENCE FOR PROMPTS
                                    else:
                                        newtarget.id = target.id
                                    newtarget.transform_space = target.transform_space
                                    newtarget.transform_type = target.transform_type
                                    newtarget.data_path = target.data_path

def add_variables_to_driver(driver,driver_vars):
    """ This function adds the driver_vars to the driver
    """
    for var in driver_vars:
        new_var = driver.driver.variables.new()
        new_var.type = var.var_type
        new_var.name = var.var_name
        new_var.targets[0].data_path = var.data_path
        new_var.targets[0].id = var.obj
        if var.var_type == 'TRANSFORMS':
            new_var.targets[0].transform_space = var.transform_space
            new_var.targets[0].transform_type = var.transform_type

def copy_assembly_drivers(template_assembly,copy_assembly):
    copy_drivers(template_assembly.obj_bp,copy_assembly.obj_bp)
    copy_drivers(template_assembly.obj_x,copy_assembly.obj_x)
    copy_drivers(template_assembly.obj_y,copy_assembly.obj_y)
    copy_drivers(template_assembly.obj_z,copy_assembly.obj_z)
    copy_prompt_drivers(template_assembly.obj_bp,copy_assembly.obj_bp)
    
def draw_driver_expression(layout,driver):
    row = layout.row(align=True)
    row.prop(driver.driver,'show_debug_info',text="",icon='OOPS')
    if driver.driver.is_valid:
        row.prop(driver.driver,"expression",text="",expand=True,icon='FILE_TICK')
        if driver.mute:
            row.prop(driver,"mute",text="",icon='OUTLINER_DATA_SPEAKER')
        else:
            row.prop(driver,"mute",text="",icon='OUTLINER_OB_SPEAKER')
    else:
        row.prop(driver.driver,"expression",text="",expand=True,icon='ERROR')
        if driver.mute:
            row.prop(driver,"mute",text="",icon='OUTLINER_DATA_SPEAKER')
        else:
            row.prop(driver,"mute",text="",icon='OUTLINER_OB_SPEAKER')

def draw_driver_variables(layout,driver,object_name):
    
    for var in driver.driver.variables:
        col = layout.column()
        boxvar = col.box()
        row = boxvar.row(align=True)
        row.prop(var,"name",text="",icon='FORWARD')
        
        props = row.operator("fd_driver.remove_variable",text="",icon='X',emboss=False)
        props.object_name = object_name
        props.data_path = driver.data_path
        props.array_index = driver.array_index
        props.var_name = var.name
        for target in var.targets:
            if driver.driver.show_debug_info:
                row = boxvar.row()
                row.prop(var,"type",text="")
                row = boxvar.row()
                row.prop(target,"id",text="")
                row = boxvar.row(align=True)
                row.prop(target,"data_path",text="",icon='ANIM_DATA')
            if target.id and target.data_path != "":
                value = eval('bpy.data.objects["' + target.id.name + '"]'"." + target.data_path)
            else:
                value = "ERROR#"
            row = boxvar.row()
            row.label("",icon='BLANK1')
            row.label("",icon='BLANK1')
            if type(value).__name__ == 'str':
                row.label("Value: " + value)
            elif type(value).__name__ == 'float':
                row.label("Value: " + str(unit.meter_to_active_unit(value)))
            elif type(value).__name__ == 'int':
                row.label("Value: " + str(value))
            elif type(value).__name__ == 'bool':
                row.label("Value: " + str(value))
                
def draw_add_variable_operators(layout,object_name,data_path,array_index):
    #GLOBAL PROMPT
    obj = bpy.data.objects[object_name]
    obj_bp = get_assembly_bp(obj)
    box = layout.box()
    box.label("Quick Variables",icon='DRIVER')
    row = box.row()
    if obj_bp:
        props = row.operator('fd_driver.get_vars_from_object',text="Group Variables",icon='DRIVER')
        props.object_name = object_name
        props.var_object_name = obj_bp.name
        props.data_path = data_path
        props.array_index = array_index    
        
#----------- OpenGL Drawing
def draw_callback_px(self, context):
    font_id = 0  # XXX, need to find out how best to get this.

    offset = 10
    text_height = 10
    text_length = int(len(self.mouse_text) * 7.3)
    
    if self.header_text != "":
        blf.size(font_id, 17, 72)
        text_w, text_h = blf.dimensions(font_id,self.header_text)
        blf.position(font_id, context.area.width/2 - text_w/2, context.area.height - 50, 0)
        blf.draw(font_id, self.header_text)

    # 50% alpha, 2 pixel width line
    if self.mouse_text != "":
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glColor4f(0.0, 0.0, 0.0, 0.5)
        bgl.glLineWidth(10)
    
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2i(self.mouse_loc[0]-offset-5, self.mouse_loc[1]+offset)
        bgl.glVertex2i(self.mouse_loc[0]+text_length-offset, self.mouse_loc[1]+offset)
        bgl.glVertex2i(self.mouse_loc[0]+text_length-offset, self.mouse_loc[1]+offset+text_height)
        bgl.glVertex2i(self.mouse_loc[0]-offset-5, self.mouse_loc[1]+offset+text_height)
        bgl.glEnd()
        
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        blf.position(font_id, self.mouse_loc[0]-offset, self.mouse_loc[1]+offset, 0)
        blf.size(font_id, 15, 72)
        blf.draw(font_id, self.mouse_text)
        
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

def draw_opengl(self,context):
    context = bpy.context
    if context.window_manager.mv.use_opengl_dimensions:
        region = bpy.context.region
        #---------- if Quadview
        if not context.space_data.region_quadviews:
            rv3d = bpy.context.space_data.region_3d
        else:
            if context.area.type != 'VIEW_3D' or context.space_data.type != 'VIEW_3D':
                return
            i = -1
            for region in context.area.regions:
                if region.type == 'WINDOW':
                    i += 1
                    if context.region.id == region.id:
                        break
            else:
                return
    
            rv3d = context.space_data.region_quadviews[i]
        
        layers = []
        for x in range(0, 20):
            if bpy.context.scene.layers[x] is True:
                layers.extend([x])
    
        objlist = context.scene.objects
    
        bgl.glEnable(bgl.GL_BLEND)
    
        for obj in objlist:
            if obj.mv.type == 'VISDIM_A':
                for x in range(0, 20):
                    if obj.layers[x] is True:
                        if x in layers:
                            opengl_dim = obj.mv.opengl_dim
                            if not opengl_dim.hide:
                                draw_dimensions(context, obj, opengl_dim, region, rv3d)
                        break
    
        #---------- restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)    
    
    else:
        return

def draw_dimensions(context, obj, opengl_dim, region, rv3d):
    scene_ogl_dim_props = bpy.context.scene.mv.opengl_dim
    
    pr = scene_ogl_dim_props.gl_precision
    fmt = "%1." + str(pr) + "f"
    
    units = scene_ogl_dim_props.gl_dim_units
    fsize = scene_ogl_dim_props.gl_font_size    
    a_size = scene_ogl_dim_props.gl_arrow_size
    a_type = scene_ogl_dim_props.gl_arrow_type
    b_type = scene_ogl_dim_props.gl_arrow_type
    
    if opengl_dim.gl_color == 0:
        rgb = scene_ogl_dim_props.gl_default_color
    elif opengl_dim.gl_color == 1:
        #WHITE
        rgb = (0.8,0.8,0.8,1.0)
    elif opengl_dim.gl_color == 2:
        #BLACK
        rgb = (0.1,0.1,0.1,1.0)        
    elif opengl_dim.gl_color == 3:
        #RED
        rgb = (0.8,0.0,0.0,1.0)
    elif opengl_dim.gl_color == 4:
        #GREEN
        rgb = (0.0,0.8,0.0,1.0)
    elif opengl_dim.gl_color == 5:
        #BLUE
        rgb = (0.0,0.0,0.8,1.0)
    elif opengl_dim.gl_color == 6:
        #YELLOW
        rgb = (0.8,0.8,0.0,1.0)          
    elif opengl_dim.gl_color == 7:
        #AQUA
        rgb = (0.0,0.8,0.8,1.0) 
    elif opengl_dim.gl_color == 8:
        #VIOLET
        rgb = (0.8,0.0,0.8,1.0)                               

    a_p1 = get_location(obj)
    
    for child in obj.children:
        if child.mv.type == 'VISDIM_B':
            b_p1 = get_location(child)
    
    dist = calc_distance(a_p1, b_p1)  

    loc = get_location(obj)
    midpoint3d = interpolate3d(a_p1, b_p1, math.fabs(dist / 2))
    vn = mathutils.Vector((midpoint3d[0] - loc[0],
                           midpoint3d[1] - loc[1],
                           midpoint3d[2] - loc[2]))

    vn.normalize()
    
    v1 = [a_p1[0], a_p1[1], a_p1[2]]
    v2 = [b_p1[0], b_p1[1], b_p1[2]]    
    
    screen_point_ap1 = get_2d_point(region, rv3d, a_p1)
    screen_point_bp1 = get_2d_point(region, rv3d, b_p1)

    if None in (screen_point_ap1,screen_point_bp1):
        return
    
    bgl.glLineWidth(opengl_dim.gl_width)
    bgl.glColor4f(rgb[0], rgb[1], rgb[2], rgb[3])
        
    midpoint3d = interpolate3d(v1, v2, math.fabs(dist / 2))
    gap3d = (midpoint3d[0], midpoint3d[1], midpoint3d[2])
    txtpoint2d = get_2d_point(region, rv3d, gap3d)
    
    if opengl_dim.gl_label == "":
        txt_dist = str(format_distance(fmt, units, dist))
    else:
        txt_dist = opengl_dim.gl_label

    draw_text(txtpoint2d[0], 
              txtpoint2d[1],
              txt_dist, 
              rgb, 
              fsize)

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(rgb[0], rgb[1], rgb[2], rgb[3])      

    draw_arrow(screen_point_ap1, screen_point_bp1, a_size, a_type, b_type)  

    draw_line(screen_point_ap1, screen_point_bp1)
    
    #TODO: FIGURE OUT HOW TO DRAW TWO LINES
#     draw_line(screen_point_ap1, end_line_point1)
#     draw_line(start_line_point1, screen_point_bp1)
    
    draw_extension_lines(screen_point_ap1, screen_point_bp1, a_size)

def draw_text(x_pos, y_pos, display_text, rgb, fsize):
    font_id = 0
    blf.size(font_id, fsize, 72)
    #- height of one line
    mwidth, mheight = blf.dimensions(font_id, "Tp")  # uses high/low letters

    # split lines
    mylines = display_text.split("|")
    idx = len(mylines) - 1
    maxwidth = 0
    maxheight = len(mylines) * mheight

    #---------- Draw all lines-+
    for line in mylines:
        text_width, text_height = blf.dimensions(font_id, line)
        # calculate new Y position
        new_y = y_pos + (mheight * idx)
        # Draw
        # Figure out how to draw the text right in the middle of the dimesion line
        # and break the line where the text is.
#         blf.position(font_id, x_pos - (text_width/2), new_y - (text_height/2), 0)

        blf.position(font_id, x_pos - (text_width/2), new_y + 3, 0)
        bgl.glColor4f(rgb[0], rgb[1], rgb[2], rgb[3])
        blf.draw(font_id, " " + line)
        
        # sub line
        idx -= 1
        # saves max width
        if maxwidth < text_width:
            maxwidth = text_width

    return maxwidth, maxheight

def format_distance(fmt, units, value, factor=1):
    scene_ogl_dim_props = bpy.context.scene.mv.opengl_dim
    getcontext().rounding = ROUND_HALF_UP
    rd_fac = Decimal(str(scene_ogl_dim_props.gl_imperial_rd_factor))
    
    s_code = "\u00bd"  # Superscript two
    
    #Unicode fraction char codes
    #1/2 "\u00bd"
    #1/4 "\u00bc"
    #1/8 "\u0d77"
    #1/16 "\u0d76"
    print(fmt)
    print(fmt % value)
    
    #---------- Units automatic
    if units == "AUTO":

        if bpy.context.scene.unit_settings.system == "IMPERIAL":
            feet = value * 3.2808399
            
            if round(feet, 2) >= 1.0:
                fmt += "'"
                tx_dist = fmt % feet
                
            else:
                inches = value * 39.3700787
                fmt += '"'
                tx_dist = fmt % inches
                
        elif bpy.context.scene.unit_settings.system == "METRIC":
            if round(value, 2) >= 1.0:
                fmt += " m"
                tx_dist = fmt % value
            else:
                if round(value, 2) >= 0.01:
                    fmt += " cm"
                    d_cm = value * 100
                    tx_dist = fmt % d_cm
                else:
                    fmt += " mm"
                    d_mm = value * 1000
                    tx_dist = fmt % d_mm
        else:
            tx_dist = fmt % value

    #---------- Units meters
    elif units == "METER":
        fmt += " m"
        tx_dist = fmt % value

    #---------- Units centimeters
    elif units == "CENTIMETER":
        fmt += " cm"
        d_cm = value * (100)
        tx_dist = fmt % d_cm

    #---------- Units millimeters
    elif units == "MILIMETER":
        fmt += " mm"
        d_mm = value * (1000)
        tx_dist = fmt % d_mm

    #---------- Units feet
    elif units == "FEET":
        fmt += "'"
        feet = value * (3.2808399)
        tx_dist = fmt % feet

    #---------- Units inches
    elif units == "INCH":
        fmt += '"'
        inches = value * 39.3700787
        dec_inches = Decimal(str(inches))
        rd_dec_inches = math.ceil(dec_inches * rd_fac)/rd_fac
        tx_dist = str(rd_dec_inches) + '"'
        
    #--------------- Default
    else:
        tx_dist = fmt % value

    return tx_dist

def draw_extension_lines(v1, v2, size=20):
    rad_a = math.radians(90)
    rad_b = math.radians(270)

    v = interpolate3d((v1[0], v1[1], 0.0), (v2[0], v2[1], 0.0), size)
    v1i = (v[0] - v1[0], v[1] - v1[1])

    v = interpolate3d((v2[0], v2[1], 0.0), (v1[0], v1[1], 0.0), size)
    v2i = (v[0] - v2[0], v[1] - v2[1])

    v1a = (int(v1i[0] * math.cos(rad_a) - v1i[1] * math.sin(rad_a) + v1[0]),
           int(v1i[1] * math.cos(rad_a) + v1i[0] * math.sin(rad_a)) + v1[1])
    v1b = (int(v1i[0] * math.cos(rad_b) - v1i[1] * math.sin(rad_b) + v1[0]),
           int(v1i[1] * math.cos(rad_b) + v1i[0] * math.sin(rad_b) + v1[1]))

    v2a = (int(v2i[0] * math.cos(rad_a) - v2i[1] * math.sin(rad_a) + v2[0]),
           int(v2i[1] * math.cos(rad_a) + v2i[0] * math.sin(rad_a)) + v2[1])
    v2b = (int(v2i[0] * math.cos(rad_b) - v2i[1] * math.sin(rad_b) + v2[0]),
           int(v2i[1] * math.cos(rad_b) + v2i[0] * math.sin(rad_b) + v2[1]))
    
    draw_line(v1, v1a)
    draw_line(v1, v1b)
    
    draw_line(v2, v2a)
    draw_line(v2, v2b)

def draw_arrow(v1, v2, size=20, a_typ="1", b_typ="1"):
    rad45 = math.radians(45)
    rad315 = math.radians(315)
    rad90 = math.radians(90)
    rad270 = math.radians(270)

    v = interpolate3d((v1[0], v1[1], 0.0), (v2[0], v2[1], 0.0), size)

    v1i = (v[0] - v1[0], v[1] - v1[1])

    v = interpolate3d((v2[0], v2[1], 0.0), (v1[0], v1[1], 0.0), size)
    v2i = (v[0] - v2[0], v[1] - v2[1])

    if a_typ == "3":
        rad_a = rad90
        rad_b = rad270
    else:
        rad_a = rad45
        rad_b = rad315

    v1a = (int(v1i[0] * math.cos(rad_a) - v1i[1] * math.sin(rad_a) + v1[0]),
           int(v1i[1] * math.cos(rad_a) + v1i[0] * math.sin(rad_a)) + v1[1])
    v1b = (int(v1i[0] * math.cos(rad_b) - v1i[1] * math.sin(rad_b) + v1[0]),
           int(v1i[1] * math.cos(rad_b) + v1i[0] * math.sin(rad_b) + v1[1]))

    if b_typ == "3":
        rad_a = rad90
        rad_b = rad270
    else:
        rad_a = rad45
        rad_b = rad315

    v2a = (int(v2i[0] * math.cos(rad_a) - v2i[1] * math.sin(rad_a) + v2[0]),
           int(v2i[1] * math.cos(rad_a) + v2i[0] * math.sin(rad_a)) + v2[1])
    v2b = (int(v2i[0] * math.cos(rad_b) - v2i[1] * math.sin(rad_b) + v2[0]),
           int(v2i[1] * math.cos(rad_b) + v2i[0] * math.sin(rad_b) + v2[1]))

    if a_typ == "1" or a_typ == "3":
        draw_line(v1, v1a)
        draw_line(v1, v1b)

    if b_typ == "1" or b_typ == "3":
        draw_line(v2, v2a)
        draw_line(v2, v2b)

    if a_typ == "2":
        draw_triangle(v1, v1a, v1b)
    if b_typ == "2":
        draw_triangle(v2, v2a, v2b)

#     draw_line(v1, v2)

def draw_line(v1, v2):
    # noinspection PyBroadException
    try:
        if v1 is not None and v2 is not None:
            bgl.glBegin(bgl.GL_LINES)
            bgl.glVertex2f(*v1)
            bgl.glVertex2f(*v2)
            bgl.glEnd()
    except:
        pass

def draw_triangle(v1, v2, v3):
    # noinspection PyBroadException
    try:
        if v1 is not None and v2 is not None and v3 is not None:
            bgl.glBegin(bgl.GL_TRIANGLES)
            bgl.glVertex2f(*v1)
            bgl.glVertex2f(*v2)
            bgl.glVertex2f(*v3)
            bgl.glEnd()
    except:
        pass

def get_2d_point(region, rv3d, point3d):
    if rv3d is not None and region is not None:
        return view3d_utils.location_3d_to_region_2d(region, rv3d, point3d)
    else:
        return get_render_location(point3d)

def get_render_location(mypoint):
    v1 = mathutils.Vector(mypoint)
    scene = bpy.context.scene
    co_2d = object_utils.world_to_camera_view(scene, scene.camera, v1)
    # Get pixel coords
    render_scale = scene.render.resolution_percentage / 100
    render_size = (int(scene.render.resolution_x * render_scale),
                   int(scene.render.resolution_y * render_scale))

    return [round(co_2d.x * render_size[0]), round(co_2d.y * render_size[1])]

def interpolate3d(v1, v2, d1):
    # calculate vector
    v = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])
    # calculate distance between points
    d0 = calc_distance(v1, v2)

    # calculate interpolate factor (distance from origin / distance total)
    # if d1 > d0, the point is projected in 3D space
    if d0 > 0:
        x = d1 / d0
    else:
        x = d1

    final = (v1[0] + (v[0] * x), v1[1] + (v[1] * x), v1[2] + (v[2] * x))
    return final

def get_location(mainobject):
    # Using World Matrix
    m4 = mainobject.matrix_world

    return [m4[0][3], m4[1][3], m4[2][3]]

def render_opengl(self, context):
    from math import ceil

    layers = []
    scene = context.scene
    for x in range(0, 20):
        if scene.layers[x] is True:
            layers.extend([x])

    objlist = context.scene.objects
    render_scale = scene.render.resolution_percentage / 100

    width = int(scene.render.resolution_x * render_scale)
    height = int(scene.render.resolution_y * render_scale)
    
    # I cant use file_format becuase the pdf writer needs jpg format
    # the file_format returns 'JPEG' not 'JPG'
#     file_format = context.scene.render.image_settings.file_format.lower()
    ren_path = bpy.path.abspath(bpy.context.scene.render.filepath) + ".jpg"
    
#     if len(ren_path) > 0:
#         if ren_path.endswith(os.path.sep):
#             initpath = os.path.realpath(ren_path) + os.path.sep
#         else:
#             (initpath, filename) = os.path.split(ren_path)
#         outpath = os.path.join(initpath, "ogl_tmp.png")
#     else:
#         self.report({'ERROR'}, "Invalid render path")
#         return False

    img = get_render_image(ren_path)
    
    if img is None:
        self.report({'ERROR'}, "Invalid render path:" + ren_path)
        return False

    tile_x = 240
    tile_y = 216
    row_num = ceil(height / tile_y)
    col_num = ceil(width / tile_x)
    
    cut4 = (col_num * tile_x * 4) - width * 4  
    totpixel4 = width * height * 4 

    viewport_info = bgl.Buffer(bgl.GL_INT, 4)
    bgl.glGetIntegerv(bgl.GL_VIEWPORT, viewport_info)
    
    img.gl_load(0, bgl.GL_NEAREST, bgl.GL_NEAREST)

    # 2.77 API change
    if bpy.app.version >= (2, 77, 0):
        tex = img.bindcode[0]
    else:
        tex = img.bindcode
    
    if context.scene.name in bpy.data.images:
        old_img = bpy.data.images[context.scene.name]
        old_img.user_clear()
        bpy.data.images.remove(old_img)
             
    img_result = bpy.data.images.new(context.scene.name, width, height)        
    
    tmp_pixels = [1] * totpixel4

    #---------- Loop for all tiles
    for row in range(0, row_num):
        for col in range(0, col_num):
            buffer = bgl.Buffer(bgl.GL_FLOAT, width * height * 4)
            bgl.glDisable(bgl.GL_SCISSOR_TEST)  # if remove this line, get blender screenshot not image
            bgl.glViewport(0, 0, tile_x, tile_y)

            bgl.glMatrixMode(bgl.GL_PROJECTION)
            bgl.glLoadIdentity()

            # defines ortographic view for single tile
            x1 = tile_x * col
            y1 = tile_y * row
            bgl.gluOrtho2D(x1, x1 + tile_x, y1, y1 + tile_y)

            # Clear
            bgl.glClearColor(0.0, 0.0, 0.0, 0.0)
            bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)

            bgl.glEnable(bgl.GL_TEXTURE_2D)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, tex)

            # defines drawing area
            bgl.glBegin(bgl.GL_QUADS)

            bgl.glColor3f(1.0, 1.0, 1.0)
            bgl.glTexCoord2f(0.0, 0.0)
            bgl.glVertex2f(0.0, 0.0)

            bgl.glTexCoord2f(1.0, 0.0)
            bgl.glVertex2f(width, 0.0)

            bgl.glTexCoord2f(1.0, 1.0)
            bgl.glVertex2f(width, height)

            bgl.glTexCoord2f(0.0, 1.0)
            bgl.glVertex2f(0.0, height)

            bgl.glEnd()

            for obj in objlist:
                if obj.mv.type == 'VISDIM_A':
                    for x in range(0, 20):
                        if obj.layers[x] is True:
                            if x in layers:
                                opengl_dim = obj.mv.opengl_dim
                                if not opengl_dim.hide:
                                    draw_dimensions(context, obj, opengl_dim, None, None)
                            break 

            #---------- copy pixels to temporary area
            bgl.glFinish()
            bgl.glReadPixels(0, 0, width, height, bgl.GL_RGBA, bgl.GL_FLOAT, buffer)  # read image data
            for y in range(0, tile_y):
                # final image pixels position
                p1 = (y * width * 4) + (row * tile_y * width * 4) + (col * tile_x * 4)
                p2 = p1 + (tile_x * 4)
                # buffer pixels position
                b1 = y * width * 4
                b2 = b1 + (tile_x * 4)

                if p1 < totpixel4:  # avoid pixel row out of area
                    if col == col_num - 1:  # avoid pixel columns out of area
                        p2 -= cut4
                        b2 -= cut4

                    tmp_pixels[p1:p2] = buffer[b1:b2]

    img_result.pixels = tmp_pixels[:]
    img.gl_free()

    img.user_clear()
    bpy.data.images.remove(img)
    os.remove(ren_path)
    bgl.glEnable(bgl.GL_SCISSOR_TEST)

    #---------- restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    
    if img_result is not None:            
        return img_result

def get_render_image(outpath):
    saved = False
    try:
        try:
            result = bpy.data.images['Render Result']
            if result.has_data is False:
                result.save_render(outpath)
                saved = True
        except:
            print("No render image found")
            return None

        if saved is False:
            result.save_render(outpath)

        img = img_utils.load_image(outpath)

        return img
    except:
        print("Unexpected render image error")
        return None

def get_2d_renderings(context):
    file_name = bpy.path.basename(context.blend_data.filepath).replace(".blend","")
    write_dir = os.path.join(bpy.app.tempdir, file_name)
    if not os.path.exists(write_dir): os.mkdir(write_dir)
    
    bpy.ops.fd_scene.prepare_2d_elevations()
    
    images = []
    
    #Render Each Scene
    for scene in bpy.data.scenes:
        if scene.mv.elevation_scene:
            context.screen.scene = scene

            # Set Render 2D Properties
            rd = context.scene.render
            rl = rd.layers.active
            freestyle_settings = rl.freestyle_settings
            rd.filepath = os.path.join(write_dir,scene.name)
            rd.image_settings.file_format = 'JPEG'
            rd.engine = 'BLENDER_RENDER'
            rd.use_freestyle = True
            rd.line_thickness = 0.75
            rd.resolution_percentage = 100
            rl.use_pass_combined = False
            rl.use_pass_z = False
            freestyle_settings.crease_angle = 2.617994
            
            # If File already exists then first remove it or this will cause Blender to crash
            if os.path.exists(bpy.path.abspath(context.scene.render.filepath) + context.scene.render.file_extension):
                os.remove(bpy.path.abspath(context.scene.render.filepath) + context.scene.render.file_extension)            
            
            bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
            
            render_image = bpy.path.abspath(context.scene.render.filepath) + context.scene.render.file_extension
            
            # Wait for Image to render before drawing opengl 
            while not os.path.exists(render_image):
                time.sleep(0.1)
            
            img_result = render_opengl(None,context)
            img_result.save_render(render_image)
             
            if os.path.exists(render_image):
                images.append(render_image)

    bpy.ops.fd_scene.clear_2d_views()
    imgs_to_remove = []
        
    for img in bpy.data.images:
        if img.users == 0:
            imgs_to_remove.append(img)
        
    for im in imgs_to_remove:
        print(im.name)
        bpy.data.images.remove(im)
            
    return images
        
def get_custom_font():
    if "Calibri-Light" in bpy.data.fonts:
        return bpy.data.fonts["Calibri-Light"]
    else:
        return bpy.data.fonts.load(os.path.join(os.path.dirname(bpy.app.binary_path),"Fonts","calibril.ttf"))        
        