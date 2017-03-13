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

bl_info = {
    "name": "Scene Optimization",
    "author": "Ryan Montes",
    "version": (1, 0, 0),
    "blender": (2, 7, 0),
    "location": "Tools Shelf",
    "description": "This add-on cleans up information in the scene to help with exporting and faster rendering.",
    "warning": "",
    "wiki_url": "",
    "category": "Fluid Designer"
}

import bpy
from mv import utils

class PANEL_Scene_Optimization(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Scene Optimization"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Fluid Designer"
    
    @classmethod
    def poll(cls, context):
        return True
    
    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='SCENE_DATA')
    
    def draw(self, context):
        layout = self.layout
        layout.operator('fd_scene_optimization.clear_all_materials_from_file',icon='MATERIAL')
        layout.operator('fd_scene_optimization.clear_all_drivers',icon='ANIM_DATA')

class OPERATOR_Clear_All_Materials_From_File(bpy.types.Operator):
    bl_idname = "fd_scene_optimization.clear_all_materials_from_file"
    bl_label = "Clear All Materials From File"
    bl_options = {'UNDO'}
    
    def execute(self,context):
        for obj in bpy.data.objects:
            for slot in obj.material_slots:
                slot.material = None
        
        for mat in bpy.data.materials:
            mat.user_clear()
            bpy.data.materials.remove(mat)
            
        for image in bpy.data.images:
            image.user_clear()
            bpy.data.images.remove(image)
        return{'FINISHED'}

class OPERATOR_Clear_All_Drivers(bpy.types.Operator):
    bl_idname = "fd_scene_optimization.clear_all_drivers"
    bl_label = "Clear All Python Drivers"
    bl_options = {'UNDO'}
    
    def execute(self,context):
        
#         delete_objs = []
        
        for obj in context.scene.objects:
            if not obj.hide and obj.layers[0]:
                if obj.animation_data:
                    for driver in obj.animation_data.drivers:
                        obj.driver_remove(driver.data_path)
                obj.select = True
                context.scene.objects.active = obj
    
                if obj.type == 'MESH':
                    if obj.data.shape_keys:
                        bpy.ops.fd_object.apply_shape_keys(object_name=obj.name)
                        
                if obj.type == 'CURVE':
                    bpy.ops.object.convert(target='MESH')
                    
                for mod in obj.modifiers:
                    bpy.ops.object.modifier_apply(apply_as='DATA',modifier=mod.name)
    
                obj.lock_location = (False,False,False)
                obj.lock_scale = (False,False,False)
                obj.lock_rotation = (False,False,False)
            
#             if obj.mv.type in {'CAGE','VPDIMX','VPDIMY','VPDIMZ'}:
#                 delete_objs.append(obj)
# 
#                 
#         utils.delete_obj_list(delete_objs)

        return{'FINISHED'}

def register():
    bpy.utils.register_class(PANEL_Scene_Optimization)
    bpy.utils.register_class(OPERATOR_Clear_All_Materials_From_File)
    bpy.utils.register_class(OPERATOR_Clear_All_Drivers)

def unregister():
    bpy.utils.unregister_class(PANEL_Scene_Optimization)
    bpy.utils.unregister_class(OPERATOR_Clear_All_Materials_From_File)
    bpy.utils.unregister_class(OPERATOR_Clear_All_Drivers)

if __name__ == "__main__":
    register()
