# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy, bgl, blf
import math
from bpy.types import Header, Menu, Operator, UIList, PropertyGroup

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty,
                       EnumProperty,
                       CollectionProperty)
import os
from mv import utils, fd_types, unit
import inspect
import subprocess
import sys

from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper,
                                 axis_conversion,
                                 )

import itertools
from mathutils import Matrix

PROJECTS = os.path.join(bpy.utils.user_resource('DATAFILES'), "projects")
THUMBNAIL_FILE_NAME = "thumbnail.blend"

def set_wire_and_xray(obj,turn_on):
    if turn_on:
        obj.draw_type = 'WIRE'
    else:
        obj.draw_type = 'TEXTURED'
    obj.show_x_ray = turn_on
    for child in obj.children:
        set_wire_and_xray(child,turn_on)

def get_thumbnail_path():
    return os.path.join(os.path.dirname(bpy.app.binary_path),THUMBNAIL_FILE_NAME)

class OPS_drag_and_drop(Operator):
    """SPECIAL OPERATOR: This is called when you drop an image to the 3dview space"""
    bl_idname = "fd_dragdrop.drag_and_drop"
    bl_label = "Drag and Drop"
#     bl_options = {'UNDO'}
 
    #READONLY
    filepath = StringProperty(name="Filepath",
                              subtype='FILE_PATH')
    objectname = StringProperty(name="Object Name")
 
    def invoke(self, context, event):
        dir, file = os.path.split(self.filepath)
        path, category_name = os.path.split(dir)
        path, library_name = os.path.split(path)
        filename, ext = os.path.splitext(file)
        library_tabs = context.scene.mv.ui.library_tabs

        if library_tabs == 'PRODUCT':
            bpy.ops.fd_general.drop_product('INVOKE_DEFAULT',
                                            product_name = filename,
                                            category_name = category_name,
                                            library_name = library_name)
        if library_tabs == 'INSERT':
            bpy.ops.fd_general.drop_insert('INVOKE_DEFAULT',
                                            product_name = filename,
                                            category_name = category_name,
                                            library_name = library_name)
        if library_tabs == 'ASSEMBLY':
            bpy.ops.fd_general.drop_assembly('INVOKE_DEFAULT',filepath = self.filepath)
        if library_tabs == 'OBJECT':
            bpy.ops.fd_general.drop_object('INVOKE_DEFAULT',filepath = self.filepath)
        if library_tabs == 'MATERIAL':
            bpy.ops.fd_general.drop_material('INVOKE_DEFAULT',filepath = self.filepath)
        if library_tabs == 'WORLD':
            bpy.ops.fd_general.drop_world('INVOKE_DEFAULT',filepath = self.filepath,world_name = filename)           
        return {'FINISHED'}

class OPS_drop_product(Operator):
    """ This will be called when you drop a cabinet in the 3D viewport.
    """
    bl_idname = "fd_general.drop_product"
    bl_label = "Drop Product"
    bl_description = "This will add a product to the scene"
#     bl_options = {'UNDO'}

    product_name = StringProperty(name="Product Name")
    category_name = StringProperty(name="Category Name")
    library_name = StringProperty(name="Library Name")

    product = None
    default_z_loc = 0.0
    default_height = 0.0
    default_depth = 0.0
    
    floor = None
    
    header_text = "Place Product   (Esc, Right Click) = Cancel Command  : (Left Click) = Place Product : (Right Click) = Show Wall Placement Options"

    def execute(self, context):
        return {'FINISHED'}

    def assign_boolean(self,obj):
        if obj:
            objs = utils.get_child_objects(self.product.obj_bp)
            for obj_bool in objs:
                if obj_bool.mv.use_as_bool_obj:
                    mod = obj.modifiers.new(obj_bool.name,'BOOLEAN')
                    mod.object = obj_bool
                    mod.operation = 'DIFFERENCE'

    def __del__(self):
        utils.delete_obj_list([self.floor])
        bpy.context.area.header_text_set()

    def get_product(self,context):
        import time
        start_time = time.time()
        bpy.ops.object.select_all(action='DESELECT')
        lib = context.window_manager.cabinetlib.lib_products[self.library_name]
        blend_path = os.path.join(lib.lib_path,self.category_name,self.product_name + ".blend")
        obj_bp = None
        if os.path.exists(blend_path):
            obj_bp = utils.get_group(blend_path)
            self.product = fd_types.Assembly(obj_bp)
        else:
            self.product = utils.get_product_class(context,self.library_name,self.category_name,self.product_name)
        if self.product:
            if obj_bp:
                if self.product.obj_bp.mv.update_id != "":
                    eval('bpy.ops.' + self.product.obj_bp.mv.update_id + '("INVOKE_DEFAULT",object_name=self.product.obj_bp.name)')
            else:
                self.product.draw()
                self.product.update()
                    
            utils.init_objects(self.product.obj_bp)
            self.default_z_loc = self.product.obj_bp.location.z
            self.default_height = self.product.obj_z.location.z
            self.default_depth = self.product.obj_y.location.y
            set_wire_and_xray(self.product.obj_bp,True)
            print(self.product.obj_bp.mv.name_object + ": Draw Time --- %s seconds ---" % (time.time() - start_time))

    def draw_floor(self,context):
        bpy.ops.mesh.primitive_plane_add()
        self.floor = context.active_object
        self.floor.location = (0,0,0)
        self.floor.draw_type = 'WIRE'
        self.floor.dimensions = (100,100,1)

    def invoke(self,context,event):
        context.window.cursor_set('WAIT')
        self.draw_floor(context)
#         selected_point, selected_obj = utils.get_selection_point(context,event)
        self.get_product(context)     
        if self.product is None:
            bpy.ops.fd_general.error('INVOKE_DEFAULT',message="Could Not Find Product Class: " + "\\" + self.library_name + "\\" + self.category_name + "\\" + self.product_name)
            return {'CANCELLED'}
        if self.product.obj_bp.mv.drop_id != "":
            eval('bpy.ops.' + self.product.obj_bp.mv.drop_id + '("INVOKE_DEFAULT",object_name=self.product.obj_bp.name)')
            return {'FINISHED'}
        context.window.cursor_set('PAINT_BRUSH')
        context.scene.update() # THE SCENE MUST BE UPDATED FOR RAY CAST TO WORK
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel_drop(self,context,event):
        if self.product:
            utils.delete_object_and_children(self.product.obj_bp)
        bpy.context.window.cursor_set('DEFAULT')
#         bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        return {'FINISHED'}

    def set_xray(self,turn_on=True):
        if turn_on:
            draw_type = 'WIRE'
        else:
            draw_type = 'TEXTURED'
        for child in self.product.obj_bp.children:
            child.draw_type = draw_type
            child.show_x_ray = turn_on
            for nchild in child.children:
                nchild.draw_type = draw_type
                nchild.show_x_ray = turn_on
                for nnchild in nchild.children:
                    nnchild.draw_type = draw_type
                    nnchild.show_x_ray = turn_on

    def get_placement(self,sel_product,cursor_location):
        """ Placement depends on mouse position
            If the mouse location is closer to the obj_bp then placement is on LEFT
            If the mouse location is closer to the obj_x then placement is on RIGHT 
            If the products don't collide in z then placement is on CENTER 
        """
        if self.product.has_height_collision(sel_product):
            sel_product_world_loc = (sel_product.obj_bp.matrix_world[0][3],
                                     sel_product.obj_bp.matrix_world[1][3],
                                     sel_product.obj_bp.matrix_world[2][3])
            
            sel_product_x_world_loc = (sel_product.obj_x.matrix_world[0][3],
                                       sel_product.obj_x.matrix_world[1][3],
                                       sel_product.obj_x.matrix_world[2][3])
            
            dist_to_bp = utils.calc_distance(cursor_location,sel_product_world_loc)
            dist_to_x = utils.calc_distance(cursor_location,sel_product_x_world_loc)
            if dist_to_bp < dist_to_x:
                return 'LEFT'
            else:
                return 'RIGHT'
        else:
            return 'CENTER'

    def product_drop(self,context,event):
        selected_point, selected_obj = utils.get_selection_point(context,event,floor=self.floor)
        self.mouse_loc = (event.mouse_region_x,event.mouse_region_y)
        obj_wall_bp = utils.get_wall_bp(selected_obj)
        wall = fd_types.Wall(obj_wall_bp)
        obj_product_bp = utils.get_bp(selected_obj,'PRODUCT')
        sel_product = None
        if obj_product_bp:
            sel_product = fd_types.Assembly(obj_product_bp)
            placement = self.get_placement(sel_product, selected_point)
            rot = sel_product.obj_bp.rotation_euler.z
            if wall.obj_bp:
                rot += wall.obj_bp.rotation_euler.z

            if placement == 'LEFT':
                add_x_loc = 0
                add_y_loc = 0
                if sel_product.obj_bp.mv.placement_type == 'Corner':
                    rot += math.radians(90)
                    add_x_loc = math.cos(rot) * sel_product.obj_y.location.y
                    add_y_loc = math.sin(rot) * sel_product.obj_y.location.y
                x_loc = sel_product.obj_bp.matrix_world[0][3] - math.cos(rot) * self.product.obj_x.location.x + add_x_loc
                y_loc = sel_product.obj_bp.matrix_world[1][3] - math.sin(rot) * self.product.obj_x.location.x + add_y_loc
            
            if placement == 'RIGHT':
                self.mouse_text = "Place on Right"
                x_loc = sel_product.obj_bp.matrix_world[0][3] + math.cos(rot) * sel_product.obj_x.location.x
                y_loc = sel_product.obj_bp.matrix_world[1][3] + math.sin(rot) * sel_product.obj_x.location.x
            
            if placement == 'CENTER':
                self.mouse_text = "Place on Center"
                x_loc = sel_product.obj_bp.matrix_world[0][3] - math.cos(rot) * ((self.product.obj_x.location.x/2) - (sel_product.obj_x.location.x/2))
                y_loc = sel_product.obj_bp.matrix_world[1][3] - math.sin(rot) * ((self.product.obj_x.location.x/2) - (sel_product.obj_x.location.x/2))
            
            self.product.obj_bp.rotation_euler.z = rot
            self.product.obj_bp.location.x = x_loc
            self.product.obj_bp.location.y = y_loc

        elif wall.obj_bp and obj_product_bp is None:
            self.product.obj_bp.rotation_euler = wall.obj_bp.rotation_euler
            self.product.obj_bp.location.x = selected_point[0]
            self.product.obj_bp.location.y = selected_point[1]
            obj_bp = utils.get_assembly_bp(selected_obj)
            rot = wall.obj_bp.rotation_euler.z
            if obj_bp:
                sel_assembly = fd_types.Assembly(obj_bp)
                if sel_assembly:
                    placement = self.get_placement(sel_assembly, selected_point)
                    if placement == 'LEFT':
                        x_loc = sel_assembly.obj_bp.matrix_world[0][3] - math.cos(rot) * self.product.obj_x.location.x
                        y_loc = sel_assembly.obj_bp.matrix_world[1][3] - math.sin(rot) * self.product.obj_x.location.x
                    if placement == 'RIGHT':
                        x_loc = sel_assembly.obj_bp.matrix_world[0][3] + math.cos(rot) * sel_assembly.obj_x.location.x
                        y_loc = sel_assembly.obj_bp.matrix_world[1][3] + math.sin(rot) * sel_assembly.obj_x.location.x
                    if placement == 'CENTER':
                        x_loc = sel_assembly.obj_bp.matrix_world[0][3] - math.cos(rot) * ((self.product.obj_x.location.x/2) - (sel_assembly.obj_x.location.x/2))
                        y_loc = sel_assembly.obj_bp.matrix_world[1][3] - math.sin(rot) * ((self.product.obj_x.location.x/2) - (sel_assembly.obj_x.location.x/2))
            
                    self.product.obj_bp.rotation_euler.z = rot
                    self.product.obj_bp.location.x = x_loc
                    self.product.obj_bp.location.y = y_loc
            
        else:
            self.product.obj_bp.location.x = selected_point[0]
            self.product.obj_bp.location.y = selected_point[1]
            
        if event.type == 'LEFTMOUSE':
            if sel_product and sel_product.obj_bp.mv.placement_type == 'Corner':
                next_wall = sel_product.get_next_wall(placement)
                if next_wall:
                    obj_wall_bp = next_wall.obj_bp
                else:
                    if placement == 'RIGHT' and sel_product.obj_bp.rotation_euler.z != 0:
                        obj_wall_bp = None
                    if placement == 'LEFT' and round(sel_product.obj_bp.rotation_euler.z,2) != round(math.radians(-90),2):
                        obj_wall_bp = None

            if obj_wall_bp:
                x_loc = utils.calc_distance((self.product.obj_bp.location.x,self.product.obj_bp.location.y,0),
                                        (obj_wall_bp.matrix_local[0][3],obj_wall_bp.matrix_local[1][3],0))
                self.product.obj_bp.location = (0,0,self.product.obj_bp.location.z)
                self.product.obj_bp.rotation_euler = (0,0,0)
                self.product.obj_bp.parent = obj_wall_bp
                self.product.obj_bp.location.x = x_loc
                
            self.assign_boolean(selected_obj)
            set_wire_and_xray(self.product.obj_bp,False)
            self.product.obj_bp.select = True
            context.scene.objects.active = self.product.obj_bp
            bpy.context.window.cursor_set('DEFAULT')
            return {'FINISHED'}

        if event.type == 'RIGHTMOUSE':
            if obj_wall_bp:
                x_loc = utils.calc_distance((self.product.obj_bp.location.x,self.product.obj_bp.location.y,0),
                                        (obj_wall_bp.matrix_local[0][3],obj_wall_bp.matrix_local[1][3],0))
                self.product.obj_bp.location = (0,0,self.product.obj_bp.location.z)
                self.product.obj_bp.rotation_euler = (0,0,0)
                self.product.obj_bp.parent = obj_wall_bp
                self.product.obj_bp.location.x = x_loc
                self.assign_boolean(selected_obj)
                bpy.ops.fd_general.place_product('INVOKE_DEFAULT',object_name=self.product.obj_bp.name)
                set_wire_and_xray(self.product.obj_bp,False)
                bpy.context.window.cursor_set('DEFAULT')
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        context.area.tag_redraw()
        context.area.header_text_set(text=self.header_text)
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        
        if event.type in {'ESC'}:
            self.cancel_drop(context,event)
            return {'FINISHED'}
        
        return self.product_drop(context,event)

class OPS_drop_insert(Operator):
    """ This will be called when you drop a cabinet in the 3D viewport.
    """
    bl_idname = "fd_general.drop_insert"
    bl_label = "Drop Insert"
    bl_description = "This will add an insert to the scene"

    product_name = StringProperty(name="Product Name")
    category_name = StringProperty(name="Category Name")
    library_name = StringProperty(name="Library Name")
    filepath = StringProperty(name="Filepath") #MAYBE DONT NEED THIS?

    insert = None
    default_z_loc = 0.0
    default_height = 0.0
    default_depth = 0.0
    
    openings = []
    objects = []
    
    header_text = "Place Insert   (Esc, Right Click) = Cancel Command  :  (Left Click) = Place Insert"
    
    def execute(self, context):
        return {'FINISHED'}

    def __del__(self):
        bpy.context.area.header_text_set()

    def get_insert(self,context):
        bpy.ops.object.select_all(action='DESELECT')
        lib = context.window_manager.cabinetlib.lib_inserts[self.library_name]
        blend_path = os.path.join(lib.lib_path,self.category_name,self.product_name + ".blend")
        obj_bp = None
        if os.path.exists(blend_path):
            obj_bp = utils.get_group(blend_path)
            self.insert = fd_types.Assembly(obj_bp)
        else:
            self.insert = utils.get_insert_class(context,self.library_name,self.category_name,self.product_name)

        if obj_bp:
            pass
        #TODO: SET UP UPDATE OPERATOR
#                 self.insert.update(obj_bp)
        else:
            self.insert.draw()
            self.insert.update()
            
        self.show_openings()
        utils.init_objects(self.insert.obj_bp)
        self.default_z_loc = self.insert.obj_bp.location.z
        self.default_height = self.insert.obj_z.location.z
        self.default_depth = self.insert.obj_y.location.y

    def invoke(self,context,event):
        context.window.cursor_set('WAIT')
        self.get_insert(context)
        if self.insert is None:
            bpy.ops.fd_general.error('INVOKE_DEFAULT',message="Could Not Find Insert Class: " + "\\" + self.library_name + "\\" + self.category_name + "\\" + self.product_name)
            return {'CANCELLED'}
        context.window.cursor_set('PAINT_BRUSH')
        context.scene.update() # THE SCENE MUST BE UPDATED FOR RAY CAST TO WORK
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel_drop(self,context,event):
        if self.insert:
            utils.delete_object_and_children(self.insert.obj_bp)
        bpy.context.window.cursor_set('DEFAULT')
        return {'FINISHED'}

    def show_openings(self):
        insert_type = self.insert.obj_bp.mv.placement_type
        for obj in  bpy.context.scene.objects:
            if obj.layers[0]: #Make sure wall is not hidden
                opening = None
                if obj.mv.type_group == 'OPENING':
                    if insert_type in {'INTERIOR','SPLITTER'}:
                        opening = fd_types.Assembly(obj) if obj.mv.interior_open else None
                    if insert_type == 'EXTERIOR':
                        opening = fd_types.Assembly(obj) if obj.mv.exterior_open else None
                    if opening:
                        cage = opening.get_cage()
                        opening.obj_x.hide = True
                        opening.obj_y.hide = True
                        opening.obj_z.hide = True
                        cage.hide_select = False
                        cage.hide = False
                        self.objects.append(cage)

    def selected_opening(self,selected_obj):
        if selected_obj:
            opening = fd_types.Assembly(selected_obj.parent)
            self.insert.obj_bp.parent = opening.obj_bp.parent
            self.insert.obj_bp.location = opening.obj_bp.location
            self.insert.obj_bp.rotation_euler = opening.obj_bp.rotation_euler
            self.insert.obj_x.location.x = opening.obj_x.location.x
            self.insert.obj_y.location.y = opening.obj_y.location.y
            self.insert.obj_z.location.z = opening.obj_z.location.z
            utils.run_calculators(self.insert.obj_bp)
            return opening
            
    def set_opening_name(self,obj,name):
        obj.mv.opening_name = name
        for child in obj.children:
            self.set_opening_name(child, name)
        
    def place_insert(self,opening):
        if self.insert.obj_bp.mv.placement_type == 'INTERIOR':
            opening.obj_bp.mv.interior_open = False
        if self.insert.obj_bp.mv.placement_type == 'EXTERIOR':
            opening.obj_bp.mv.exterior_open = False
        if self.insert.obj_bp.mv.placement_type == 'SPLITTER':
            opening.obj_bp.mv.interior_open = False
            opening.obj_bp.mv.exterior_open = False

        utils.copy_assembly_drivers(opening,self.insert)
        #DONT ASSIGN PROPERTIES ID's SO USERS CAN ACCESS PROPERTIES FOR INSERTS USED IN CLOSET LIBRARY
#         cabinet_utils.set_property_id(self.insert.obj_bp,opening.obj_bp.mv.property_id)
        self.set_opening_name(self.insert.obj_bp, opening.obj_bp.mv.opening_name)
        
        for obj in self.objects:
            obj.hide = True
            obj.hide_render = True
            obj.hide_select = True

    def insert_drop(self,context,event):
        if len(self.objects) == 0:
            bpy.ops.fd_general.error('INVOKE_DEFAULT',message="There are no openings in this scene.")
            return self.cancel_drop(context,event)
        else:
            selected_point, selected_obj = utils.get_selection_point(context,event,objects=self.objects)
            bpy.ops.object.select_all(action='DESELECT')
            selected_opening = self.selected_opening(selected_obj)
            if selected_opening:
                selected_obj.select = True
    
                if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                    self.place_insert(selected_opening)
                    context.scene.objects.active = self.insert.obj_bp
                    # THIS NEEDS TO BE RUN TWICE TO AVOID RECAL ERRORS
                    utils.run_calculators(self.insert.obj_bp)
                    utils.run_calculators(self.insert.obj_bp)

                    bpy.context.window.cursor_set('DEFAULT')
                    return {'FINISHED'}

            return {'RUNNING_MODAL'}

    def modal(self, context, event):
        context.area.tag_redraw()
        context.area.header_text_set(text=self.header_text)
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        
        if event.type in {'ESC','RIGHTMOUSE'}:
            self.cancel_drop(context,event)
            return {'FINISHED'}
        
        return self.insert_drop(context,event)

class OPS_drop_material(Operator):
    bl_idname = "fd_general.drop_material"
    bl_label = "Assign Materials"
#     bl_options = {'UNDO'}
    
    #READONLY
    filepath = StringProperty(name="Material Name")

    material = None

    header_text = "Place Material   (Esc, Right Click) = Cancel Command  :  (HOLD Shift) = Recursive Assignment : (Left Click) = Assign to Material Pointer"

    def __del__(self):
        bpy.context.area.header_text_set()

    def get_material(self,context):
        path, filename = os.path.split(self.filepath)
        file, ext = os.path.splitext(filename)
        path2, folder_dir = os.path.split(path)
        print('MAT PATH',path2)
        if path2 == utils.get_library_dir("materials"):
            self.material = utils.get_material((folder_dir,),file)
        else:
            path2, folder_dir = os.path.split(path)
            path3, folder_dir2 = os.path.split(path2)
            self.material = utils.get_material((folder_dir2,folder_dir),file)
        
    def cancel_drop(self,context,event):
        context.window.cursor_set('DEFAULT')
        return {'FINISHED'}
        
    def modal(self, context, event):
        context.window.cursor_set('PAINT_BRUSH')
        context.area.tag_redraw()
        context.area.header_text_set(text=self.header_text)
        selected_point, selected_obj = utils.get_selection_point(context,event)
        bpy.ops.object.select_all(action='DESELECT')
        if selected_obj:
            selected_obj.select = True
            
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if selected_obj and selected_obj.type == 'MESH':
                
                if len(selected_obj.data.uv_textures) == 0:
                    bpy.ops.fd_object.unwrap_mesh(object_name=selected_obj.name)
                if len(selected_obj.material_slots) > 1:
                    bpy.ops.fd_material.assign_material('INVOKE_DEFAULT',material_name = self.material.name, object_name = selected_obj.name)
                    return self.cancel_drop(context,event)
                else:
                    if len(selected_obj.material_slots) == 0:
                        bpy.ops.fd_object.add_material_slot(object_name=selected_obj.name)
                    
                    for i, mat in enumerate(selected_obj.material_slots):
                        mat.material = self.material
                        
#                     if self.material.name not in context.scene.materiallib.scene_materials:
#                         material = context.scene.materiallib.scene_materials.add()
#                         material.name = mat.name
                
                if event.shift:
                    self.get_material(context)
                    context.window.cursor_set('PAINT_BRUSH')
                else:
                    return self.cancel_drop(context,event)
                
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            bpy.ops.fd_material.assign_material_interface('INVOKE_DEFAULT',filepath = self.filepath)
            return self.cancel_drop(context,event)
            
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
            
        if event.type == 'ESC':
            return self.cancel_drop(context,event)
            
        return {'RUNNING_MODAL'}
        
    def execute(self,context):
        path, ext = os.path.splitext(self.filepath)
        if ext == '.blend':
            bpy.ops.fd_general.open_blend_file('INVOKE_DEFAULT',filepath=self.filepath)
            return {'FINISHED'}
        self.get_material(context)
        if self.material is None:
            path, image_file = os.path.split(self.filepath)
            img_file_name, img_ext = os.path.splitext(image_file) 
            bpy.ops.fd_general.error('INVOKE_DEFAULT',message="Could Not Find " + img_file_name)
            return {'FINISHED'}
        else:
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
    
class OPS_drop_assembly(Operator):
    bl_idname = "fd_general.drop_assembly"
    bl_label = "Drop Assembly"
#     bl_options = {'UNDO'}
    
    #READONLY
    filepath = StringProperty(name="FilePath")
    type_insert = StringProperty(name="Type Insert")
    
    item_name = None
    dir_name = ""
    
    group = None
    assembly = None
    
    cages = []
    machining_objs = []
    
    header_text = "Place Assembly   (Esc, Right Click) = Cancel Command  :  (Left Click) = Place Assembly"

    def __del__(self):
        bpy.context.area.header_text_set()

    def get_assembly(self,context):
        file, ext = os.path.splitext(self.filepath)
        obj_bp = utils.get_group(file+'.blend')
        if obj_bp:
            self.assembly = fd_types.Assembly(obj_bp)
        else:
            print("NO BP FOODNDOS")
    
    def invoke(self, context, event):
        self.cages = []
        self.machining_objs = []
        self.get_assembly(context)

        context.window.cursor_set('PAINT_BRUSH')
        context.scene.update() # THE SCENE MUST BE UPDATED FOR RAY CAST TO WORK
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel_drop(self,context,event):
        if self.assembly:
            utils.delete_object_and_children(self.assembly.obj_bp)
        bpy.context.window.cursor_set('DEFAULT')
        return {'FINISHED'}

    def set_child_properties(self,obj):
        for child in obj.children:
            utils.assign_materials_from_pointers(child)
            if child.mv.use_as_bool_obj:
                self.machining_objs.append(child)
                child.hide = True
                child.draw_type = 'WIRE'
            if child.cabinetlib.type_mesh != 'MACHINING':
                child.draw_type = 'TEXTURED'
            if child.mv.type == 'CAGE':
                self.cages.append(child)
            self.set_child_properties(child)

    def assembly_drop(self,context,event):
        selected_point, selected_obj = utils.get_selection_point(context,event)
        bpy.ops.object.select_all(action='DESELECT')
        obj_wall_bp = utils.get_wall_bp(selected_obj)
        if obj_wall_bp:
            self.assembly.obj_bp.rotation_euler = obj_wall_bp.rotation_euler
        self.assembly.obj_bp.location = selected_point
        
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.set_child_properties(self.assembly.obj_bp)

            if selected_obj:
                for machining_obj in self.machining_objs:
                    mod = selected_obj.modifiers.new('Cutout',type='BOOLEAN')
                    mod.operation = 'DIFFERENCE'
                    mod.object = machining_obj   
                    utils.delete_obj_list(self.cages)

            bpy.ops.object.select_all(action='DESELECT')
            self.assembly.delete_cage()
            self.assembly.obj_bp.select = True
            context.scene.objects.active = self.assembly.obj_bp
            bpy.context.window.cursor_set('DEFAULT')
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        context.area.tag_redraw()
        context.area.header_text_set(text=self.header_text)
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        
        if event.type in {'ESC'}:
            self.cancel_drop(context,event)
            return {'FINISHED'}
        
        return self.assembly_drop(context,event)
    
class OPS_drop_object(Operator):
    bl_idname = "fd_general.drop_object"
    bl_label = "Drop Object"
#     bl_options = {'UNDO'}
    
    #READONLY
    filepath = StringProperty(name="Material Name")

    item_name = None
    dir_name = ""
    
    obj = None
    file_name = ""
    
    cages = []
    
    header_text = "Place Object   (Esc, Right Click) = Cancel Command  :  (Left Click) = Place Object"
    
    def __del__(self):
        bpy.context.area.header_text_set()
    
    def get_object(self,context):
        file, ext = os.path.splitext(self.filepath)
        self.obj = utils.get_object(file+".blend")

    def invoke(self, context, event):
        self.get_object(context)
        self.obj.draw_type = 'WIRE'
        context.window.cursor_set('PAINT_BRUSH')
        context.scene.update() # THE SCENE MUST BE UPDATED FOR RAY CAST TO WORK
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel_drop(self,context,event):
        objs  = []
        objs.append(self.obj)
        utils.delete_obj_list(objs)
        bpy.context.window.cursor_set('DEFAULT')
        return {'FINISHED'}

    def object_drop(self,context,event):
        selected_point, selected_obj = utils.get_selection_point(context,event)
        bpy.ops.object.select_all(action='DESELECT')
        obj_product_bp = utils.get_bp(selected_obj,'PRODUCT')
        self.obj.location = selected_point

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.obj.draw_type = 'TEXTURED'
            bpy.context.window.cursor_set('DEFAULT')
            utils.assign_materials_from_pointers(self.obj)
            context.scene.objects.active = self.obj
            self.obj.select = True
            self.obj.mv.name_object = self.file_name
            return {'FINISHED'}
        
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            if selected_obj and selected_obj.parent:
                if selected_obj.parent.mv.type == 'BPWALL':
                    self.obj.draw_type = 'TEXTURED'
                    bpy.context.window.cursor_set('DEFAULT')
                    utils.assign_materials_from_pointers(self.obj)
                    context.scene.objects.active = self.obj
                    self.obj.select = True
                    self.obj.location = (0,0,0)
                    self.obj.rotation_euler = (0,0,0)
                    self.obj.parent = selected_obj.parent
                    return {'FINISHED'}
        
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        context.area.tag_redraw()
        context.area.header_text_set(text=self.header_text)
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        
        if event.type in {'ESC'}:
            self.cancel_drop(context,event)
            return {'FINISHED'}
        
        return self.object_drop(context,event)

class OPS_drop_world(Operator):
    bl_idname = "fd_general.drop_world"
    bl_label = "Drop World"
#     bl_options = {'UNDO'}
  
    #READONLY
    filepath = StringProperty(name="Filepath")
    world_name = StringProperty(name="World Name")
    
    def invoke(self, context, event):
        path, ext = os.path.splitext(self.filepath)
        abs_path = bpy.path.abspath(path)
        if ext == '.blend':
            bpy.ops.fd_general.open_blend_file('INVOKE_DEFAULT',filepath=self.filepath)
            return {'FINISHED'}

        files = os.listdir(os.path.dirname(abs_path))
        
        for file in files:
            blendname, ext = os.path.splitext(file)
            if ext == ".blend":
                blendfile_path = os.path.join(os.path.dirname(path),file)
                with bpy.data.libraries.load(blendfile_path, False, False) as (data_from, data_to):
                    for world in data_from.worlds:
                        if world == self.world_name:
                            if world not in bpy.data.worlds:
                                data_to.worlds = [world]
                                break
                         
                for world in data_to.worlds:
                    context.scene.world = world
                    
        return {'FINISHED'}

class OPS_place_product(bpy.types.Operator):
    bl_idname = "fd_general.place_product"
    bl_label = "Product Placement Options"
    bl_options = {'UNDO'}
    
    #READONLY
    object_name = StringProperty(name="Object Name")
    
    placement_on_wall = EnumProperty(name="Placement on Wall",items=[('SELECTED_POINT',"Selected Point",""),
                                                                     ('FILL',"Fill",""),
                                                                     ('FILL_LEFT',"Fill Left",""),
                                                                     ('LEFT',"Left",""),
                                                                     ('CENTER',"Center",""),
                                                                     ('RIGHT',"Right",""),
                                                                     ('FILL_RIGHT',"Fill Right","")],default = 'SELECTED_POINT')
    
    quantity = IntProperty(name="Quantity",default=1)
    left_offset = FloatProperty(name="Left Offset", default=0,subtype='DISTANCE')
    right_offset = FloatProperty(name="Right Offset", default=0,subtype='DISTANCE')
    product_width = FloatProperty(name="Product Width", default=0,subtype='DISTANCE')
    
    library_type = 'PRODUCT'
    product = None
    default_width = 0
    selected_location = 0
    
    allow_quantites = True
    allow_fills = True
    
    def set_product_defaults(self):
        self.product.obj_bp.location.x = self.selected_location + self.left_offset
        self.product.obj_x.location.x = self.default_width - (self.left_offset + self.right_offset)
    
    def check(self,context):
        left_x = self.product.get_collision_location('LEFT')
        right_x = self.product.get_collision_location('RIGHT')
        offsets = self.left_offset + self.right_offset
        self.set_product_defaults()
        if self.placement_on_wall == 'FILL':
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = (right_x - left_x - offsets) / self.quantity
        if self.placement_on_wall == 'FILL_LEFT':
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = (self.default_width + (self.selected_location - left_x) - offsets) / self.quantity
        if self.placement_on_wall == 'LEFT':
            if self.product.obj_bp.mv.placement_type == 'Corner':
                self.product.obj_bp.rotation_euler.z = math.radians(0)
            self.product.obj_bp.location.x = left_x + self.left_offset
            self.product.obj_x.location.x = self.product_width
        if self.placement_on_wall == 'CENTER':
            self.product.obj_x.location.x = self.product_width
            self.product.obj_bp.location.x = left_x + (right_x - left_x)/2 - ((self.product.calc_width()/2) * self.quantity)
        if self.placement_on_wall == 'RIGHT':
            if self.product.obj_bp.mv.placement_type == 'Corner':
                self.product.obj_bp.rotation_euler.z = math.radians(-90)
            self.product.obj_x.location.x = self.product_width
            self.product.obj_bp.location.x = (right_x - self.product.calc_width()) - self.right_offset
        if self.placement_on_wall == 'FILL_RIGHT':
            self.product.obj_bp.location.x = self.selected_location + self.left_offset
            self.product.obj_x.location.x = ((right_x - self.selected_location) - offsets) / self.quantity
        utils.run_calculators(self.product.obj_bp)
        self.update_quantity_cage()
        return True
    
    def copy_product(self,product):
        bpy.ops.object.select_all(action='DESELECT')
        list_children = utils.get_child_objects(product.obj_bp)
        for child in list_children:
            child.hide = False
            child.select = True
        bpy.ops.object.duplicate_move()
        obj = bpy.data.objects[bpy.context.object.name]
        new_product = fd_types.Assembly(utils.get_bp(obj,'PRODUCT'))
        return new_product

    def update_quantity_cage(self):
        cage = self.product.get_cage()
        cage.hide = False
        cage.hide_select = False
        cage.select = True
        if 'QTY ARRAY' in cage.modifiers:
            mod = cage.modifiers['QTY ARRAY']
        else:
            mod = cage.modifiers.new('QTY ARRAY','ARRAY')
        mod.count = self.quantity
        mod.use_constant_offset = True
        mod.use_relative_offset = False
        if self.placement_on_wall in {'RIGHT'}:
            mod.constant_offset_displace = ((self.product.obj_x.location.x) *-1,0,0)
        else:
            mod.constant_offset_displace = (self.product.obj_x.location.x,0,0)
    
    def invoke(self, context, event):
        obj = bpy.data.objects[self.object_name]
        self.product = fd_types.Assembly(utils.get_bp(obj,'PRODUCT'))
        self.selected_location = self.product.obj_bp.location.x
        self.default_width = self.product.obj_x.location.x
        self.product_width = self.product.obj_x.location.x
        self.placement_on_wall = 'SELECTED_POINT'
        self.left_offset = 0
        self.right_offset = 0
        self.quantity = 1
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(400))
    
    def execute(self,context):
        x_placement = self.product.obj_bp.location.x + self.product.obj_x.location.x
        self.product.delete_cage()
        self.product.obj_x.hide = True
        self.product.obj_y.hide = True
        self.product.obj_z.hide = True
        self.product.obj_bp.select = True
        context.scene.objects.active = self.product.obj_bp
        previous_product = None
        products = []
        products.append(self.product.obj_bp)
        if self.quantity > 1:
            for i in range(self.quantity - 1):
                if previous_product:
                    next_product = self.copy_product(previous_product)
                else:
                    next_product = self.copy_product(self.product)
                if self.placement_on_wall == 'RIGHT':
                    next_product.x_loc(value = x_placement - self.product.obj_x.location.x - next_product.obj_x.location.x)
                else:
                    next_product.x_loc(value = x_placement)
                next_product.z_loc(value = self.product.obj_bp.location.z)
                next_product.x_dim(value = self.product.obj_x.location.x)
                next_product.y_dim(value = self.product.obj_y.location.y)
                next_product.z_dim(value = self.product.obj_z.location.z)
                next_product.delete_cage()
                next_product.obj_x.hide = True
                next_product.obj_y.hide = True
                next_product.obj_z.hide = True
                previous_product = next_product
                products.append(next_product.obj_bp)
                if self.placement_on_wall == 'RIGHT':
                    x_placement -= self.product.obj_x.location.x
                else:
                    x_placement += self.product.obj_x.location.x
                
        for product_bp in products:
            utils.init_objects(product_bp)
            
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        if self.product.obj_bp.mv.placement_type == 'Corner':
            self.allow_fills = False
            self.allow_quantites = False
        
        if self.product.obj_x.lock_location[0]:
            self.allow_fills = False
        box = layout.box()
        row = box.row(align=False)
        row.label('Placement Options',icon='LATTICE_DATA')
        row = box.row(align=False)
        row.prop_enum(self, "placement_on_wall", 'SELECTED_POINT', icon='MAN_TRANS', text="Selected Point")
        if self.allow_fills:
            row.prop_enum(self, "placement_on_wall", 'FILL', icon='ARROW_LEFTRIGHT', text="Fill")
        row = box.row(align=True)
        if self.allow_fills:
            row.prop_enum(self, "placement_on_wall", 'FILL_LEFT', icon='PREV_KEYFRAME', text="Fill Left") 
        row.prop_enum(self, "placement_on_wall", 'LEFT', icon='TRIA_LEFT', text="Left") 
        row.prop_enum(self, "placement_on_wall", 'CENTER', icon='TRIA_DOWN', text="Center")
        row.prop_enum(self, "placement_on_wall", 'RIGHT', icon='TRIA_RIGHT', text="Right") 
        if self.allow_fills:  
            row.prop_enum(self, "placement_on_wall", 'FILL_RIGHT', icon='NEXT_KEYFRAME', text="Fill Right")
        if self.allow_quantites:
            row = box.row(align=True)
            row.prop(self,'quantity')
        split = box.split(percentage=0.5)
        col = split.column(align=True)
        col.label("Dimensions:")
        if self.placement_on_wall in {'LEFT','RIGHT','CENTER'}:
            col.prop(self,"product_width",text="Width")
        else:
            col.label('Width: ' + str(round(unit.meter_to_active_unit(self.product.obj_x.location.x),4)))
        col.prop(self.product.obj_y,"location",index=1,text="Depth")
        col.prop(self.product.obj_z,"location",index=2,text="Height")

        col = split.column(align=True)
        col.label("Offset:")
        col.prop(self,"left_offset",text="Left")
        col.prop(self,"right_offset",text="Right")
        col.prop(self.product.obj_bp,"location",index=2,text="Height From Floor")

class OPS_change_file_browser_path(Operator):
    bl_idname = "fd_general.change_file_browser_path"
    bl_label = "Change Library"

    path = StringProperty(name="Path")
    
    def execute(self, context):
        utils.update_file_browser_space(context,self.path)
        for area in context.screen.areas:
            if area.type == 'FILE_BROWSER':
                for space in area.spaces:
                    if space.type == 'FILE_BROWSER':
                        params = space.params
                        params.use_filter = False
        return {'FINISHED'}
    
class OPS_change_library(Operator):
    bl_idname = "fd_general.change_library"
    bl_label = "Change Library"

    library_name = StringProperty(name="Library Name")
    
    def execute(self, context):
        library_tabs = context.scene.mv.ui.library_tabs
        
        if library_tabs == 'PRODUCT':
            context.scene.mv.product_library_name = self.library_name
            lib = context.window_manager.cabinetlib.lib_products[self.library_name]
            path = lib.lib_path
            dirs = os.listdir(path)
            for cat in dirs:
                target_path = os.path.join(path,cat)
                if os.path.isdir(target_path):
                    context.scene.mv.product_category_name = cat
                    path = target_path
                    break
                else:
                    context.scene.mv.product_category_name = ""

        elif library_tabs == 'INSERT':
            context.scene.mv.insert_library_name = self.library_name
            lib = context.window_manager.cabinetlib.lib_inserts[self.library_name]
            path = lib.lib_path
            dirs = os.listdir(path)
            for cat in dirs:
                target_path = os.path.join(path,cat)
                if os.path.isdir(target_path):
                    context.scene.mv.insert_category_name = cat
                    path = target_path
                    break
                else:
                    context.scene.mv.insert_category_name = ""
            
        elif library_tabs == 'ASSEMBLY':
            path = os.path.join(utils.get_library_dir("assemblies"),self.library_name)
            context.scene.mv.assembly_library_name = self.library_name
            dirs = os.listdir(path)
            for cat in dirs:
                target_path = os.path.join(path,cat)
                if os.path.isdir(target_path):
                    context.scene.mv.assembly_category_name = cat
                    path = target_path
                    break
                else:
                    context.scene.mv.assembly_category_name = ""
            
        elif library_tabs == 'OBJECT':
            path = os.path.join(utils.get_library_dir("objects"),self.library_name)
            context.scene.mv.object_library_name = self.library_name
            dirs = os.listdir(path)
            for cat in dirs:
                target_path = os.path.join(path,cat)
                if os.path.isdir(target_path):
                    context.scene.mv.object_category_name = cat
                    path = target_path
                    break
                else:
                    context.scene.mv.object_category_name = ""
                    
        elif library_tabs == 'MATERIAL':
            path = os.path.join(utils.get_library_dir("materials"),self.library_name)
            context.scene.mv.material_library_name = self.library_name
            dirs = os.listdir(path)
            for cat in dirs:
                target_path = os.path.join(path,cat)
                if os.path.isdir(target_path):
                    context.scene.mv.material_category_name = cat
                    path = target_path
                    break
                else:
                    context.scene.mv.material_category_name = ""
            
        elif library_tabs == 'WORLD':
            path = os.path.join(utils.get_library_dir("worlds"),self.library_name)
            context.scene.mv.world_library_name = self.library_name
            dirs = os.listdir(path)
            for cat in dirs:
                target_path = os.path.join(path,cat)
                if os.path.isdir(target_path):
                    context.scene.mv.world_category_name = cat
                    path = target_path
                    break
                else:
                    context.scene.mv.world_category_name = ""
            
        if os.path.isdir(path):
            utils.update_file_browser_space(context,path)
        else:
            print("ERROR")
        return {'FINISHED'}

class OPS_change_category(Operator):
    bl_idname = "fd_general.change_category"
    bl_label = "Change Category"
    
    category_name = StringProperty(name="Category Name")
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        library_tabs = context.scene.mv.ui.library_tabs
        if library_tabs == 'SCENE':
            library_name = context.scene.mv.scene_library_name
            path = os.path.join(utils.get_library_dir("scenes"),library_name,self.category_name)
            context.scene.mv.scene_category_name = self.category_name        
        if library_tabs == 'PRODUCT':
            lib = context.window_manager.cabinetlib.lib_products[context.scene.mv.product_library_name]
            path = os.path.join(lib.lib_path,self.category_name)         
            context.scene.mv.product_category_name = self.category_name
        elif library_tabs == 'INSERT':
            lib = context.window_manager.cabinetlib.lib_inserts[context.scene.mv.insert_library_name]
            path = os.path.join(lib.lib_path,self.category_name)    
            context.scene.mv.insert_category_name = self.category_name
        elif library_tabs == 'ASSEMBLY':
            library_name = context.scene.mv.assembly_library_name
            path = os.path.join(utils.get_library_dir("assemblies"),library_name,self.category_name)
            context.scene.mv.assembly_category_name = self.category_name
        elif library_tabs == 'OBJECT':
            library_name = context.scene.mv.object_library_name
            path = os.path.join(utils.get_library_dir("objects"),library_name,self.category_name)
            context.scene.mv.object_category_name = self.category_name
        elif library_tabs == 'MATERIAL':
            library_name = context.scene.mv.material_library_name
            path = os.path.join(utils.get_library_dir("materials"),library_name,self.category_name)
            context.scene.mv.material_category_name = self.category_name
        elif library_tabs == 'WORLD':
            library_name = context.scene.mv.world_library_name
            path = os.path.join(utils.get_library_dir("worlds"),library_name,self.category_name)
            context.scene.mv.world_category_name = self.category_name
        if os.path.isdir(path):
            utils.update_file_browser_space(context,path)
        else:
            print("ERROR")
        return {'FINISHED'}

class OPS_add_floor_plan(Operator):
    bl_idname = "fd_general.add_floor_plan"
    bl_label = "Add Floor Plan"

    def execute(self, context):
        
        bpy.ops.view3d.background_image_add()
        return {'FINISHED'}

class OPS_reload_library(Operator):
    bl_idname = "fd_general.reload_library"
    bl_label = "Reload Library"

    def execute(self, context):
        context.scene.mv.ui.library_tabs = context.scene.mv.ui.library_tabs
        return {'FINISHED'}

class OPS_open_new_window(Operator):
    bl_idname = "fd_general.open_new_window"
    bl_label = "Open New Window"

    space_type = StringProperty(name="Space Type")
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        for window in context.window_manager.windows:
            if len(window.screen.areas) == 1 and window.screen.areas[0].type == 'USER_PREFERENCES':
                window.screen.areas[0].type = self.space_type
        return {'FINISHED'}

class OPS_properties(Operator):
    bl_idname = "fd_general.properties"
    bl_label = "Properties"

    @classmethod
    def poll(cls, context):
        if context.object:
            return True
        else:
            return False

    def check(self,context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self,context,event):
        obj = context.object
        if obj:
            if obj.mv.property_id != "":
                try:
                    eval('bpy.ops.' + obj.mv.property_id + '("INVOKE_DEFAULT",object_name=obj.name)')
                except:
                    bpy.ops.fd_general.error('INVOKE_DEFAULT',message='Could Not Find "' + obj.mv.property_id + '" Interface')
                    
                return {'FINISHED'}
            else:
                if context.object.type == 'CAMERA':
                    bpy.ops.fd_object.camera_properties('INVOKE_DEFAULT')
                    return{'FINISHED'}    
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(400))

    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj and obj.parent:
            if obj.parent.mv.type == 'BPWALL' and obj.mv.type != 'BPASSEMBLY':
                wall = fd_types.Wall(obj.parent)
                wall.draw_transform(layout)
                for obj in wall.obj_bp.children:
                    if obj.mv.is_wall_mesh:
                        row = layout.row(align=True)
                        row.prop_enum(obj, "draw_type", 'WIRE',text="Wire") 
                        row.prop_enum(obj, "draw_type", 'TEXTURED',text="Textured") 
                return None
        
        obj_bp = utils.get_parent_assembly_bp(obj)
        if obj_bp:
            group = fd_types.Assembly(obj_bp)
            group.draw_transform(layout,show_prompts=True)
        else:
            utils.draw_object_info(layout,obj)
            if obj.type == 'LAMP':
                utils.draw_object_data(layout,obj)

class OPS_add_library_package(Operator):
    """ This will load all of the products from the products module.
    """
    bl_idname = "fd_general.add_library_package"
    bl_label = "Add Library Package"
    bl_description = "This will add a library package to Fluid Designer"
    bl_options = {'UNDO'}

    def execute(self, context):
        wm = context.window_manager.mv
        wm.library_packages.add()
        return {'FINISHED'}

class OPS_delete_library_package(Operator):
    """ This will load all of the products from the products module.
    """
    bl_idname = "fd_general.delete_library_package"
    bl_label = "Add Library Package"
    bl_description = "This will add a library package to Fluid Designer"
    bl_options = {'UNDO'}
    
    library_index = IntProperty(name="Library Index")
    
    def execute(self, context):
        wm = context.window_manager.mv
        wm.library_packages.remove(self.library_index)
        bpy.ops.fd_general.update_library_xml()
        return {'FINISHED'}

class OPS_update_library_xml(Operator):
    """ This will load all of the products from the products module.
    """
    bl_idname = "fd_general.update_library_xml"
    bl_label = "Update Library XML"
    bl_description = "This will Update the Library XML file that stores the library paths"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        xml = fd_types.MV_XML()
        root = xml.create_tree()
        paths = xml.add_element(root,'LibraryPaths')
        
        wm = context.window_manager
        packages = xml.add_element(paths,'Packages')
        for package in wm.mv.library_packages:
            if os.path.exists(package.lib_path):
                lib_package = xml.add_element(packages,'Package',package.lib_path)
                xml.add_element_with_text(lib_package,'Enabled',str(package.enabled))
        
        if os.path.exists(wm.mv.library_module_path):
            xml.add_element_with_text(paths,'Modules',wm.mv.library_module_path)
        else:
            xml.add_element_with_text(paths,'Modules',"")
         
        if os.path.exists(wm.mv.assembly_library_path):
            xml.add_element_with_text(paths,'Assemblies',wm.mv.assembly_library_path)
        else:
            xml.add_element_with_text(paths,'Assemblies',"")
             
        if os.path.exists(wm.mv.object_library_path):
            xml.add_element_with_text(paths,'Objects',wm.mv.object_library_path)
        else:
            xml.add_element_with_text(paths,'Objects',"")
             
        if os.path.exists(wm.mv.material_library_path):
            xml.add_element_with_text(paths,'Materials',wm.mv.material_library_path)
        else:
            xml.add_element_with_text(paths,'Materials',"")
             
        if os.path.exists(wm.mv.world_library_path):
            xml.add_element_with_text(paths,'Worlds',wm.mv.world_library_path)
        else:
            xml.add_element_with_text(paths,'Worlds',"")
    
        xml.write(utils.get_library_path_file())
    
        return {'FINISHED'}

class OPS_load_library_modules(Operator):
    """ This will load all of the products from the products module.
    """
    bl_idname = "fd_general.load_library_modules"
    bl_label = "Load Library Modules"
    bl_description = "This will load the available product library modules"
    bl_options = {'UNDO'}
    
    external_lib_only = bpy.props.BoolProperty(name="External Libraries Only", default=False)

    def get_library(self,libraries,library_name,module_name,package_name,path):
        if library_name in libraries:
            lib = libraries[library_name]
        else:
            lib = libraries.add()
            lib.name = library_name
            lib.module_name = module_name
            lib.package_name = package_name
            lib.lib_path = path
        return lib

    def execute(self, context):
        from importlib import import_module
        wm = context.window_manager.cabinetlib

        for library in wm.lib_products:
            wm.lib_products.remove(0)
        
        for library in wm.lib_inserts:
            wm.lib_inserts.remove(0)        
        
        packages = utils.get_library_packages(context, only_external=True if self.external_lib_only else False)
        
        for package in packages:
            pkg = import_module(package)
            for mod_name, mod in inspect.getmembers(pkg):
                for name, obj in inspect.getmembers(mod):
                    if inspect.isclass(obj) and "PRODUCT_" in name:
                        product = obj()
                        if product.assembly_name == "":
                            product.assembly_name = name.replace("PRODUCT_","").replace("_"," ")
                        path = os.path.join(os.path.dirname(pkg.__file__),"products",product.library_name)
                        lib = self.get_library(wm.lib_products,product.library_name,mod_name,package,path)
                        item = lib.items.add()
                        item.name = product.assembly_name
                        item.class_name = name
                        item.library_name = product.library_name
                        item.category_name = product.category_name
                        item.lib_path = os.path.join(os.path.dirname(pkg.__file__),"products",product.library_name)
                        thumbnail_path = os.path.join(item.lib_path,item.category_name,item.name.strip() + ".png")
                        if os.path.exists(thumbnail_path):
                            item.has_thumbnail = True
                        else:
                            item.has_thumbnail = False
                        file_path = os.path.join(item.lib_path,item.category_name,item.name.strip() + ".blend")
                        if os.path.exists(file_path):
                            item.has_file = True
                        else:
                            item.has_file = False            
                            
                    if inspect.isclass(obj) and "INSERT_" in name:
                        insert = obj()
                        if insert.assembly_name == "":
                            insert.assembly_name = name.replace("INSERT_","").replace("_"," ")
                        path = os.path.join(os.path.dirname(pkg.__file__),"inserts",insert.library_name)
                        lib = self.get_library(wm.lib_inserts,insert.library_name,mod_name,package,path)
                        item = lib.items.add()
                        item.name = insert.assembly_name
                        item.class_name = name
                        item.library_name = insert.library_name
                        item.category_name = insert.category_name
                        item.lib_path = os.path.join(os.path.dirname(pkg.__file__),"inserts",insert.library_name)
                        thumbnail_path = os.path.join(item.lib_path,item.category_name,item.name.strip() + ".png")
                        if os.path.exists(thumbnail_path):
                            item.has_thumbnail = True
                        else:
                            item.has_thumbnail = False
                        file_path = os.path.join(item.lib_path,item.category_name,item.name.strip() + ".blend")
                        if os.path.exists(file_path):
                            item.has_file = True
                        else:
                            item.has_file = False       
        return {'FINISHED'}

class OPS_brd_library_items(Operator):
    """ This will rebuild the entire library.
    """
    bl_idname = "fd_general.brd_library_items"
    bl_label = "Build Render Draw Library Items"
    bl_description = "This operator will build render or draw every selected item in the library"
    bl_options = {'UNDO'}
    
    operation_type = EnumProperty(name="Operation Type",items=[('BUILD','Build','Build'),
                                                               ('RENDER','Render','Render'),
                                                               ('DRAW','Draw','Draw')])
    
    library_type = EnumProperty(name="Library Type",items=[('PRODUCT','Product','Product'),
                                                           ('INSERT','Insert','Insert')])
    
    _timer = None
    
    item_list = []
    current_product = 0
    package_name = ""
    module_name = ""
    library_path = ""
    
    placement = 0
    
    def __del__(self):
        bpy.context.window.cursor_set('DEFAULT')
        bpy.context.area.header_text_set()
    
    def invoke(self, context, event):
        wm = context.window_manager
        
        if self.library_type == 'PRODUCT':
            collection = wm.cabinetlib.lib_products[wm.cabinetlib.lib_product_index].items
            self.module_name = wm.cabinetlib.lib_products[wm.cabinetlib.lib_product_index].module_name
            self.package_name = wm.cabinetlib.lib_products[wm.cabinetlib.lib_product_index].package_name
            self.library_path = wm.cabinetlib.lib_products[wm.cabinetlib.lib_product_index].lib_path
            
        if self.library_type == 'INSERT':
            collection = wm.cabinetlib.lib_inserts[wm.cabinetlib.lib_insert_index].items
            self.module_name = wm.cabinetlib.lib_inserts[wm.cabinetlib.lib_insert_index].module_name
            self.package_name = wm.cabinetlib.lib_inserts[wm.cabinetlib.lib_insert_index].package_name
            self.library_path = wm.cabinetlib.lib_inserts[wm.cabinetlib.lib_insert_index].lib_path
            
        self.item_list = []
        for item in collection:
            if item.selected:
                self.item_list.append(item)
                
        wm.cabinetlib.total_items = len(self.item_list)
        
        self._timer = wm.event_timer_add(0.1, context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        context.window.cursor_set('WAIT')
        context.area.tag_redraw()
        progress = context.window_manager.cabinetlib
        header_text = "Processing Item 1 of " + str(progress.total_items)
        context.area.header_text_set(text=header_text)
        
        self.mouse_loc = (event.mouse_region_x,event.mouse_region_y)
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return self.cancel(context)
        
        if event.type == 'TIMER':
            if progress.current_item + 1 <= len(self.item_list):
                if self.operation_type == 'RENDER':
                    if self.library_type == 'INSERT':
                        self.render_insert(self.item_list[progress.current_item].class_name)
                    else:
                        self.render_product(self.item_list[progress.current_item].class_name)
                if self.operation_type == 'BUILD':
                    self.build_product(self.item_list[progress.current_item].class_name)
                if self.operation_type == 'DRAW':
                    self.draw_product(self.item_list[progress.current_item].class_name)
                progress.current_item += 1
                if progress.current_item + 1 <= len(self.item_list):
                    header_text = "Processing Item " + str(progress.current_item + 1) + " of " + str(progress.total_items)
                context.area.header_text_set(text=header_text)
            else:
                return self.cancel(context)
        return {'PASS_THROUGH'}
    
    def render_product(self,class_name):
        filepath = get_thumbnail_path()
        script = os.path.join(bpy.app.tempdir,'thumbnail.py')
        script_file = open(script,'w')
        script_file.write("import bpy\n")
        script_file.write("import os\n")
        script_file.write("from mv import utils\n")
        script_file.write("bpy.ops.fd_material.reload_spec_group_from_library_modules()\n")
        script_file.write("from mv import utils\n")
        script_file.write("pkg = __import__('" + self.package_name + "')\n")
        script_file.write("item = eval('pkg." + self.module_name + "." + class_name + "()')" + "\n")
        script_file.write("item.draw()\n")
        script_file.write("item.update()\n")
        script_file.write("file_name = item.assembly_name if item.assembly_name != '' else utils.get_product_class_name('" + class_name + "')\n")
        script_file.write("tn_path = os.path.join(r'" + self.library_path + "',item.category_name,file_name)\n")
        script_file.write('utils.render_assembly(item,tn_path)\n')
        script_file.close()
        subprocess.call(bpy.app.binary_path + ' "' + filepath + '" -b --python "' + script + '"')

    def render_insert(self,class_name):
        filepath = get_thumbnail_path()
        script = os.path.join(bpy.app.tempdir,'thumbnail.py')
        script_file = open(script,'w')
        script_file.write("import bpy\n")
        script_file.write("import os\n")
        script_file.write("from mv import utils\n")
        script_file.write("bpy.ops.fd_material.reload_spec_group_from_library_modules()\n")
        script_file.write("from mv import utils\n")
        script_file.write("pkg = __import__('" + self.package_name + "')\n")
        script_file.write("item = eval('pkg." + self.module_name + "." + class_name + "()')" + "\n")
        script_file.write("item.draw()\n")
        script_file.write("item.update()\n")
        script_file.write("file_name = item.assembly_name if item.assembly_name != '' else utils.get_insert_class_name('" + class_name + "')\n")
        script_file.write("tn_path = os.path.join(r'" + self.library_path + "',item.category_name,file_name)\n")
        script_file.write('utils.render_assembly(item,tn_path)\n')
        script_file.close()
        subprocess.call(bpy.app.binary_path + ' "' + filepath + '" -b --python "' + script + '"')

    def build_product(self,class_name):
        script = os.path.join(bpy.app.tempdir,'building.py')
        script_file = open(script,'w')
        script_file.write("from mv import utils\n")
        script_file.write("pkg = __import__('" + self.package_name + "')\n")
        script_file.write("item = eval('pkg." + self.module_name + "." + class_name + "()')" + "\n")
        script_file.write("item.draw()\n")
        script_file.write("item.update()\n")
        script_file.write("if item.assembly_name == '':\n")
        script_file.write("    item.assembly_name = utils.get_product_class_name('" + class_name + "')\n")
        script_file.write('utils.save_assembly(item,r"' + self.library_path + '"' + ')\n')
        script_file.close()
        subprocess.call(bpy.app.binary_path + ' -b --python "' + script + '"')    
    
    def draw_product(self,class_name):
        pkg = __import__(self.package_name)
        item = eval("pkg." + self.module_name + "." + class_name + "()")
        item.draw()
        item.update()
        utils.init_objects(item.obj_bp)
        item.obj_bp.location.x = self.placement
        self.placement += item.obj_x.location.x + unit.inch(10)
        
    def cancel(self, context):
        progress = context.window_manager.cabinetlib
        progress.current_item = 0
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        return {'FINISHED'}

class OPS_load_fluid_designer_defaults(Operator):
    bl_idname = "fd_general.load_fluid_designer_defaults"
    bl_label = "Load Fluid Designer Defaults"

    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        import shutil
        path,filename = os.path.split(os.path.normpath(__file__))
        src_userpref_file = os.path.join(path,"fd_userpref.blend")
        src_startup_file = os.path.join(path,"fd_startup.blend")
        userpath = os.path.join(bpy.utils.resource_path(type='USER'),"config")
        if not os.path.exists(userpath): os.makedirs(userpath)
        dst_userpref_file = os.path.join(userpath,"fd_userpref.blend")
        dst_startup_file = os.path.join(userpath,"fd_startup.blend")
        shutil.copyfile(src_userpref_file,dst_userpref_file)
        shutil.copyfile(src_startup_file,dst_startup_file)
        return {'FINISHED'}
        
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(550))
        
    def draw(self, context):
        layout = self.layout
        layout.label("Are you sure you want to restore the Fluid Designer default startup file and user preferences?",icon='QUESTION')
        layout.label("You will need to restart the application for the changes to take effect.",icon='BLANK1')
        
class OPS_load_blender_defaults(Operator):
    bl_idname = "fd_general.load_blender_defaults"
    bl_label = "Load Blender Defaults"
    bl_description = "This will reload the blender default startup file and user preferences"
    
    def execute(self, context):
        bpy.ops.wm.read_factory_settings()
        context.scene.mv.ui.use_default_blender_interface = True
        return {'FINISHED'}
        
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(350))
        
    def draw(self, context):
        layout = self.layout
        layout.label("This will load a new file. You will lose any unsaved changes.",icon='QUESTION')
        layout.label("Do you want to continue?",icon='BLANK1')
        
class OPS_save_startup_file(Operator):
    bl_idname = "fd_general.save_startup_file"
    bl_label = "Save Startup File"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.wm.save_homefile()
        return {'FINISHED'}
        
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(400))
        
    def draw(self, context):
        layout = self.layout
        layout.label("Are you sure you want to save the current file as the startup file?",icon='QUESTION')
        layout.label("The current state of the interface will be saved as the default.",icon='BLANK1')

class OPS_open_blend_file(Operator):
    bl_idname = "fd_general.open_blend_file"
    bl_label = "Open Blend File"
    
    filepath = StringProperty(name="Filepath")
    
    @classmethod
    def poll(cls, context):
        return True
        
    def execute(self, context):
        bpy.ops.wm.open_mainfile(load_ui=False,filepath=self.filepath)
        return {'FINISHED'}
        
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(300))
        
    def draw(self, context):
        layout = self.layout
        layout.label("Are you sure you want to open this blend file?",icon='QUESTION')
        layout.label("You will lose any unsaved changes",icon='BLANK1')
        
class OPS_change_shademode(Operator):
    bl_idname = "fd_general.change_shademode"
    bl_label = "Change Shademode"

    shade_mode = bpy.props.EnumProperty(
            name="Shade Mode",
            items=(('WIREFRAME', "Wire Frame", "WIREFRAME",'WIRE',1),
                   ('SOLID', "Solid", "SOLID",'SOLID',2),
                   ('MATERIAL', "Material","MATERIAL",'MATERIAL',3),
                   ('RENDERED', "Rendered", "RENDERED",'SMOOTH',4)
                   ),
            )

    def execute(self, context):
        context.scene.render.engine = 'CYCLES'
        context.space_data.viewport_shade = self.shade_mode
        return {'FINISHED'}
        
class OPS_change_mode(Operator):
    bl_idname = "fd_general.change_mode"
    bl_label = "Change Shademode"

    mode = bpy.props.EnumProperty(
            name="Shade Mode",
            items=(('OBJECT', "Object Mode", "OBJECT_DATAMODE",'OBJECT_DATAMODE',1),
                   ('EDIT', "Edit Mode", "EDITMODE_HLT",'EDITMODE_HLT',2)
                   ),
            )

    def execute(self, context):
        obj = context.active_object
        if obj.mode != self.mode:
            bpy.ops.object.editmode_toggle()
        return {'FINISHED'}
        
class OPS_dialog_show_filters(Operator):
    bl_idname = "fd_general.dialog_show_filters"
    bl_label = "Show Filters"
    bl_options = {'UNDO'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(300))

    def draw(self, context):
        layout = self.layout
        st = context.space_data
        params = st.params
        if params:
#             row = layout.row()
#             row.label('File Display Mode:')
#             row.prop(params, "display_type", expand=False,text="")
            layout.prop(params, "use_filter", text="Use Filters", icon='FILTER')
            layout.separator()
            box = layout.box()
            box.prop(params, "use_filter_folder", text="Show Folders")
            box.prop(params, "use_filter_blender", text="Show Blender Files")
            box.prop(params, "use_filter_backup", text="Show Backup Files")
            box.prop(params, "use_filter_image", text="Show Image Files")
            box.prop(params, "use_filter_movie", text="Show Video Files")
            box.prop(params, "use_filter_script", text="Show Script Files")
            box.prop(params, "use_filter_font", text="Show Font Files")
            box.prop(params, "use_filter_text", text="Show Text Files")
            box.prop(params, "show_hidden",text='Show Hidden Folders',icon='VISIBLE_IPO_ON')
            
class OPS_error(Operator):
    bl_idname = "fd_general.error"
    bl_label = "Fluid Designer"

    message = StringProperty(name="Message",default="Error")

    def execute(self, context):
        return {'FINISHED'} 

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(380))

    def draw(self, context):
        layout = self.layout
        layout.label(self.message)
    
class OPS_set_cursor_location(Operator):
    bl_idname = "fd_general.set_cursor_location"
    bl_label = "Cursor Location"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(200))

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.scene,"cursor_location",text="")

class OPS_start_debug(Operator):
    bl_idname = "fluidgeneral.start_debug"
    bl_label = "Start Debug"
    bl_description = "Start Debug with Eclipse"

    def execute(self, context):
        import pydevd
        pydevd.settrace()
        return {'FINISHED'}

class OPS_open_browser_window(Operator):
    bl_idname = "fd_general.open_browser_window"
    bl_label = "Open Browser Window"
    bl_description = "This will open the path that is passed in a file browser"

    path = StringProperty(name="Message",default="Error")

    def execute(self, context):
        import subprocess
        if 'Windows' in str(bpy.app.build_platform):
            subprocess.Popen(r'explorer ' + self.path)
        elif 'Darwin' in str(bpy.app.build_platform):
            subprocess.Popen(['open' , os.path.normpath(self.path)])
        else:
            subprocess.Popen(['xdg-open' , os.path.normpath(self.path)])
        return {'FINISHED'}

#USEFUL FOR REFERENCE
class OPS_check_for_updates(Operator):
    bl_idname = "fd_general.check_for_updates"
    bl_label = "Check For Updates"

    info = {}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        pass
        return {'FINISHED'}
        
    def invoke(self,context,event):
        wm = context.window_manager
        import urllib.request
        url = urllib.request.urlopen("http://www.microvellum.com/AppInterfaces/FluidDesignerUpdate/CurrentUpdate.html")
        mybytes = url.read()
        mystr = mybytes.decode("utf8")
        lines = mystr.split('<p>')
        for line in lines:
            if 'CurrentVersion=' in line:
                new_line = line.replace('</p>','')
                self.info['CurrentVersion'] = new_line[len('CurrentVersion='):].strip()
            if 'InstallPath=' in line:
                new_line = line.replace('</p>','')
                self.info['InstallPath'] = new_line[len('InstallPath='):].strip()

        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(320))
        
    def draw(self, context):
        layout = self.layout
        layout.label('Current Version: ' + self.info['CurrentVersion'],icon='MOD_FLUIDSIM')
        layout.operator("wm.url_open", text="Download New Version", icon='URL').url = self.info['InstallPath']

class OPS_dimension_interface(Operator):
    bl_idname = "fd_general.dimension_interface"
    bl_label = "Dimension Global Options"

    info = {}

    @classmethod
    def poll(cls, context):
        return True

    def check(self, context):
        return True

    def execute(self, context):
        pass
        return {'FINISHED'}
        
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(320))
        
    def draw(self, context):
        wm = context.window_manager.mv
        scene = context.scene
        if wm.use_opengl_dimensions is False:
            icon = 'VISIBLE_IPO_ON'
            txt = 'Show Dimensions'
        else:
            icon = "VISIBLE_IPO_OFF"
            txt = 'Hide Dimensions'
        
        layout = self.layout
        box = layout.box()
        box.prop(scene.mv.opengl_dim, 'gl_dim_units')
        box.prop(scene.mv.opengl_dim, 'gl_arrow_type',)
        row = box.row()
        row.label("Color:")        
        row.prop(scene.mv.opengl_dim, 'gl_default_color', text="")        
        row = box.row()
        
        if scene.mv.opengl_dim.gl_dim_units in ('INCH', 'FEET'):
            row.label("Round to the nearest:")
            row.prop(scene.mv.opengl_dim, 'gl_imperial_rd_factor', text="")
            row = box.row()
            row.label("Number format:")
            row.prop(scene.mv.opengl_dim, 'gl_number_format', text="")
            
        else:         
            row.label("Precision:")
            row.prop(scene.mv.opengl_dim, 'gl_precision',text="")
        
        row = box.row()
        row.label("Text Size:")
        row.prop(scene.mv.opengl_dim, 'gl_font_size',text="")
        row = box.row()
        row.label("Arrow Size:")        
        row.prop(scene.mv.opengl_dim, 'gl_arrow_size', text="")

class OPS_toggle_dimension_handles(Operator):
    bl_idname = "fd_general.toggle_dimension_handles"
    bl_label = "Toggle Dimension Handles"

    turn_on = BoolProperty(name="Turn On",default=False)

    def execute(self, context):
        for obj in context.scene.objects:
            if obj.mv.type == 'VISDIM_A':
                obj.empty_draw_type = 'SPHERE'
                obj.empty_draw_size = unit.inch(1)
                obj.hide = False if self.turn_on else True
            elif obj.mv.type == 'VISDIM_B':
                obj.rotation_euler.z = math.radians(-90)
                obj.empty_draw_type = 'PLAIN_AXES'
                obj.empty_draw_size = unit.inch(2)
                obj.hide = False if self.turn_on else True
        return {'FINISHED'}

class OPS_create_single_dimension(Operator):
    bl_idname = "fd_general.create_single_dimension"
    bl_label = "Create Single Dimension"

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        dim = fd_types.Dimension()
        dim.end_x(value = unit.inch(0))
        dim.anchor.select = True
        context.scene.objects.active = dim.anchor
        bpy.ops.fd_general.toggle_dimension_handles(turn_on=True)
        context.window_manager.mv.use_opengl_dimensions = True
        return {'FINISHED'}

class OPS_Add_Dimension(Operator):
    bl_idname = "fd_general.add_dimension"
    bl_label = "Add Dimension" 
    bl_options = {'UNDO'}

    label = StringProperty(name="Dimension Label",
                           default="")
    
    offset = FloatProperty(name="Offset", subtype='DISTANCE')
    
    above_assembly_draw_to = EnumProperty(name="Draw to Above Assembly Top or Bottom",
                                          items=[('Top',"Top","Top"),
                                                 ('BOTTOM',"Bottom","Bottom")],
                                          default='BOTTOM')

    configuration = EnumProperty(name="configuration",
                                 items=[('WIDTH',"Width",'Width of Assembly'),
                                        ('HEIGHT',"Height",'Height of Assembly'),
                                        ('DEPTH',"Depth",'Depth of Assembly'),
                                        ('WALL_TOP',"Wall Top",'Top of Wall'),
                                        ('WALL_BOTTOM',"Wall Bottom",'Bottom of Wall'),
                                        ('WALL_LEFT',"Wall Left",'Left Wall End'),
                                        ('WALL_RIGHT',"Wall Right",'Right Wall End'),
                                        ('AVAILABLE_SPACE_ABOVE',"Available Space Above",'Available Space Above'),
                                        ('AVAILABLE_SPACE_BELOW',"Available Space Below",'Available Space Below'),
                                        ('AVAILABLE_SPACE_LEFT',"Available Space Left",'Available Space Left'),
                                        ('AVAILABLE_SPACE_RIGHT',"Available Space Right",'Available Space Right')],                                      
                                 default = 'WIDTH')
    
    dimension = None
    assembly = None
    wall = None
    del_dim = True
    neg_z_dim = False
    
    @classmethod
    def poll(cls, context):
        if utils.get_bp(context.object, 'PRODUCT'):
            return True   
        else:
            return False 
    
    def check(self, context):
        self.dimension.anchor.location = (0,0,0)
        self.dimension.end_point.location = (0,0,0)  
        
        self.dimension.set_label(self.label)
        
        if self.configuration in ['HEIGHT','WALL_TOP','WALL_BOTTOM','AVAILABLE_SPACE_ABOVE','AVAILABLE_SPACE_BELOW']:
            self.dimension.anchor.location.x += self.offset
        else:         
            self.dimension.anchor.location.z += self.offset
        
        if self.configuration == 'WIDTH':
            self.dimension.end_point.location.x =self.assembly.obj_x.location.x
            
        if self.configuration == 'HEIGHT':
            self.dimension.end_point.location.z = self.assembly.obj_z.location.z
            
        if self.configuration == 'DEPTH':
            self.dimension.end_point.location.y = self.assembly.obj_y.location.y            
            
        if self.configuration == 'WALL_TOP':
            if self.neg_z_dim == False:
                self.dimension.anchor.location.z = self.assembly.obj_z.location.z
                self.dimension.end_point.location.z = self.wall.obj_z.location.z -\
                                                      self.assembly.obj_bp.location.z -\
                                                      self.assembly.obj_z.location.z         
            else:
                self.dimension.end_point.location.z = self.wall.obj_z.location.z -\
                                                      self.assembly.obj_bp.location.z               
            
        if self.configuration == 'WALL_BOTTOM':
            if self.neg_z_dim == False:
                self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z
            else:
                self.dimension.anchor.location.z = self.assembly.obj_z.location.z
                self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z -\
                                                      self.assembly.obj_z.location.z
            
        if self.configuration == 'WALL_LEFT':
            self.dimension.end_point.location.x = -self.assembly.obj_bp.location.x
            
        if self.configuration == 'WALL_RIGHT': 
            self.dimension.anchor.location.x = self.assembly.obj_x.location.x
            self.dimension.end_point.location.x = self.wall.obj_x.location.x -\
                                                  self.assembly.obj_bp.location.x -\
                                                  self.assembly.obj_x.location.x
            
        if self.configuration == 'AVAILABLE_SPACE_ABOVE':
            if self.neg_z_dim == False:
                self.dimension.anchor.location.z = self.assembly.obj_z.location.z 
                assembly_dim_z = self.assembly.obj_z.location.z
            else:
                assembly_dim_z = 0.0                
            
            assembly_a = self.assembly.get_adjacent_assembly(direction='ABOVE')
            
            if assembly_a:
                above_assembly_loc_z = assembly_a.obj_bp.location.z
                
                if self.above_assembly_draw_to == 'BOTTOM':                                                           
                    above_assembly_dim_z = assembly_a.obj_z.location.z
                    self.dimension.end_point.location.z = above_assembly_loc_z +\
                                                          above_assembly_dim_z -\
                                                          self.assembly.obj_bp.location.z -\
                                                          assembly_dim_z 
                                                                                                                        
                else:
                    self.dimension.end_point.location.z = above_assembly_loc_z -\
                                                          self.assembly.obj_bp.location.z -\
                                                          assembly_dim_z                    
               
            else:
                self.dimension.end_point.location.z = self.wall.obj_z.location.z -\
                                                      self.assembly.obj_bp.location.z -\
                                                      assembly_dim_z
         
        if self.configuration == 'AVAILABLE_SPACE_BELOW':
            if self.assembly.obj_z.location.z < 0:
                self.dimension.anchor.location.z = self.assembly.obj_z.location.z
            
            assembly_b = self.assembly.get_adjacent_assembly(direction='BELOW')
            if assembly_b:
                if self.neg_z_dim == False:
                    self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z +\
                                                          assembly_b.obj_bp.location.z +\
                                                          assembly_b.obj_z.location.z
                else:
                    self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z -\
                                                          self.assembly.obj_z.location.z +\
                                                          assembly_b.obj_bp.location.z +\
                                                          assembly_b.obj_z.location.z
            else:
                self.dimension.end_point.location.z = -self.assembly.obj_bp.location.z
        
        if self.configuration == 'AVAILABLE_SPACE_LEFT':
            if self.assembly.get_adjacent_assembly(direction='LEFT'):
                self.dimension.end_point.location.x = -self.assembly.obj_bp.location.x +\
                                                      self.assembly.get_adjacent_assembly(direction='LEFT').obj_bp.location.x +\
                                                      self.assembly.get_adjacent_assembly(direction='LEFT').obj_x.location.x
            else:
                self.dimension.end_point.location.x = -self.assembly.obj_bp.location.x
            
        if self.configuration == 'AVAILABLE_SPACE_RIGHT':
            self.dimension.anchor.location.x = self.assembly.obj_x.location.x
            if self.assembly.get_adjacent_assembly(direction='RIGHT'):
                self.dimension.end_point.location.x = self.assembly.get_adjacent_assembly(direction='RIGHT').obj_bp.location.x -\
                                                      self.assembly.obj_bp.location.x -\
                                                      self.assembly.obj_x.location.x           
            else:
                self.dimension.end_point.location.x = self.wall.obj_x.location.x -\
                                                      self.assembly.obj_bp.location.x -\
                                                      self.assembly.obj_x.location.x
                                                            
        return True
    
    def __del__(self):
        if self.del_dim == True:
            obj_del = []
            obj_del.append(self.dimension.anchor)
            obj_del.append(self.dimension.end_point)
            utils.delete_obj_list(obj_del)
    
    def invoke(self, context, event):
        wm = context.window_manager
        
        if wm.mv.use_opengl_dimensions == False:
            wm.mv.use_opengl_dimensions = True
        
        if context.object:
            obj_wall_bp = utils.get_wall_bp(context.object)
            if obj_wall_bp:
                self.wall = fd_types.Wall(obj_wall_bp)
                
#             obj_assembly_bp = utils.get_parent_assembly_bp(context.object)
            obj_assembly_bp = utils.get_bp(context.object, 'PRODUCT')
            if obj_assembly_bp:
                self.assembly = fd_types.Assembly(obj_assembly_bp)
                wall_bp = utils.get_wall_bp(obj_assembly_bp)
                self.wall = fd_types.Wall(wall_bp)
        
        self.dimension = fd_types.Dimension()
        self.dimension.set_color(value=7)
        self.dimension.parent(obj_assembly_bp)
        self.dimension.end_point.location.x = self.assembly.obj_x.location.x
        
        if self.assembly.obj_z.location.z < 0:
            self.neg_z_dim = True
        else:
            self.neg_z_dim = False
            
        self.configuration = 'WIDTH'
        self.label = ""
        
        
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(550))
    
    def execute(self, context):
        self.del_dim = False
        self.dimension.set_color(value=0)
        self.dimension.anchor.hide = False
        self.dimension.end_point.hide = False
        
        if self.label != "":
            self.dimension.set_label(self.label)
        
        wall_dim_x = self.wall.get_var("dim_x", "wall_dim_x")
        wall_dim_z = self.wall.get_var("dim_z", "wall_dim_z")
        
        assembly_loc_x = self.assembly.get_var("loc_x", "assembly_loc_x")
        assembly_loc_z = self.assembly.get_var("loc_z", "assembly_loc_z")
        assembly_dim_x = self.assembly.get_var("dim_x", "assembly_dim_x")
        assembly_dim_z = self.assembly.get_var("dim_z", "assembly_dim_z")        
        
        assembly_l = self.assembly.get_adjacent_assembly(direction='LEFT')
        if assembly_l:
            assembly_l_loc_x = assembly_l.get_var("loc_x", "assembly_l_loc_x")
            assembly_l_dim_x = assembly_l.get_var("dim_x", "assembly_l_dim_x")               
        
        assembly_r = self.assembly.get_adjacent_assembly(direction='RIGHT')
        if assembly_r:
            assembly_r_loc_x = assembly_r.get_var("loc_x", "assembly_r_loc_x")
            
        assembly_a = self.assembly.get_adjacent_assembly(direction='ABOVE')
        if assembly_a:
            assembly_a_loc_z = assembly_a.get_var("loc_z", "assembly_a_loc_z")
            assembly_a_dim_z = assembly_a.get_var("dim_z", "assembly_a_dim_z")
        
        assembly_b = self.assembly.get_adjacent_assembly(direction="BELOW")
        if assembly_b:
            assembly_b_loc_z = assembly_b.get_var("loc_z", "assembly_b_loc_z")
            assembly_b_dim_z = assembly_b.get_var("dim_z", "assembly_b_dim_z")
        
        if self.configuration == 'WIDTH':
            self.dimension.end_x(expression="dim_x",driver_vars=[self.assembly.get_var("dim_x")])
            
        if self.configuration == 'HEIGHT':
            self.dimension.end_z(expression="dim_z",driver_vars=[self.assembly.get_var("dim_z")])
            
        if self.configuration == 'DEPTH':
            self.dimension.end_y(expression="dim_y",driver_vars=[self.assembly.get_var("dim_y")])            
            
        if self.configuration == 'WALL_TOP':
            if self.neg_z_dim == False: 
                self.dimension.start_z(expression="assembly_dim_z", 
                                       driver_vars=[assembly_dim_z])
                
                self.dimension.end_z(expression="wall_dim_z-assembly_loc_z-assembly_dim_z",
                                     driver_vars=[wall_dim_z, assembly_loc_z, assembly_dim_z])
            else:
                self.dimension.end_z(expression="wall_dim_z-assembly_loc_z", 
                                     driver_vars=[wall_dim_z,assembly_loc_z])
            
        if self.configuration == 'WALL_BOTTOM':
            if self.neg_z_dim == False:
                self.dimension.end_z(expression="-assembly_loc_z",driver_vars=[assembly_loc_z])
            else:
                self.dimension.start_z(expression="assembly_dim_z", driver_vars=[assembly_dim_z])
                self.dimension.end_z(expression="-assembly_loc_z-assembly_dim_z",
                                     driver_vars=[assembly_loc_z, assembly_dim_z])
            
        if self.configuration == 'WALL_LEFT':
            self.dimension.end_x(expression="-assembly_loc_x",driver_vars=[assembly_loc_x])
            
        if self.configuration == 'WALL_RIGHT': 
            self.dimension.start_x(expression="dim_x", driver_vars=[self.assembly.get_var("dim_x")])
            self.dimension.end_x(expression="wall_dim_x-assembly_dim_x-assembly_loc_x", 
                                 driver_vars=[wall_dim_x, assembly_dim_x, assembly_loc_x])
            
        if self.configuration == 'AVAILABLE_SPACE_ABOVE':
            if assembly_a:
                self.dimension.start_z(expression="dim_z", driver_vars=[self.assembly.get_var("dim_z")])
                
                if self.above_assembly_draw_to == 'BOTTOM':
                    self.dimension.end_z(expression="assembly_a_loc_z+assembly_a_dim_z-assembly_loc_z-assembly_dim_z", 
                                         driver_vars=[assembly_a_loc_z,
                                                      assembly_a_dim_z,
                                                      assembly_loc_z,
                                                      assembly_dim_z])                     
                else:
                    self.dimension.end_z(expression="assembly_a_loc_z-assembly_loc_z-assembly_dim_z", 
                                         driver_vars=[assembly_a_loc_z,
                                                      assembly_loc_z,
                                                      assembly_dim_z])                   
            else:
                if self.neg_z_dim == False:
                    self.dimension.end_z(expression="wall_dim_z-assembly_loc_z-assembly_dim_z", 
                                         driver_vars=[wall_dim_z,
                                                      assembly_loc_z,
                                                      assembly_dim_z])
                else:
                    self.dimension.end_z(expression="wall_dim_z-assembly_loc_z", 
                                         driver_vars=[wall_dim_z,
                                                      assembly_loc_z])
         
        if self.configuration == 'AVAILABLE_SPACE_BELOW':
            if assembly_b:
                if self.neg_z_dim == False:
                    self.dimension.end_z(expression="-assembly_loc_z+assembly_b_loc_z+assembly_b_dim_z", 
                                         driver_vars=[assembly_loc_z,
                                                      assembly_b_loc_z,
                                                      assembly_b_dim_z])
                else:
                    self.dimension.start_z(expression="assembly_dim_z",driver_vars=[assembly_dim_z])
                    self.dimension.end_z(expression="-assembly_loc_z-assembly_dim_z+assembly_b_loc_z+assembly_b_dim_z",
                                         driver_vars=[assembly_loc_z,
                                                      assembly_dim_z,
                                                      assembly_b_loc_z,
                                                      assembly_b_dim_z])
            else:
                self.dimension.end_z(expression="-loc_z", 
                                     driver_vars=[self.assembly.get_var("loc_z")])
        
        if self.configuration == 'AVAILABLE_SPACE_LEFT':
            if assembly_l:
                self.dimension.end_x(expression="-assembly_loc_x+assembly_l_loc_x+assembly_l_dim_x", 
                                     driver_vars=[assembly_l_loc_x,
                                                  assembly_loc_x,
                                                  assembly_l_dim_x])
            else:
                self.dimension.end_x(expression="-assembly_loc_x", driver_vars=[assembly_loc_x])
            
        if self.configuration == 'AVAILABLE_SPACE_RIGHT':
            self.dimension.start_x(expression="dim_x", driver_vars=[self.assembly.get_var("dim_x")])
            if assembly_r:
                self.dimension.end_x(expression="assembly_r_loc_x-assembly_loc_x-assembly_dim_x", 
                                     driver_vars=[assembly_r_loc_x,
                                                  assembly_loc_x,
                                                  assembly_dim_x])    
                
            else:
                self.dimension.end_x(expression="wall_dim_x-assembly_loc_x-assembly_dim_x", 
                                     driver_vars=[wall_dim_x,
                                                  assembly_loc_x,
                                                  assembly_dim_x])
        
        return {'FINISHED'}    
    
    def draw(self,context):
        layout = self.layout
        config_box = layout.box()  
        config_box.label("Configuration")
        
        row = config_box.row()
        split1 = row.split(align=True)
        split1.label("Assembly Dimension: ")
        split1.prop_enum(self, "configuration", 'WIDTH')
        split1.prop_enum(self, "configuration", 'HEIGHT')
        split1.prop_enum(self, "configuration", 'DEPTH')
        
        row = config_box.row()
        split2 = row.split(align=True)
        split2.label("To Wall: ")
        split2.prop_enum(self, "configuration", 'WALL_LEFT', text="Left")
        split2.prop_enum(self, "configuration", 'WALL_RIGHT', text="Right")
        split2.prop_enum(self, "configuration", 'WALL_TOP', text="Top")
        split2.prop_enum(self, "configuration", 'WALL_BOTTOM', text="Bottom")
        
        row = config_box.row()
        split3 = row.split(align=True)
        split3.label("Available Space: ")
        split3.prop_enum(self, "configuration", 'AVAILABLE_SPACE_LEFT', text="Left")
        split3.prop_enum(self, "configuration", 'AVAILABLE_SPACE_RIGHT', text="Right")
        split3.prop_enum(self, "configuration", 'AVAILABLE_SPACE_ABOVE', text="Above")
        split3.prop_enum(self, "configuration", 'AVAILABLE_SPACE_BELOW', text="Below")
            
        if self.configuration == 'AVAILABLE_SPACE_ABOVE' and self.assembly.get_adjacent_assembly(direction='ABOVE'):
            row = config_box.row()
            row.prop(self, "above_assembly_draw_to", text="Draw to Above Assembly")                            
        
        box2 = layout.box()
        col = box2.column()
        col.prop(self, "label", text="Label")
        col.prop(self, "offset", text="Offset")

class OPS_select_all_products(Operator):   
    bl_idname = "fd_general.select_all_products"
    bl_label = "Select All Products"
    bl_description = "This will select all of the products in the library list"
    
    select_all = BoolProperty(name="Select All",default=True)
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.cabinetlib
        if len(wm.lib_products) > 0:
            return True
        else:
            return False

    def execute(self,context):
        wm = context.window_manager.cabinetlib
        lib = wm.lib_products[wm.lib_product_index]
        for item in lib.items:
            item.selected = self.select_all
        return{'FINISHED'}
    
class OPS_select_all_inserts(Operator):   
    bl_idname = "fd_general.select_all_inserts"
    bl_label = "Select All Inserts"
    bl_description = "This will select all of the inserts in the library list"    
    
    select_all = BoolProperty(name="Select All",default=True)
    
    @classmethod
    def poll(cls, context):
        wm = context.window_manager.cabinetlib
        if len(wm.lib_inserts) > 0:
            return True
        else:
            return False

    def execute(self,context):
        wm = context.window_manager.cabinetlib
        lib = wm.lib_inserts[wm.lib_insert_index]
        for item in lib.items:
            item.selected = self.select_all
        return{'FINISHED'}

class OPS_select_all_elevation_scenes(Operator):   
    bl_idname = "fd_general.select_all_elevation_scenes"
    bl_label = "Select All Elevation Scenes"
    bl_description = "This will select all of the scenes in the elevation scenes list"
    
    select_all = BoolProperty(name="Select All",default=True)
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self,context):
        for scene in bpy.data.scenes:
            if scene.mv.elevation_scene or scene.mv.plan_view_scene:
                scene.mv.elevation_selected = self.select_all
            
        return{'FINISHED'}

class OPS_create_screen_shot(Operator):   
    bl_idname = "fd_general.create_screen_shot"
    bl_label = "Create Screen Shot"
    bl_description = "This will create a screen shot"
    
    @classmethod
    def poll(cls, context):
        if bpy.data.filepath == "":
            return False
        else:
            return True

    def execute(self,context):
        path, filename = os.path.split(bpy.data.filepath)
        file, ext = os.path.splitext(filename)
        save_path = os.path.join(path,file)
        if not os.path.exists(save_path):
            os.mkdir(save_path)
            
        if os.path.exists(os.path.join(save_path,file+".png")):
            counter = 1
            while True:
                if os.path.exists(os.path.join(save_path,file+ " " + str(counter) + ".png")):
                    counter += 1
                else:
                    bpy.ops.screen.screenshot(filepath=os.path.join(save_path,file+ " " + str(counter) + ".png"),full=False)
                    break
        else:
            bpy.ops.screen.screenshot(filepath=os.path.join(save_path,file+".png"),full=False)
            
        return{'FINISHED'}

class OPS_project_info(Operator):
    bl_idname = "fd_general.project_info"
    bl_label = "Create Project"

    def check(self,context):
        return True
    
    def execute(self, context):
        return {'FINISHED'}
        
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(350))
        
    def draw(self, context):
        props = context.scene.mv
        layout = self.layout
        layout.prop(props,"job_name")
        layout.prop(props,"designer_name")
        layout.prop(props,"client_name")
        layout.prop(props,"client_phone")
        layout.prop(props,"client_email")

def select_all_items(self,context):
    wm = context.window_manager.mv
    
    blend_files = wm.data_from_libs
    
    for file in blend_files:
        if self.select_all:
            file.show_expanded = self.select_all
        for item in file.items:
            item.is_selected = self.select_all
 
def expand_all_files(self,context):
    wm = context.window_manager.mv
    
    blend_files = wm.data_from_libs
    
    for file in blend_files:
        file.show_expanded = self.expand_all
    
class OPS_append_items(Operator):   
    bl_idname = "fd_general.append_items"
    bl_label = "Append Items"
    bl_description = "This will append items from the active Library"
    
    blend_files = None
    select_all = BoolProperty(name="Select All",default=False,update=select_all_items)
    expand_all = BoolProperty(name="Expand All",default=False,update=expand_all_files)
    library_tabs = None
    item_icon = 'ERROR'

    @classmethod
    def poll(cls, context):
        if context.scene.mv.ui.library_tabs in ('PRODUCT','INSERT'):
            return False
        else:
            return True

    def execute(self,context):
        scene = context.scene
        for file in self.blend_files:
            for item in file.items:
                if item.is_selected:     
                    file_path = os.path.join(self.path,file.name)

                    if self.library_tabs == 'ASSEMBLY':
                            with bpy.data.libraries.load(file_path, False, False) as (data_from, data_to):
                                for grp in data_from.groups:
                                    if grp == item.name:
                                        data_to.groups = [grp]
                                        break               
                                     
                            for grp in data_to.groups:
                                for obj in grp.objects:
                                    scene.objects.link(obj)     
                 
                    if self.library_tabs == 'OBJECT':
                        with bpy.data.libraries.load(file_path, False, False) as (data_from, data_to):
                            for obj in data_from.objects:
                                if obj == item.name:
                                    data_to.objects = [obj]
                                    break  
                            
                        for obj in data_to.objects:
                            scene.objects.link(obj)                                             
          
                    if self.library_tabs == 'MATERIAL':               
                        mats = []
                        with bpy.data.libraries.load(file_path, False, False) as (data_from, data_to):
                            for mat in data_from.materials:
                                if mat == item.name:
                                    mats.append(mat)
                                    break        
                            
                            data_to.materials = mats                              
                 
                    if self.library_tabs == 'WORLD':
                            worlds = []
                            with bpy.data.libraries.load(file_path, False, False) as (data_from, data_to):
                                for world in data_from.worlds:
                                    if world == item.name:
                                        worlds.append(world)
                                        break        
                                  
                                data_to.worlds = worlds                
                                     
        return{'FINISHED'}

    def invoke(self,context,event):
        self.blend_files = context.window_manager.mv.data_from_libs
        
        self.path = utils.get_file_browser_path(context)
        self.library_tabs = context.scene.mv.ui.library_tabs
        files = os.listdir(self.path)
        
        for file in self.blend_files:
            self.blend_files.remove(0)
        
        for filename in files:
            if ".blend" in filename:
                blend_file = self.blend_files.add()
                blend_file.name = filename
                
                file_path = os.path.join(self.path,filename)
                
                with bpy.data.libraries.load(file_path, False, False) as (data_from, data_to):
                    if self.library_tabs == 'ASSEMBLY':
                        for grp in data_from.groups:
                            lib_item = blend_file.items.add()
                            lib_item.name = grp
                            self.item_icon = 'OUTLINER_DATA_LATTICE'
                    
                    if self.library_tabs == 'OBJECT':
                        for obj in data_from.objects:
                            lib_item = blend_file.items.add()
                            lib_item.name = obj
                            self.item_icon = 'OBJECT_DATA'
                            
                    if self.library_tabs == 'MATERIAL':
                        for mat in data_from.materials:
                            lib_item = blend_file.items.add()
                            lib_item.name = mat
                            self.item_icon = 'MATERIAL'
                    
                    if self.library_tabs == 'WORLD':
                        for world in data_from.worlds:
                            lib_item = blend_file.items.add()
                            lib_item.name = world  
                            self.item_icon = 'WORLD'                                      
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(350))
    
    def check(self,context):
        return True
        
    def draw(self, context):     
        layout = self.layout
        header_box = layout.box()
        row = header_box.row(align=True)
        
        row.prop(self,
                 "select_all",
                 text="Select All",
                 icon='CHECKBOX_HLT' if self.select_all else 'CHECKBOX_DEHLT',
                 emboss=False)
        
        row.prop(self,
                 "expand_all",
                 text="Expand All",
                 icon='CHECKBOX_HLT' if self.expand_all else 'CHECKBOX_DEHLT',
                 emboss=False)        
        
        for blend_file in self.blend_files:
            col = layout.column(align=True)
            box = col.box()
            col = box.column(align=True)
            row = col.row()
            row.prop(blend_file,"show_expanded",
                     text="",
                     icon='TRIA_DOWN' if blend_file.show_expanded else 'TRIA_RIGHT',
                     emboss=False)
            
            row.label(blend_file.name,icon='FILE_BLEND')
            
            for item in blend_file.items:
                if blend_file.show_expanded:
                    row = col.row()
                    row.label(text="",icon='BLANK1')
                    row.label(text="",icon='BLANK1')
                    row.label(text=item.name,icon=self.item_icon)
                    row.prop(item,"is_selected",text="")       

class OPS_create_thumbnails(Operator):   
    bl_idname = "fd_general.create_thumbnails"
    bl_label = "Create Thumbnails"
    bl_description = "This will create all of the thumbnails for selected items in the current directory"
    
    blend_files = None
    select_all = BoolProperty(name="Select All",default=False,update=select_all_items)
    expand_all = BoolProperty(name="Expand All",default=False,update=expand_all_files)
    library_tabs = None
    item_icon = 'ERROR'

    @classmethod
    def poll(cls, context):
        if context.scene.mv.ui.library_tabs in ('PRODUCT','INSERT'):
            return False
        else:
            return True

    def create_assembly_thumbnail_script(self,source_dir,source_file,assembly_name):

        file = open(os.path.join(source_dir,"temp.py"),'w')
        file.write("import bpy\n")
        file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
        file.write("    for grp in data_from.groups:\n")
        file.write("        if grp == '" + assembly_name + "':\n")
        file.write("            data_to.groups = [grp]\n")
        file.write("            break\n")
        file.write("for grp in data_to.groups:\n")
        file.write("    for obj in grp.objects:\n")
        file.write("        bpy.context.scene.objects.link(obj)\n")
        file.write("        obj.select = True\n")
        file.write("    bpy.ops.view3d.camera_to_view_selected()\n")
        file.write("    render = bpy.context.scene.render\n")
        file.write("    render.use_file_extension = True\n")
        file.write("    render.filepath = r'" + os.path.join(source_dir,assembly_name) + "'\n")
        file.write("    bpy.ops.render.render(write_still=True)\n")
        file.close()
        return os.path.join(source_dir,'temp.py')

    def create_object_thumbnail_script(self,source_dir,source_file,object_name):
        file = open(os.path.join(source_dir,"temp.py"),'w')
        file.write("import bpy\n")
        file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
        file.write("    for obj in data_from.objects:\n")
        file.write("        if obj == '" + object_name + "':\n")
        file.write("            data_to.objects = [obj]\n")
        file.write("            break\n")
        file.write("for obj in data_to.objects:\n")
        file.write("    bpy.context.scene.objects.link(obj)\n")
        file.write("    obj.select = True\n")
        file.write("    if obj.type == 'CURVE':\n")
        file.write("        bpy.context.scene.camera.rotation_euler = (0,0,0)\n")
        file.write("        obj.data.dimensions = '2D'\n")
        file.write("    bpy.context.scene.objects.active = obj\n")
        file.write("    bpy.ops.view3d.camera_to_view_selected()\n")
        file.write("    render = bpy.context.scene.render\n")
        file.write("    render.use_file_extension = True\n")
        file.write("    render.filepath = r'" + os.path.join(source_dir,object_name) + "'\n")
        file.write("    bpy.ops.render.render(write_still=True)\n")
        file.close()
        return os.path.join(source_dir,'temp.py')  

    def create_material_thumbnail_script(self,source_dir,source_file,material_name):
        file = open(os.path.join(source_dir,"temp.py"),'w')
        file.write("import bpy\n")
        file.write("from mv import unit\n")
        file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
        file.write("    for mat in data_from.materials:\n")
        file.write("        if mat == '" + material_name + "':\n")
        file.write("            data_to.materials = [mat]\n")
        file.write("            break\n")
        file.write("for mat in data_to.materials:\n")
        file.write("    bpy.ops.mesh.primitive_cube_add()\n")
        file.write("    obj = bpy.context.scene.objects.active\n")
        file.write("    obj.dimensions = (unit.inch(24),unit.inch(24),unit.inch(24))\n")
        file.write("    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)\n")
        file.write("    mod = obj.modifiers.new('bevel','BEVEL')\n")
        file.write("    mod.segments = 5\n")
        file.write("    mod.width = .05\n")
        file.write("    bpy.ops.object.modifier_apply(modifier='bevel')\n")
        file.write("    bpy.ops.fd_object.unwrap_mesh(object_name=obj.name)\n")
        file.write("    bpy.ops.fd_object.add_material_slot(object_name=obj.name)\n")
        file.write("    for slot in obj.material_slots:\n")
        file.write("        slot.material = mat\n")
        file.write("    bpy.context.scene.objects.active = obj\n")
        file.write("    bpy.ops.view3d.camera_to_view_selected()\n")
        file.write("    render = bpy.context.scene.render\n")
        file.write("    render.use_file_extension = True\n")
        file.write("    render.filepath = r'" + os.path.join(source_dir,material_name) + "'\n")
        file.write("    bpy.ops.render.render(write_still=True)\n")
        file.close()
        return os.path.join(source_dir,'temp.py')

    def create_world_thumbnail_script(self,source_dir,source_file,world_name):
        file = open(os.path.join(source_dir,"temp.py"),'w')
        file.write("import bpy\n")
        file.write("with bpy.data.libraries.load(r'" + source_file + "', False, True) as (data_from, data_to):\n")
        file.write("    for world in data_from.worlds:\n")
        file.write("        if world == '" + world_name + "':\n")
        file.write("            data_to.worlds = [world]\n")
        file.write("            break\n")
        file.write("for world in data_to.worlds:\n")
        file.write("    bpy.context.scene.world = world\n")
        file.write("    bpy.context.scene.camera.data.type = 'PANO'\n")
        file.write("    bpy.context.scene.camera.data.cycles.panorama_type = 'EQUIRECTANGULAR'\n")
        file.write("    bpy.context.scene.cycles.film_transparent = False\n")
        file.write("    render = bpy.context.scene.render\n")
        file.write("    render.use_file_extension = True\n")
        file.write("    render.filepath = r'" + os.path.join(source_dir,world_name) + "'\n")
        file.write("    bpy.ops.render.render(write_still=True)\n")
        file.close()
        return os.path.join(source_dir,'temp.py')

    def execute(self,context):
        
        for file in self.blend_files:
            for item in file.items:
                if item.is_selected:
                    file_path = os.path.join(self.path,file.name) 
                    
                    if self.library_tabs == 'ASSEMBLY':
                        script = self.create_assembly_thumbnail_script(self.path,file_path,item.name)  
                 
                    if self.library_tabs == 'OBJECT':
                        script = self.create_object_thumbnail_script(self.path,file_path,item.name)
          
                    if self.library_tabs == 'MATERIAL':               
                        script = self.create_material_thumbnail_script(self.path,file_path,item.name)                        
                 
                    if self.library_tabs == 'WORLD':
                        script = self.create_world_thumbnail_script(self.path,file_path,item.name)
                    
                    subprocess.call(bpy.app.binary_path + ' "' + get_thumbnail_path() + '" -b --python "' + script + '"')                          
                    
                    os.remove(script)
                                     
        return{'FINISHED'}

    def invoke(self,context,event):
        self.blend_files = context.window_manager.mv.data_from_libs
        for file in self.blend_files:
            self.blend_files.remove(0)
                
        self.path = utils.get_file_browser_path(context)
        self.library_tabs = context.scene.mv.ui.library_tabs
        files = os.listdir(self.path)
        
        for filename in files:
            if ".blend" in filename:
                blend_file = self.blend_files.add()
                blend_file.name = filename
                
                file_path = os.path.join(self.path,filename)
                
                with bpy.data.libraries.load(file_path, False, False) as (data_from, data_to):
                    if self.library_tabs == 'ASSEMBLY':
                        for grp in data_from.groups:
                            lib_item = blend_file.items.add()
                            lib_item.name = grp
                            self.item_icon = 'OUTLINER_DATA_LATTICE'
                    
                    if self.library_tabs == 'OBJECT':
                        for obj in data_from.objects:
                            lib_item = blend_file.items.add()
                            lib_item.name = obj
                            self.item_icon = 'OBJECT_DATA'
                            
                    if self.library_tabs == 'MATERIAL':
                        for mat in data_from.materials:
                            lib_item = blend_file.items.add()
                            lib_item.name = mat
                            self.item_icon = 'MATERIAL'
                    
                    if self.library_tabs == 'WORLD':
                        for world in data_from.worlds:
                            lib_item = blend_file.items.add()
                            lib_item.name = world  
                            self.item_icon = 'WORLD'                                      
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(350))
    
    def check(self,context):
        return True
        
    def draw(self, context):     
        layout = self.layout
        header_box = layout.box()
        row = header_box.row(align=True)
        
        row.prop(self,
                 "select_all",
                 text="Select All",
                 icon='CHECKBOX_HLT' if self.select_all else 'CHECKBOX_DEHLT',
                 emboss=False)
        
        row.prop(self,
                 "expand_all",
                 text="Expand All",
                 icon='CHECKBOX_HLT' if self.expand_all else 'CHECKBOX_DEHLT',
                 emboss=False)        
        
        for blend_file in self.blend_files:
            col = layout.column(align=True)
            box = col.box()
            col = box.column(align=True)
            row = col.row()
            row.prop(blend_file,"show_expanded",
                     text="",
                     icon='TRIA_DOWN' if blend_file.show_expanded else 'TRIA_RIGHT',
                     emboss=False)
            
            row.label(blend_file.name,icon='FILE_BLEND')
            
            for item in blend_file.items:
                if blend_file.show_expanded:
                    row = col.row()
                    row.label(text="",icon='BLANK1')
                    row.label(text="",icon='BLANK1')
                    row.label(text=item.name,icon=self.item_icon)
                    row.prop(item,"is_selected",text="")                                 

#------REGISTER
classes = [
           OPS_drag_and_drop,
           OPS_drop_product,
           OPS_drop_insert,
           OPS_drop_material,
           OPS_drop_assembly,
           OPS_drop_object,
           OPS_drop_world,
           OPS_properties,
           OPS_change_mode,
           OPS_add_library_package,
           OPS_delete_library_package,
           OPS_update_library_xml,
           OPS_load_library_modules,
           OPS_brd_library_items,
           OPS_place_product,
           OPS_change_file_browser_path,
           OPS_change_library,
           OPS_change_category,
           OPS_add_floor_plan,
           OPS_reload_library,
           OPS_open_new_window,
           OPS_load_fluid_designer_defaults,
           OPS_save_startup_file,
           OPS_open_blend_file,
           OPS_dialog_show_filters,
           OPS_change_shademode,
           OPS_error,
           OPS_start_debug,
           OPS_set_cursor_location,
           OPS_load_blender_defaults,
           OPS_open_browser_window,
           OPS_check_for_updates,
           OPS_dimension_interface,
           OPS_toggle_dimension_handles,
           OPS_create_single_dimension,
           OPS_Add_Dimension,
           OPS_select_all_products,
           OPS_select_all_inserts,
           OPS_select_all_elevation_scenes,
           OPS_create_thumbnails,
           OPS_append_items,
           OPS_create_screen_shot,
           OPS_project_info
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
