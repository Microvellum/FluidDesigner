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
    "name": "2D Views",
    "author": "Ryan Montes",
    "version": (1, 0, 0),
    "blender": (2, 7, 0),
    "location": "Tools Shelf",
    "description": "This add-on creates a UI to generate 2D Views",
    "warning": "",
    "wiki_url": "",
    "category": "Fluid Designer"
}

import bpy
from mv import utils, fd_types, unit
import math
import os
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import legal, inch, A4, landscape
from reportlab.platypus import Paragraph, Table, TableStyle, SimpleDocTemplate, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import reportlab.lib.colors as colors

class PANEL_2d_views(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"
    bl_label = "2D Views"
    bl_category = "Fluid Designer"
    bl_options = {'DEFAULT_CLOSED'}    
    
    @classmethod
    def poll(cls, context):
        return True
    
    def draw_header(self, context):
        layout = self.layout
        layout.label('',icon='ALIGN')
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        panel_box = layout.box()
        
        row = panel_box.row(align=True)
        row.scale_y = 1.3
        
        elv_scenes = []
        for scene in bpy.data.scenes:
            if scene.mv.elevation_scene:
                elv_scenes.append(scene)
                
        if len(elv_scenes) < 1:
            row.operator("2dviews.genereate_2d_views",text="Prepare 2D Views",icon='SCENE_DATA')
        else:
            row.operator("2dviews.genereate_2d_views",text="",icon='FILE_REFRESH')
            row.operator("2dviews.render_2d_views",text="Render Selected Scenes",icon='SCENE_DATA')
            row.menu('MENU_elevation_scene_options',text="",icon='DOWNARROW_HLT')
            panel_box.template_list("LIST_scenes", 
                                    " ", 
                                    bpy.data, 
                                    "scenes", 
                                    bpy.context.window_manager.mv, 
                                    "elevation_scene_index")
        image_views = context.window_manager.mv.image_views
        
        if len(image_views) > 0:
            panel_box.label("Image Views",icon='RENDERLAYERS')
            panel_box.template_list("LIST_2d_images"," ",context.window_manager.mv,"image_views",context.window_manager.mv,"image_view_index")
            
            panel_box.operator('2dviews.create_pdf',text="Create PDF",icon='FILE_BLANK')
            
class MENU_elevation_scene_options(bpy.types.Menu):
    bl_label = "Elevation Scene Options"

    def draw(self, context):
        layout = self.layout
        layout.operator("fd_general.select_all_elevation_scenes",text="Select All",icon='CHECKBOX_HLT').select_all = True
        layout.operator("fd_general.select_all_elevation_scenes",text="Deselect All",icon='CHECKBOX_DEHLT').select_all = False
        layout.separator()
        layout.operator('fd_general.project_info',text="View Project Info",icon='INFO')
        layout.operator("2dviews.create_new_view",text="Create Snap Shot",icon='SCENE')
        layout.separator()
        layout.operator("fd_scene.clear_2d_views",text="Clear All 2D Views",icon='X')

class LIST_scenes(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        
        if item.mv.plan_view_scene or item.mv.elevation_scene:
            layout.label(item.mv.name_scene,icon='RENDER_REGION')
            layout.prop(item.mv, 'elevation_selected', text="")
        else:
            layout.label(item.name,icon='SCENE_DATA')

class LIST_2d_images(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        show_cover_option = True
        for iv in data.image_views:
            if iv.use_as_cover_image:
                show_cover_option = False
        
        layout.label(item.name,icon='RENDER_RESULT')
        if item.use_as_cover_image or show_cover_option:
            layout.prop(item,"use_as_cover_image")
        layout.operator('2dviews.view_image',text="",icon='RESTRICT_VIEW_OFF',emboss=False).image_name = item.name
        layout.operator('2dviews.delete_image',text="",icon='X',emboss=False).image_name = item.name
        
class OPERATOR_genereate_2d_views(bpy.types.Operator):
    bl_idname = "2dviews.genereate_2d_views"    
    bl_label = "Generate 2d Views"
    bl_description = "Generates 2D Views"
    bl_options = {'UNDO'}

    ev_pad = bpy.props.FloatProperty(name="Elevation View Padding",
                                     default=0.75)
    
    pv_pad = bpy.props.FloatProperty(name="Plan View Padding",
                                     default=1.5)
    
    main_scene = None
    
    ignore_obj_list = []
    
    def get_world(self):
        if "2D Environment" in bpy.data.worlds:
            return bpy.data.worlds["2D Environment"]
        else:
            world = bpy.data.worlds.new("2D Environment")
            world.horizon_color = (1.0, 1.0, 1.0) 
            return world
    
    def create_camera(self,scene):
        camera_data = bpy.data.cameras.new(scene.name)
        camera_obj = bpy.data.objects.new(name=scene.name,object_data=camera_data)
        scene.objects.link(camera_obj)
        scene.camera = camera_obj                        
        camera_obj.data.type = 'ORTHO'
        scene.render.resolution_y = 1280
        
        scene.mv.ui.render_type_tabs = 'NPR'
         
        fs = scene.render.layers[0].freestyle_settings

        lineset = fs.linesets.new("Visible")
#         lineset.linestyle = lineset.linestyle
        
#         lineset = fs.linesets.new("Hidden")
#         lineset.linestyle = lineset.linestyle
#         lineset.visibility = 'HIDDEN'
#         lineset.edge_type_combination = 'AND'
#         lineset.select_edge_mark = True
#         lineset.select_crease = False
#         lineset.linestyle.name = "Dashed"
#         lineset.linestyle.use_dashed_line = True
#         lineset.linestyle.dash1 = 30
#         lineset.linestyle.dash2 = 30
#         lineset.linestyle.dash3 = 30
#         lineset.linestyle.gap1 = 30
#         lineset.linestyle.gap2 = 30
#         lineset.linestyle.gap3 = 30
        
        #TODO: Create a new world and assign it to the new scenes
        scene.world = self.get_world()
        scene.render.display_mode = 'NONE'
        scene.render.use_lock_interface = True        
        scene.render.image_settings.file_format = 'JPEG'
#         scene.mv.ui.render_type_tabs = 'NPR'
        
        return camera_obj
    
    def link_dims_to_scene(self, scene, obj_bp):
        for child in obj_bp.children:
            if child not in self.ignore_obj_list:
                if child.mv.type in ('VISDIM_A','VISDIM_B'):
                    scene.objects.link(child)
                if len(child.children) > 0:
                    self.link_dims_to_scene(scene, child)     
    
    def group_children(self,grp,obj):
        if obj.mv.type != 'CAGE' and obj not in self.ignore_obj_list:
            grp.objects.link(obj)   
        for child in obj.children:
            if len(child.children) > 0:
                self.group_children(grp,child)
            else:
                if not child.mv.is_wall_mesh:
                    if child.mv.type != 'CAGE' and obj not in self.ignore_obj_list:
                        grp.objects.link(child)  
        return grp
    
    def create_default_plan(self,obj_bp):
        pass
    
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
                
                dim = fd_types.Dimension()
                dim.parent(wall.obj_bp)
                dim.start_y(value = unit.inch(4) + wall.obj_y.location.y)
                dim.start_z(value = wall.obj_z.location.z + unit.inch(6))
                dim.end_x(value = wall.obj_x.location.x)  
                
                self.ignore_obj_list.append(dim.anchor)
                self.ignore_obj_list.append(dim.end_point)
  
                bpy.ops.object.text_add()
                text = context.active_object
                text.parent = wall.obj_bp
                text.location = (wall.obj_x.location.x/2,unit.inch(1.5),wall.obj_z.location.z)
                text.data.size = .1
                text.data.body = wall.obj_bp.mv.name_object
                text.data.align_x = 'CENTER'
                text.data.font = self.font
                 
                self.ignore_obj_list.append(dim.anchor)
                self.ignore_obj_list.append(dim.end_point)
                 
                obj_bps = wall.get_wall_groups()
                #Create Cubes for all products
                for obj_bp in obj_bps:
                    if obj_bp.mv.plan_draw_id != "":
                        eval('bpy.ops.' + obj_bp.mv.plan_draw_id + '(object_name=obj_bp.name)')
                    else:
                        assembly = fd_types.Assembly(obj_bp)
                        assembly_mesh = utils.create_cube_mesh(assembly.obj_bp.mv.name_object,
                                                            (assembly.obj_x.location.x,
                                                             assembly.obj_y.location.y,
                                                             assembly.obj_z.location.z))
                        assembly_mesh.parent = wall.obj_bp
                        assembly_mesh.location = assembly.obj_bp.location
                        assembly_mesh.rotation_euler = assembly.obj_bp.rotation_euler
                        assembly_mesh.mv.type = 'CAGE'
                        distance = unit.inch(14) if assembly.obj_bp.location.z > 1 else unit.inch(8)
                        distance += wall.obj_y.location.y
                        
                        dim = fd_types.Dimension()
                        dim.parent(assembly_mesh)
                        dim.start_y(value = distance)
                        dim.start_z(value = 0)
                        dim.end_x(value = assembly.obj_x.location.x)
                        
                        self.ignore_obj_list.append(dim.anchor)
                        self.ignore_obj_list.append(dim.end_point)
                        
                if wall and wall.get_wall_mesh():
                    wall.get_wall_mesh().select = True
                
        camera = self.create_camera(pv_scene)
        camera.rotation_euler.z = math.radians(-90.0)
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.ortho_scale += self.pv_pad
    
    def create_elv_view_scene(self,context,wall):
        bpy.ops.scene.new('INVOKE_DEFAULT',type='EMPTY')
        wall_group = bpy.data.groups.new(wall.obj_bp.mv.name_object)
        
        new_scene = context.scene
        new_scene.name = wall_group.name
        new_scene.mv.name_scene = wall.obj_bp.mv.name_object
        new_scene.mv.elevation_img_name = wall.obj_bp.name
        new_scene.mv.plan_view_scene = False
        new_scene.mv.elevation_scene = True
        
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
        
        bpy.ops.object.text_add()
        
        text = context.active_object
        text.parent = wall.obj_bp
        text.location.x = unit.inch(-2)
        text.location.z = unit.inch(-10)
        text.rotation_euler.x = math.radians(90)
        text.data.size = .1
        text.data.body = wall.obj_bp.mv.name_object
        text.data.align_x = 'RIGHT'
        text.data.font = self.font
        
        camera = self.create_camera(new_scene)
        camera.rotation_euler.x = math.radians(90.0)
        camera.rotation_euler.z = wall.obj_bp.rotation_euler.z   
        bpy.ops.object.select_all(action='DESELECT')
        wall_mesh.select = True
        bpy.ops.view3d.camera_to_view_selected()
        camera.data.ortho_scale += self.pv_pad
        
    def execute(self, context):
        context.window_manager.mv.use_opengl_dimensions = True
        
        self.font = utils.get_custom_font()
        
        bpy.ops.fd_scene.clear_2d_views()
        
        self.main_scene = context.scene
        context.scene.name = "_Main"
        self.create_plan_view_scene(context)
        
        for obj in self.main_scene.objects:
            if obj.mv.type == 'BPWALL':
                wall = fd_types.Wall(obj_bp = obj)
                if len(wall.get_wall_groups()) > 0:
                    self.create_elv_view_scene(context, wall)

        bpy.context.screen.scene = self.main_scene
        context.window_manager.mv.elevation_scene_index = 0
        return {'FINISHED'}

class OPERATOR_render_2d_views(bpy.types.Operator):
    bl_idname = "2dviews.render_2d_views"
    bl_label = "Render 2D Views"
    bl_description = "Renders 2d Scenes"
    
    def render_scene(self,context,scene):
        context.screen.scene = scene
        scene.mv.opengl_dim.gl_default_color = (0.1, 0.1, 0.1, 1.0)
        rd = scene.render
        rl = rd.layers.active
        freestyle_settings = rl.freestyle_settings
        
        rd.engine = 'BLENDER_RENDER'
        rd.use_freestyle = True
        rd.image_settings.file_format = 'JPEG'
        rd.line_thickness = 0.75
        rd.resolution_percentage = 100
        rl.use_pass_combined = False
        rl.use_pass_z = False
        freestyle_settings.crease_angle = 2.617994
        
#         file_format = scene.render.image_settings.file_format.lower()
        
        bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)

        while not os.path.exists(bpy.path.abspath(scene.render.filepath) + ".jpg"):
            time.sleep(0.1)
        
        img_result = utils.render_opengl(self,context)
        
        image_view = context.window_manager.mv.image_views.add()
        image_view.name = img_result.name
        image_view.image_name = img_result.name
        if scene.mv.plan_view_scene:
            image_view.is_plan_view = True
        
        if scene.mv.elevation_scene:
            image_view.is_elv_view = True
                
    def execute(self, context):
        file_path = bpy.app.tempdir if bpy.data.filepath == "" else os.path.dirname(bpy.data.filepath)
        
        # HACK: YOU HAVE TO SET THE CURRENT SCENE TO RENDER JPEG BECAUSE
        # OF REPORTS LAB AND BLENDER LIMITATIONS. :(
        rd = context.scene.render
        rd.image_settings.file_format = 'JPEG'
        
        current_scene = context.screen.scene
        
        for scene in bpy.data.scenes:
            if scene.mv.elevation_selected:
                self.render_scene(context,scene)
        
        context.screen.scene = current_scene
#                 context.scene.render.filepath = os.path.join(file_path,scene.name)
#                 bpy.ops.fd_scene.render_scene(write_still=False)
                 
#         for image in bpy.data.images:
#             if image.type == 'RENDER_RESULT':
#                 print(image.name)

        return {'FINISHED'}


class OPERATOR_view_image(bpy.types.Operator):
    bl_idname = "2dviews.view_image"
    bl_label = "View Image"
    bl_description = "Opens the image editor to view the 2D view."
    
    image_name = bpy.props.StringProperty(name="Object Name",
                                          description="This is the readable name of the object")
    
    def execute(self, context):
        bpy.ops.fd_general.open_new_window(space_type = 'IMAGE_EDITOR')
        
        image_view = context.window_manager.mv.image_views[self.image_name]
        
        print(image_view.name,image_view.image_name)
        
        areas = context.screen.areas
        
        for area in areas:
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    for image in bpy.data.images:
                        if image.name == image_view.image_name:
                            space.image = image
                    # This causing blender to crash :(
                    # TODO: Figure out how to view the entire image automatically
#                     override = {'area':area}
#                     bpy.ops.image.view_all(override,fit_view=True)

        return {'FINISHED'}
    
class OPERATOR_delete_image(bpy.types.Operator):
    bl_idname = "2dviews.delete_image"
    bl_label = "View Image"
    bl_description = "Delete the Image"
    
    image_name = bpy.props.StringProperty(name="Object Name",
                                          description="This is the readable name of the object")
    
    def execute(self, context):
        for index, iv in enumerate(context.window_manager.mv.image_views):
            if iv.name == self.image_name:
                context.window_manager.mv.image_views.remove(index)
        
        for image in bpy.data.images:
            if image.name == self.image_name:
                bpy.data.images.remove(image)
                break

        return {'FINISHED'}
    
class OPERATOR_create_new_view(bpy.types.Operator):
    bl_idname = "2dviews.create_new_view"
    bl_label = "Create New View"
    bl_description = "Renders 2d Scenes"

    def execute(self, context):
        bpy.ops.view3d.toolshelf()
        context.area.header_text_set(text="Position view then LEFT CLICK to take screen shot. ESC to Cancel.")
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        
    def get_file_path(self):
        counter = 1
        while os.path.exists(os.path.join(bpy.app.tempdir,"View " + str(counter) + ".png")):
            counter += 1
        return os.path.join(bpy.app.tempdir,"View " + str(counter) + ".png")
        
    def modal(self, context, event):
        context.area.tag_redraw()
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
            
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            context.area.header_text_set()
            bpy.ops.view3d.toolshelf()
            return {'FINISHED'}
            
        if event.type in {'LEFTMOUSE'}:
            context.area.header_text_set(" ")
            file_path = self.get_file_path()
            # The PDF writter can only use JPEG images
            context.scene.render.image_settings.file_format = 'JPEG'
            bpy.ops.screen.screenshot(filepath=file_path,full=False) 
            bpy.ops.view3d.toolshelf()
            context.area.header_text_set()
            image = bpy.data.images.load(file_path)
            image_view = context.window_manager.mv.image_views.add()
            image_view.name = os.path.splitext(image.name)[0]
            image_view.image_name = image.name
            
            return {'FINISHED'}
            
        return {'RUNNING_MODAL'}
        
class OPERATOR_create_pdf(bpy.types.Operator):
    bl_idname = "2dviews.create_pdf"
    bl_label = "Create PDF"
    bl_description = "This creates a pdf of all of the images"
    
    image_name = bpy.props.StringProperty(name="Object Name",
                                          description="This is the readable name of the object")
    
    def sort_images(self,images):
        image_list = []
        for image in images:
            image_list.append(image)
        
        imgs = []
        
        cover_image = None
        plan_view_image = None
        
        while len(image_list) > 0:
            img = image_list.pop()
            if img.use_as_cover_image:
                cover_image = img
            elif img.is_plan_view:
                plan_view_image = img
            else:
                imgs.append(img)
               
        file_images = []
                
        if cover_image:
            file_images.append(cover_image)
        
        if plan_view_image:
            file_images.append(plan_view_image)
        
        for img in imgs:
            file_images.append(img)
                
        return file_images

    def execute(self, context):
        pdf_images = []
        props = context.scene.mv
        width, height = landscape(legal)
        
        images = self.sort_images(context.window_manager.mv.image_views)
        for img in images:
            image = bpy.data.images[img.image_name]
            image.save_render(os.path.join(bpy.app.tempdir, image.name + ".jpg"))
            pdf_images.append(os.path.join(bpy.app.tempdir, image.name + ".jpg"))

        if bpy.data.filepath == "":
            file_path = bpy.app.tempdir
            room_name = "Unsaved"
        else:
            project_path = os.path.dirname(bpy.data.filepath)
            room_name, ext = os.path.splitext(os.path.basename(bpy.data.filepath))
            file_path = os.path.join(project_path,room_name)
            if not os.path.exists(file_path):
                os.makedirs(file_path)

        file_name = '2D Views.pdf'
        
        c = canvas.Canvas(os.path.join(file_path,file_name), pagesize=landscape(legal))
        logo = os.path.join(os.path.dirname(__file__),"logo.jpg")
        for img in pdf_images:
            #PICTURE
            c.drawImage(img,20,80,width=width-40, height=height-100, mask='auto',preserveAspectRatio=True)  
            #LOGO
            c.drawImage(logo,25,20,width=200, height=60, mask='auto',preserveAspectRatio=True) 
            #PICTURE BOX
            c.rect(20,80,width-40,height-100)
            #LOGO BOX
            c.rect(20,20,220,60)
            #COMMENT BOX
            c.setFont("Times-Roman",9)
            c.drawString(width-20-250+5, 67, "COMMENTS:")
            c.rect(width-20-248,20,248,60)
            #CLIENT
            c.drawString(245, 67, "CLIENT: " + props.client_name)
            c.rect(240,60,250,20)
            #PHONE
            c.drawString(245, 47, "PHONE: " + props.client_phone)
            c.rect(240,40,250,20)
            #EMAIL
            c.drawString(245, 27, "EMAIL: " + props.client_email)
            c.rect(240,20,250,20)                  
            #JOBNAME
            c.drawString(495, 67, "JOB NAME: " + props.job_name)
            c.rect(490,60,250,20)
            #JOBNAME
            c.drawString(495, 47, "ROOM: " + room_name)
            c.rect(490,40,250,20)
            #DRAWN BY
            c.drawString(495, 27, "DRAWN BY: " + props.designer_name)
            c.rect(490,20,250,20)
            c.showPage()
            
        c.save()

        #FIX FILE PATH To remove all double backslashes 
        fixed_file_path = os.path.normpath(file_path)

        if os.path.exists(os.path.join(fixed_file_path,file_name)):
            os.system('start "Title" /D "'+fixed_file_path+'" "' + file_name + '"')
        else:
            print('Cannot Find ' + os.path.join(fixed_file_path,file_name))
            
        return {'FINISHED'}
        
def register():
    bpy.utils.register_class(PANEL_2d_views)
    bpy.utils.register_class(LIST_scenes)
    bpy.utils.register_class(LIST_2d_images)
    bpy.utils.register_class(MENU_elevation_scene_options)
    bpy.utils.register_class(OPERATOR_genereate_2d_views)
    bpy.utils.register_class(OPERATOR_render_2d_views)
    bpy.utils.register_class(OPERATOR_view_image)
    bpy.utils.register_class(OPERATOR_delete_image)
    bpy.utils.register_class(OPERATOR_create_new_view)
    bpy.utils.register_class(OPERATOR_create_pdf)

def unregister():
    bpy.utils.unregister_class(PANEL_2d_views)
    bpy.utils.unregister_class(LIST_scenes)
    bpy.utils.unregister_class(LIST_2d_images)
    bpy.utils.unregister_class(MENU_elevation_scene_options)
    bpy.utils.unregister_class(OPERATOR_genereate_2d_views)
    bpy.utils.unregister_class(OPERATOR_render_2d_views)
    bpy.utils.unregister_class(OPERATOR_view_image)
    bpy.utils.unregister_class(OPERATOR_delete_image)
    bpy.utils.unregister_class(OPERATOR_create_new_view)
    bpy.utils.unregister_class(OPERATOR_create_pdf)

if __name__ == "__main__":
    register()
