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

import bpy
import bgl
import math
from bpy.types import Header, Menu, Operator
import os, subprocess
import time
from bpy.app.handlers import persistent
import bpy_extras.image_utils as img_utils
from mv import utils, fd_types, unit
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       PointerProperty,
                       EnumProperty)

from mathutils import Matrix
from bpy_extras.io_utils import axis_conversion
from mathutils.geometry import normal

def get_export_prompts(obj_bp):
    """ Used in create_fluid_project_xml
        this collects all of the needed product prompts for the 121 product match
    """
    
    prompts = {}
    
    def add_prompt(prompt):
        if prompt.Type == 'NUMBER':
            prompts[prompt.name] = str(prompt.NumberValue)
        if prompt.Type == 'QUANTITY':
            prompts[prompt.name] = str(prompt.QuantityValue)
        if prompt.Type == 'COMBOBOX':
            prompts[prompt.name] = str(prompt.COL_EnumItem[prompt.EnumIndex].name)
        if prompt.Type == 'CHECKBOX':
            prompts[prompt.name] = str(prompt.CheckBoxValue)
        if prompt.Type == 'TEXT':
            prompts[prompt.name] = str(prompt.TextValue)
        if prompt.Type == 'DISTANCE':
            prompts[prompt.name] = str(round(unit.meter_to_active_unit(prompt.DistanceValue),4))
        if prompt.Type == 'ANGLE':
            prompts[prompt.name] = str(prompt.AngleValue)
        if prompt.Type == 'PERCENTAGE':
            prompts[prompt.name] = str(prompt.PercentageValue)
        if prompt.Type == 'PRICE':
            prompts[prompt.name] = str(prompt.PriceValue)
    
    def add_child_prompts(obj):
        for child in obj.children:
            if child.mv.type == 'BPASSEMBLY':
                add_prompts(child)
            if len(child.children) > 0:
                add_child_prompts(child)
        
    def add_prompts(obj):
        for prompt in obj.mv.PromptPage.COL_Prompt:
            if prompt.export:
                add_prompt(prompt)
                
    add_prompts(obj_bp)
    add_child_prompts(obj_bp)

    return prompts

def faces_from_mesh(ob, global_matrix, use_mesh_modifiers=False, triangulate=True):
    """
    From an object, return a generator over a list of faces.

    Each faces is a list of his vertexes. Each vertex is a tuple of
    his coordinate.

    use_mesh_modifiers
        Apply the preview modifier to the returned liste

    triangulate
        Split the quad into two triangles
    """

    # get the editmode data
    ob.update_from_editmode()

    # get the modifiers
    try:
        mesh = ob.to_mesh(bpy.context.scene, use_mesh_modifiers, "PREVIEW")
    except RuntimeError:
        raise StopIteration

    mesh.transform(global_matrix * ob.matrix_world)

    if triangulate:
        # From a list of faces, return the face triangulated if needed.
        def iter_face_index():
            for face in mesh.tessfaces:
                vertices = face.vertices[:]
                if len(vertices) == 4:
                    yield vertices[0], vertices[1], vertices[2]
                    yield vertices[2], vertices[3], vertices[0]
                else:
                    yield vertices
    else:
        def iter_face_index():
            for face in mesh.tessfaces:
                yield face.vertices[:]

    vertices = mesh.vertices

    for indexes in iter_face_index():
        yield [vertices[index].co.copy() for index in indexes]

    bpy.data.meshes.remove(mesh)

class OPS_render_scene(Operator):
    bl_idname = "fd_scene.render_scene"
    bl_label = "Render Scene"

    write_still = BoolProperty(name="Write Still",
                               description="Write image to disk after render",
                               default=False)

    def execute(self, context):
        ui = context.scene.mv.ui
        rd = context.scene.render
        rl = rd.layers.active
        freestyle_settings = rl.freestyle_settings
        scene = context.scene

        if scene.camera is None:
            self.report({'ERROR'}, "Cannot render - there is no camera in the scene!")
            #Add camera automatically?
            return {'FINISHED'}

        if ui.render_type_tabs == 'NPR':
            rd.engine = 'BLENDER_RENDER'
            rd.use_freestyle = True
            rd.line_thickness = 0.75
            rd.resolution_percentage = 100
            rl.use_pass_combined = False
            rl.use_pass_z = False
            freestyle_settings.crease_angle = 2.617994
            
        if context.window_manager.mv.use_opengl_dimensions:
            file_format = context.scene.render.image_settings.file_format.lower()
            
            bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
            
            while not os.path.exists(bpy.path.abspath(context.scene.render.filepath) + "." + file_format):
                time.sleep(0.1)
                
            img_result = utils.render_opengl(self,context)
            
            if self.write_still == True:
                abs_filepath = bpy.path.abspath(context.scene.render.filepath)
                save_path = abs_filepath.replace("_tmp","") + "." + file_format.lower()
                img_result.save_render(save_path)
                
        else:
            bpy.ops.render.render('INVOKE_DEFAULT')
            
            if self.write_still == True:
                bpy.ops.render.render('INVOKE_DEFAULT',write_still=True)
                
        return {'FINISHED'}

    @persistent
    def set_to_cycles_re(self):
        bpy.context.scene.render.engine = 'CYCLES'

    bpy.app.handlers.render_complete.append(set_to_cycles_re)

class OPS_render_settings(Operator): 
    bl_idname = "fd_scene.render_settings"
    bl_label = "Render Settings"
    
    def execute(self, context):
        return {'FINISHED'}
    
    def check(self,context):
        return True
    
    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(400))

    def draw(self, context):
        layout = self.layout
        scene = bpy.context.scene
        rd = scene.render
        image_settings = rd.image_settings
        ui = context.scene.mv.ui
        rl = rd.layers.active
        linestyle = rl.freestyle_settings.linesets[0].linestyle
        
        box = layout.box()
        row = box.row(align=True)
        row.prop_enum(ui,"render_type_tabs", 'PRR',icon='RENDER_STILL',text="Photo Realistic Render")
        row.prop_enum(ui,"render_type_tabs", 'NPR',icon='SNAP_FACE',text="Line Drawing")
        row = box.row(align=True)
        row.label(text="Render Size:",icon='STICKY_UVS_VERT')        
        row.prop(rd, "resolution_x", text="X")
        row.prop(rd, "resolution_y", text="Y")
        row = box.row(align=True)
        row.label("Resolution Percentage:")
        row.prop(rd, "resolution_percentage", text="")
        
        if ui.render_type_tabs == 'PRR':
            row = box.row()
            row.label(text="Rendering Quality:",icon='IMAGE_COL')
            row.prop(scene.cycles,"samples",text='Passes')
            row = box.row()
            row.label(text="Image Format:",icon='IMAGE_DATA')
            row.prop(image_settings,"file_format",text="")
            row = box.row()
            row.label(text="Display Mode:",icon='RENDER_RESULT')
            row.prop(rd,"display_mode",text="")
            row = box.row()
            row.label(text="Use Transparent Film:",icon='SEQUENCE')
            row.prop(scene.cycles,"film_transparent",text='')
            
        if ui.render_type_tabs == 'NPR':
            row = box.row()
            row.label(text="Image Format:",icon='IMAGE_DATA')
            row.prop(image_settings,"file_format",text="")
            row = box.row()
            row.label(text="Display Mode:",icon='RENDER_RESULT')
            row.prop(rd,"display_mode",text="")
            row = box.row()
            row.prop(linestyle, "color", text="Line Color")
            row = box.row()
            row.prop(bpy.data.worlds[0], "horizon_color", text="Background Color")
        
class OPS_add_thumbnail_camera_and_lighting(Operator):
    bl_idname = "fd_scene.add_thumbnail_camera_and_lighting"
    bl_label = "Add Thumbnail Camera"
    bl_options = {'UNDO'}

    def execute(self, context):
        bpy.ops.object.camera_add(view_align=True)
        camera = context.active_object
        context.scene.camera = camera
        context.scene.cycles.film_transparent = True
        
        camera.data.clip_end = 9999
        camera.scale = (10,10,10)
        
        bpy.ops.object.lamp_add(type='SUN')
        sun = bpy.context.object
        sun.select = False
        sun.rotation_euler = (.785398, .785398, 0.0)
        
        context.scene.render.resolution_x = 1080
        context.scene.render.resolution_y = 1080
        context.scene.render.resolution_percentage = 25
        
        override = {}
        for window in bpy.context.window_manager.windows:
            screen = window.screen
             
            for area in screen.areas:
                if area.type == 'VIEW_3D':
                    override = {'window': window, 'screen': screen, 'area': area}
                    bpy.ops.view3d.camera_to_view(override)
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.lock_camera = True
                    break
        return {'FINISHED'}
        
class OPS_create_unity_build(Operator): #Not Used
    bl_idname = "fd_scene.create_unity_build"
    bl_label = "Build for Unity 3D"
    bl_options = {'UNDO'}
    
    save_name = StringProperty(name="Name")
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        subprocess.call("\"C:\\Program Files (x86)\\Unity\\Editor\\Unity.exe\"" + \
                         "-batchmode -executeMethod PerformBuild.build", shell=False)
        return {'FINISHED'}            

class OPS_prepare_For_sketchfab(Operator):
    """ This prepares the scene for uploading to Sketchfab.
    """
    bl_idname = "cabinetlib.delete_hidden_objects"
    bl_label = "Delete Hidden Objects"
    bl_description = "This simplifies the scene."
    bl_options = {'UNDO'}
    
    _timer = None
    current_item = 0
    objects = []
    delete_objs = []
    bps = []
    
    def invoke(self, context, event):
        wm = context.window_manager
        
        for obj in bpy.context.scene.objects:
            if obj.type == 'CURVE' and obj.parent:
                obj.select = True
                bpy.context.scene.objects.active = obj
                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.select_all(action='DESELECT')
                #these also need to be unwraped correctly
            
            if obj.type == 'MESH':
                if len(obj.data.vertices) > 1:
                    self.objects.append(obj)   
        
        self._timer = wm.event_timer_add(0.001, context.window)
        wm.modal_handler_add(self)
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(utils.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            self.mouse_loc = []
            self.mouse_text = "Preparing Object "  + str(self.current_item + 1) + " of " + str(len(self.objects))
            self.header_text = "Preparing Object " + str(self.current_item + 1) + " of " + str(len(self.objects))
        return {'RUNNING_MODAL'}    
    
    def modal(self, context, event):
        context.area.tag_redraw()
        self.mouse_loc = (event.mouse_region_x,event.mouse_region_y)
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return self.cancel(context)
        
        if event.type == 'TIMER':
            if self.current_item + 1 <= len(self.objects):                     
                obj = self.objects[self.current_item]
                bpy.context.scene.objects.active = obj
                #clear shapekeys
                if obj.data.shape_keys:
                    bpy.ops.fd_object.apply_shape_keys(object_name=obj.name)           
                
                #clear modifiers 
#                 for mod in obj.modifiers:
#                     bpy.ops.object.modifier_apply(mod.name)
#                 if obj.modifiers != 'NONE':  
                    #obj.to_mesh(context.scene,True,'PREVIEW')
                    #This needs to be done in the correct order (mods applied only if first in stack)
                bpy.ops.fd_object.apply_hook_modifiers(object_name=obj.name)
                bpy.ops.fd_object.apply_bool_modifiers(object_name=obj.name)
                    #bpy.ops.fd_object.apply_array_modifiers(object_name=obj.name)
#                     #Apply Bevel Modifiers
                
                #clear drivers 
                if obj.animation_data:
                    for DR in obj.animation_data.drivers:
                        obj.driver_remove(DR.data_path)                 
                
                #clear vertex groups         
                if obj.vertex_groups:
                    bpy.context.scene.objects.active = obj
                    bpy.ops.object.vertex_group_remove(all=True) 
                
                #clear parent and keep transformation          
                obj.matrix_local = obj.matrix_world
                obj.parent = None
                    
                self.current_item += 1
                
                if self.current_item + 1 <= len(self.objects):
                    self.mouse_text = "Preparing Object " + str(self.current_item + 1) + " of " + str(len(self.objects))
                    self.header_text = "Preparing Object " + str(self.current_item + 1) + " of " + str(len(self.objects))
                context.area.tag_redraw()
            else:
                self.delete_extra_objs()
                bpy.ops.fd_material.clear_material_copies()
                bpy.ops.fd_scene.join_meshes_by_material()  
                return self.cancel(context)
        return {'PASS_THROUGH'}    
    
    def delete_extra_objs(self):  
        for obj in bpy.context.scene.objects:
            if obj.parent:
                if obj.parent.mv.type != 'BPWALL': 
                    if obj not in self.delete_objs:
                        self.delete_objs.append(obj)
                             
                    if obj.type == 'EMPTY':
                        if obj not in self.delete_objs:
                            self.delete_objs.append(obj)
                             
                    if obj.mv.type == 'BPASSEMBLY':
                        if obj not in self.delete_objs:
                            self.delete_objs.append(obj)
                             
            if obj.mv.use_as_bool_obj:
                if obj not in self.delete_objs:
                    self.delete_objs.append(obj)
                 
            if obj.mv.type in {'BPWALL','BPASSEMBLY','VPDIMX','VPDIMY','VPDIMZ'}:
                if obj not in self.delete_objs:
                    self.delete_objs.append(obj)    
                    
            if obj.hide == True or obj.hide_select == True:
                if obj not in self.delete_objs:
                    self.delete_objs.append(obj) 
                      
        utils.delete_obj_list(self.delete_objs)        
    
    def cancel(self, context):
        progress = context.window_manager.cabinetlib
        progress.current_item = 0
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        return {'FINISHED'}    

class OPS_join_meshes_by_material(Operator):
    bl_idname = "fd_scene.join_meshes_by_material"
    bl_label = "Join Meshes by Material"
    bl_options = {'UNDO'}
    
    obj_join = []

    def gather_objects_by_material(self, mat):
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                if obj.material_slots:
                    if obj.material_slots[0].material == mat:
                        self.obj_join.append(obj)        

    def execute(self, context):                 
        objects = bpy.context.scene.objects
        materials = bpy.data.materials
        
        #seperate meshes by material slots
#         for obj in objects:
#             obj.select = True
        bpy.ops.object.select_all(action='SELECT')    
        bpy.ops.mesh.separate(type='MATERIAL')
        bpy.ops.object.select_all(action='DESELECT')            
        #bpy.context.scene.objects.active = None

        #add objs w same materials to list
        #do this faster
        
        for mat in materials:
            self.gather_objects_by_material(mat)

            #join objects
            if self.obj_join:
                bpy.context.scene.objects.active = self.obj_join[0]
                for obj in self.obj_join:
                    obj.select = True
                    #bpy.context.selected_objects.append(obj)  
                
                if bpy.context.active_object != 'NONE':    
                    bpy.ops.object.join()              
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.scene.objects.active = None
                
            self.obj_join.clear()
#                       
#                 bpy.ops.object.join()
#                 bpy.ops.object.select_all(action='DESELECT')
#                 bpy.context.scene.objects.active = None
#                 obj_join.clear()
#                 
#             else:
#                 continue
            
        return {'FINISHED'}

class OPS_Prepare_Plan_view(Operator):
    bl_idname = "fd_scene.prepare_plan_view"    
    bl_label = "Prepare Plan View"
    bl_description = "Prepare Plan View"
    bl_options = {'UNDO'}    
    
    padding = FloatProperty(name="Padding",
                            default=0.25)
    
    def execute(self,context):
        print("NEW OP")
        original_scene = context.screen.scene
        
        prev_pv = None

        for scene in bpy.data.scenes:
            if scene.mv.plan_view_scene:
                prev_pv = scene
                context.screen.scene = scene
                bpy.ops.scene.delete()        
            
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')   
        pv_scene = context.scene     
        pv_scene.name = "Plan View"
        pv_scene.mv.name_scene = "Plan View" 
        pv_scene.mv.plan_view_scene = True 
        if prev_pv:
            pv_scene.mv.elevation_selected = prev_pv.mv.elevation_selected
            
        for obj in original_scene.objects:
            if obj.mv.type == 'BPWALL':
                for child in obj.children:
                    if child.mv.is_wall_mesh:
                        print(obj,"MESH")
                        pv_scene.objects.link(obj)    
            
        for obj in pv_scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj_bp = obj)
                wall.get_wall_mesh().select = True
                
        cam_name = "Plan View Camera"
        
        camera_data = bpy.data.cameras.new(cam_name)
        camera_obj = bpy.data.objects.new(name=cam_name, 
                                          object_data=camera_data)
        
        pv_scene.objects.link(camera_obj)
        pv_scene.camera = camera_obj                
                
        camera_obj.rotation_euler.z = math.radians(-90.0)    
        camera_obj.data.type = 'ORTHO'
        pv_scene.render.resolution_y = 1280
        bpy.ops.view3d.camera_to_view_selected()    
        camera_obj.data.ortho_scale += self.padding                
        
        pv_scene.mv.opengl_dim.gl_default_color = (0.1, 0.1, 0.1, 1.0)
        pv_scene.mv.ui.render_type_tabs = 'NPR'
        lineset = pv_scene.render.layers["RenderLayer"].freestyle_settings.linesets.new("LineSet")
        lineset.linestyle = \
        original_scene.render.layers["RenderLayer"].freestyle_settings.linesets["LineSet"].linestyle
        
        if pv_scene.world == None:
            pv_scene.world = bpy.data.worlds["World"]        
        
        pv_scene.world.horizon_color = (1.0, 1.0, 1.0)
        pv_scene.render.display_mode = 'NONE'
        pv_scene.render.use_lock_interface = True

        context.window_manager.mv.use_opengl_dimensions = True
        
        return {'FINISHED'}   
    
class OPS_Prepare_Plan_view_OLD(Operator):
    bl_idname = "fd_scene.prepare_plan_view_old"    
    bl_label = "Prepare Plan View"
    bl_description = "Prepare Plan View"
    bl_options = {'UNDO'}    
    
    padding = FloatProperty(name="Padding",
                            default=0.25)
    
    def execute(self,context):
        
        original_scene = context.screen.scene
        
        prev_pv = None

        for scene in bpy.data.scenes:
            if scene.mv.plan_view_scene:
                prev_pv = scene
                context.screen.scene = scene
                bpy.ops.scene.delete()        
            
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')   
        pv_scene = context.scene     
        pv_scene.name = "Plan View"
        pv_scene.mv.name_scene = "Plan View" 
        pv_scene.mv.plan_view_scene = True 
        if prev_pv:
            pv_scene.mv.elevation_selected = prev_pv.mv.elevation_selected
            
        for obj in original_scene.objects:
            pv_scene.objects.link(obj)    
            
        for obj in pv_scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj_bp = obj)
                wall.get_wall_mesh().select = True
                
        cam_name = "Plan View Camera"
        
        camera_data = bpy.data.cameras.new(cam_name)
        camera_obj = bpy.data.objects.new(name=cam_name, 
                                          object_data=camera_data)
        
        pv_scene.objects.link(camera_obj)
        pv_scene.camera = camera_obj                
                
        camera_obj.rotation_euler.z = math.radians(-90.0)    
        camera_obj.data.type = 'ORTHO'
        pv_scene.render.resolution_y = 1280
        bpy.ops.view3d.camera_to_view_selected()    
        camera_obj.data.ortho_scale += self.padding                
        
        pv_scene.mv.opengl_dim.gl_default_color = (0.1, 0.1, 0.1, 1.0)
        pv_scene.mv.ui.render_type_tabs = 'NPR'
        lineset = pv_scene.render.layers["RenderLayer"].freestyle_settings.linesets.new("LineSet")
        lineset.linestyle = \
        original_scene.render.layers["RenderLayer"].freestyle_settings.linesets["LineSet"].linestyle
        
        if pv_scene.world == None:
            pv_scene.world = bpy.data.worlds["World"]        
        
        pv_scene.world.horizon_color = (1.0, 1.0, 1.0)
        pv_scene.render.display_mode = 'NONE'
        pv_scene.render.use_lock_interface = True

        context.window_manager.mv.use_opengl_dimensions = True
        
        return {'FINISHED'}       
    
class OPS_Prepare_2d_elevations(Operator):
    bl_idname = "fd_scene.prepare_2d_elevations"    
    bl_label = "Prepare for Printing 2D Elevation"
    bl_description = "Prepare for Printing 2D Elevation"
    bl_options = {'UNDO'}    
    
    padding = 0.75  
    
    def group_wall_objects(self, obj_bp, group):
        objs = []
        objs.append(obj_bp)
        
        for child in obj_bp.children:
            if len(child.children) > 0:
                self.group_wall_objects(child, group)
            else:
                objs.append(child)

        for obj in objs:
            group.objects.link(obj)
            
    def link_grp_instance_to_scene(self, group, scene, obj_bp):  
        instance = bpy.data.objects.new(obj_bp.mv.name_object + " "  + "Instance" , None)
        scene.objects.link(instance)
        instance.dupli_type = 'GROUP'
        instance.dupli_group = group        
        
    def set_cameras(self, current_scene, new_scene, wall):  
        camera_data = bpy.data.cameras.new(new_scene.name)
        camera_obj = bpy.data.objects.new(name=camera_data.name + " Camera", 
                                          object_data=camera_data)
         
        current_scene.objects.link(camera_obj)    
        current_scene.camera = camera_obj
        camera_obj.data.type = 'ORTHO'
        camera_obj.rotation_euler.x = math.radians(90.0) 
        camera_obj.rotation_euler.z = wall.obj_bp.rotation_euler.z    
        camera_obj.location = wall.obj_bp.location       
        
        bpy.ops.object.select_all(action='DESELECT')
        wall.get_wall_mesh().select = True
        bpy.ops.view3d.camera_to_view_selected()     
        
        current_scene.camera = None
        current_scene.objects.unlink(camera_obj)
        new_scene.objects.link(camera_obj)
        new_scene.camera = camera_obj
        new_scene.render.resolution_y = 1280
        bpy.data.cameras[new_scene.name].ortho_scale += self.padding
        
    def link_vis_dim_empties_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if child.mv.type in ('VISDIM_A','VISDIM_B'):
                scene.objects.link(child)
            if len(child.children) > 0:
                self.link_vis_dim_empties_to_scene(scene, child) 
                      
    def execute(self, context):
        original_scene = bpy.data.scenes[context.scene.name]
        context.window_manager.mv.use_opengl_dimensions = True
        walls = []
        existing_scenes = {}
        
        bpy.ops.fd_scene.clear_2d_views()
#         for scene in bpy.data.scenes:
#             if scene.mv.elevation_scene or scene.mv.plan_view_scene:
#                 existing_scenes[scene.name] = scene.mv.elevation_selected
#                 context.screen.scene = scene
#                 bpy.ops.scene.delete()
         
        for obj in context.scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj_bp = obj)
                walls.append(wall)
                if len(wall.get_wall_groups()) > 0:
                     
                    wall_group = bpy.data.groups.new(obj.mv.name_object)
                    self.group_wall_objects(obj, wall_group)
                      
                    bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')
                    new_scene = context.scene
                    new_scene.name = obj.name
                    
                    if new_scene.name in existing_scenes:
                        new_scene.mv.elevation_selected = existing_scenes[new_scene.name]
                        print("NEW SCENE",new_scene.mv.elevation_selected)
                        
                    new_scene.mv.name_scene = obj.mv.name_object + " " + str(obj.mv.item_number)
                    new_scene.mv.elevation_img_name = obj.name
                    new_scene.mv.elevation_scene = True
                    
                    new_scene.world = original_scene.world
                    self.link_vis_dim_empties_to_scene(new_scene, obj)
      
                    bpy.context.screen.scene = original_scene
                        
                    self.link_grp_instance_to_scene(wall_group, new_scene, obj)   
                         
                    self.set_cameras(original_scene, new_scene, wall)
                
                    new_scene.mv.opengl_dim.gl_default_color = (0.1, 0.1, 0.1, 1.0)
                    new_scene.mv.ui.render_type_tabs = 'NPR'
                    lineset = new_scene.render.layers["RenderLayer"].freestyle_settings.linesets.new("LineSet")
                    lineset.linestyle = \
                    original_scene.render.layers["RenderLayer"].freestyle_settings.linesets["LineSet"].linestyle                
                    
                    if new_scene.world.name != "World":
                        new_scene.world = bpy.data.worlds["World"]
                        
                    new_scene.world.horizon_color = (1.0, 1.0, 1.0)
                    new_scene.render.display_mode = 'NONE'
                    new_scene.render.use_lock_interface = True
         
        bpy.ops.fd_scene.prepare_plan_view()
        bpy.context.screen.scene = original_scene
        
        return {'FINISHED'}
    
class OPS_clear_2d_views(Operator):   
    bl_idname = "fd_scene.clear_2d_views"    
    bl_label = "Delete 2d View Scenes"
    bl_description = "Delete all 2d view scenes"
    bl_options = {'UNDO'}     
    
    def execute(self, context):
        for scene in bpy.data.scenes:
            if scene.mv.elevation_scene or scene.mv.plan_view_scene:
                context.screen.scene = scene
                bpy.ops.scene.delete()                         
                
        for view in context.window_manager.mv.image_views:
            context.window_manager.mv.image_views.remove(0)
                
        return {'FINISHED'}
    
class OPS_genereate_views(Operator):
    bl_idname = "fd_scene.genereate_2d_views"    
    bl_label = "Generate 2d View Scenes"
    bl_description = "Prepare 2D View Scenes"
    bl_options = {'UNDO'}

    ev_pad = FloatProperty(name="Elevation View Padding",
                           default=0.75)
    
    pv_pad = FloatProperty(name="Plan View Padding",
                           default=0.75)
    
    main_scene = None
    
    def create_camera(self,scene):
        camera_data = bpy.data.cameras.new(scene.name)
        camera_obj = bpy.data.objects.new(name=scene.name,object_data=camera_data)
        scene.objects.link(camera_obj)
        scene.camera = camera_obj                        
        camera_obj.data.type = 'ORTHO'
        scene.render.resolution_y = 1280
        
        scene.mv.ui.render_type_tabs = 'NPR'
        lineset = scene.render.layers["RenderLayer"].freestyle_settings.linesets.new("LineSet")
        lineset.linestyle = \
        self.main_scene.render.layers["RenderLayer"].freestyle_settings.linesets["LineSet"].linestyle 
        
        scene.world = bpy.data.worlds[0]
        scene.world.horizon_color = (1.0, 1.0, 1.0)
        scene.render.display_mode = 'NONE'
        scene.render.use_lock_interface = True        
        
        scene.mv.ui.render_type_tabs = 'NPR'
        lineset = scene.render.layers["RenderLayer"].freestyle_settings.linesets.new("LineSet")
        lineset.linestyle = \
        self.main_scene.render.layers["RenderLayer"].freestyle_settings.linesets["LineSet"].linestyle                
        
        scene.world.horizon_color = (1.0, 1.0, 1.0)
        scene.render.display_mode = 'NONE'
        scene.render.use_lock_interface = True        
        
        return camera_obj
    
    def link_dims_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if child.mv.type in ('VISDIM_A','VISDIM_B'):
                scene.objects.link(child)
            if len(child.children) > 0:
                self.link_dims_to_scene(scene, child)     
    
    def group_children(self,grp,obj):
        grp.objects.link(obj)   
        for child in obj.children:
            if len(child.children) > 0:
                self.group_children(grp,child)
            else:
                if not child.mv.is_wall_mesh:
                    grp.objects.link(child)  
        return grp
    
    def create_plan_view_scene(self,context):
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')   
        pv_scene = context.scene     
        pv_scene.name = "Plan View"
        pv_scene.mv.name_scene = "Plan View" 
        pv_scene.mv.plan_view_scene = True 
    
        for obj in self.main_scene.objects:
            if obj.mv.type == 'BPWALL':
                pv_scene.objects.link(obj)
                #Only link all of the wall meshes
                for child in obj.children:
                    if child.mv.is_wall_mesh:
                        child.select = True
                        pv_scene.objects.link(child)
                wall = fd_types.Wall(obj_bp = obj)
                obj_bps = wall.get_wall_groups()
                #Create Cubes for all products
                for obj_bp in obj_bps:
                    assembly = fd_types.Assembly(obj_bp)
                    assembly_mesh = utils.create_cube_mesh(assembly.obj_bp.mv.name_object,
                                                        (assembly.obj_x.location.x,
                                                         assembly.obj_y.location.y,
                                                         assembly.obj_z.location.z))
                    assembly_mesh.parent = wall.obj_bp
                    assembly_mesh.location = assembly.obj_bp.location
                    assembly_mesh.rotation_euler = assembly.obj_bp.rotation_euler
                wall.get_wall_mesh().select = True
                
        camera = self.create_camera(pv_scene)
        camera.rotation_euler.z = math.radians(-90.0)
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.ortho_scale += self.pv_pad
    
    def create_elv_view_scene(self,context,wall):
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')
        new_scene = context.scene
        new_scene.name = wall.obj_bp.name
        new_scene.mv.name_scene = wall.obj_bp.mv.name_object + " " + str(wall.obj_bp.mv.item_number)
        new_scene.mv.elevation_img_name = wall.obj_bp.name
        new_scene.mv.plan_view_scene = False
        new_scene.mv.elevation_scene = True
        
        wall_group = bpy.data.groups.new(wall.obj_bp.name)
        self.group_children(wall_group,wall.obj_bp)                    
        wall_mesh = utils.create_cube_mesh(wall.obj_bp.mv.name_object,(wall.obj_x.location.x,wall.obj_y.location.y,wall.obj_z.location.z))
        wall_mesh.parent = wall.obj_bp
        wall_group.objects.link(wall_mesh)  
        
        instance = bpy.data.objects.new(wall.obj_bp.mv.name_object + " "  + "Instance" , None)
        new_scene.objects.link(instance)
        instance.dupli_type = 'GROUP'
        instance.dupli_group = wall_group
        
        new_scene.world = self.main_scene.world
        
        self.link_dims_to_scene(new_scene, wall.obj_bp)
        
        camera = self.create_camera(new_scene)
        camera.rotation_euler.x = math.radians(90.0)
        camera.rotation_euler.z = wall.obj_bp.rotation_euler.z   
        bpy.ops.object.select_all(action='DESELECT')
        wall_mesh.select = True
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.ortho_scale += self.pv_pad
        
    def execute(self, context):
        context.window_manager.mv.use_opengl_dimensions = True

        bpy.ops.fd_scene.clear_2d_views()
        
        self.main_scene = context.scene
        
        self.create_plan_view_scene(context)
        
        for obj in self.main_scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj_bp = obj)
                if len(wall.get_wall_groups()) > 0:
                    self.create_elv_view_scene(context, wall)
                    
        bpy.context.screen.scene = self.main_scene
  
        return {'FINISHED'}
    
class OPS_prepare_2d_views(Operator):   
    bl_idname = "fd_scene.prepare_2d_views"    
    bl_label = "Prepare 2d View Scenes"
    bl_description = "Prepare 2D View Scenes"
    bl_options = {'UNDO'}          

    ev_pad = FloatProperty(name="Elevation View Padding",
                           default=0.75)
    
    pv_pad = FloatProperty(name="Plan View Padding",
                           default=0.75)
            
    def link_grp_instance_to_scene(self, group, scene, obj_bp):  
        instance = bpy.data.objects.new(obj_bp.mv.name_object + " "  + "Instance" , None)
        scene.objects.link(instance)
        instance.dupli_type = 'GROUP'
        instance.dupli_group = group
        
    def set_cameras(self, new_scene, wall, wall_mesh):  
        """ Create camera in new scene, sets cameras properties and sets the 
            entire wall to be visible by camera.
        """
        
        #Create Camera
        camera_data = bpy.data.cameras.new(new_scene.name)
        camera_obj = bpy.data.objects.new(name=camera_data.name + " Camera", 
                                          object_data=camera_data)

        #Set Scene
        bpy.context.screen.scene = new_scene
        
        #Link Camera to Scene This might not
        new_scene.objects.link(camera_obj)
        new_scene.camera = camera_obj
        new_scene.render.resolution_y = 1280
        
        #Set Properties on camera
        camera_obj.data.type = 'ORTHO'
        camera_obj.rotation_euler.x = math.radians(90.0) 
        camera_obj.rotation_euler.z = wall.obj_bp.rotation_euler.z    
        camera_obj.location = wall.obj_bp.location 
        camera_obj.location.x = unit.inch(12)
        camera_obj.data.ortho_scale += self.ev_pad
        
        #Set Camera to View entire scene
        bpy.ops.object.select_all(action='DESELECT')
        wall_mesh.select = True
        bpy.ops.view3d.camera_to_view_selected()
        
        #Lock Camera to View
        bpy.context.space_data.lock_camera = True
        
    def link_vis_dim_empties_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if child.mv.type in ('VISDIM_A','VISDIM_B'):
                scene.objects.link(child)
            if len(child.children) > 0:
                self.link_vis_dim_empties_to_scene(scene, child) 
                      
    def clear_old_scenes(self):
        """ If you run the command twice we need to remove all
            of the old scenes so we dont create duplicates.
        """ 
        pass

    def group_children(self,grp,obj):
        grp.objects.link(obj)   
        for child in obj.children:
            if len(child.children) > 0:
                self.group_children(grp,child)
            else:
                
                if not child.mv.is_wall_mesh:
                    grp.objects.link(child)   
        return grp                      
                      
    def execute(self, context):
        context.window_manager.mv.use_opengl_dimensions = True

        bpy.ops.fd_scene.clear_2d_views()
        
        main_scene = context.scene
        
        #Existing scenes are stored in a dictionary because we want to know
        #if the user had the scene selected so we can reset the checked scenes
        #after they are rebuilt.
#         existing_scenes = {}
#         for scene in bpy.data.scenes:
#             if scene.mv.elevation_scene or scene.mv.plan_view_scene:
#                 existing_scenes[scene.name] = scene.mv.elevation_selected
#                 context.screen.scene = scene
#                 bpy.ops.scene.delete()
#             else:
#                 original_scene = bpy.data.scenes[context.scene.name]
#         context.screen.scene = original_scene        
             
        #Create a plan view scene
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')   
        pv_scene = context.scene     
        pv_scene.name = "Plan View"
        pv_scene.mv.name_scene = "Plan View" 
        pv_scene.mv.plan_view_scene = True 
            
#         if pv_scene.name in existing_scenes:
#             pv_scene.mv.elevation_selected = existing_scenes[pv_scene.name]            
            
        #Only link all of the walls and their base points.
        for obj in main_scene.objects:
            if obj.mv.type == 'BPWALL':
                pv_scene.objects.link(obj)
                for child in obj.children:
                    if child.mv.is_wall_mesh:
                        pv_scene.objects.link(child)

        #Create a cube for all products
        for obj in pv_scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj_bp = obj)
                obj_bps = wall.get_wall_groups()
                for obj_bp in obj_bps:
                    assembly = fd_types.Assembly(obj_bp)
                    assembly_mesh = utils.create_cube_mesh(assembly.obj_bp.mv.name_object,
                                                        (assembly.obj_x.location.x,
                                                         assembly.obj_y.location.y,
                                                         assembly.obj_z.location.z))
                    assembly_mesh.parent = wall.obj_bp
                    assembly_mesh.location = assembly.obj_bp.location
                    assembly_mesh.rotation_euler = assembly.obj_bp.rotation_euler
                wall.get_wall_mesh().select = True
                
        cam_name = "Plan View Camera"
        camera_data = bpy.data.cameras.new(cam_name)
        camera_obj = bpy.data.objects.new(name=cam_name,object_data=camera_data)
        pv_scene.objects.link(camera_obj)
        pv_scene.camera = camera_obj                        
        camera_obj.rotation_euler.z = math.radians(-90.0)    
        camera_obj.data.type = 'ORTHO'
        pv_scene.render.resolution_y = 1280
        bpy.ops.view3d.camera_to_view_selected()    
        camera_obj.data.ortho_scale += self.pv_pad                
        
        pv_scene.mv.ui.render_type_tabs = 'NPR'
        lineset = pv_scene.render.layers["RenderLayer"].freestyle_settings.linesets.new("LineSet")
        lineset.linestyle = \
        main_scene.render.layers["RenderLayer"].freestyle_settings.linesets["LineSet"].linestyle 
        
        pv_scene.world = bpy.data.worlds["World"]
        pv_scene.world.horizon_color = (1.0, 1.0, 1.0)
        pv_scene.render.display_mode = 'NONE'
        pv_scene.render.use_lock_interface = True
        
        # Create a scene for every wall
        for obj in main_scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj_bp = obj)
                if len(wall.get_wall_groups()) > 0:
                    bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')
                    new_scene = context.scene
                    new_scene.name = obj.name
                    new_scene.mv.name_scene = obj.mv.name_object + " " + str(obj.mv.item_number)
                    new_scene.mv.elevation_img_name = obj.name
                    new_scene.mv.plan_view_scene = False
                    new_scene.mv.elevation_scene = True
                    
                    wall_group = bpy.data.groups.new(wall.obj_bp.name)
                    self.group_children(wall_group,wall.obj_bp)                    
                    wall_mesh = utils.create_cube_mesh(wall.obj_bp.mv.name_object,(wall.obj_x.location.x,wall.obj_y.location.y,wall.obj_z.location.z))
                    wall_mesh.parent = wall.obj_bp
                    wall_group.objects.link(wall_mesh)  
                    
                    #when creating a new scene first elevation scene.mv.plan_view_scene == True
                    #Should be False by default
                    #This could be from using bpy.ops to create a new scene instead of creating new from data.scenes collection
                    
                    
                    
                    new_scene.world = main_scene.world
                    
#                     if new_scene.name in existing_scenes:
#                         new_scene.mv.elevation_selected = existing_scenes[new_scene.name]
                    
                    self.link_vis_dim_empties_to_scene(new_scene, obj)
        
                    bpy.context.screen.scene = main_scene
                          
                    self.link_grp_instance_to_scene(wall_group, new_scene, obj)   
                    
                    self.set_cameras(new_scene, wall, wall_mesh)
                    
                    new_scene.mv.ui.render_type_tabs = 'NPR'
                    lineset = new_scene.render.layers["RenderLayer"].freestyle_settings.linesets.new("LineSet")
                    lineset.linestyle = \
                    main_scene.render.layers["RenderLayer"].freestyle_settings.linesets["LineSet"].linestyle                
                    
                    new_scene.world.horizon_color = (1.0, 1.0, 1.0)
                    new_scene.render.display_mode = 'NONE'
                    new_scene.render.use_lock_interface = True

        bpy.context.screen.scene = main_scene

        return {'FINISHED'}
       
class OPS_prepare_2d_views_OLD(Operator):   
    bl_idname = "fd_scene.prepare_2d_views_old"    
    bl_label = "Prepare 2d View Scenes"
    bl_description = "Prepare 2D View Scenes"
    bl_options = {'UNDO'}          

    ev_pad = FloatProperty(name="Elevation View Padding",
                           default=0.75)
    
    pv_pad = FloatProperty(name="Plan View Padding",
                           default=0.75)
            
    def link_grp_instance_to_scene(self, group, scene, obj_bp):  
        instance = bpy.data.objects.new(obj_bp.mv.name_object + " "  + "Instance" , None)
        scene.objects.link(instance)
        instance.dupli_type = 'GROUP'
        instance.dupli_group = group        
        
    def set_cameras(self, current_scene, new_scene, wall):  
        """ Create camera in new scene, sets camear properties and sets the 
            entire wall to be visible by camera.
        """
        camera_data = bpy.data.cameras.new(new_scene.name)
        camera_obj = bpy.data.objects.new(name=camera_data.name + " Camera", 
                                          object_data=camera_data)
         
        current_scene.objects.link(camera_obj)    
        current_scene.camera = camera_obj
        camera_obj.data.type = 'ORTHO'
        camera_obj.rotation_euler.x = math.radians(90.0) 
        camera_obj.rotation_euler.z = wall.obj_bp.rotation_euler.z    
        camera_obj.location = wall.obj_bp.location

        bpy.ops.object.select_all(action='DESELECT')
        wall.get_wall_mesh().select = True
        bpy.ops.view3d.camera_to_view_selected()
        
        current_scene.camera = None
        current_scene.objects.unlink(camera_obj)
        new_scene.objects.link(camera_obj)
        new_scene.camera = camera_obj
        new_scene.render.resolution_y = 1280
        bpy.data.cameras[new_scene.name].ortho_scale += self.ev_pad
        
        bpy.context.space_data.lock_camera = True
        
    def link_vis_dim_empties_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if child.mv.type in ('VISDIM_A','VISDIM_B'):
                scene.objects.link(child)
            if len(child.children) > 0:
                self.link_vis_dim_empties_to_scene(scene, child) 
                      
    def execute(self, context):
        context.window_manager.mv.use_opengl_dimensions = True
        
        existing_scenes = {}
        for scene in bpy.data.scenes:
            if scene.mv.elevation_scene or scene.mv.plan_view_scene:
                existing_scenes[scene.name] = scene.mv.elevation_selected
                context.screen.scene = scene
                bpy.ops.scene.delete()
            else:
                original_scene = bpy.data.scenes[context.scene.name]
        context.screen.scene = original_scene        
            
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')   
        pv_scene = context.scene     
        pv_scene.name = "Plan View"
        pv_scene.mv.name_scene = "Plan View" 
        pv_scene.mv.plan_view_scene = True 
            
        if pv_scene.name in existing_scenes:
            pv_scene.mv.elevation_selected = existing_scenes[pv_scene.name]            
            
        for obj in original_scene.objects:
            pv_scene.objects.link(obj)    
            
        for obj in pv_scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj_bp = obj)
                wall.get_wall_mesh().select = True
                
        cam_name = "Plan View Camera"
        camera_data = bpy.data.cameras.new(cam_name)
        camera_obj = bpy.data.objects.new(name=cam_name,object_data=camera_data)
        pv_scene.objects.link(camera_obj)
        pv_scene.camera = camera_obj                        
        camera_obj.rotation_euler.z = math.radians(-90.0)    
        camera_obj.data.type = 'ORTHO'
        pv_scene.render.resolution_y = 1280
        bpy.ops.view3d.camera_to_view_selected()    
        camera_obj.data.ortho_scale += self.pv_pad                
        
        pv_scene.mv.ui.render_type_tabs = 'NPR'
        lineset = pv_scene.render.layers["RenderLayer"].freestyle_settings.linesets.new("LineSet")
        lineset.linestyle = \
        original_scene.render.layers["RenderLayer"].freestyle_settings.linesets["LineSet"].linestyle 
        
        pv_scene.world = bpy.data.worlds["World"]
        pv_scene.world.horizon_color = (1.0, 1.0, 1.0)
        pv_scene.render.display_mode = 'NONE'
        pv_scene.render.use_lock_interface = True        

        for obj in context.scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj_bp = obj)
                if len(wall.get_wall_groups()) > 0:
                    
                    wall_group = wall.create_wall_group()
                       
                    bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')
                    new_scene = context.scene
                    new_scene.name = obj.name   
                    new_scene.mv.name_scene = obj.mv.name_object + " " + str(obj.mv.item_number)
                    new_scene.mv.elevation_img_name = obj.name
                    
                    #when creating a new scene first elevation scene.mv.plan_view_scene == True
                    #Should be False by default
                    #This could be from using bpy.ops to create a new scene instead of creating new from data.scenes collection
                    new_scene.mv.plan_view_scene = False
                    
                    new_scene.mv.elevation_scene = True
                    new_scene.world = original_scene.world                      
                      
                    if new_scene.name in existing_scenes:
                        new_scene.mv.elevation_selected = existing_scenes[new_scene.name]
                    
                    self.link_vis_dim_empties_to_scene(new_scene, obj)
        
                    bpy.context.screen.scene = original_scene
                          
                    self.link_grp_instance_to_scene(wall_group, new_scene, obj)   
                           
                    self.set_cameras(original_scene, new_scene, wall)
                  
                    new_scene.mv.ui.render_type_tabs = 'NPR'
                    lineset = new_scene.render.layers["RenderLayer"].freestyle_settings.linesets.new("LineSet")
                    lineset.linestyle = \
                    original_scene.render.layers["RenderLayer"].freestyle_settings.linesets["LineSet"].linestyle                
                              
                    new_scene.world.horizon_color = (1.0, 1.0, 1.0)
                    new_scene.render.display_mode = 'NONE'
                    new_scene.render.use_lock_interface = True

        bpy.context.screen.scene = original_scene

        return {'FINISHED'}       
       
class OPS_render_2d_views(Operator):
    bl_idname = "fd_scene.render_2d_views"
    bl_label = "Render 2D Views"
    bl_description = "Renders 2d Scenes"
    
    render_all = BoolProperty(name="Render all elevation scenes", default=False)
    
    def invoke(self, context, event):
        wm = context.window_manager
        if not bpy.data.is_saved:
            return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(400))     
        else:
            return self.execute(context)         
    
    def draw(self,context):
        layout = self.layout
        layout.label("File must be saved before rendering",icon='INFO')  
    
    def execute(self, context):
        active_filename = bpy.path.basename(context.blend_data.filepath).replace(".blend","")
        write_dir = bpy.path.abspath("//") + active_filename
        
        bpy.ops.fd_scene.prepare_2d_views()
        
        if not os.path.exists(write_dir):
            os.mkdir(write_dir)        
        else:
            for file in os.listdir(write_dir):
                os.unlink(write_dir + "\\" + file)        
        
        if self.render_all:
            bpy.ops.fd_general.select_all_elevation_scenes(select_all=True)
        
        for scene in bpy.data.scenes:
            if scene.mv.elevation_selected:
                
                scene.mv.opengl_dim.gl_default_color = (0.1, 0.1, 0.1, 1.0)
                
                if scene.mv.plan_view_scene:
                    img_name = active_filename + "_tmp"
                else:
                    img_name = scene.mv.elevation_img_name + "_tmp"
                
                context.screen.scene = scene
                context.scene.render.filepath = "//" + active_filename + "\\" + img_name
                bpy.ops.fd_scene.render_scene(write_still=True)
                 
        if not self.render_all:
            for scene in bpy.data.scenes:
                if not scene.mv.elevation_scene or not scene.mv.plan_view_scene:
                    context.screen.scene = scene
                    default_glcolor = scene.mv.opengl_dim.gl_default_color
                    
            for scene in bpy.data.scenes:
                scene.mv.opengl_dim.gl_default_color = default_glcolor
                
            file_format = context.screen.scene.render.file_extension        
            bpy.ops.fd_general.open_browser_window(path=bpy.path.abspath("//") +\
                                                   active_filename +\
                                                   "\\" +\
                                                   img_name.replace("_tmp","") +\
                                                   file_format)                
        
        return {'FINISHED'}
       
class OPS_render_all_elevation_scenes(Operator):
    bl_idname = "fd_scene.render_all_elevation_scenes"
    bl_label = "Render all elevation scenes"
    bl_description = "Renders all elevation scenes"
        
    render = True    
    render_all = BoolProperty(name="Render all elevation scenes", default=False)
    selected_scenes = []
        
    def execute(self, context):
        if not bpy.data.is_saved or not self.render:
            return {'FINISHED'}
    
        ren_path = "//"
        file_name = bpy.path.basename(context.blend_data.filepath).replace(".blend","")
        write_dir = bpy.path.abspath(ren_path) + file_name.replace(".blend","")
        original_scene = context.scene
        
        bpy.ops.fd_scene.prepare_2d_elevations()
        
        if not os.path.exists(write_dir):
            os.mkdir(write_dir)        
        else:
            for file in os.listdir(write_dir):
                os.unlink(write_dir + "\\" + file)
        
        if self.render_all == True:
            for scene in bpy.data.scenes:
                if scene.mv.elevation_scene:
                    if scene.mv.plan_view_scene:
                        img_name = file_name + "_tmp"
                    else:
                        img_name = scene.mv.elevation_img_name + "_tmp"
                        
                    context.screen.scene = scene
                    context.scene.render.filepath = "//" + file_name + "\\" + img_name
                    bpy.ops.fd_scene.render_scene(write_still=True)
        else:
            for scene in bpy.data.scenes:
                if (scene.mv.elevation_scene or scene.mv.plan_view_scene) and scene.mv.elevation_selected:
                    if scene.mv.plan_view_scene:
                        img_name = file_name
                    else:
                        img_name = scene.mv.elevation_img_name
                    
                    print(scene, img_name)    
                    context.screen.scene = scene
                    context.scene.render.filepath = "//" + file_name + "\\" + img_name
                    bpy.ops.fd_scene.render_scene(write_still=True)
                    
            context.screen.scene = original_scene
            file_format = context.screen.scene.render.file_extension
            bpy.ops.fd_general.open_browser_window(path=bpy.path.abspath("//") +\
                                                   file_name +\
                                                   "\\" +\
                                                   img_name +\
                                                   file_format)
                
        return{'FINISHED'}
        
#     def invoke(self,context,event):
#         wm = context.window_manager
#         
#         for scene in bpy.data.scenes:
#             if scene.mv.elevation_selected:
#                 self.selected_scenes.append(scene)
# 
#         if len(self.selected_scenes) < 1:
#             self.render = False
#         
#         if not bpy.data.is_saved:
#             return wm.invoke_props_dialog(self, width=utils.get_prop_dialog_width(400))  
#         else:
#             return self.execute(context)
#      
#     def draw(self,context):
#         layout = self.layout
#         layout.label("File must be saved before rendering",icon='INFO')           


class OPS_render_all_2D_views(Operator):
    bl_idname = "fd_scene.render_all_2d_views"
    bl_label = "Render All 2D Views"
    bl_description = "Renders all elevation scenes"
    
    def set_rendering_properties(self,context):
        rd = context.scene.render
        rl = rd.layers.active
        freestyle_settings = rl.freestyle_settings
        
        rd.engine = 'BLENDER_RENDER'
        rd.use_freestyle = True
        rd.line_thickness = 0.75
        rd.resolution_percentage = 100
        rl.use_pass_combined = False
        rl.use_pass_z = False
        freestyle_settings.crease_angle = 2.617994
    
    def execute(self, context):

        #Create Temp Directory
        file_name = bpy.path.basename(context.blend_data.filepath).replace(".blend","")
        write_dir = os.path.join(bpy.app.tempdir, file_name)
        if not os.path.exists(write_dir): os.mkdir(write_dir)

        bpy.ops.fd_scene.prepare_2d_elevations()

        images = []
        
        #Render Each Scene
        for scene in bpy.data.scenes:
            if scene.mv.elevation_scene:
                context.screen.scene = scene

                rd = context.scene.render
                rl = rd.layers.active
                freestyle_settings = rl.freestyle_settings
                rd.filepath = os.path.join(write_dir,scene.name)
                rd.engine = 'BLENDER_RENDER'
                rd.use_freestyle = True
                rd.line_thickness = 0.75
                rd.resolution_percentage = 100
                rl.use_pass_combined = False
                rl.use_pass_z = False
                freestyle_settings.crease_angle = 2.617994
                
                # If file already found remove before rendering
                if os.path.exists(bpy.path.abspath(context.scene.render.filepath) + context.scene.render.file_extension):
                    os.remove(bpy.path.abspath(context.scene.render.filepath) + context.scene.render.file_extension)
                
                bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
                
                render_image = bpy.path.abspath(context.scene.render.filepath) + context.scene.render.file_extension
                
                while not os.path.exists(render_image):
                    time.sleep(0.1)
                
                img_result = utils.render_opengl(self,context)
                img_result.save_render(render_image)
                
                if os.path.exists(render_image):
                    images.append(render_image)
                    
        for image in images:
            print('Picture',image)
            
        bpy.ops.fd_scene.clear_2d_views()
            
        imgs_to_remove = []
            
        for img in bpy.data.images:
            if img.users == 0:
                imgs_to_remove.append(img)
            
        for im in imgs_to_remove:
            bpy.data.images.remove(im)
            
        bpy.ops.fd_general.open_browser_window(path=write_dir)
        
        return{'FINISHED'}

class OPS_export_mvfd(Operator):
    bl_idname = "cabinetlib.export_mvfd"
    bl_label = "Export MVFD File"
    bl_description = "This will export a mvfd file. The file must be saved first."
    
    walls = []
    products = []
    buyout_products = []
    
    buyout_materials = []
    solid_stock_materials = {}
    
    xml = None
    
    @classmethod
    def poll(cls, context):
        if bpy.data.filepath != "":
            return True
        else:
            return False

    def distance(self,distance):
        return str(math.fabs(round(unit.meter_to_active_unit(distance),4)))
    
    def location(self,location):
        return str(round(unit.meter_to_active_unit(location),4))
    
    def angle(self,angle):
        return str(round(math.degrees(angle),4))
    
    def clear_and_collect_data(self,context):
        for product in self.products:
            self.products.remove(product)
        
        for wall in self.walls:
            self.walls.remove(wall)

        bpy.ops.fd_material.get_materials()
        for scene in bpy.data.scenes:
            if not scene.mv.plan_view_scene and not scene.mv.elevation_scene:
                for obj in scene.objects:
                    if obj.mv.type == 'BPWALL':
                        self.walls.append(obj)
                    if obj.mv.type == 'BPASSEMBLY':
                        if obj.mv.type_group == 'PRODUCT':
                            self.products.append(obj)
                    if obj.cabinetlib.type_mesh == 'BUYOUT' and obj.parent is None:
                        self.buyout_products.append(obj)
    
    def write_properties(self,project_node):
        elm_properties = self.xml.add_element(project_node,'Properties')
        for scene in bpy.data.scenes:
            for prop in scene.mv.project_properties:
                elm_prop = self.xml.add_element(elm_properties,'Property',prop.name)
                self.xml.add_element_with_text(elm_prop,'Value',prop.value)
                self.xml.add_element_with_text(elm_prop,'GlobalVariableName',prop.global_variable_name)
                self.xml.add_element_with_text(elm_prop,'ProjectWizardVariableName',prop.project_wizard_variable_name)
                self.xml.add_element_with_text(elm_prop,'SpecificationGroupName',prop.specification_group_name)
    
    def write_locations(self,project_node):
        elm_locations = self.xml.add_element(project_node,'Locations')
        for scene in bpy.data.scenes:
            if not scene.mv.plan_view_scene and not scene.mv.elevation_scene:
                self.xml.add_element(elm_locations,'Location',scene.name)
    
    def write_walls(self,project_node):
        elm_walls = self.xml.add_element(project_node,"Walls")
        
        for obj_wall in self.walls:
            wall = fd_types.Wall(obj_wall)
            wall_name = wall.obj_bp.mv.name_object if wall.obj_bp.mv.name_object != "" else wall.name
            elm_wall = self.xml.add_element(elm_walls,'Wall',wall.obj_bp.mv.name_object)
            self.xml.add_element_with_text(elm_wall,'LinkID',obj_wall.name)
            self.xml.add_element_with_text(elm_wall,'LinkIDLocation',obj_wall.users_scene[0].name)
            self.xml.add_element_with_text(elm_wall,'Width',self.distance(wall.obj_x.location.x))
            self.xml.add_element_with_text(elm_wall,'Height',self.distance(wall.obj_z.location.z))
            self.xml.add_element_with_text(elm_wall,'Depth',self.distance(wall.obj_y.location.y))
            self.xml.add_element_with_text(elm_wall,'XOrigin',self.location(obj_wall.matrix_world[0][3]))
            self.xml.add_element_with_text(elm_wall,'YOrigin',self.location(obj_wall.matrix_world[1][3]))
            self.xml.add_element_with_text(elm_wall,'ZOrigin',self.location(obj_wall.matrix_world[2][3]))
            self.xml.add_element_with_text(elm_wall,'Angle',self.angle(obj_wall.rotation_euler.z))

    def write_products(self,project_node):
        specgroups = bpy.context.scene.mv.spec_groups
        elm_products = self.xml.add_element(project_node,"Products")
        item_number = 1
        for obj_product in self.products:
            spec_group = specgroups[obj_product.cabinetlib.spec_group_index]
            product = fd_types.Assembly(obj_product)
            product_name = product.obj_bp.mv.name_object if product.obj_bp.mv.name_object != "" else product.obj_bp.name
            elm_product = self.xml.add_element(elm_products,'Product',product_name)
            self.xml.add_element_with_text(elm_product,'LinkID',obj_product.name)
            if obj_product.parent:
                self.xml.add_element_with_text(elm_product,'LinkIDWall',obj_product.parent.name)
            else:
                self.xml.add_element_with_text(elm_product,'LinkIDWall','None')
                
            self.xml.add_element_with_text(elm_product,'IsBuyout','False')
            self.xml.add_element_with_text(elm_product,'IsCorner','False')
            self.xml.add_element_with_text(elm_product,'LinkIDLocation',obj_product.users_scene[0].name)
            self.xml.add_element_with_text(elm_product,'LinkIDSpecificationGroup',spec_group.name)
            if obj_product.mv.item_number == 0:
                self.xml.add_element_with_text(elm_product,'ItemNumber',str(item_number))
                item_number += 1
            else:
                self.xml.add_element_with_text(elm_product,'ItemNumber',str(obj_product.mv.item_number))
            self.xml.add_element_with_text(elm_product,'LinkIDLibrary',obj_product.mv.library_name)
            self.xml.add_element_with_text(elm_product,'Width',self.distance(product.obj_x.location.x))
            self.xml.add_element_with_text(elm_product,'Height',self.distance(product.obj_z.location.z))
            self.xml.add_element_with_text(elm_product,'Depth',self.distance(product.obj_y.location.y))
            self.xml.add_element_with_text(elm_product,'XOrigin',self.location(obj_product.matrix_world[0][3]))
            self.xml.add_element_with_text(elm_product,'YOrigin',self.location(obj_product.matrix_world[1][3]))
            self.xml.add_element_with_text(elm_product,'ZOrigin',self.location(obj_product.location.z))
            self.xml.add_element_with_text(elm_product,'Comment',obj_product.mv.comment)
            if obj_product.parent:
                angle = obj_product.parent.rotation_euler.z + obj_product.rotation_euler.z
                self.xml.add_element_with_text(elm_product,'Angle',self.angle(angle))
            else:
                self.xml.add_element_with_text(elm_product,'Angle',self.angle(obj_product.rotation_euler.z))

            #PROMPTS
            elm_prompts = self.xml.add_element(elm_product,"Prompts")
            prompts_dict = get_export_prompts(obj_product)
            for prompt in prompts_dict:
                elm_prompt = self.xml.add_element(elm_prompts,'Prompt',prompt)
                prompt_value = prompts_dict[prompt]
                if prompt_value == 'True':
                    prompt_value = str(1)
                if prompt_value == 'False':
                    prompt_value = str(0)
                self.xml.add_element_with_text(elm_prompt,'Value',prompt_value)

            #HEIGHT ABOVE FLOOR
            if obj_product.location.z > 0:
                elm_prompt = self.xml.add_element(elm_prompts,'Prompt',"HeightAboveFloor")
                self.xml.add_element_with_text(elm_prompt,'Value',self.location(obj_product.location.z))
                
            elm_parts = self.xml.add_element(elm_product,"Parts")
            self.write_parts_for_product(elm_parts,obj_product,spec_group)
            
            elm_hardware = self.xml.add_element(elm_product,"Hardware")
            self.write_hardware_for_product(elm_hardware,obj_product)
            
#             elm_buyout = self.xml.add_element(elm_product,"Buyout")
#             self.write_buyout_for_product(elm_buyout,obj_product)                
            
            elm_subassemblies = self.xml.add_element(elm_product,"Subassemblies")
            self.write_subassemblies_for_product(elm_subassemblies,obj_product,spec_group)                 

        #This is needed so we can export buyout objects that aren't assigned to a product
        for obj in self.buyout_products:
            spec_group = specgroups[obj.cabinetlib.spec_group_index]
            buyout_product_name = obj.mv.name_object if obj.mv.name_object != "" else obj.name
            elm_product = self.xml.add_element(elm_products,'Product',buyout_product_name)
            self.xml.add_element_with_text(elm_product,'LinkID',obj.name)
            self.xml.add_element_with_text(elm_product,'LinkIDWall','None')
            self.xml.add_element_with_text(elm_product,'IsBuyout','True')
            self.xml.add_element_with_text(elm_product,'IsCorner','False')
            self.xml.add_element_with_text(elm_product,'LinkIDLocation',obj.users_scene[0].name)
            self.xml.add_element_with_text(elm_product,'LinkIDSpecificationGroup',spec_group.name)
            if obj.mv.item_number == 0:
                self.xml.add_element_with_text(elm_product,'ItemNumber',str(item_number))
                item_number += 1
            else:
                self.xml.add_element_with_text(elm_product,'ItemNumber',str(obj.mv.item_number))
            self.xml.add_element_with_text(elm_product,'LinkIDLibrary',obj.mv.library_name)
            self.xml.add_element_with_text(elm_product,'Width',self.distance(obj.dimensions.x))
            self.xml.add_element_with_text(elm_product,'Height',self.distance(obj.dimensions.z))
            self.xml.add_element_with_text(elm_product,'Depth',self.distance(obj.dimensions.y))
            self.xml.add_element_with_text(elm_product,'XOrigin',self.location(obj.matrix_world[0][3]))
            self.xml.add_element_with_text(elm_product,'YOrigin',self.location(obj.matrix_world[1][3]))
            self.xml.add_element_with_text(elm_product,'ZOrigin',self.location(obj.location.z))
            self.xml.add_element_with_text(elm_product,'Comment',obj.mv.comment)
            self.xml.add_element_with_text(elm_product,'Angle',self.angle(obj.rotation_euler.z))
            
            elm_parts = self.xml.add_element(elm_product,"Parts")
            elm_part = self.xml.add_element(elm_parts,'Part',buyout_product_name)
            self.xml.add_element_with_text(elm_part,'PartType',"4")

            if buyout_product_name not in self.buyout_materials:
                self.buyout_materials.append(obj.mv.name_object)

            self.xml.add_element_with_text(elm_part,'LinkID',obj.name)
            self.xml.add_element_with_text(elm_part,'Qty',"1")
            self.xml.add_element_with_text(elm_part,'MaterialName',utils.get_material_name(obj))
            self.xml.add_element_with_text(elm_part,'Thickness',str(unit.meter_to_active_unit(obj.dimensions.z)))
            self.xml.add_element_with_text(elm_part,'UseSMA','True' if obj.mv.use_sma else 'False')
            self.xml.add_element_with_text(elm_part,'LinkIDProduct',obj.name)
            self.xml.add_element_with_text(elm_part,'LinkIDParent',"None")
            self.xml.add_element_with_text(elm_part,'PartLength',str(unit.meter_to_active_unit(obj.dimensions.x)))
            self.xml.add_element_with_text(elm_part,'PartWidth',str(unit.meter_to_active_unit(obj.dimensions.y)))
            self.xml.add_element_with_text(elm_part,'Comment',obj.mv.comment)
            self.xml.add_element_with_text(elm_part,'XOrigin',self.get_part_x_location(obj,obj.location.x))
            self.xml.add_element_with_text(elm_part,'YOrigin',self.get_part_y_location(obj,obj.location.y))
            self.xml.add_element_with_text(elm_part,'ZOrigin',self.get_part_z_location(obj,obj.location.z))
            self.xml.add_element_with_text(elm_part,'XRotation',self.angle(obj.rotation_euler.x))
            self.xml.add_element_with_text(elm_part,'YRotation',self.angle(obj.rotation_euler.y))
            self.xml.add_element_with_text(elm_part,'ZRotation',self.angle(obj.rotation_euler.z))
            self.xml.add_element_with_text(elm_part,'EdgeWidth1',utils.get_edgebanding_name_from_pointer_name(obj.mv.edge_w1,spec_group))
            self.xml.add_element_with_text(elm_part,'EdgeLength1',utils.get_edgebanding_name_from_pointer_name(obj.mv.edge_l1,spec_group))
            self.xml.add_element_with_text(elm_part,'EdgeWidth2',utils.get_edgebanding_name_from_pointer_name(obj.mv.edge_w2,spec_group))
            self.xml.add_element_with_text(elm_part,'EdgeLength2',utils.get_edgebanding_name_from_pointer_name(obj.mv.edge_l2,spec_group))
            self.xml.add_element_with_text(elm_part,'DrawToken3D',"DRAW3DBOX CABINET")
            self.xml.add_element_with_text(elm_part,'ElvToken2D',"DRAW2DBOX CABINET")
            self.xml.add_element_with_text(elm_part,'BasePoint',"1")
            self.xml.add_element_with_text(elm_part,'MachinePoint',"1")
            self.xml.add_element_with_text(elm_part,'Par1',"")
            self.xml.add_element_with_text(elm_part,'Par2',"")
            self.xml.add_element_with_text(elm_part,'Par3',"")

            item_number += 1
            
    def write_materials(self,project_node):
        elm_materials = self.xml.add_element(project_node,"Materials")
        for material in bpy.context.scene.cabinetlib.sheets:
            material_name = material.name if material.name != "" else "Unnamed"
            elm_material = self.xml.add_element(elm_materials,'Material',material_name)
            self.xml.add_element_with_text(elm_material,'Type',"2")
            self.xml.add_element_with_text(elm_material,'Thickness',self.distance(material.thickness))
            self.xml.add_element_with_text(elm_material,'LinkIDCoreRendering',material.core_material)
            self.xml.add_element_with_text(elm_material,'LinkIDTopFaceRendering',material.top_material)
            self.xml.add_element_with_text(elm_material,'LinkIDBottomFaceRendering',material.bottom_material)
            elm_sheets = self.xml.add_element(elm_material,"Sheets")
            for sheet in material.sizes:
                elm_sheet = self.xml.add_element(elm_sheets,'Sheet',self.distance(sheet.width) + " X " + self.distance(sheet.length))
                self.xml.add_element_with_text(elm_sheet,'Width',self.distance(sheet.width))
                self.xml.add_element_with_text(elm_sheet,'Length',self.distance(sheet.length))
                self.xml.add_element_with_text(elm_sheet,'LeadingLengthTrim',self.distance(sheet.leading_length_trim))
                self.xml.add_element_with_text(elm_sheet,'TrailingLengthTrim',self.distance(sheet.trailing_length_trim))
                self.xml.add_element_with_text(elm_sheet,'LeadingWidthTrim',self.distance(sheet.leading_width_trim))
                self.xml.add_element_with_text(elm_sheet,'TrailingWidthTrim',self.distance(sheet.trailing_width_trim))

    def write_edgebanding(self,project_node):
        elm_edgebanding = self.xml.add_element(project_node,"Edgebanding")
        for edgeband in bpy.context.scene.cabinetlib.edgebanding:
            edgeband_name = edgeband.name if edgeband.name != "" else "Unnamed"
            elm_edge = self.xml.add_element(elm_edgebanding,'Edgeband',edgeband_name)
            self.xml.add_element_with_text(elm_edge,'Type',"3")
            self.xml.add_element_with_text(elm_edge,'Thickness',str(unit.meter_to_active_unit(edgeband.thickness)))

    def write_buyout_materials(self,project_node):
        elm_buyouts = self.xml.add_element(project_node,"Buyouts")
        for buyout in self.buyout_materials:
            buyout_name = buyout if buyout != "" else "Unnamed"
            self.xml.add_element(elm_buyouts,'Buyout',buyout_name)
    
    def write_solid_stock_material(self,project_node):
        elm_solid_stocks = self.xml.add_element(project_node,"SolidStocks")
        for solid_stock in self.solid_stock_materials:
            solid_stock_name = solid_stock if solid_stock != "" else "Unnamed"
            elm_solid_stock = self.xml.add_element(elm_solid_stocks,'SolidStock',solid_stock_name)
            self.xml.add_element_with_text(elm_solid_stock,'Thickness',str(unit.meter_to_active_unit(self.solid_stock_materials[solid_stock])))
        
    def write_spec_groups(self,project_node):
        elm_spec_groups = self.xml.add_element(project_node,"SpecGroups")
        
        for spec_group in bpy.context.scene.mv.spec_groups:
            spec_group_name = spec_group.name if spec_group.name != "" else "Unnamed"
            elm_spec_group = self.xml.add_element(elm_spec_groups,'SpecGroup',spec_group_name)
            elm_cutparts = self.xml.add_element(elm_spec_group,'CutParts')
            for cutpart in spec_group.cutparts:
                elm_cutpart_name = cutpart.mv_pointer_name if cutpart.mv_pointer_name != "" else "Unnamed"
                elm_cutpart = self.xml.add_element(elm_cutparts,'PointerName',elm_cutpart_name)
                mat_name = utils.get_material_name_from_pointer(cutpart,spec_group)
                material_name = mat_name if mat_name != "" else "Unnamed"
                self.xml.add_element_with_text(elm_cutpart,'MaterialName',material_name)
                 
            elm_edgeparts = self.xml.add_element(elm_spec_group,'EdgeParts')
            for edgepart in spec_group.edgeparts:
                elm_edgepart_name = edgepart.mv_pointer_name if edgepart.mv_pointer_name != "" else "Unnamed"
                elm_edgepart = self.xml.add_element(elm_edgeparts,'PointerName',elm_edgepart_name)
                mat_name = utils.get_edgebanding_name_from_pointer_name(edgepart.name,spec_group)
                edge_material_name = mat_name if mat_name != "" else "Unnamed"
                self.xml.add_element_with_text(elm_edgepart,'MaterialName',edge_material_name)
                
    def write_subassemblies_for_product(self,elm_subassembly,obj_bp,spec_group):
        for child in obj_bp.children:
            
            if child.mv.is_cabinet_door:
                assembly = fd_types.Assembly(child)
                hide = assembly.get_prompt("Hide")
                if hide and not hide.value():
                    comment = ""
                    for achild in assembly.obj_bp.children:
                        if achild.mv.comment != "":
                            comment = achild.mv.comment
                            break
                    sub_name = assembly.obj_bp.mv.name_object if assembly.obj_bp.mv.name_object != "" else assembly.obj_bp.name
                    elm_item = self.xml.add_element(elm_subassembly,'Subassembly',sub_name)
                    self.xml.add_element_with_text(elm_item,'LinkID',assembly.obj_bp.name)
                    self.xml.add_element_with_text(elm_item,'XLocation',self.distance(assembly.obj_bp.location.x))
                    self.xml.add_element_with_text(elm_item,'YLocation',self.distance(assembly.obj_bp.location.y))
                    self.xml.add_element_with_text(elm_item,'ZLocation',self.distance(assembly.obj_bp.location.z))
                    self.xml.add_element_with_text(elm_item,'XDimension',self.distance(assembly.obj_x.location.x))
                    self.xml.add_element_with_text(elm_item,'YDimension',self.distance(assembly.obj_y.location.y))
                    self.xml.add_element_with_text(elm_item,'ZDimension',self.distance(assembly.obj_z.location.z))                
                    self.xml.add_element_with_text(elm_item,'Comment',comment)
                    elm_parts = self.xml.add_element(elm_item,"Parts")
                    self.write_parts_for_product(elm_parts,assembly.obj_bp,spec_group)
            
            if child.mv.is_cabinet_drawer_box:
                assembly = fd_types.Assembly(child)
                hide = assembly.get_prompt("Hide")
                if hide and not hide.value():
                    sub_name = assembly.obj_bp.mv.name_object if assembly.obj_bp.mv.name_object != "" else assembly.obj_bp.name
                    elm_item = self.xml.add_element(elm_subassembly,'Subassembly',sub_name)
                    self.xml.add_element_with_text(elm_item,'LinkID',assembly.obj_bp.name)
                    self.xml.add_element_with_text(elm_item,'XLocation',self.distance(assembly.obj_bp.location.x))
                    self.xml.add_element_with_text(elm_item,'YLocation',self.distance(assembly.obj_bp.location.y))
                    self.xml.add_element_with_text(elm_item,'ZLocation',self.distance(assembly.obj_bp.location.z))
                    self.xml.add_element_with_text(elm_item,'XDimension',self.distance(assembly.obj_x.location.x))
                    self.xml.add_element_with_text(elm_item,'YDimension',self.distance(assembly.obj_y.location.y))
                    self.xml.add_element_with_text(elm_item,'ZDimension',self.distance(assembly.obj_z.location.z))                
                    self.xml.add_element_with_text(elm_item,'Comment',assembly.obj_bp.mv.comment)
                    elm_parts = self.xml.add_element(elm_item,"Parts")
                    self.write_parts_for_product(elm_parts,assembly.obj_bp,spec_group)
                    
            self.write_subassemblies_for_product(elm_subassembly, child,spec_group)
            
    def write_hardware_for_product(self,elm_hardware,obj_bp):
        for child in obj_bp.children:
            if child.cabinetlib.type_mesh == 'HARDWARE':
                if not child.hide:

                    #TODO: Figure out how to locate hardware correctly
                    #product_bp = utils.get_bp(child,'PRODUCT')
                    #diff = product_bp.matrix_world - child.matrix_world
                    hardware_name = child.mv.name_object if child.mv.name_object != "" else child.name
                    elm_item = self.xml.add_element(elm_hardware,'Hardware',hardware_name)
                    self.xml.add_element_with_text(elm_item,'XDimension',self.distance(child.dimensions.x))
                    self.xml.add_element_with_text(elm_item,'YDimension',self.distance(child.dimensions.y))
                    self.xml.add_element_with_text(elm_item,'ZDimension',self.distance(child.dimensions.z))
                    self.xml.add_element_with_text(elm_item,'XOrigin',self.get_part_x_location(child,child.location.x))
                    self.xml.add_element_with_text(elm_item,'YOrigin',self.get_part_y_location(child,child.location.y))
                    self.xml.add_element_with_text(elm_item,'ZOrigin',self.get_part_z_location(child,child.location.z))                    
                    self.xml.add_element_with_text(elm_item,'Comment',child.mv.comment)
                    self.write_machine_tokens(elm_item,child)
            self.write_hardware_for_product(elm_hardware, child)

    def write_buyout_for_product(self,elm_buyout,obj_bp):
        for child in obj_bp.children:
            if child.cabinetlib.type_mesh == 'BUYOUT':
                if not child.hide:
                    buyout_name = child.mv.name_object if child.mv.name_object != "" else child.name
                    elm_item = self.xml.add_element(elm_buyout,'Buyout',buyout_name)
                    self.xml.add_element_with_text(elm_item,'Comment',child.mv.comment)
            self.write_buyout_for_product(elm_buyout, child)
            
    def write_parts_for_product(self,elm_parts,obj_bp,spec_group):
        for child in obj_bp.children:
            if child.cabinetlib.type_mesh in {'CUTPART','SOLIDSTOCK','BUYOUT'}:
                if not child.hide:
                    self.write_part_node(elm_parts, child, spec_group)
            self.write_parts_for_product(elm_parts, child, spec_group)
    
    def get_part_x_location(self,obj,value):
        if obj.parent is None or obj.parent.mv.type_group == 'PRODUCT':
            return self.location(value)
        value += obj.parent.location.x
        return self.get_part_x_location(obj.parent,value)

    def get_part_y_location(self,obj,value):
        if obj.parent is None or obj.parent.mv.type_group == 'PRODUCT':
            return self.location(value)
        value += obj.parent.location.y
        return self.get_part_y_location(obj.parent,value)

    def get_part_z_location(self,obj,value):
        if obj.parent is None or obj.parent.mv.type_group == 'PRODUCT':
            return self.location(value)
        value += obj.parent.location.z
        return self.get_part_z_location(obj.parent,value)

    def write_part_node(self,node,obj,spec_group):
        if obj.mv.type == 'BPASSEMBLY':
            assembly = fd_types.Assembly(obj)
        else:
            assembly = fd_types.Assembly(obj.parent)
        if assembly.obj_bp.mv.type_group != "PRODUCT":
            if obj.type == 'CURVE':
                curve_name = obj.mv.name_object if obj.mv.name_object != "" else obj.name
                elm_part = self.xml.add_element(node,'Part',curve_name)
            else:
                obj_name = assembly.obj_bp.mv.name_object if assembly.obj_bp.mv.name_object != "" else assembly.obj_bp.name
                elm_part = self.xml.add_element(node,'Part',obj_name)
            
            if obj.cabinetlib.type_mesh == 'CUTPART':
                self.xml.add_element_with_text(elm_part,'PartType',"2")
    
            if obj.cabinetlib.type_mesh == 'BUYOUT':
                self.xml.add_element_with_text(elm_part,'PartType',"4")
                if utils.get_material_name(obj) not in self.buyout_materials:
                    self.buyout_materials.append(utils.get_material_name(obj))
                    
            if obj.cabinetlib.type_mesh == 'SOLIDSTOCK':
                self.xml.add_element_with_text(elm_part,'PartType',"3")
                if utils.get_material_name(obj) not in self.solid_stock_materials:
                    self.solid_stock_materials[utils.get_material_name(obj)] = utils.get_part_thickness(obj)
                    
            self.xml.add_element_with_text(elm_part,'LinkID',assembly.obj_bp.name)
            self.xml.add_element_with_text(elm_part,'Qty',"1")
            self.xml.add_element_with_text(elm_part,'MaterialName',utils.get_material_name(obj))
            self.xml.add_element_with_text(elm_part,'Thickness',self.distance(utils.get_part_thickness(obj)))
            self.xml.add_element_with_text(elm_part,'UseSMA','True' if obj.mv.use_sma else 'False')
            self.xml.add_element_with_text(elm_part,'LinkIDProduct',utils.get_bp(obj,'PRODUCT').name)
            self.xml.add_element_with_text(elm_part,'LinkIDParent',assembly.obj_bp.parent.name)
            self.xml.add_element_with_text(elm_part,'PartLength',self.distance(assembly.obj_x.location.x))
            self.xml.add_element_with_text(elm_part,'PartWidth',self.distance(assembly.obj_y.location.y))
            self.xml.add_element_with_text(elm_part,'Comment',assembly.obj_bp.mv.comment)
            self.xml.add_element_with_text(elm_part,'XOrigin',self.get_part_x_location(assembly.obj_bp,assembly.obj_bp.location.x))
            self.xml.add_element_with_text(elm_part,'YOrigin',self.get_part_y_location(assembly.obj_bp,assembly.obj_bp.location.y))
            self.xml.add_element_with_text(elm_part,'ZOrigin',self.get_part_z_location(assembly.obj_bp,assembly.obj_bp.location.z))
            self.xml.add_element_with_text(elm_part,'XRotation',self.angle(assembly.obj_bp.rotation_euler.x))
            self.xml.add_element_with_text(elm_part,'YRotation',self.angle(assembly.obj_bp.rotation_euler.y))
            self.xml.add_element_with_text(elm_part,'ZRotation',self.angle(assembly.obj_bp.rotation_euler.z))
            self.xml.add_element_with_text(elm_part,'EdgeWidth1',utils.get_edgebanding_name_from_pointer_name(obj.mv.edge_w1,spec_group))
            self.xml.add_element_with_text(elm_part,'EdgeLength1',utils.get_edgebanding_name_from_pointer_name(obj.mv.edge_l1,spec_group))
            self.xml.add_element_with_text(elm_part,'EdgeWidth2',utils.get_edgebanding_name_from_pointer_name(obj.mv.edge_w2,spec_group))
            self.xml.add_element_with_text(elm_part,'EdgeLength2',utils.get_edgebanding_name_from_pointer_name(obj.mv.edge_l2,spec_group))
            self.xml.add_element_with_text(elm_part,'DrawToken3D',"DRAW3DBOX CABINET")
            self.xml.add_element_with_text(elm_part,'ElvToken2D',"DRAW2DBOX CABINET")
            self.xml.add_element_with_text(elm_part,'BasePoint',self.get_part_base_point(assembly))
            self.xml.add_element_with_text(elm_part,'MachinePoint',"1")
            self.xml.add_element_with_text(elm_part,'Par1',"")
            self.xml.add_element_with_text(elm_part,'Par2',"")
            self.xml.add_element_with_text(elm_part,'Par3',"")
            
            self.write_machine_tokens(elm_part, obj)
            if obj.mv.use_sma:
                global_matrix = axis_conversion(to_forward='Y',to_up='Z').to_4x4() * Matrix.Scale(1.0, 4)
                faces = faces_from_mesh(obj, global_matrix, True)
                self.write_geometry(elm_part, faces)

    def get_part_base_point(self,assembly):
        mx = False
        my = False
        mz = False
        
        if assembly.obj_x.location.x < 0:
            mx = True
        if assembly.obj_y.location.y < 0:
            my = True
        if assembly.obj_z.location.z < 0:
            mz = True
            
        if (mx == False) and (my == False) and (mz == False):
            return "1"
        if (mx == False) and (my == False) and (mz == True):
            return "2"        
        if (mx == False) and (my == True) and (mz == False):
            return "3"
        if (mx == False) and (my == True) and (mz == True):
            return "4"
        if (mx == True) and (my == True) and (mz == False):
            return "5"
        if (mx == True) and (my == True) and (mz == True):
            return "6"        
        if (mx == True) and (my == False) and (mz == False):
            return "7"
        if (mx == True) and (my == False) and (mz == True):
            return "8"   
             
        return "1"
        
    def write_geometry(self,elm_part,faces):
        elm_geo = self.xml.add_element(elm_part,"Geometry")
        for face in faces:
            elm_face = self.xml.add_element(elm_geo,'Face',"Face")
            nor = '%f,%f,%f' % normal(*face)[:]
            norm = nor.split(",")
            elm_normal = self.xml.add_element(elm_face,'Normal','Normal')
            self.xml.add_element_with_text(elm_normal,'X',str(norm[0]))
            self.xml.add_element_with_text(elm_normal,'Y',str(norm[1]))
            self.xml.add_element_with_text(elm_normal,'Z',str(norm[2]))
            for vert in face:
                elm_vertex = self.xml.add_element(elm_face,'Vertex',"Vertex")
                self.xml.add_element_with_text(elm_vertex,'X',str(unit.meter_to_active_unit(vert[0])))
                self.xml.add_element_with_text(elm_vertex,'Y',str(unit.meter_to_active_unit(vert[1])))
                self.xml.add_element_with_text(elm_vertex,'Z',str(unit.meter_to_active_unit(vert[2])))

    def write_machine_tokens(self,elm_part,obj_part):
        elm_tokens = self.xml.add_element(elm_part,"MachineTokens")
        for token in obj_part.mv.mp.machine_tokens:
            token_name = token.name if token.name != "" else "Unnamed"
            elm_token = self.xml.add_element(elm_tokens,'MachineToken',token_name)
            param_dict = token.create_parameter_dictionary()
            if token.type_token in {'CORNERNOTCH','CHAMFER'}:
                instructions = token.type_token + token.face + " " + token.edge
            elif token.type_token == 'SLIDE':
                instructions = token.type_token
            else:
                instructions = token.type_token + token.face
            self.xml.add_element_with_text(elm_token,'Instruction',instructions)
            self.xml.add_element_with_text(elm_token,'Par1',param_dict['Par1'])
            self.xml.add_element_with_text(elm_token,'Par2',param_dict['Par2'])
            self.xml.add_element_with_text(elm_token,'Par3',param_dict['Par3'])
            self.xml.add_element_with_text(elm_token,'Par4',param_dict['Par4'])
            self.xml.add_element_with_text(elm_token,'Par5',param_dict['Par5'])
            self.xml.add_element_with_text(elm_token,'Par6',param_dict['Par6'])
            self.xml.add_element_with_text(elm_token,'Par7',param_dict['Par7'])
            self.xml.add_element_with_text(elm_token,'Par8',param_dict['Par8'])
            self.xml.add_element_with_text(elm_token,'Par9',param_dict['Par9'])
 
    def execute(self, context):
        project_name, ext = os.path.splitext(os.path.basename(bpy.data.filepath))
        
        self.clear_and_collect_data(context)
        
        # CREATE XML
        self.xml = fd_types.MV_XML()
        root = self.xml.create_tree()
        
        elm_project = self.xml.add_element(root,'Project',project_name)
        self.write_properties(elm_project)
        self.write_locations(elm_project)
        self.write_walls(elm_project)
        self.write_products(elm_project)
        self.write_materials(elm_project)
        self.write_edgebanding(elm_project)
        self.write_buyout_materials(elm_project)
        self.write_solid_stock_material(elm_project)
#         self.write_spec_groups(elm_project)
        
        # WRITE FILE
        path = os.path.join(os.path.dirname(bpy.data.filepath),"MV.xml")
        self.xml.write(path)
        return {'FINISHED'}

#------REGISTER

classes = [
           OPS_render_scene,
           OPS_render_settings,
           OPS_add_thumbnail_camera_and_lighting,
           OPS_create_unity_build,
           OPS_prepare_For_sketchfab,
           OPS_join_meshes_by_material,
           OPS_Prepare_Plan_view,
           OPS_Prepare_2d_elevations,
           OPS_clear_2d_views,
           OPS_genereate_views,
           OPS_prepare_2d_views,
           OPS_render_2d_views,
           OPS_render_all_2D_views,
           OPS_render_all_elevation_scenes,
           OPS_export_mvfd
           ]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
