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
    "name": "Room Builder",
    "author": "Andrew Peel",
    "version": (1, 0, 0),
    "blender": (2, 7, 0),
    "location": "Tools Shelf",
    "description": "This add-on creates a UI to help you build rooms in Fluid Designer",
    "warning": "",
    "wiki_url": "",
    "category": "Fluid Designer"
}

import bpy
from mv import fd_types, utils, unit
import math
from mathutils import Vector
import os
from bpy.types import PropertyGroup, UIList, Panel, Operator
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty,
                       CollectionProperty,
                       EnumProperty)

PAINT_LIBRARY_NAME = "Paint"
FLOORING_LIBRARY_NAME = "Flooring"
PAINT_CATEGORY_NAME = "Textured Wall Paint"
CARPET_CATEGORY_NAME = "Carpet"
TILE_CATEGORY_NAME = "Tile"
HARDWOOD_CATEGORY_NAME = "Wood Flooring"

preview_collections = {}

def enum_carpet(self,context):
    if context is None:
        return []
    
    icon_dir = os.path.join(utils.get_library_dir("materials"),FLOORING_LIBRARY_NAME,CARPET_CATEGORY_NAME)
    pcoll = preview_collections["carpet"]
    return utils.get_image_enum_previews(icon_dir,pcoll)

def enum_wood_floor(self,context):
    if context is None:
        return []

    icon_dir = os.path.join(utils.get_library_dir("materials"),FLOORING_LIBRARY_NAME,HARDWOOD_CATEGORY_NAME)
    pcoll = preview_collections["wood_floor"]
    return utils.get_image_enum_previews(icon_dir,pcoll)

def enum_tile_floor(self,context):
    if context is None:
        return []

    icon_dir = os.path.join(utils.get_library_dir("materials"),FLOORING_LIBRARY_NAME,TILE_CATEGORY_NAME)
    pcoll = preview_collections["tile"]
    return utils.get_image_enum_previews(icon_dir,pcoll)

def enum_wall_material(self,context):
    if context is None:
        return []

    icon_dir = os.path.join(utils.get_library_dir("materials"),PAINT_LIBRARY_NAME,PAINT_CATEGORY_NAME)
    pcoll = preview_collections["paint"]
    return utils.get_image_enum_previews(icon_dir,pcoll)

def update_wall_index(self,context): 
    bpy.ops.object.select_all(action='DESELECT')
    wall = self.walls[self.wall_index]
    
    obj = bpy.data.objects[wall.bp_name]
    for child in obj.children:
        if child.type == 'MESH' and child.mv.type!= 'BPASSEMBLY':
            child.select = True
            context.scene.objects.active = child

def update_obstacle_index(self,context): 
    bpy.ops.object.select_all(action='DESELECT')
    wall = context.scene.fd_roombuilder.walls[context.scene.fd_roombuilder.wall_index]
    obstacle = wall.obstacles[wall.obstacle_index]
    
    obj = bpy.data.objects[obstacle.bp_name]
    for child in obj.children:
        if child.type == 'MESH' and child.mv.type!= 'BPASSEMBLY':
            child.hide_select = False
            child.select = True
            context.scene.objects.active = child
            
class Obstacle(PropertyGroup):
    
    bp_name = StringProperty("BP Name")
    base_point = StringProperty("Base Point")
    
bpy.utils.register_class(Obstacle)
    
class Wall(PropertyGroup):
    
    bp_name = StringProperty("BP Name")
    
    obstacle_index = IntProperty(name="ObstacleIndex",update=update_obstacle_index)
    obstacles = CollectionProperty(name="Obstacles",type=Obstacle)

    def add_obstacle(self,objstacle,base_point):
        obst = self.obstacles.add()
        obst.name = objstacle.obj_bp.mv.name_object
        obst.bp_name = objstacle.obj_bp.name
        obst.base_point = base_point
    
bpy.utils.register_class(Wall)

class Scene_Props(PropertyGroup):
    
    room_type = EnumProperty(name="Room Type",
                             items=[('CUSTOM',"Custom Room",'Custom Room'),
                                    ('SINGLE',"Single Wall",'Single Wall'),
                                    ('LSHAPE',"L Shape",'L Shape Room'),
                                    ('USHAPE',"U Shape",'U Shape Room'),
                                    ('SQUARE',"Square Room",'Sqaure Room')],
                             default = 'SQUARE')
    
    wall_index = IntProperty(name="Wall Index",update=update_wall_index)
    walls = CollectionProperty(name="Walls",type=Wall)

    background_image_scale = FloatProperty(name="Backgroud Image Scale",
                                           description="Property used to set the scale properly for background images.",
                                           unit='LENGTH')
    
    floor_type = EnumProperty(name="Floor Type",
                             items=[('CARPET',"Carpet",'Carpet'),
                                    ('TILE',"Tile",'Tile'),
                                    ('WOOD',"Wood Floor",'Wood Floor')],
                             default = 'CARPET')
    
    paint_type = EnumProperty(name="Paint Type",
                              items=[('TEXTURED',"Paint",'Textured Paint')],
                              default = 'TEXTURED')
    
    carpet_material = EnumProperty(name="Carpet Material",items=enum_carpet)
    wood_floor_material = EnumProperty(name="Wood Floor Material",items=enum_wood_floor)
    tile_material = EnumProperty(name="Tile Material",items=enum_tile_floor)
    wall_material = EnumProperty(name="Wall Material",items=enum_wall_material)
    
class Object_Props(PropertyGroup):
    
    is_floor = BoolProperty(name="Is Floor")
    is_ceiling = BoolProperty(name="Is Ceiling")

class PANEL_Room_Builder(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "Room Builder"
    bl_category = "Fluid Designer"
    
    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='MOD_BUILD')
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.fd_roombuilder
        mv = context.scene.mv

        main_box = layout.box()
        box = main_box.box()
        box.label('Room Setup:',icon='SNAP_PEEL_OBJECT')
        box.prop(props,'room_type',text="Room Template")

        row = box.row(align=True)
        row.prop(props,'floor_type',text="Floor",icon='FILE_FOLDER')
        if props.floor_type == 'CARPET':
            row.prop(props,'carpet_material',text="")
        if props.floor_type == 'WOOD':
            row.prop(props,'wood_floor_material',text="")
        if props.floor_type == 'TILE':
            row.prop(props,'tile_material',text="")
        row = box.row(align=True)
        row.prop(props,'paint_type',text="Walls",icon='FILE_FOLDER')
        row.prop(props,'wall_material',text="")

        row = box.row(align=True)
        row.prop(mv,'default_wall_height')
        row.prop(mv,'default_wall_depth')

        if props.room_type == 'CUSTOM':
            row = box.row()
            row.operator('fd_assembly.draw_wall',text="Draw Walls",icon='GREASEPENCIL')
            row.operator('fd_roombuilder.collect_walls',icon='FILE_REFRESH')
            self.draw_custom_room_options(layout,context)
        else:
            col = box.column()
            col.scale_y = 1.3
            col.operator('fd_roombuilder.build_room',text="Build Room",icon='SNAP_PEEL_OBJECT')

        if len(props.walls) > 0:
            box = main_box.box()
            box.label("Room Objects:",icon='SNAP_FACE')
            box.template_list("FD_UL_walls", "", props, "walls", props, "wall_index", rows=len(props.walls))
            wall = props.walls[props.wall_index]
            if wall.bp_name in context.scene.objects:
                obj = context.scene.objects[wall.bp_name]
                if obj.fd_roombuilder.is_ceiling:
                    box.operator('fd_roombuilder.add_floor_obstacle',text="Add Obstacle To Ceiling",icon='PLUG')
                elif obj.fd_roombuilder.is_floor:
                    box.operator('fd_roombuilder.add_floor_obstacle',text="Add Obstacle To Floor",icon='PLUG')
                else:
                    box.operator('fd_roombuilder.add_obstacle',text="Add Obstacle To Wall",icon='PLUG')
                
                if len(wall.obstacles) > 0:
                    box.template_list("FD_UL_obstacles", "", wall, "obstacles", wall, "obstacle_index", rows=4)

    def draw_custom_room_options(self,layout,context):
        view = context.space_data
        use_multiview = context.scene.render.use_multiview

        mainbox = layout.box()
        mainbox.operator("view3d.background_image_add", text="Add Image",icon='ZOOMIN')

        for i, bg in enumerate(view.background_images):
            layout.active = view.show_background_images
            box = mainbox.box()
            row = box.row(align=True)
            row.prop(bg, "show_expanded", text="", emboss=False)
            if bg.source == 'IMAGE' and bg.image:
                row.prop(bg.image, "name", text="", emboss=False)
            elif bg.source == 'MOVIE_CLIP' and bg.clip:
                row.prop(bg.clip, "name", text="", emboss=False)
            else:
                row.label(text="Select an Image with the open button")

            if bg.show_background_image:
                row.prop(bg, "show_background_image", text="", emboss=False, icon='RESTRICT_VIEW_OFF')
            else:
                row.prop(bg, "show_background_image", text="", emboss=False, icon='RESTRICT_VIEW_ON')

            row.operator("view3d.background_image_remove", text="", emboss=False, icon='X').index = i

            if bg.show_expanded:
                
                has_bg = False
                if bg.source == 'IMAGE':
                    row = box.row()
                    row.template_ID(bg, "image", open="image.open")
                    
                    if bg.image is not None:
                        box.prop(bg, "view_axis", text="Display View")
                        box.prop(bg, "draw_depth", expand=False,text="Draw Depth")
                        has_bg = True

                        if use_multiview and bg.view_axis in {'CAMERA', 'ALL'}:
                            box.prop(bg.image, "use_multiview")

                            column = box.column()
                            column.active = bg.image.use_multiview

                            column.label(text="Views Format:")
                            column.row().prop(bg.image, "views_format", expand=True)

                elif bg.source == 'MOVIE_CLIP':
                    box.prop(bg, "use_camera_clip")

                    column = box.column()
                    column.active = not bg.use_camera_clip
                    column.template_ID(bg, "clip", open="clip.open")

                    if bg.clip:
                        column.template_movieclip(bg, "clip", compact=True)

                    if bg.use_camera_clip or bg.clip:
                        has_bg = True

                    column = box.column()
                    column.active = has_bg
                    column.prop(bg.clip_user, "proxy_render_size", text="")
                    column.prop(bg.clip_user, "use_render_undistorted")

                if has_bg:
                    row = box.row()
                    row.label("Image Opacity")
                    row.prop(bg, "opacity", slider=True,text="")

                    row = box.row()
                    row.label("Rotation:")
                    row.prop(bg, "rotation",text="")

                    row = box.row()
                    row.label("Location:")
                    row.prop(bg, "offset_x", text="X")
                    row.prop(bg, "offset_y", text="Y")

                    row = box.row()
                    row.label("Flip Image:")
                    row.prop(bg, "use_flip_x",text="Horizontally")
                    row.prop(bg, "use_flip_y",text="Vertically")

                    row = box.row()
                    row.prop(context.scene.fd_roombuilder, "background_image_scale", text="Known Dimension")
                    row.operator('fd_roombuilder.select_two_points',text="Select Two Points",icon='MAN_TRANS')

                    row = box.row()
                    row.label("Image Size:")
                    row.prop(bg, "size",text="")

class FD_UL_walls(UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item.bp_name in context.scene.objects:
            wall_bp = context.scene.objects[item.bp_name]
            
            obstacle_count = len(item.obstacles)
            count_text = ""
            if obstacle_count > 0:
                count_text = "(" + str(obstacle_count) + ")"
            
            if wall_bp.fd_roombuilder.is_floor or wall_bp.fd_roombuilder.is_ceiling:
                layout.label(text="",icon='MESH_GRID')
                layout.label(text=item.name + "   " + count_text)
                layout.label("Area: " + str(unit.meter_to_active_unit(wall_bp.dimensions.x) * unit.meter_to_active_unit(wall_bp.dimensions.y)))
                if wall_bp.hide:
                    layout.operator('fd_roombuilder.show_plane',text="",icon='RESTRICT_VIEW_ON',emboss=False).object_name = wall_bp.name
                else:
                    layout.operator('fd_roombuilder.hide_plane',text="",icon='RESTRICT_VIEW_OFF',emboss=False).object_name = wall_bp.name
            else:
                wall = fd_types.Wall(wall_bp)
                layout.label(text="",icon='SNAP_FACE')
                layout.label(text=item.name + "   " + count_text)
                layout.label("Length: " + str(unit.meter_to_active_unit(wall.obj_x.location.x)))
                if wall.obj_bp.hide:
                    props = layout.operator('fd_roombuilder.hide_show_wall',text="",icon='RESTRICT_VIEW_ON',emboss=False)
                    props.wall_bp_name = wall_bp.name
                    props.hide = False
                else:
                    props = layout.operator('fd_roombuilder.hide_show_wall',text="",icon='RESTRICT_VIEW_OFF',emboss=False)
                    props.wall_bp_name = wall_bp.name
                    props.hide = True
                    
class FD_UL_obstacles(UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        wall = context.scene.fd_roombuilder.walls[context.scene.fd_roombuilder.wall_index]
        wall_obj = context.scene.objects[wall.bp_name]
        obs_obj = context.scene.objects[item.bp_name]
        layout.label(text="",icon='PLUG')
        layout.label(text=item.name)
        for child in obs_obj.children:
            if child.mv.type =='CAGE':
                layout.prop(child,'draw_type',text="")
        if wall_obj.fd_roombuilder.is_floor or wall_obj.fd_roombuilder.is_ceiling:
            layout.operator('fd_roombuilder.add_floor_obstacle',text="",icon='INFO').obstacle_bp_name = item.bp_name
        else:
            layout.operator('fd_roombuilder.add_obstacle',text="",icon='INFO').obstacle_bp_name = item.bp_name
        layout.operator('fd_roombuilder.delete_obstacle',text="",icon='X').obstacle_bp_name = item.bp_name
        
class OPERATOR_Add_Obstacle(Operator):
    bl_idname = "fd_roombuilder.add_obstacle"
    bl_label = "Add Obstacle" 
    bl_options = {'UNDO'}

    obstacle_bp_name = StringProperty(name="Obstacle BP Name",
                                      description="Pass the base point name to reposition an existing obstacle",
                                      default="")

    base_point = EnumProperty(name="Base Point",
                             items=[('TOP_LEFT',"Top Left",'Top Left of Wall'),
                                    ('TOP_RIGHT',"Top Right",'Top Right of Wall'),
                                    ('BOTTOM_LEFT',"Bottom Left",'Bottom Left of Wall'),
                                    ('BOTTOM_RIGHT',"Bottom_Right",'Bottom Right of Wall')],
                             default = 'BOTTOM_LEFT')

    obstacle_name = StringProperty(name="Obstacle Name",
                                   description="Enter the Name of the Obstacle",
                                   default="New Obstacle")

    obstacle_width = FloatProperty(name="Obstacle Width",
                                   description="Enter the Width of the Obstacle",
                                   default=unit.inch(3),
                                   unit='LENGTH',
                                   precision=4)

    obstacle_height = FloatProperty(name="Obstacle Height",
                                    description="Enter the Height of the Obstacle",
                                    default=unit.inch(4),
                                    unit='LENGTH',
                                    precision=4)

    x_location = FloatProperty(name="X Location",
                               description="Enter the X Location of the Obstacle",
                               default=unit.inch(0),
                               unit='LENGTH',
                               precision=4)

    z_location = FloatProperty(name="Z Location",
                               description="Enter the Z Location of the Obstacle",
                               default=unit.inch(0),
                               unit='LENGTH',
                               precision=4)

    obstacle = None
    wall = None
    wall_item = None
    click_ok = False
    
    def check(self, context):
        if self.obstacle and self.wall:
            
            self.obstacle.obj_z.location.z = self.obstacle_height
            self.obstacle.obj_x.location.x = self.obstacle_width
            
            if self.base_point == 'TOP_LEFT':
                self.obstacle.obj_bp.location.x = self.x_location
                self.obstacle.obj_bp.location.z = self.wall.obj_z.location.z - self.z_location - self.obstacle_height
            if self.base_point == 'TOP_RIGHT':
                self.obstacle.obj_bp.location.x = self.wall.obj_x.location.x - self.x_location - self.obstacle_width
                self.obstacle.obj_bp.location.z = self.wall.obj_z.location.z - self.z_location - self.obstacle_height
            if self.base_point == 'BOTTOM_LEFT':
                self.obstacle.obj_bp.location.x = self.x_location
                self.obstacle.obj_bp.location.z = self.z_location
            if self.base_point == 'BOTTOM_RIGHT':
                self.obstacle.obj_bp.location.x = self.wall.obj_x.location.x - self.x_location - self.obstacle_width
                self.obstacle.obj_bp.location.z = self.z_location
                
        #SET VIEW FOR USER
#         view3d = context.space_data.region_3d
#         print(view3d.view_rotation)
#         view3d.view_distance = 7
#         view3d.view_location = (self.wall.obj_bp.location.x+self.wall.obj_x.location.x,
#                                 self.wall.obj_bp.location.y,
#                                 self.wall.obj_bp.location.z)
#         view3d.view_rotation = (.8416,.4984,-.1004,-.1824)

        return True
    
    def __del__(self):
        self.set_draw_type(bpy.context, 'TEXTURED')

        if self.click_ok == False: # Only delete The obstacle if user didn't click OK
            utils.delete_object_and_children(self.obstacle.obj_bp)
        
    def set_draw_type(self,context,draw_type='WIRE'):
        for obj in context.scene.objects:
            if obj.mv.product_type == 'Obstacle':
                continue
            if obj.mv.type == 'CAGE':
                continue            
            if obj.parent:
                if obj.parent.name == self.wall.obj_bp.name:
                    pass
                else:
                    obj.draw_type = draw_type
        if self.obstacle:
            for child in self.obstacle.obj_bp.children:
                child.draw_type = 'WIRE'
    
    def invoke(self,context,event):
        wm = context.window_manager
        self.click_ok = False
        
        self.wall_item = context.scene.fd_roombuilder.walls[context.scene.fd_roombuilder.wall_index]
        wall_bp = context.scene.objects[self.wall_item.bp_name]
        self.wall = fd_types.Wall(wall_bp)
            
        self.set_draw_type(context)
        
        obstacle_item = None
        
        #Get Existing obstacle assembly so we can set properties then delete it. 
        if self.obstacle_bp_name in context.scene.objects:
            for obstacle in self.wall_item.obstacles:
                if obstacle.bp_name == self.obstacle_bp_name:
                    obstacle_item = obstacle
                    self.base_point = obstacle.base_point
            
            obj_bp = context.scene.objects[self.obstacle_bp_name]
            self.obstacle = fd_types.Assembly(obj_bp)
            self.obstacle_name = self.obstacle.obj_bp.mv.name_object
            self.obstacle_height = self.obstacle.obj_z.location.z
            self.obstacle_width = self.obstacle.obj_x.location.x
            if self.base_point == 'TOP_LEFT':
                self.x_location = self.obstacle.obj_bp.location.x
                self.z_location = self.wall.obj_z.location.z - self.obstacle.obj_bp.location.z - self.obstacle_height
            if self.base_point == 'TOP_RIGHT':
                self.x_location = self.wall.obj_x.location.x - self.obstacle.obj_bp.location.x - self.obstacle_width
                self.z_location = self.wall.obj_z.location.z - self.obstacle.obj_bp.location.z - self.obstacle_height
            if self.base_point == 'BOTTOM_LEFT':
                self.x_location = self.obstacle.obj_bp.location.x
                self.z_location = self.obstacle.obj_bp.location.z
            if self.base_point == 'BOTTOM_RIGHT':
                self.x_location = self.wall.obj_x.location.x - self.obstacle.obj_bp.location.x - self.obstacle_width
                self.z_location = self.obstacle.obj_bp.location.z
            utils.delete_object_and_children(obj_bp)
            
        #Create Obstacle Assembly 
        self.obstacle = fd_types.Assembly()
        self.obstacle.create_assembly()
        cage = self.obstacle.get_cage()
        cage.select = True
        cage.show_x_ray = True
        self.obstacle.obj_x.hide = True
        self.obstacle.obj_y.hide = True
        self.obstacle.obj_z.hide = True
        
        self.obstacle.obj_bp.parent = self.wall.obj_bp
        self.obstacle.obj_x.location.x = self.obstacle_width
        self.obstacle.obj_y.location.y = self.wall.obj_y.location.y + unit.inch(2)
        self.obstacle.obj_z.location.z = self.obstacle_height
        self.obstacle.obj_bp.location.y = - unit.inch(1)
        #Set bp_name for obstacle item just in case user doesn't click OK.
        if obstacle_item:
            obstacle_item.bp_name = self.obstacle.obj_bp.name
        self.check(context)
        
        return wm.invoke_props_dialog(self, width=400)
    
    def execute(self, context):
        self.click_ok = True
        Width = self.obstacle.get_var('dim_x','Width')
        
        dim = fd_types.Dimension()
        dim.parent(self.obstacle.obj_bp)
        dim.start_z(value = unit.inch(.5))
        dim.start_x('Width/2',[Width])
        dim.set_label(self.obstacle_name)
        
        self.obstacle.obj_bp.mv.name_object = self.obstacle_name
        
        if self.obstacle_bp_name == "":
            self.wall_item.add_obstacle(self.obstacle,self.base_point)
            
            if self.obstacle:
                self.obstacle.obj_bp.mv.type = 'NONE'
            
        for obstacle in self.wall_item.obstacles:
            if obstacle.bp_name == self.obstacle_bp_name:
                obstacle.name = self.obstacle_name
                obstacle.bp_name = self.obstacle.obj_bp.name
                
        if self.obstacle:
            for child in self.obstacle.obj_bp.children:
                child.mv.product_type = 'Obstacle'
                child.draw_type = 'WIRE'
                
#         self.obstacle = None
#         self.obstacle_bp_name = ""
        return {'FINISHED'}
        
    def draw(self,context):
        layout = self.layout
        box = layout.box()

        box.prop(self,"obstacle_name")
        
        col = box.column(align=False)
        
        row = col.row(align=True)
        row.prop_enum(self, "base_point", 'TOP_LEFT', icon='TRIA_LEFT', text="Top Left") 
        row.prop_enum(self, "base_point", 'TOP_RIGHT', icon='TRIA_RIGHT', text="Top Right") 
        row = col.row(align=True)
        row.prop_enum(self, "base_point", 'BOTTOM_LEFT', icon='TRIA_LEFT', text="Bottom Left") 
        row.prop_enum(self, "base_point", 'BOTTOM_RIGHT', icon='TRIA_RIGHT', text="Bottom Right")   
        
        row = col.row()
        row.label("Obstacle Width:")
        row.prop(self,"obstacle_width",text="")
        
        if self.wall:
            row = col.row()
            row.label("Obstacle Height:")
            row.prop(self,"obstacle_height",text="")
        else:
            row = col.row()
            row.label("Obstacle Depth:")
            row.prop(self,"obstacle_depth",text="")
        
        row = col.row()
        row.label("Obstacle X Location:")
        row.prop(self,"x_location",text="")
        
        if self.wall:
            row = col.row()
            row.label("Obstacle Z Location:")
            row.prop(self,"z_location",text="")
        else:
            row = col.row()
            row.label("Obstacle Y Location:")
            row.prop(self,"y_location",text="")

class OPERATOR_Add_Floor_Obstacle(Operator):
    bl_idname = "fd_roombuilder.add_floor_obstacle"
    bl_label = "Add Floor Obstacle" 
    bl_options = {'UNDO'}

    obstacle_bp_name = StringProperty(name="Obstacle BP Name",
                                      description="Pass the base point name to reposition an existing obstacle",
                                      default="")

    base_point = EnumProperty(name="Base Point",
                             items=[('FRONT_LEFT',"Front Left",'Front Left of Room'),
                                    ('FRONT_RIGHT',"Front Right",'Front Right of Room'),
                                    ('BACK_LEFT',"Back Left",'Back Left of Room'),
                                    ('BACK_RIGHT',"Back",'Back Right of Room')],
                             default = 'FRONT_LEFT')

    obstacle_name = StringProperty(name="Obstacle Name",
                                   description="Enter the Name of the Obstacle",
                                   default="New Obstacle")

    obstacle_width = FloatProperty(name="Obstacle Width",
                                   description="Enter the Width of the Obstacle",
                                   default=unit.inch(3),
                                   unit='LENGTH',
                                   precision=4)

    obstacle_depth = FloatProperty(name="Obstacle Depth",
                                   description="Enter the Depth of the Obstacle",
                                   default=unit.inch(4),
                                   unit='LENGTH',
                                   precision=4)

    x_location = FloatProperty(name="X Location",
                               description="Enter the X Location of the Obstacle",
                               default=unit.inch(0),
                               unit='LENGTH',
                               precision=4)

    y_location = FloatProperty(name="Y Location",
                               description="Enter the Y Location of the Obstacle",
                               default=unit.inch(0),
                               unit='LENGTH',
                               precision=4)

    obstacle = None
    plane = None
    wall_item = None
    
    def check(self, context):
        if self.obstacle and self.plane:
            
            self.obstacle.obj_bp.location.z = unit.inch(-1)
            self.obstacle.obj_y.location.y = self.obstacle_depth
            self.obstacle.obj_x.location.x = self.obstacle_width
            self.obstacle.obj_z.location.z = unit.inch(2)
            
            if self.base_point == 'FRONT_LEFT':
                self.obstacle.obj_bp.location.x = self.x_location
                self.obstacle.obj_bp.location.y = self.y_location
            if self.base_point == 'FRONT_RIGHT':
                self.obstacle.obj_bp.location.x = self.plane.dimensions.x - self.x_location - self.obstacle_width
                self.obstacle.obj_bp.location.y = self.y_location
            if self.base_point == 'BACK_LEFT':
                self.obstacle.obj_bp.location.x = self.x_location
                self.obstacle.obj_bp.location.y = self.plane.dimensions.y - self.y_location - self.obstacle_depth
            if self.base_point == 'BACK_RIGHT':
                self.obstacle.obj_bp.location.x = self.plane.dimensions.x - self.x_location - self.obstacle_width
                self.obstacle.obj_bp.location.y = self.plane.dimensions.y - self.y_location - self.obstacle_depth
            
        return True
    
    def set_draw_type(self,context,draw_type='WIRE'):
        for obj in context.scene.objects:
            if obj.parent:
                if obj.parent.name == self.plane.name:
                    pass
                else:
                    obj.draw_type = draw_type
        if self.obstacle:
            self.obstacle.obj_bp.draw_type = 'WIRE'
            for child in self.obstacle.obj_bp.children:
                child.draw_type = 'WIRE'    
    
    def set_obstacle_defaults(self,context):
        if self.obstacle_bp_name in context.scene.objects:
            obj_bp = context.scene.objects[self.obstacle_bp_name]
            self.obstacle = fd_types.Assembly(obj_bp)
        else:
            self.obstacle = fd_types.Assembly()
            self.obstacle.create_assembly()
        self.obstacle_name = self.obstacle.obj_bp.mv.name_object
        self.obstacle_depth = self.obstacle.obj_y.location.y
        self.obstacle_width = self.obstacle.obj_x.location.x
        if self.base_point == 'FRONT_LEFT':
            self.x_location = self.obstacle.obj_bp.location.x
            self.y_location = self.obstacle.obj_bp.location.y
        if self.base_point == 'FRONT_RIGHT':
            self.x_location = self.obstacle.obj_bp.location.x - self.obstacle_width
            self.y_location = self.obstacle.obj_bp.location.y
        if self.base_point == 'BACK_LEFT':
            self.x_location = self.obstacle.obj_bp.location.x
            self.y_location = self.obstacle.obj_bp.location.y
        if self.base_point == 'BACK_RIGHT':
            self.x_location = self.obstacle.obj_bp.location.x - self.obstacle_width
            self.y_location = self.obstacle.obj_bp.location.y - self.obstacle_depth
#         utils.delete_object_and_children(obj_bp)
    
    def __del__(self):
        self.set_draw_type(bpy.context,'TEXTURED')
        
        if self.obstacle and self.obstacle_bp_name == "": # Only delete The obstacle if user didn't click OK
            utils.delete_object_and_children(self.obstacle.obj_bp)
    
    def invoke(self,context,event):
        wm = context.window_manager
        
        self.wall_item = context.scene.fd_roombuilder.walls[context.scene.fd_roombuilder.wall_index]
        self.plane = context.scene.objects[self.wall_item.bp_name]
        
        self.set_draw_type(context)
        
        if self.obstacle_bp_name in context.scene.objects:
            for obstacle in self.wall_item.obstacles:
                if obstacle.bp_name == self.obstacle_bp_name:
                    self.base_point = obstacle.base_point
            
        self.set_obstacle_defaults(context)

        cage = self.obstacle.get_cage()
        cage.select = True
        self.obstacle.obj_x.hide = True
        self.obstacle.obj_y.hide = True
        self.obstacle.obj_z.hide = True
        
        self.obstacle.obj_bp.parent = self.plane
        self.obstacle.obj_x.location.x = self.obstacle_width
        self.obstacle.obj_y.location.y = self.obstacle_depth
        self.obstacle.obj_z.location.z = - unit.inch(1)
        self.obstacle.obj_bp.location.y = self.y_location
        
        self.check(context)
        
        return wm.invoke_props_dialog(self, width=400)
    
    def execute(self, context):
        Width = self.obstacle.get_var('dim_x','Width')
        Depth = self.obstacle.get_var('dim_y','Depth')
        
        dim = fd_types.Dimension()
        dim.parent(self.obstacle.obj_bp)
        dim.start_z(value = unit.inch(.5))
        dim.start_y('Depth/2',[Depth])
        dim.start_x('Width/2',[Width])
        dim.set_label(self.obstacle_name)
        
        self.obstacle.obj_bp.mv.name_object = self.obstacle_name
        
        if self.obstacle_bp_name == "":
            self.wall_item.add_obstacle(self.obstacle,self.base_point)
            
            if self.obstacle:
                self.obstacle.obj_bp.mv.type = 'NONE'
            
        for obstacle in self.wall_item.obstacles:
            if obstacle.bp_name == self.obstacle_bp_name:
                obstacle.name = self.obstacle_name
                obstacle.bp_name = self.obstacle.obj_bp.name
            
        self.obstacle = None
        self.obstacle_bp_name = ""
        return {'FINISHED'}
        
    def draw(self,context):
        layout = self.layout
        box = layout.box()

        box.prop(self,"obstacle_name")
        
        col = box.column(align=False)

        row = col.row(align=True)
        row.prop_enum(self, "base_point", 'BACK_LEFT', icon='TRIA_LEFT', text="Back Left") 
        row.prop_enum(self, "base_point", 'BACK_RIGHT', icon='TRIA_RIGHT', text="Back Right")   
        row = col.row(align=True)
        row.prop_enum(self, "base_point", 'FRONT_LEFT', icon='TRIA_LEFT', text="Front Left") 
        row.prop_enum(self, "base_point", 'FRONT_RIGHT', icon='TRIA_RIGHT', text="Front Right") 
        
        row = col.row()
        row.label("Obstacle Width:")
        row.prop(self,"obstacle_width",text="")
        
        row = col.row()
        row.label("Obstacle Depth:")
        row.prop(self,"obstacle_depth",text="")
        
        row = col.row()
        row.label("Obstacle X Location:")
        row.prop(self,"x_location",text="")
        
        row = col.row()
        row.label("Obstacle Y Location:")
        row.prop(self,"y_location",text="")

class OPERATOR_Build_Room(Operator):
    bl_idname = "fd_roombuilder.build_room"
    bl_label = "Build Room" 
    bl_options = {'UNDO'}

    back_wall_length = FloatProperty(name="Back Wall Length",
                                     description="Enter the Back Wall Length",
                                     default=unit.inch(120),
                                     unit='LENGTH',
                                     precision=4)

    side_wall_length = FloatProperty(name="Side Wall Length",
                                     description="Enter the Side Wall Length",
                                     default=unit.inch(120),
                                     unit='LENGTH',
                                     precision=4)
    
    left_return_length = FloatProperty(name="Left Return Length",
                                       description="Enter the Left Return Wall Length",
                                       default=unit.inch(25),
                                       unit='LENGTH',
                                       precision=4)
    
    right_return_length = FloatProperty(name="Right Return Length",
                                       description="Enter the Right Return Wall Length",
                                       default=unit.inch(25),
                                       unit='LENGTH',
                                       precision=4)
    
    wall_height = FloatProperty(name="Wall Height",
                                description="Enter the Wall Height",
                                default=unit.inch(108),
                                unit='LENGTH',
                                precision=4)
    
    wall_thickness = FloatProperty(name="Wall Thickness",
                                   description="Enter the Wall Thickness",
                                   default=unit.inch(4),
                                   unit='LENGTH',
                                   precision=4)
    
    opening_height = FloatProperty(name="Opening Height",
                                   description="Enter the Height of the Opening",
                                   default=unit.inch(83),
                                   unit='LENGTH',
                                   precision=4)
    
    obstacle = None
    left_side_wall = None
    back_wall = None
    entry_wall = None
    right_side_wall = None
    door = None
    
    wall_mesh_objs = []
    
    floor = None
    
    clicked_ok = False
    
    def check(self, context):
        self.update_wall_properties(context)
        self.set_camera_position(context)
        return True
    
    def set_camera_position(self,context):
        view3d = context.space_data.region_3d
        if unit.meter_to_active_unit(self.back_wall_length) / 17 < 7:
            distance = 7
        elif unit.meter_to_active_unit(self.back_wall_length) / 17 > 12:
            distance = 12
        else:
            distance = unit.meter_to_active_unit(self.back_wall_length) / 17
        view3d.view_distance = distance
        view3d.view_location = (self.back_wall_length/2,self.side_wall_length,0)
        view3d.view_rotation = (.8416,.4984,-.1004,-.1824)
    
    def update_square_room(self):
        self.left_side_wall.obj_z.location.z = self.wall_height
        self.left_side_wall.obj_y.location.y = self.wall_thickness
        self.left_side_wall.obj_x.location.x = self.side_wall_length
        self.left_side_wall.obj_bp.mv.name_object = "Wall A"
        
        self.back_wall.obj_z.location.z = self.wall_height
        self.back_wall.obj_y.location.y = self.wall_thickness
        self.back_wall.obj_x.location.x = self.back_wall_length
        self.back_wall.obj_bp.mv.name_object = "Wall B"
        
        self.right_side_wall.obj_z.location.z = self.wall_height
        self.right_side_wall.obj_y.location.y = self.wall_thickness
        self.right_side_wall.obj_x.location.x = self.side_wall_length
        self.right_side_wall.obj_bp.mv.name_object = "Wall C"
        
        self.entry_wall.obj_z.location.z = self.wall_height
        self.entry_wall.obj_y.location.y = self.wall_thickness
        self.entry_wall.obj_x.location.x = self.back_wall_length
        self.entry_wall.obj_bp.mv.name_object = "Wall D"
        
        self.door.obj_bp.location.x = self.right_return_length
        self.door.obj_x.location.x = self.back_wall_length - self.right_return_length - self.left_return_length
        self.door.obj_y.location.y = self.wall_thickness + unit.inch(.01)
        self.door.obj_z.location.z = self.opening_height

        self.left_side_wall.obj_z.hide = True
        self.left_side_wall.obj_y.hide = True
        self.left_side_wall.obj_x.hide = True
        self.back_wall.obj_z.hide = True
        self.back_wall.obj_y.hide = True
        self.back_wall.obj_x.hide = True
        self.right_side_wall.obj_z.hide = True
        self.right_side_wall.obj_y.hide = True
        self.right_side_wall.obj_x.hide = True
        self.entry_wall.obj_z.hide = True
        self.entry_wall.obj_y.hide = True
        self.entry_wall.obj_x.hide = True
        self.door.obj_z.hide = True
        self.door.obj_y.hide = True
        self.door.obj_x.hide = True
    
    def update_single_room(self):
        self.back_wall.obj_z.location.z = self.wall_height
        self.back_wall.obj_y.location.y = self.wall_thickness
        self.back_wall.obj_x.location.x = self.back_wall_length
        self.back_wall.obj_bp.mv.name_object = "Wall A"
    
        self.back_wall.obj_z.hide = True
        self.back_wall.obj_y.hide = True
        self.back_wall.obj_x.hide = True
    
    def update_l_shape_wall(self):
        self.back_wall.obj_z.location.z = self.wall_height
        self.back_wall.obj_y.location.y = self.wall_thickness
        self.back_wall.obj_x.location.x = self.back_wall_length
        self.back_wall.obj_bp.mv.name_object = "Wall B"
    
        self.left_side_wall.obj_z.location.z = self.wall_height
        self.left_side_wall.obj_y.location.y = self.wall_thickness
        self.left_side_wall.obj_x.location.x = self.left_return_length
        self.left_side_wall.obj_bp.mv.name_object = "Wall A"

        self.left_side_wall.obj_z.hide = True
        self.left_side_wall.obj_y.hide = True
        self.left_side_wall.obj_x.hide = True
    
        self.back_wall.obj_z.hide = True
        self.back_wall.obj_y.hide = True
        self.back_wall.obj_x.hide = True
        
    def update_u_shape_wall(self):
        self.left_side_wall.obj_z.location.z = self.wall_height
        self.left_side_wall.obj_y.location.y = self.wall_thickness
        self.left_side_wall.obj_x.location.x = self.left_return_length
        self.left_side_wall.obj_bp.mv.name_object = "Wall A"
        
        self.back_wall.obj_z.location.z = self.wall_height
        self.back_wall.obj_y.location.y = self.wall_thickness
        self.back_wall.obj_x.location.x = self.back_wall_length
        self.back_wall.obj_bp.mv.name_object = "Wall B"
        
        self.right_side_wall.obj_z.location.z = self.wall_height
        self.right_side_wall.obj_y.location.y = self.wall_thickness
        self.right_side_wall.obj_x.location.x = self.right_return_length
        self.right_side_wall.obj_bp.mv.name_object = "Wall C"
    
        self.left_side_wall.obj_z.hide = True
        self.left_side_wall.obj_y.hide = True
        self.left_side_wall.obj_x.hide = True
        self.back_wall.obj_z.hide = True
        self.back_wall.obj_y.hide = True
        self.back_wall.obj_x.hide = True
        self.right_side_wall.obj_z.hide = True
        self.right_side_wall.obj_y.hide = True
        self.right_side_wall.obj_x.hide = True
    
    def update_wall_properties(self,context):
        props = bpy.context.scene.fd_roombuilder
        
        if props.room_type == 'SQUARE':
            self.update_square_room()
        if props.room_type == 'LSHAPE':
            self.update_l_shape_wall()
        if props.room_type == 'USHAPE':
            self.update_u_shape_wall()
        if props.room_type == 'SINGLE':
            self.update_single_room()
        
    def create_wall(self,context):
        wall = fd_types.Wall()
        wall.create_wall()
        wall.build_wall_mesh()
        wall.obj_bp.location = (0,0,0)
        return wall
    
    def build_sqaure_room(self,context):
        self.left_side_wall = self.create_wall(context)
        self.left_side_wall.obj_bp.rotation_euler.z = math.radians(90)
        self.back_wall = self.create_wall(context)
        self.right_side_wall = self.create_wall(context)
        self.right_side_wall.obj_bp.rotation_euler.z = math.radians(-90)
        self.entry_wall = self.create_wall(context)
        self.entry_wall.obj_bp.rotation_euler.z = math.radians(180)
        
        back_wall = self.back_wall.get_wall_mesh()
        self.wall_mesh_objs.append(back_wall)
        back_wall.data.vertices[1].co[0] -= self.wall_thickness 
        back_wall.data.vertices[2].co[0] += self.wall_thickness 
        back_wall.data.vertices[5].co[0] -= self.wall_thickness 
        back_wall.data.vertices[6].co[0] += self.wall_thickness 
         
        left_side_wall = self.left_side_wall.get_wall_mesh()
        self.wall_mesh_objs.append(left_side_wall)
        left_side_wall.data.vertices[1].co[0] -= self.wall_thickness 
        left_side_wall.data.vertices[2].co[0] += self.wall_thickness 
        left_side_wall.data.vertices[5].co[0] -= self.wall_thickness 
        left_side_wall.data.vertices[6].co[0] += self.wall_thickness 
         
        right_side_wall = self.right_side_wall.get_wall_mesh()
        self.wall_mesh_objs.append(right_side_wall)
        right_side_wall.data.vertices[1].co[0] -= self.wall_thickness 
        right_side_wall.data.vertices[2].co[0] += self.wall_thickness 
        right_side_wall.data.vertices[5].co[0] -= self.wall_thickness 
        right_side_wall.data.vertices[6].co[0] += self.wall_thickness 

        entry_wall = self.entry_wall.get_wall_mesh()
        self.wall_mesh_objs.append(entry_wall)
        entry_wall.data.vertices[1].co[0] -= self.wall_thickness 
        entry_wall.data.vertices[2].co[0] += self.wall_thickness 
        entry_wall.data.vertices[5].co[0] -= self.wall_thickness 
        entry_wall.data.vertices[6].co[0] += self.wall_thickness 
        
        #TODO: Develop a way for users to change entry door style. (Sliding, Bifold, Single, Double)
        bp = utils.get_group(os.path.join(os.path.dirname(__file__),"Entry Doors","Entry Door Frame.blend"))
        self.door = fd_types.Assembly(bp)
        self.door.obj_bp.mv.type_group = 'PRODUCT'
        self.door.obj_bp.parent = self.entry_wall.obj_bp
        
        objs = utils.get_child_objects(self.door.obj_bp)
        for obj_bool in objs:
            obj_bool.draw_type = 'TEXTURED'
            if obj_bool.mv.use_as_bool_obj:
                mod = entry_wall.modifiers.new(obj_bool.name,'BOOLEAN')
                mod.object = obj_bool
                mod.operation = 'DIFFERENCE'
        
        utils.connect_objects_location(self.left_side_wall.obj_x,self.back_wall.obj_bp)
        utils.connect_objects_location(self.back_wall.obj_x,self.right_side_wall.obj_bp)
        utils.connect_objects_location(self.right_side_wall.obj_x,self.entry_wall.obj_bp)
        
    def build_single_wall(self,context):
        self.back_wall = self.create_wall(context)
        
    def build_l_shape_room(self,context):
        self.left_side_wall = self.create_wall(context)
        self.left_side_wall.obj_bp.rotation_euler.z = math.radians(90)
        self.back_wall = self.create_wall(context)

        back_wall = self.back_wall.get_wall_mesh()
        self.wall_mesh_objs.append(back_wall)
        back_wall.data.vertices[1].co[0] -= self.wall_thickness 
        back_wall.data.vertices[5].co[0] -= self.wall_thickness 
         
        left_side_wall = self.left_side_wall.get_wall_mesh()
        self.wall_mesh_objs.append(left_side_wall)
        left_side_wall.data.vertices[2].co[0] += self.wall_thickness 
        left_side_wall.data.vertices[6].co[0] += self.wall_thickness 

        utils.connect_objects_location(self.left_side_wall.obj_x,self.back_wall.obj_bp)
        
    def build_u_shape_room(self,context):
        self.left_side_wall = self.create_wall(context)
        self.left_side_wall.obj_bp.rotation_euler.z = math.radians(90)
        self.back_wall = self.create_wall(context)
        self.right_side_wall = self.create_wall(context)
        self.right_side_wall.obj_bp.rotation_euler.z = math.radians(-90)

        back_wall = self.back_wall.get_wall_mesh()
        self.wall_mesh_objs.append(back_wall)
        back_wall.data.vertices[1].co[0] -= self.wall_thickness 
        back_wall.data.vertices[2].co[0] += self.wall_thickness 
        back_wall.data.vertices[5].co[0] -= self.wall_thickness 
        back_wall.data.vertices[6].co[0] += self.wall_thickness 
        
        left_side_wall = self.left_side_wall.get_wall_mesh()
        self.wall_mesh_objs.append(left_side_wall)
        left_side_wall.data.vertices[2].co[0] += self.wall_thickness 
        left_side_wall.data.vertices[6].co[0] += self.wall_thickness 
        
        right_side_wall = self.right_side_wall.get_wall_mesh()
        self.wall_mesh_objs.append(right_side_wall)
        right_side_wall.data.vertices[1].co[0] -= self.wall_thickness 
        right_side_wall.data.vertices[5].co[0] -= self.wall_thickness 
        
        utils.connect_objects_location(self.left_side_wall.obj_x,self.back_wall.obj_bp)
        utils.connect_objects_location(self.back_wall.obj_x,self.right_side_wall.obj_bp)
        
    def invoke(self,context,event):
        self.wall_mesh_objs = []
        utils.delete_obj_list(bpy.data.objects)
        props = bpy.context.scene.fd_roombuilder
        self.wall_height = context.scene.mv.default_wall_height
        self.wall_thickness = context.scene.mv.default_wall_depth
        
        if props.room_type == 'SQUARE':
            self.build_sqaure_room(context)
        if props.room_type == 'LSHAPE':
            self.build_l_shape_room(context)
        if props.room_type == 'USHAPE':
            self.build_u_shape_room(context)
        if props.room_type == 'SINGLE':
            self.build_single_wall(context)
        
        self.update_wall_properties(context)
        self.set_camera_position(context)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def execute(self, context):
        return {'FINISHED'}
        
    def __del__(self):
        #FIX MESH SIZE FOR EDITING AFTER ROOM CREATION
        for mesh in self.wall_mesh_objs:
            bpy.ops.fd_assembly.connect_meshes_to_hooks_in_assembly(object_name = mesh.name)
        
        #HIDE EMPTIES AFTER CONNECTING HOOKS
        for obj in bpy.context.scene.objects:
            if obj.type == 'EMPTY':
                obj.hide = True
        
        bpy.ops.fd_roombuilder.collect_walls()     
        
    def draw(self,context):
        layout = self.layout
        box = layout.box()
        
        props = bpy.context.scene.fd_roombuilder
        
        if props.room_type == 'SQUARE':
        
            row = box.row()
            row.label("Room Length:")
            row.prop(self,"back_wall_length",text="")
            
            row = box.row()
            row.label("Room Depth:")
            row.prop(self,"side_wall_length",text="")
            
            row = box.row()
            row.label('Return Walls:')
            row.prop(self,"left_return_length",text="Left")
            row.prop(self,"right_return_length",text='Right')
            
            row = box.row()
            row.label("Opening Height:")
            row.prop(self,"opening_height",text="")
            
        if props.room_type == 'SINGLE':
            row = box.row()
            row.label("Wall Length:")
            row.prop(self,"back_wall_length",text="")
        
        if props.room_type == 'LSHAPE':
            row = box.row()
            row.label("Back Wall Length:")
            row.prop(self,"back_wall_length",text="")
            
            row = box.row()
            row.label("Left Wall Length:")
            row.prop(self,"left_return_length",text="")
        
        if props.room_type == 'USHAPE':
            row = box.row()
            row.label("Back Wall Length:")
            row.prop(self,"back_wall_length",text="")
            
            row = box.row()
            row.label("Left Wall Length:")
            row.prop(self,"left_return_length",text="")
        
            row = box.row()
            row.label("Right Wall Length:")
            row.prop(self,"right_return_length",text="")
        
class OPERATOR_Collect_Walls(Operator):
    bl_idname = "fd_roombuilder.collect_walls"
    bl_label = "Collect Walls" 
    bl_options = {'UNDO'}

#     floor = None

    def assign_floor_material(self,context,obj):
        props = context.scene.fd_roombuilder
        if props.floor_type == 'CARPET':
            material = utils.get_material((FLOORING_LIBRARY_NAME,CARPET_CATEGORY_NAME),props.carpet_material)
        if props.floor_type == 'WOOD':    
            material = utils.get_material((FLOORING_LIBRARY_NAME,HARDWOOD_CATEGORY_NAME),props.wood_floor_material)
        if props.floor_type == 'TILE':
            material = utils.get_material((FLOORING_LIBRARY_NAME,TILE_CATEGORY_NAME),props.tile_material)
        if material:
            bpy.ops.fd_object.unwrap_mesh(object_name=obj.name)
            bpy.ops.fd_object.add_material_slot(object_name=obj.name)
            for i, mat in enumerate(obj.material_slots):
                mat.material = material

    def assign_wall_material(self,context,obj):
        props = context.scene.fd_roombuilder
        material = utils.get_material((PAINT_LIBRARY_NAME,PAINT_CATEGORY_NAME),props.wall_material)
        if material:
            bpy.ops.fd_object.unwrap_mesh(object_name=obj.name)
            bpy.ops.fd_object.add_material_slot(object_name=obj.name)
            for i, mat in enumerate(obj.material_slots):
                mat.material = material
                
    def execute(self, context):
        props = context.scene.fd_roombuilder
        mv = context.scene.mv
        
        for old_wall in props.walls:
            props.walls.remove(0)
        
        bpy.ops.fd_object.draw_floor_plane()
        obj_floor = context.active_object
        obj_floor.name = "Floor"
        obj_floor.mv.name_object = "Floor"
        obj_floor.fd_roombuilder.is_floor = True
        self.assign_floor_material(context,obj_floor)
        
        bpy.ops.fd_object.draw_floor_plane()
        ceiling = context.active_object
        ceiling.name = 'Ceiling'
        ceiling.mv.name_object = "Ceiling"
        ceiling.location.z = mv.default_wall_height
        ceiling.hide = True
        ceiling.fd_roombuilder.is_ceiling = True
        
        bpy.ops.fd_object.add_room_lamp()
        
        for obj in context.scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj)
                self.assign_wall_material(context, wall.get_wall_mesh())
                wall = props.walls.add()
                wall.name = obj.mv.name_object
                wall.bp_name = obj.name
            if obj.fd_roombuilder.is_floor:
                floor = props.walls.add()
                floor.name = obj.mv.name_object
                floor.bp_name = obj.name
            if obj.fd_roombuilder.is_ceiling:
                ceiling = props.walls.add()
                ceiling.name = obj.mv.name_object
                ceiling.bp_name = obj.name

        return {'FINISHED'}
        
class OPERATOR_Delete_Obstacle(Operator):
    bl_idname = "fd_roombuilder.delete_obstacle"
    bl_label = "Delete Obstacle" 
    bl_options = {'UNDO'}

    obstacle_bp_name = StringProperty(name="Obstacle BP Name",
                                      description="Pass the base point name to reposition an existing obstacle",
                                      default="")

    def execute(self, context):
        props = bpy.context.scene.fd_roombuilder
        wall = props.walls[props.wall_index]
        
        for index, obstacle in enumerate(wall.obstacles):
            if obstacle.bp_name == self.obstacle_bp_name:
                wall.obstacles.remove(index)
            
        obj_bp = context.scene.objects[self.obstacle_bp_name]
        
        utils.delete_object_and_children(obj_bp)
        return {'FINISHED'}

class OPERATOR_Hide_Plane(Operator):
    bl_idname = "fd_roombuilder.hide_plane"
    bl_label = "Hide Plane"
    
    object_name = StringProperty("Object Name",default="")
    
    def execute(self, context):
        if self.object_name in context.scene.objects:
            obj = context.scene.objects[self.object_name]
        else:
            obj = context.active_object

        children = utils.get_child_objects(obj)
        
        for child in children:
            child.hide = True
        
        obj.hide = True
        
        return {'FINISHED'}

class OPERATOR_Hide_Show_Wall(Operator):
    bl_idname = "fd_roombuilder.hide_show_wall"
    bl_label = "Hide Wall"
    
    wall_bp_name = StringProperty("Wall BP Name",default="")
    
    hide = BoolProperty("Hide",default=False)
    
    def execute(self, context):
        # This assumes that layer 1 is the layer you have everything on
        # Layer 2 is the layer we are placing the hidden objects on
        # This is kind of a hack there might be a better way to do this.
        # But we cannot hide objects on a wall becuase many hide properties
        # are driven my python drivers and after the scene recalcs hidden objects
        # are shown again.
        hide_layers = (False,True,False,False,False,False,False,False,False,False,
                       False,False,False,False,False,False,False,False,False,False)
        
        visible_layers = (True,False,False,False,False,False,False,False,False,False,
                          False,False,False,False,False,False,False,False,False,False)        
        
        obj = context.scene.objects[self.wall_bp_name]
        
        wall_bp = utils.get_wall_bp(obj)
        
        children = utils.get_child_objects(wall_bp)
        
        for child in children:
            if self.hide:
                child.layers = hide_layers
            else:
                child.layers = visible_layers
            
        wall_bp.hide = self.hide
        
        return {'FINISHED'}

class OPERATOR_Show_Plane(Operator):
    bl_idname = "fd_roombuilder.show_plane"
    bl_label = "Show Plane"
    
    object_name = StringProperty("Object Name",default="")
    
    def execute(self, context):
        if self.object_name in context.scene.objects:
            obj = context.scene.objects[self.object_name]
        else:
            obj = context.active_object

        children = utils.get_child_objects(obj)
        
        for child in children:
            if child.type != 'EMPTY':
                child.hide = False
        
        obj.hide = False
        
        return {'FINISHED'}

class OPERATOR_Select_Two_Points(Operator):
    bl_idname = "fd_roombuilder.select_two_points"
    bl_label = "Select Two Points"
    bl_options = {'UNDO'}
    
    #READONLY
    drawing_plane = None

    first_point = (0,0,0)
    second_point = (0,0,0)
    
    header_text = "Select the First Point"
    
    def cancel_drop(self,context,event):
        context.window.cursor_set('DEFAULT')
        utils.delete_obj_list([self.drawing_plane])
        return {'FINISHED'}
        
    def __del__(self):
        bpy.context.area.header_text_set()
        
    def event_is_cancel(self,event):
        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            return True
        elif event.type == 'ESC' and event.value == 'PRESS':
            return True
        else:
            return False
            
    def modal(self, context, event):
        context.window.cursor_set('PAINT_BRUSH')
        context.area.tag_redraw()
        selected_point, selected_obj = utils.get_selection_point(context,event,objects=[self.drawing_plane]) #Pass in Drawing Plane
        bpy.ops.object.select_all(action='DESELECT')
        if selected_obj:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                if self.first_point != (0,0,0):
                    self.second_point = selected_point
                    
                    distance = utils.calc_distance(self.first_point,self.second_point)
                    
                    diff = context.scene.fd_roombuilder.background_image_scale / distance

                    view = context.space_data
                    for bg in view.background_images:
                        bg_size = bg.size
                        bg.size = bg_size*diff
                    return self.cancel_drop(context,event)
                else:
                    self.first_point = selected_point

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
            
        if self.event_is_cancel(event):
            return self.cancel_drop(context,event)
            
        return {'RUNNING_MODAL'}
        
    def execute(self,context):
        self.first_point = (0,0,0)
        self.second_point = (0,0,0)
        bpy.ops.mesh.primitive_plane_add()
        plane = context.active_object
        plane.location = (0,0,0)
        self.drawing_plane = context.active_object
        self.drawing_plane.draw_type = 'WIRE'
        self.drawing_plane.dimensions = (100,100,1)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
def register():
    bpy.utils.register_class(Scene_Props)
    bpy.types.Scene.fd_roombuilder = PointerProperty(type = Scene_Props)
    bpy.utils.register_class(Object_Props)
    bpy.types.Object.fd_roombuilder = PointerProperty(type = Object_Props)
    
    bpy.utils.register_class(PANEL_Room_Builder)
    bpy.utils.register_class(FD_UL_walls)
    bpy.utils.register_class(FD_UL_obstacles)
    
    bpy.utils.register_class(OPERATOR_Hide_Show_Wall)
    bpy.utils.register_class(OPERATOR_Add_Obstacle)
    bpy.utils.register_class(OPERATOR_Add_Floor_Obstacle)
    bpy.utils.register_class(OPERATOR_Build_Room)
    bpy.utils.register_class(OPERATOR_Collect_Walls)
    bpy.utils.register_class(OPERATOR_Delete_Obstacle)
    bpy.utils.register_class(OPERATOR_Hide_Plane)
    bpy.utils.register_class(OPERATOR_Show_Plane)
    bpy.utils.register_class(OPERATOR_Select_Two_Points)

    carpet_coll = bpy.utils.previews.new()
    carpet_coll.my_previews_dir = ""
    carpet_coll.my_previews = ()

    wood_floor_coll = bpy.utils.previews.new()
    wood_floor_coll.my_previews_dir = ""
    wood_floor_coll.my_previews = ()

    tile_floor_coll = bpy.utils.previews.new()
    tile_floor_coll.my_previews_dir = ""
    tile_floor_coll.my_previews = ()

    paint_coll = bpy.utils.previews.new()
    paint_coll.my_previews_dir = ""
    paint_coll.my_previews = ()
    
    preview_collections["carpet"] = carpet_coll
    preview_collections["wood_floor"] = wood_floor_coll
    preview_collections["tile"] = tile_floor_coll
    preview_collections["paint"] = paint_coll

def unregister():
    bpy.utils.unregister_class(Scene_Props)
    del bpy.types.Scene.fd_roombuilder
    bpy.utils.unregister_class(Object_Props)
    del bpy.types.Object.fd_roombuilder
    
    bpy.utils.unregister_class(PANEL_Room_Builder)
    bpy.utils.unregister_class(FD_UL_walls)
    bpy.utils.unregister_class(FD_UL_obstacles)
    
    bpy.utils.unregister_class(OPERATOR_Hide_Show_Wall)
    bpy.utils.unregister_class(OPERATOR_Add_Obstacle)
    bpy.utils.unregister_class(OPERATOR_Add_Floor_Obstacle)
    bpy.utils.unregister_class(OPERATOR_Build_Room)
    bpy.utils.unregister_class(OPERATOR_Collect_Walls)
    bpy.utils.unregister_class(OPERATOR_Delete_Obstacle)
    bpy.utils.unregister_class(OPERATOR_Hide_Plane)
    bpy.utils.unregister_class(OPERATOR_Show_Plane)
    bpy.utils.unregister_class(OPERATOR_Select_Two_Points)
    
if __name__ == "__main__":
    register()
