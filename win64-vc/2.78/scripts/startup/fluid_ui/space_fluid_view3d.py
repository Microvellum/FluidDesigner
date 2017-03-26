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
import math
from bpy.types import Header, Menu, Panel
from bpy.app.translations import pgettext_iface as iface_ #for decimate modifier
from mv import utils, fd_types, unit

def draw_modifier(mod,layout,obj):
    
    def draw_show_expanded(mod,layout):
        if mod.show_expanded:
            layout.prop(mod,'show_expanded',text="",emboss=False)
        else:
            layout.prop(mod,'show_expanded',text="",emboss=False)
    
    def draw_apply_close(layout,mod_name):
        layout.operator('object.modifier_apply',text="",icon='EDIT_VEC',emboss=False).modifier = mod.name
        layout.operator('object.modifier_remove',text="",icon='PANEL_CLOSE',emboss=False).modifier = mod.name
    
    def draw_array_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_ARRAY')
        draw_apply_close(row,mod.name)
        
        if mod.show_expanded:
            box = col.box()
            box.prop(mod, "fit_type")
    
            if mod.fit_type == 'FIXED_COUNT':
                box.prop(mod, "count")
            elif mod.fit_type == 'FIT_LENGTH':
                box.prop(mod, "fit_length")
            elif mod.fit_type == 'FIT_CURVE':
                box.prop(mod, "curve")
    
            box.separator()
    
            split = box.split()
    
            col = split.column()
            col.prop(mod, "use_constant_offset")
            sub = col.column()
            sub.active = mod.use_constant_offset
            sub.prop(mod, "constant_offset_displace", text="")
    
            col.separator()
    
            col.prop(mod, "use_merge_vertices", text="Merge")
            sub = col.column()
            sub.active = mod.use_merge_vertices
            sub.prop(mod, "use_merge_vertices_cap", text="First Last")
            sub.prop(mod, "merge_threshold", text="Distance")
    
            col = split.column()
            col.prop(mod, "use_relative_offset")
            sub = col.column()
            sub.active = mod.use_relative_offset
            sub.prop(mod, "relative_offset_displace", text="")
    
            col.separator()
    
            col.prop(mod, "use_object_offset")
            sub = col.column()
            sub.active = mod.use_object_offset
            sub.prop(mod, "offset_object", text="")
    
            box.separator()
    
            box.prop(mod, "start_cap")
            box.prop(mod, "end_cap")
            
    def draw_bevel_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_BEVEL')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            split = box.split()
    
            col = split.column()
            col.prop(mod, "width")
            col.prop(mod, "segments")
            col.prop(mod, "profile")
    
            col = split.column()
            col.prop(mod, "use_only_vertices")
            col.prop(mod, "use_clamp_overlap")
    
            box.label(text="Limit Method:")
            box.row().prop(mod, "limit_method", expand=True)
            if mod.limit_method == 'ANGLE':
                box.prop(mod, "angle_limit")
            elif mod.limit_method == 'VGROUP':
                box.label(text="Vertex Group:")
                box.prop_search(mod, "vertex_group", obj, "vertex_groups", text="")
    
            box.label(text="Width Method:")
            box.row().prop(mod, "offset_type", expand=True)
    
    def draw_boolean_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_BOOLEAN')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            split = box.split()
    
            col = split.column()
            col.label(text="Operation:")
            col.prop(mod, "operation", text="")
    
            col = split.column()
            col.label(text="Object:")
            col.prop(mod, "object", text="")
    
    def draw_curve_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_CURVE')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            split = box.split()
    
            col = split.column()
            col.label(text="Object:")
            col.prop(mod, "object", text="")
            col = split.column()
            col.label(text="Vertex Group:")
            col.prop_search(mod, "vertex_group", obj, "vertex_groups", text="")
            box.label(text="Deformation Axis:")
            box.row().prop(mod, "deform_axis", expand=True)
    
    def draw_decimate_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_DECIM')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            decimate_type = mod.decimate_type
    
            row = box.row()
            row.prop(mod, "decimate_type", expand=True)
    
            if decimate_type == 'COLLAPSE':
                box.prop(mod, "ratio")
    
                split = box.split()
                row = split.row(align=True)
                row.prop_search(mod, "vertex_group", obj, "vertex_groups", text="")
                row.prop(mod, "invert_vertex_group", text="", icon='ARROW_LEFTRIGHT')
    
                split.prop(mod, "use_collapse_triangulate")
            elif decimate_type == 'UNSUBDIV':
                box.prop(mod, "iterations")
            else:  # decimate_type == 'DISSOLVE':
                box.prop(mod, "angle_limit")
                box.prop(mod, "use_dissolve_boundaries")
                box.label("Delimit:")
                row = box.row()
                row.prop(mod, "delimit")
    
            box.label(text=iface_("Face Count: %d") % mod.face_count, translate=False)
    
    def draw_edge_split_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_EDGESPLIT')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            split = box.split()
    
            col = split.column()
            col.prop(mod, "use_edge_angle", text="Edge Angle")
            sub = col.column()
            sub.active = mod.use_edge_angle
            sub.prop(mod, "split_angle")
    
            split.prop(mod, "use_edge_sharp", text="Sharp Edges")
    
    def draw_hook_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='HOOK')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            split = box.split()
    
            col = split.column()
            col.label(text="Object:")
            col.prop(mod, "object", text="")
            if mod.object and mod.object.type == 'ARMATURE':
                col.label(text="Bone:")
                col.prop_search(mod, "subtarget", mod.object.data, "bones", text="")
            col = split.column()
            col.label(text="Vertex Group:")
            col.prop_search(mod, "vertex_group", obj, "vertex_groups", text="")
    
            layout.separator()
    
            split = box.split()
    
#             col = split.column()
#             col.prop(mod, "falloff")
#             col.prop(mod, "force", slider=True)
    
            col = split.column()
            col.operator("object.hook_reset", text="Reset")
            col.operator("object.hook_recenter", text="Recenter")
    
            if obj.mode == 'EDIT':
                layout.separator()
                row = layout.row()
                row.operator("object.hook_select", text="Select")
                row.operator("object.hook_assign", text="Assign")
    
    def draw_mask_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_MASK')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            split = box.split()
    
            col = split.column()
            col.label(text="Mode:")
            col.prop(mod, "mode", text="")
    
            col = split.column()
            if mod.mode == 'ARMATURE':
                col.label(text="Armature:")
                col.prop(mod, "armature", text="")
            elif mod.mode == 'VERTEX_GROUP':
                col.label(text="Vertex Group:")
                row = col.row(align=True)
                row.prop_search(mod, "vertex_group", obj, "vertex_groups", text="")
                sub = row.row(align=True)
                sub.active = bool(mod.vertex_group)
                sub.prop(mod, "invert_vertex_group", text="", icon='ARROW_LEFTRIGHT')
    
    def draw_mirror_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_MIRROR')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            split = box.split(percentage=0.25)
    
            col = split.column()
            col.label(text="Axis:")
            col.prop(mod, "use_x")
            col.prop(mod, "use_y")
            col.prop(mod, "use_z")
    
            col = split.column()
            col.label(text="Options:")
            col.prop(mod, "use_mirror_merge", text="Merge")
            col.prop(mod, "use_clip", text="Clipping")
            col.prop(mod, "use_mirror_vertex_groups", text="Vertex Groups")
    
            col = split.column()
            col.label(text="Textures:")
            col.prop(mod, "use_mirror_u", text="U")
            col.prop(mod, "use_mirror_v", text="V")
    
            col = box.column()
    
            if mod.use_mirror_merge is True:
                col.prop(mod, "merge_threshold")
            col.label(text="Mirror Object:")
            col.prop(mod, "mirror_object", text="") 
    
    def draw_solidify_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_SOLIDIFY')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            split = box.split()
    
            col = split.column()
            col.prop(mod, "thickness")
            col.prop(mod, "thickness_clamp")
    
            col.separator()
    
            row = col.row(align=True)
            row.prop_search(mod, "vertex_group", obj, "vertex_groups", text="")
            sub = row.row(align=True)
            sub.active = bool(mod.vertex_group)
            sub.prop(mod, "invert_vertex_group", text="", icon='ARROW_LEFTRIGHT')
    
            sub = col.row()
            sub.active = bool(mod.vertex_group)
            sub.prop(mod, "thickness_vertex_group", text="Factor")
    
            col.label(text="Crease:")
            col.prop(mod, "edge_crease_inner", text="Inner")
            col.prop(mod, "edge_crease_outer", text="Outer")
            col.prop(mod, "edge_crease_rim", text="Rim")
    
            col = split.column()
    
            col.prop(mod, "offset")
            col.prop(mod, "use_flip_normals")
    
            col.prop(mod, "use_even_offset")
            col.prop(mod, "use_quality_normals")
            col.prop(mod, "use_rim")
    
            col.separator()
    
            col.label(text="Material Index Offset:")
    
            sub = col.column()
            row = sub.split(align=True, percentage=0.4)
            row.prop(mod, "material_offset", text="")
            row = row.row(align=True)
            row.active = mod.use_rim
            row.prop(mod, "material_offset_rim", text="Rim")
    
    def draw_subsurf_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_SUBSURF')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            box.row().prop(mod, "subdivision_type", expand=True)
    
            split = box.split()
            col = split.column()
            col.label(text="Subdivisions:")
            col.prop(mod, "levels", text="View")
            col.prop(mod, "render_levels", text="Render")
    
            col = split.column()
            col.label(text="Options:")
            col.prop(mod, "use_subsurf_uv")
            col.prop(mod, "show_only_control_edges")
    
    def draw_skin_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_SKIN')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            box.operator("object.skin_armature_create", text="Create Armature")
    
            box.separator()
    
            col = box.column(align=True)
            col.prop(mod, "branch_smoothing")
            col.prop(mod, "use_smooth_shade")
    
            split = box.split()
    
            col = split.column()
            col.label(text="Selected Vertices:")
            sub = col.column(align=True)
            sub.operator("object.skin_loose_mark_clear", text="Mark Loose").action = 'MARK'
            sub.operator("object.skin_loose_mark_clear", text="Clear Loose").action = 'CLEAR'
    
            sub = col.column()
            sub.operator("object.skin_root_mark", text="Mark Root")
            sub.operator("object.skin_radii_equalize", text="Equalize Radii")
    
            col = split.column()
            col.label(text="Symmetry Axes:")
            col.prop(mod, "use_x_symmetry")
            col.prop(mod, "use_y_symmetry")
            col.prop(mod, "use_z_symmetry")
    
    def draw_triangulate_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_TRIANGULATE')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            row = box.row()
    
            col = row.column()
            col.label(text="Quad Method:")
            col.prop(mod, "quad_method", text="")
            col = row.column()
            col.label(text="Ngon Method:")
            col.prop(mod, "ngon_method", text="")  
    
    def draw_simple_deform_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_SIMPLEDEFORM')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            box.row().prop(mod, "deform_method", expand=True)
    
            split = box.split()
    
            col = split.column()
            col.label(text="Vertex Group:")
            col.prop_search(mod, "vertex_group", obj, "vertex_groups", text="")
    
            split = box.split()
    
            col = split.column()
            col.label(text="Origin:")
            col.prop(mod, "origin", text="")
    
            if mod.deform_method in {'TAPER', 'STRETCH', 'TWIST'}:
                col.label(text="Lock:")
                col.prop(mod, "lock_x")
                col.prop(mod, "lock_y")
    
            col = split.column()
            col.label(text="Deform:")
            if mod.deform_method in {'TAPER', 'STRETCH'}:
                col.prop(mod, "factor")
            else:
                col.prop(mod, "angle")
            col.prop(mod, "limits", slider=True)
    
    def draw_wireframe_modifier(layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        draw_show_expanded(mod,row)
        row.prop(mod,'name',text="",icon='MOD_WIREFRAME')
        draw_apply_close(row,mod.name)
        if mod.show_expanded:
            box = col.box()
            has_vgroup = bool(mod.vertex_group)
    
            split = box.split()
    
            col = split.column()
            col.prop(mod, "thickness", text="Thickness")
    
            row = col.row(align=True)
            row.prop_search(mod, "vertex_group", obj, "vertex_groups", text="")
            sub = row.row(align=True)
            sub.active = has_vgroup
            sub.prop(mod, "invert_vertex_group", text="", icon='ARROW_LEFTRIGHT')
            row = col.row(align=True)
            row.active = has_vgroup
            row.prop(mod, "thickness_vertex_group", text="Factor")
    
            col.prop(mod, "use_crease", text="Crease Edges")
            col.prop(mod, "crease_weight", text="Crease Weight")
    
            col = split.column()
    
            col.prop(mod, "offset")
            col.prop(mod, "use_even_offset", text="Even Thickness")
            col.prop(mod, "use_relative_offset", text="Relative Thickness")
            col.prop(mod, "use_boundary", text="Boundary")
            col.prop(mod, "use_replace", text="Replace Original")
    
            col.prop(mod, "material_offset", text="Material Offset")                            
    
    if mod.type == 'ARRAY':
        draw_array_modifier(layout)
    elif mod.type == 'BEVEL':
        draw_bevel_modifier(layout)
    elif mod.type == 'BOOLEAN':
        draw_boolean_modifier(layout)
    elif mod.type == 'CURVE':
        draw_curve_modifier(layout)
    elif mod.type == 'DECIMATE':
        draw_decimate_modifier(layout)
    elif mod.type == 'EDGE_SPLIT':
        draw_edge_split_modifier(layout)
    elif mod.type == 'HOOK':
        draw_hook_modifier(layout)
    elif mod.type == 'MASK':
        draw_mask_modifier(layout)
    elif mod.type == 'MIRROR':
        draw_mirror_modifier(layout)
    elif mod.type == 'SOLIDIFY':
        draw_solidify_modifier(layout)
    elif mod.type == 'SUBSURF':
        draw_subsurf_modifier(layout)
    elif mod.type == 'SKIN':
        draw_skin_modifier(layout)
    elif mod.type == 'SIMPLE_DEFORM':
        draw_simple_deform_modifier(layout)
    elif mod.type == 'TRIANGULATE':
        draw_triangulate_modifier(layout)
    elif mod.type == 'WIREFRAME':
        draw_wireframe_modifier(layout)
    else:
        row = layout.row()
        row.label(mod.name + " view ")
    
def draw_constraint(con,layout,obj):

    def draw_show_expanded(con,layout):
        if con.show_expanded:
            layout.prop(con,'show_expanded',text="",emboss=False)
        else:
            layout.prop(con,'show_expanded',text="",emboss=False)

    def space_template(layout, con, target=True, owner=True):
        if target or owner:

            split = layout.split(percentage=0.2)

            split.label(text="Space:")
            row = split.row()

            if target:
                row.prop(con, "target_space", text="")

            if target and owner:
                row.label(icon='ARROW_LEFTRIGHT')

            if owner:
                row.prop(con, "owner_space", text="")

    def target_template(layout, con, subtargets=True):
        layout.prop(con, "target")  # XXX limiting settings for only 'curves' or some type of object

        if con.target and subtargets:
            if con.target.type == 'ARMATURE':
                layout.prop_search(con, "subtarget", con.target.data, "bones", text="Bone")

                if hasattr(con, "head_tail"):
                    row = layout.row()
                    row.label(text="Head/Tail:")
                    row.prop(con, "head_tail", text="")
            elif con.target.type in {'MESH', 'LATTICE'}:
                layout.prop_search(con, "subtarget", con.target, "vertex_groups", text="Vertex Group")

    def draw_copy_location_constraint(layout):
        col = layout.column(align=True)
        box = col.template_constraint(con)

        if con.show_expanded:
            target_template(box, con)
            
            split = box.split()
    
            col = split.column()
            col.prop(con, "use_x", text="X")
            sub = col.column()
            sub.active = con.use_x
            sub.prop(con, "invert_x", text="Invert")
    
            col = split.column()
            col.prop(con, "use_y", text="Y")
            sub = col.column()
            sub.active = con.use_y
            sub.prop(con, "invert_y", text="Invert")
    
            col = split.column()
            col.prop(con, "use_z", text="Z")
            sub = col.column()
            sub.active = con.use_z
            sub.prop(con, "invert_z", text="Invert")
    
            box.prop(con, "use_offset")
    
            space_template(box, con)
            
            if con.type not in {'RIGID_BODY_JOINT', 'NULL'}:
                box.prop(con, "influence")            
     
    def draw_copy_rotation_constraint(layout):
        col = layout.column(align=True)
        box = col.template_constraint(con)

        if con.show_expanded:        
            target_template(box, con)
    
            split = box.split()
    
            col = split.column()
            col.prop(con, "use_x", text="X")
            sub = col.column()
            sub.active = con.use_x
            sub.prop(con, "invert_x", text="Invert")
    
            col = split.column()
            col.prop(con, "use_y", text="Y")
            sub = col.column()
            sub.active = con.use_y
            sub.prop(con, "invert_y", text="Invert")
    
            col = split.column()
            col.prop(con, "use_z", text="Z")
            sub = col.column()
            sub.active = con.use_z
            sub.prop(con, "invert_z", text="Invert")
    
            box.prop(con, "use_offset")
    
            space_template(box, con) 
            
            if con.type not in {'RIGID_BODY_JOINT', 'NULL'}:
                box.prop(con, "influence")            
    
    def draw_copy_scale_constraint(layout):
        col = layout.column(align=True)
        box = col.template_constraint(con)

        if con.show_expanded:        
            target_template(box, con)
    
            row = box.row(align=True)
            row.prop(con, "use_x", text="X")
            row.prop(con, "use_y", text="Y")
            row.prop(con, "use_z", text="Z")
    
            box.prop(con, "use_offset")
    
            space_template(box, con)
            
            if con.type not in {'RIGID_BODY_JOINT', 'NULL'}:
                box.prop(con, "influence")  
    
    def draw_copy_transforms_constraint(layout):
        col = layout.column(align=True)
        box = col.template_constraint(con)

        if con.show_expanded:        
            target_template(box, con)

            space_template(box, con)
            
            if con.type not in {'RIGID_BODY_JOINT', 'NULL'}:
                box.prop(con, "influence")  
    
    def draw_limit_distance_constraint(layout):
        col = layout.column(align=True)
        box = col.template_constraint(con)

        if con.show_expanded:        
            target_template(box, con)
    
            col = box.column(align=True)
            col.prop(con, "distance")
            col.operator("constraint.limitdistance_reset")
    
            row = box.row()
            row.label(text="Clamp Region:")
            row.prop(con, "limit_mode", text="")
    
            row = box.row()
            row.prop(con, "use_transform_limit")
            row.label()
    
            space_template(box, con) 
            
            if con.type not in {'RIGID_BODY_JOINT', 'NULL'}:
                box.prop(con, "influence")  
    
    def draw_limit_location_constraint(layout):
        col = layout.column(align=True)
        box = col.template_constraint(con)

        if con.show_expanded:        
            split = box.split()
    
            col = split.column()
            col.prop(con, "use_min_x")
            sub = col.column()
            sub.active = con.use_min_x
            sub.prop(con, "min_x", text="")
            col.prop(con, "use_max_x")
            sub = col.column()
            sub.active = con.use_max_x
            sub.prop(con, "max_x", text="")
    
            col = split.column()
            col.prop(con, "use_min_y")
            sub = col.column()
            sub.active = con.use_min_y
            sub.prop(con, "min_y", text="")
            col.prop(con, "use_max_y")
            sub = col.column()
            sub.active = con.use_max_y
            sub.prop(con, "max_y", text="")
    
            col = split.column()
            col.prop(con, "use_min_z")
            sub = col.column()
            sub.active = con.use_min_z
            sub.prop(con, "min_z", text="")
            col.prop(con, "use_max_z")
            sub = col.column()
            sub.active = con.use_max_z
            sub.prop(con, "max_z", text="")
    
            row = box.row()
            row.prop(con, "use_transform_limit")
            row.label()
    
            row = box.row()
            row.label(text="Convert:")
            row.prop(con, "owner_space", text="")
            
            if con.type not in {'RIGID_BODY_JOINT', 'NULL'}:
                box.prop(con, "influence")  
    
    def draw_limit_rotation_constraint(layout):
        col = layout.column(align=True)
        box = col.template_constraint(con)

        if con.show_expanded:        
            split = box.split()
    
            col = split.column(align=True)
            col.prop(con, "use_limit_x")
            sub = col.column(align=True)
            sub.active = con.use_limit_x
            sub.prop(con, "min_x", text="Min")
            sub.prop(con, "max_x", text="Max")
    
            col = split.column(align=True)
            col.prop(con, "use_limit_y")
            sub = col.column(align=True)
            sub.active = con.use_limit_y
            sub.prop(con, "min_y", text="Min")
            sub.prop(con, "max_y", text="Max")
    
            col = split.column(align=True)
            col.prop(con, "use_limit_z")
            sub = col.column(align=True)
            sub.active = con.use_limit_z
            sub.prop(con, "min_z", text="Min")
            sub.prop(con, "max_z", text="Max")
    
            box.prop(con, "use_transform_limit")
    
            row = box.row()
            row.label(text="Convert:")
            row.prop(con, "owner_space", text="")
            
            if con.type not in {'RIGID_BODY_JOINT', 'NULL'}:
                box.prop(con, "influence")   
    
    def draw_limit_scale_constraint(layout):
        col = layout.column(align=True)
        box = col.template_constraint(con)

        if con.show_expanded:        
            split = box.split()
    
            col = split.column()
            col.prop(con, "use_min_x")
            sub = col.column()
            sub.active = con.use_min_x
            sub.prop(con, "min_x", text="")
            col.prop(con, "use_max_x")
            sub = col.column()
            sub.active = con.use_max_x
            sub.prop(con, "max_x", text="")
    
            col = split.column()
            col.prop(con, "use_min_y")
            sub = col.column()
            sub.active = con.use_min_y
            sub.prop(con, "min_y", text="")
            col.prop(con, "use_max_y")
            sub = col.column()
            sub.active = con.use_max_y
            sub.prop(con, "max_y", text="")
    
            col = split.column()
            col.prop(con, "use_min_z")
            sub = col.column()
            sub.active = con.use_min_z
            sub.prop(con, "min_z", text="")
            col.prop(con, "use_max_z")
            sub = col.column()
            sub.active = con.use_max_z
            sub.prop(con, "max_z", text="")
    
            row = box.row()
            row.prop(con, "use_transform_limit")
            row.label()
    
            row = box.row()
            row.label(text="Convert:")
            row.prop(con, "owner_space", text="")
            
            if con.type not in {'RIGID_BODY_JOINT', 'NULL'}:
                box.prop(con, "influence")                     
            
    if con.type == 'COPY_LOCATION':
        draw_copy_location_constraint(layout)
    elif con.type == 'COPY_ROTATION':
        draw_copy_rotation_constraint(layout)
    elif con.type == 'COPY_SCALE':
        draw_copy_scale_constraint(layout)
    elif con.type == 'COPY_TRANSFORMS':
        draw_copy_transforms_constraint(layout)
    elif con.type == 'LIMIT_DISTANCE':
        draw_limit_distance_constraint(layout)
    elif con.type == 'LIMIT_LOCATION':
        draw_limit_location_constraint(layout)
    elif con.type == 'LIMIT_ROTATION':
        draw_limit_rotation_constraint(layout)
    elif con.type == 'LIMIT_SCALE':
        draw_limit_scale_constraint(layout)
    else:
        row = layout.row()
        row.label(con.name + " view ")            

def draw_object_properties(layout,obj):
    ui = bpy.context.scene.mv.ui
    col = layout.column(align=True)
    box = col.box()
    row = box.row(align=True)
    draw_object_tabs(row,obj)
    box = col.box()
    col = box.column()
    if ui.interface_object_tabs == 'INFO':
        draw_object_info(col,obj)
    if ui.interface_object_tabs == 'DISPLAY':
        box = col.box()
        row = box.row()
        row.prop(obj,'draw_type',expand=True)
        box.prop(obj,'hide_select')
        box.prop(obj,'hide')
        box.prop(obj,'hide_render')
        box.prop(obj,'show_x_ray',icon='GHOST_ENABLED',text='Show X-Ray')
        box.prop(obj.cycles_visibility,'camera',icon='CAMERA_DATA',text='Show in Viewport Render')
    if ui.interface_object_tabs == 'MATERIAL':
        draw_object_materials(col,obj)
    if ui.interface_object_tabs == 'CONSTRAINTS':
        row = col.row()
        row.operator_menu_enum("fd_object.add_constraint", "type", icon='CONSTRAINT_DATA')
        row.operator("fd_object.collapse_all_constraints",text="",icon='FULLSCREEN_EXIT')
        for con in obj.constraints:
            draw_constraint(con,layout,obj)
    if ui.interface_object_tabs == 'MODIFIERS':
        row = col.row()
        row.operator_menu_enum("fd_object.add_modifier", "type", icon='MODIFIER')
        row.operator("fd_object.collapse_all_modifiers",text="",icon='FULLSCREEN_EXIT')
        for mod in obj.modifiers:
            draw_modifier(mod,layout,obj)
    if ui.interface_object_tabs == 'MESHDATA':
        utils.draw_object_data(col,obj)
    if ui.interface_object_tabs == 'CURVEDATA':
        utils.draw_object_data(col,obj)
    if ui.interface_object_tabs == 'TEXTDATA':
        utils.draw_object_data(col,obj)
    if ui.interface_object_tabs == 'EMPTYDATA':
        utils.draw_object_data(col,obj)
    if ui.interface_object_tabs == 'LIGHTDATA':
        utils.draw_object_data(col,obj)
    if ui.interface_object_tabs == 'CAMERADATA':
        utils.draw_object_data(col,obj)
    if ui.interface_object_tabs == 'DRIVERS':
        draw_object_drivers(col,obj)
    if ui.interface_object_tabs == 'TOKENS':
        if obj.type == 'MESH':
            col.prop(obj.mv,"use_sma")
            col.operator_menu_enum("cabinetlib.add_machine_token", "token_type", icon='SCULPTMODE_HLT')
            obj.mv.mp.draw_machine_tokens(col)

def draw_object_tabs(layout,obj):
    ui = bpy.context.scene.mv.ui
    if obj.type == 'MESH':
        layout.prop_enum(ui, "interface_object_tabs", 'INFO', icon='INFO', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'DISPLAY', icon='RESTRICT_VIEW_OFF', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'MATERIAL', icon='MATERIAL', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'CONSTRAINTS', icon='CONSTRAINT', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'MODIFIERS', icon='MODIFIER', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'MESHDATA', icon='MESH_DATA', text="")  
        layout.prop_enum(ui, "interface_object_tabs", 'DRIVERS', icon='AUTO', text="")   
        layout.prop_enum(ui, "interface_object_tabs", 'TOKENS', icon='SCULPTMODE_HLT', text="")   
    if obj.type == 'CURVE':
        layout.prop_enum(ui, "interface_object_tabs", 'INFO', icon='INFO', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'DISPLAY', icon='RESTRICT_VIEW_OFF', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'MATERIAL', icon='MATERIAL', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'CONSTRAINTS', icon='CONSTRAINT', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'MODIFIERS', icon='MODIFIER', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'CURVEDATA', icon='CURVE_DATA', text="")  
        layout.prop_enum(ui, "interface_object_tabs", 'DRIVERS', icon='AUTO', text="")  
    if obj.type == 'FONT':
        layout.prop_enum(ui, "interface_object_tabs", 'INFO', icon='INFO', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'DISPLAY', icon='RESTRICT_VIEW_OFF', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'MATERIAL', icon='MATERIAL', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'CONSTRAINTS', icon='CONSTRAINT', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'MODIFIERS', icon='MODIFIER', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'TEXTDATA', icon='FONT_DATA', text="")  
        layout.prop_enum(ui, "interface_object_tabs", 'DRIVERS', icon='AUTO', text="")  
    if obj.type == 'EMPTY':
        layout.prop_enum(ui, "interface_object_tabs", 'INFO', icon='INFO', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'DISPLAY', icon='RESTRICT_VIEW_OFF', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'CONSTRAINTS', icon='CONSTRAINT', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'EMPTYDATA', icon='EMPTY_DATA', text="")  
        layout.prop_enum(ui, "interface_object_tabs", 'DRIVERS', icon='AUTO', text="")  
    if obj.type == 'LAMP':
        layout.prop_enum(ui, "interface_object_tabs", 'INFO', icon='INFO', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'DISPLAY', icon='RESTRICT_VIEW_OFF', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'CONSTRAINTS', icon='CONSTRAINT', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'LIGHTDATA', icon='LAMP_SPOT', text="")  
        layout.prop_enum(ui, "interface_object_tabs", 'DRIVERS', icon='AUTO', text="")  
    if obj.type == 'CAMERA':
        layout.prop_enum(ui, "interface_object_tabs", 'INFO', icon='INFO', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'CONSTRAINTS', icon='CONSTRAINT', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'CAMERADATA', icon='OUTLINER_DATA_CAMERA', text="")  
        layout.prop_enum(ui, "interface_object_tabs", 'DRIVERS', icon='AUTO', text="")  
    if obj.type == 'ARMATURE':
        layout.prop_enum(ui, "interface_object_tabs", 'INFO', icon='INFO', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'DISPLAY', icon='RESTRICT_VIEW_OFF', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'CONSTRAINTS', icon='CONSTRAINT', text="") 
        layout.prop_enum(ui, "interface_object_tabs", 'DRIVERS', icon='AUTO', text="")  

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
    
def draw_object_materials(layout,obj):
    
    if obj.type in {'MESH','CURVE'}:
        spec_group = bpy.context.scene.mv.spec_groups[obj.cabinetlib.spec_group_index]
        layout.prop(obj.cabinetlib,'type_mesh')
        if obj.cabinetlib.type_mesh == 'CUTPART':
            row = layout.row(align=True)
            row.prop_search(obj.cabinetlib,"cutpart_name",spec_group,"cutparts",icon='MOD_UVPROJECT',text="")
            row = layout.row(align=True)
            row.prop_search(obj.cabinetlib,"edgepart_name",spec_group,"edgeparts",icon='EDGESEL',text="")

        if obj.cabinetlib.type_mesh == 'EDGEBANDING':
            row = layout.row(align=True)
            row.prop_search(obj.cabinetlib,"edgepart_name",spec_group,"edgeparts",icon='EDGESEL',text="")
            
        if obj.cabinetlib.type_mesh == 'SOLIDSTOCK':
            row = layout.row(align=True)
            row.prop(obj.mv,"solid_stock")

        row = layout.row()
        row.label('Material Slots:')
        row.operator("object.material_slot_add", icon='ZOOMIN', text="")
        row.operator("object.material_slot_remove", icon='ZOOMOUT', text="")
        row.operator("fd_material.assign_materials_from_pointers", icon='FILE_REFRESH', text="").object_name = obj.name
        row.operator('fd_general.open_new_window',text="",icon='NODETREE').space_type = 'NODE_EDITOR'
        layout.template_list("FD_UL_materials", "", obj, "material_slots", obj, "active_material_index", rows=1)
        layout.template_ID(obj, "active_material", new="material.new")
        slot = None
        if len(obj.material_slots) > 0:
            slot = obj.material_slots[obj.active_material_index]

        if slot:
#             col = layout.column(align=True)
#             col.template_list("FD_UL_materials", "", obj, "material_slots", obj, "active_material_index", rows=1)
            if len(obj.cabinetlib.material_slots) != len(obj.material_slots):
                if obj.cabinetlib.type_mesh != "NONE":
                    layout.operator("cabinetlib.sync_material_slots", icon='ZOOMIN', text="Sync").object_name = obj.name
            else:
                if spec_group:
                    mvslot = obj.cabinetlib.material_slots[obj.active_material_index]
                    box = layout.box()
                    box.prop(mvslot,"name")
                    box.prop_search(mvslot,"pointer_name",spec_group,"materials",icon='HAND')
                    box.label("Category Name: " + mvslot.category_name)
                    box.label("Material Name: " + mvslot.item_name)
        else:
            if obj.cabinetlib.type_mesh == 'CUTPART':
                layout.operator("cabinetlib.create_cutpart_material_slots", icon='MATERIAL',text="Setup Materials").object_name = obj.name

    if obj.mode == 'EDIT':
        row = layout.row(align=True)
        row.operator("object.material_slot_assign", text="Assign")
        row.operator("object.material_slot_select", text="Select")
        row.operator("object.material_slot_deselect", text="Deselect")

def draw_object_drivers(layout,obj):
    if obj:
        if not obj.animation_data:
            layout.label("There are no drivers assigned to the object",icon='ERROR')
        else:
            if len(obj.animation_data.drivers) == 0:
                layout.label("There are no drivers assigned to the object",icon='ERROR')
            for DR in obj.animation_data.drivers:
                box = layout.box()
                row = box.row()
                DriverName = DR.data_path
                if DriverName in {"location","rotation_euler","dimensions" ,"lock_scale",'lock_location','lock_rotation'}:
                    if DR.array_index == 0:
                        DriverName = DriverName + " X"
                    if DR.array_index == 1:
                        DriverName = DriverName + " Y"
                    if DR.array_index == 2:
                        DriverName = DriverName + " Z"                     
                value = eval('bpy.data.objects["' + obj.name + '"].' + DR.data_path)
                if type(value).__name__ == 'str':
                    row.label(DriverName + " = " + str(value),icon='AUTO')
                elif type(value).__name__ == 'float':
                    row.label(DriverName + " = " + str(unit.meter_to_active_unit(value)),icon='AUTO')
                elif type(value).__name__ == 'int':
                    row.label(DriverName + " = " + str(value),icon='AUTO')
                elif type(value).__name__ == 'bool':
                    row.label(DriverName + " = " + str(value),icon='AUTO')
                elif type(value).__name__ == 'bpy_prop_array':
                    row.label(DriverName + " = " + str(value[DR.array_index]),icon='AUTO')
                elif type(value).__name__ == 'Vector':
                    row.label(DriverName + " = " + str(unit.meter_to_active_unit(value[DR.array_index])),icon='AUTO')
                elif type(value).__name__ == 'Euler':
                    row.label(DriverName + " = " + str(unit.meter_to_active_unit(value[DR.array_index])),icon='AUTO')
                else:
                    row.label(DriverName + " = " + str(type(value)),icon='AUTO')

                props = row.operator("fd_driver.add_variable_to_object",text="",icon='ZOOMIN')
                props.object_name = obj.name
                props.data_path = DR.data_path
                props.array_index = DR.array_index
                obj_bp = utils.get_assembly_bp(obj)
                if obj_bp:
                    props = row.operator('fd_driver.get_vars_from_object',text="",icon='DRIVER')
                    props.object_name = obj.name
                    props.var_object_name = obj_bp.name
                    props.data_path = DR.data_path
                    props.array_index = DR.array_index
                utils.draw_driver_expression(box,DR)
#                 draw_add_variable_operators(box,obj.name,DR.data_path,DR.array_index)
                utils.draw_driver_variables(box,DR,obj.name)

class VIEW3D_HT_fluidheader(Header):
    bl_space_type = 'VIEW_3D'

    def draw(self, context):
        layout = self.layout

        if not context.scene.mv.ui.use_default_blender_interface:
            if context.scene.layers[0] != True:
                layout.label('Some layers are not visible',icon='ERROR')
                layout.operator('view3d.layers',text="Show All Layers").nr = 1
                
            obj = context.active_object
            toolsettings = context.tool_settings
    
            row = layout.row(align=True)
            row.separator()
            row.template_header()
            
            VIEW3D_MT_fd_menus.draw_collapsible(context, layout)
            
            #TODO Add object mode/edit mode toggle here
            #row = layout.row()
            
            if context.space_data.viewport_shade == 'WIREFRAME':
                layout.operator_menu_enum("fd_general.change_shademode","shade_mode",text="Wire Frame",icon='WIRE')
            if context.space_data.viewport_shade == 'SOLID':
                layout.operator_menu_enum("fd_general.change_shademode","shade_mode",text="Solid",icon='SOLID')
            if context.space_data.viewport_shade == 'MATERIAL':
                layout.operator_menu_enum("fd_general.change_shademode","shade_mode",text="Material",icon='MATERIAL')
            if context.space_data.viewport_shade == 'RENDERED':
                layout.operator_menu_enum("fd_general.change_shademode","shade_mode",text="Rendered",icon='SMOOTH')

            row = layout.row()
            row.prop(context.space_data,"pivot_point",text="")
            
            row = layout.row(align=True)
            row.prop(context.space_data,"show_manipulator",text="")
            row.prop(context.space_data,"transform_manipulators",text="")
            row.prop(context.space_data,"transform_orientation",text="")
        
            if not obj or obj.mode not in {'SCULPT', 'VERTEX_PAINT', 'WEIGHT_PAINT', 'TEXTURE_PAINT'}:
                snap_element = toolsettings.snap_element
                row = layout.row(align=True)
                row.prop(toolsettings, "use_snap", text="")
                row.prop(toolsettings, "snap_element", icon_only=True)
                if snap_element == 'INCREMENT':
                    row.prop(toolsettings, "use_snap_grid_absolute", text="")
                else:
                    row.prop(toolsettings, "snap_target", text="")
                    if obj:
                        if obj.mode in {'OBJECT', 'POSE'} and snap_element != 'VOLUME':
                            row.prop(toolsettings, "use_snap_align_rotation", text="")
                        elif obj.mode == 'EDIT':
                            row.prop(toolsettings, "use_snap_self", text="")
    
                if snap_element == 'VOLUME':
                    row.prop(toolsettings, "use_snap_peel_object", text="")
                elif snap_element == 'FACE':
                    row.prop(toolsettings, "use_snap_project", text="")
                    
            if obj:
                if obj.type in {'MESH','CURVE'}:
                    if obj.mode == 'EDIT':
                        layout.operator_menu_enum('fd_general.change_mode',"mode",icon='EDITMODE_HLT',text="Edit Mode")
                    else:
                        layout.operator_menu_enum('fd_general.change_mode',"mode",icon='OBJECT_DATAMODE',text="Object Mode")
                    
            row = layout.row(align=True)
            row.operator('view3d.ruler',text="Ruler")
            
            layout.operator('fd_general.create_screen_shot',text="",icon='SCENE')
            
class VIEW3D_MT_fd_menus(Menu):
    bl_space_type = 'VIEW3D_MT_editor_menus'
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        layout.menu("VIEW3D_MT_fluidview",icon='VIEWZOOM',text="   View   ")
        layout.menu("INFO_MT_fluidaddobject",icon='GREASEPENCIL',text="   Add   ")
        layout.menu("VIEW3D_MT_fluidtools",icon='MODIFIER',text="   Tools   ")
        layout.menu("VIEW3D_MT_selectiontools",icon='RESTRICT_SELECT_OFF',text="   Select   ")
        layout.menu("MENU_cursor_tools",icon='CURSOR',text="   Cursor   ")

class PANEL_object_properties(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = " "
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        if context.object:
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        obj = context.object
        layout.label(text="Object: " + obj.name,icon='OBJECT_DATA')

    def draw(self, context):
        layout = self.layout
        obj = context.object
        if obj:
            draw_object_properties(layout,obj)
                
class PANEL_assembly_properties(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = " "
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        obj_bp = utils.get_assembly_bp(context.object)
        if obj_bp:
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        obj_bp = utils.get_assembly_bp(context.object)
        if obj_bp:
            layout.label(text='Assembly: ' + obj_bp.mv.name_object,icon='OUTLINER_DATA_LATTICE')

    def draw(self, context):
        layout = self.layout
        obj_bp = utils.get_assembly_bp(context.object)
        if obj_bp:
            group = fd_types.Assembly(obj_bp)
            group.draw_properties(layout)

class PANEL_wall_properties(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = " "
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        obj_bp = utils.get_wall_bp(context.object)
        if obj_bp:
            return True
        else:
            return False

    def draw_header(self, context):
        layout = self.layout
        obj_bp = utils.get_wall_bp(context.object)
        if obj_bp:
            layout.label(text="Wall: " + obj_bp.name,icon='SNAP_PEEL_OBJECT')

    def draw(self, context):
        layout = self.layout
        obj_bp = utils.get_wall_bp(context.object)
        if obj_bp:
            group = fd_types.Assembly(obj_bp)
            box = layout.box()
            group.draw_transform(box)

class PANEL_product_info(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_label = " "
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        obj = utils.get_bp(context.object,'PRODUCT')
        if obj:
            return True
        else:
            return False
        
    def draw_header(self, context):
        layout = self.layout
        obj = utils.get_bp(context.object,'PRODUCT')
        if obj:
            layout.label("Product: " + obj.mv.name_object,icon='OUTLINER_OB_LATTICE')
    
    def draw(self, context):
        layout = self.layout
        obj_product_bp = utils.get_bp(context.object,'PRODUCT')
        if obj_product_bp:
            product = fd_types.Assembly(obj_product_bp)
            product.draw_properties(layout)

class PANEL_insert_info(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_label = " "
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        obj = utils.get_bp(context.object,'INSERT')
        if obj:
            return True
        else:
            return False
        
    def draw_header(self, context):
        layout = self.layout
        obj = utils.get_bp(context.object,'INSERT')
        if obj:
            layout.label("Insert: " + obj.mv.name_object,icon='STICKY_UVS_LOC')
    
    def draw(self, context):
        layout = self.layout
        obj_insert_bp = utils.get_bp(context.object,'INSERT')
        if obj_insert_bp:
            insert = fd_types.Assembly(obj_insert_bp)
            insert.draw_properties(layout)

class VIEW3D_MT_fluidview(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.toolshelf",icon='MENU_PANEL')
        layout.operator("view3d.properties",icon='MENU_PANEL')
        layout.separator()
        layout.operator("view3d.view_all",icon='VIEWZOOM')
        layout.operator("view3d.view_selected",text="Zoom To Selected",icon='ZOOM_SELECTED')

        layout.separator()

        layout.operator("view3d.navigate",icon='RESTRICT_VIEW_OFF',text="First Person View")
        
        layout.separator()

        layout.operator("view3d.viewnumpad", text="Camera",icon='CAMERA_DATA').type = 'CAMERA'
        layout.operator("view3d.viewnumpad", text="Top",icon='TRIA_DOWN').type = 'TOP'
        layout.operator("view3d.viewnumpad", text="Front",icon='TRIA_UP').type = 'FRONT'
        layout.operator("view3d.viewnumpad", text="Left",icon='TRIA_LEFT').type = 'LEFT'
        layout.operator("view3d.viewnumpad", text="Right",icon='TRIA_RIGHT').type = 'RIGHT'

        layout.separator()

        layout.operator("view3d.view_persportho",icon='SCENE')
        
        layout.operator_context = 'INVOKE_REGION_WIN'
        
        layout.separator()

        layout.operator("screen.area_dupli",icon='GHOST')
        layout.operator("screen.region_quadview",icon='VIEW3D_VEC')
        layout.operator("screen.screen_full_area",icon='FULLSCREEN_ENTER')
        
        layout.separator()
        
        layout.menu("MENU_viewport_settings",icon='SCRIPTPLUGINS',text="Viewport Settings")
        
class INFO_MT_fluidaddobject(Menu):
    bl_label = "Add Object"

    def draw(self, context):
        layout = self.layout

        # note, don't use 'EXEC_SCREEN' or operators wont get the 'v3d' context.

        # Note: was EXEC_AREA, but this context does not have the 'rv3d', which prevents
        #       "align_view" to work on first call (see [#32719]).
        layout.operator_context = 'INVOKE_REGION_WIN'
        
        layout.operator("fd_assembly.draw_wall",icon='SNAP_PEEL_OBJECT')
        layout.operator("fd_object.draw_floor_plane", icon='MESH_GRID')
        layout.separator()
        layout.operator("fd_assembly.add_assembly", icon='OUTLINER_DATA_LATTICE')

        layout.operator_context = 'EXEC_REGION_WIN'
        layout.separator()
        layout.menu("INFO_MT_mesh_add", icon='OUTLINER_OB_MESH')

        layout.menu("INFO_MT_curve_add", icon='OUTLINER_OB_CURVE')
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.text_add", text="Text", icon='OUTLINER_OB_FONT')
        layout.separator()

        layout.operator_menu_enum("object.empty_add", "type", text="Empty", icon='OUTLINER_OB_EMPTY')
        layout.separator()
        layout.operator("fd_object.add_camera",text="Camera",icon='OUTLINER_OB_CAMERA')
        layout.menu("MENU_add_lamp", icon='OUTLINER_OB_LAMP')
        layout.separator()
        layout.menu("MENU_add_grease_pencil", icon='GREASEPENCIL')
        layout.separator()
        
        if len(bpy.data.groups) > 10:
            layout.operator_context = 'INVOKE_REGION_WIN'
            layout.operator("object.group_instance_add", text="Group Instance...", icon='OUTLINER_OB_EMPTY')
        else:
            layout.operator_menu_enum("object.group_instance_add", "group", text="Group Instance", icon='OUTLINER_OB_EMPTY')

class VIEW3D_MT_fluidtools(Menu):
    bl_context = "objectmode"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_objecttools",icon='OBJECT_DATA')
        layout.menu("VIEW3D_MT_grouptools",icon='GROUP')
        layout.menu("VIEW3D_MT_assemblytools",icon='OUTLINER_DATA_LATTICE')
        layout.menu("VIEW3D_MT_producttools",icon='OUTLINER_OB_LATTICE')
        layout.menu("VIEW3D_MT_dimensiontools",icon='ALIGN')

class VIEW3D_MT_transformtools(Menu):
    bl_context = "objectmode"
    bl_label = "Transforms"

    def draw(self, context):
        layout = self.layout
        layout.operator("transform.translate",text='Grab',icon='MAN_TRANS')
        layout.operator("transform.rotate",icon='MAN_ROT')
        layout.operator("transform.resize",text="Scale",icon='MAN_SCALE')

class VIEW3D_MT_selectiontools(Menu):
    bl_context = "objectmode"
    bl_label = "Selection"

    def draw(self, context):
        layout = self.layout
        if context.active_object:
            if context.active_object.mode == 'OBJECT':
                layout.operator("object.select_all",text='Toggle De/Select',icon='MAN_TRANS')
            else:
                layout.operator("mesh.select_all",text='Toggle De/Select',icon='MAN_TRANS')
        else:
            layout.operator("object.select_all",text='Toggle De/Select',icon='MAN_TRANS')
        layout.operator("view3d.select_border",icon='BORDER_RECT')
        layout.operator("view3d.select_circle",icon='BORDER_LASSO')

class VIEW3D_MT_origintools(Menu):
    bl_context = "objectmode"
    bl_label = "Origin Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.origin_set",text="Origin to Cursor",icon='CURSOR').type = 'ORIGIN_CURSOR'
        layout.operator("object.origin_set",text="Origin to Geometry",icon='CLIPUV_HLT').type = 'ORIGIN_GEOMETRY'

class VIEW3D_MT_shadetools(Menu):
    bl_context = "objectmode"
    bl_label = "Object Shading"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.shade_smooth",icon='SOLID')
        layout.operator("object.shade_flat",icon='SNAP_FACE')

class VIEW3D_MT_objecttools(Menu):
    bl_context = "objectmode"
    bl_label = "Object Tools"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_transformtools",icon='MAN_TRANS')
        layout.separator()
        layout.operator("object.duplicate_move",icon='PASTEDOWN')
        layout.operator("object.convert", text="Convert to Mesh",icon='MOD_REMESH').target = 'MESH'
        layout.operator("object.join",icon='ROTATECENTER')
        layout.separator()
        layout.menu("VIEW3D_MT_origintools",icon='SPACE2')
        layout.separator()
        layout.menu("VIEW3D_MT_shadetools",icon='MOD_MULTIRES')
        layout.separator()
        layout.operator("object.delete",icon='X').use_global = False

class VIEW3D_MT_grouptools(Menu):
    bl_context = "objectmode"
    bl_label = "Group Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("fd_group.make_group_from_selection",icon='GROUP')
        layout.operator("fd_group.make_group_from_scene",icon='SCENE_DATA')
        
class VIEW3D_MT_producttools(Menu):
    bl_context = "objectmode"
    bl_label = "Product Tools"

    def draw(self, context):
        layout = self.layout
        product_bp = utils.get_bp(context.object,'PRODUCT')
        if product_bp:
            if product_bp.parent:
                if product_bp.parent.mv.type == 'BPWALL':
                    props = layout.operator('fd_general.place_product',text="Place Product",icon='LATTICE_DATA')
                    props.object_name = product_bp.name
            props = layout.operator('cabinetlib.make_static_product',text="Make Product Static",icon='MOD_DISPLACE')
            props.object_name = product_bp.name
            layout.operator('cabinetlib.select_product',text="Select All Product Objects",icon='MAN_TRANS').object_name = product_bp.name
            layout.separator()
            layout.operator("fd_assembly.copy_parent_assembly",text="Copy Selected Product",icon='PASTEDOWN')
            layout.operator("fd_assembly.select_parent_assemby_base_point",text="Select Product Base Point",icon='MAN_TRANS')
            layout.operator('fd_assembly.delete_selected_product',text="Delete Selected Product",icon='X').object_name = product_bp.name
        else:
            layout.label("A Product is not selected")
        
class VIEW3D_MT_assemblytools(Menu):
    bl_context = "objectmode"
    bl_label = "Assembly Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("fd_assembly.make_assembly_from_selected_object",icon='LATTICE_DATA')
        layout.operator("fd_assembly.make_group_from_selected_assembly",icon='GROUP')
        layout.separator()
        layout.operator("fd_assembly.copy_selected_assembly",icon='PASTEDOWN')
        layout.operator("fd_assembly.select_selected_assemby_base_point",icon='MAN_TRANS')
        layout.operator('fd_assembly.delete_selected_assembly',icon='X')
        
class VIEW3D_MT_extrusiontools(Menu):
    bl_context = "objectmode"
    bl_label = "Extrusion Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("fd_ops.extrude_curve", icon='IPO_CONSTANT')

class VIEW3D_MT_dimensiontools(Menu):
    bl_context = "objectmode"
    bl_label = "Dimension Tools"

    def draw(self, context):
        layout = self.layout
        
        layout.prop(context.window_manager.mv, "use_opengl_dimensions", text="Enable Dimensions")
        layout.operator("fd_general.toggle_dimension_handles",text="Show Dimension Handles",icon='OUTLINER_OB_EMPTY').turn_on = True
        layout.operator("fd_general.toggle_dimension_handles",text="Hide Dimension Handles",icon='OUTLINER_OB_EMPTY').turn_on = False
        layout.operator("fd_general.add_dimension", text="Add Dimension to Selected Assembly", icon='CURVE_NCURVE')
        layout.operator("fd_general.create_single_dimension", text="Add Single Dimension", icon='ZOOMIN')
        layout.separator()
        layout.operator("fd_general.dimension_interface", text="Dimension Options",icon='INFO')
        
class MENU_mode(Menu):
    bl_label = "Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("curve.handle_type_set",icon='CURVE_PATH')

class MENU_cursor_tools(Menu):
    bl_label = "Cursor Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("fd_general.set_cursor_location",icon='CURSOR',text="Set Cursor Location")
        layout.separator()
        layout.operator("view3d.snap_cursor_to_selected",icon='CURSOR')
        layout.operator("view3d.snap_cursor_to_center",icon='VIEW3D_VEC')
        layout.operator("view3d.snap_selected_to_cursor",icon='SPACE2')

class MENU_mesh_selection(Menu):
    bl_label = "Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.select_mode",text="Vertex Select",icon='VERTEXSEL').type='VERT'
        layout.operator("mesh.select_mode",text="Edge Select",icon='EDGESEL').type='EDGE'
        layout.operator("mesh.select_mode",text="Face Select",icon='FACESEL').type='FACE'

class MENU_mesh_display(Menu):
    bl_label = "Menu"

    def draw(self, context):
        mesh = context.active_object.data
        toolsettings = context.tool_settings
        obj = context.active_object
                
        layout = self.layout
        layout.label("Normals:")
        layout.prop(mesh, "show_normal_face", text="Show Face Normals", icon='FACESEL')
        layout.prop(toolsettings, "normal_size", text="Size")    
        layout.operator("mesh.normals_make_consistent", text="Recalculate")
        layout.operator("mesh.flip_normals", text="Flip Direction")
        layout.separator()    
        layout.label("Edge/Face Info:")
        layout.prop(obj.data,'show_extra_edge_length')
        layout.prop(obj.data,'show_extra_face_angle')
        layout.prop(obj.data,'show_extra_face_area')

class MENU_delete_selection(Menu):
    bl_label = "Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.delete",text="Delete Vertices",icon='VERTEXSEL').type='VERT'
        layout.operator("mesh.delete",text="Delete Edges",icon='EDGESEL').type='EDGE'
        layout.operator("mesh.delete",text="Delete Faces",icon='FACESEL').type='FACE'
        layout.operator("mesh.delete",text="Delete Only Faces",icon='FACESEL').type='ONLY_FACE'
        
class MENU_delete_selection_curve(Menu):
    bl_label = "Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("curve.delete",text="Delete Vertices",icon='VERTEXSEL').type='VERT'
        layout.operator("curve.delete",text="Delete Edges",icon='EDGESEL').type='SEGMENT'
        
class MENU_mesh_modeling_tools(Menu):
    bl_label = "Mesh Modeling Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.edit_mesh_extrude_move_normal",icon='CURVE_PATH')
        layout.operator("mesh.inset",icon='MOD_MESHDEFORM')
        layout.operator("mesh.knife_tool",icon='SCULPTMODE_HLT')
        layout.operator("mesh.subdivide",icon='OUTLINER_OB_LATTICE')
        layout.operator("mesh.loopcut_slide",icon='SNAP_EDGE')
        layout.operator("transform.edge_slide",icon='SNAP_EDGE')
        layout.operator("mesh.bevel",icon='MOD_BEVEL')
        layout.operator("mesh.edge_face_add",icon='SNAP_FACE')
        layout.operator("mesh.separate",icon='UV_ISLANDSEL').type = 'SELECTED'
        layout.operator("mesh.remove_doubles",icon='MOD_DISPLACE')
        
class MENU_vertex_groups(Menu):
    bl_label = "Vertex Groups"

    def draw(self, context):
        layout = self.layout
        for vgroup in context.active_object.vertex_groups:
            count = 0
            for vert in context.active_object.data.vertices:
                for group in vert.groups:
                    if group.group == vgroup.index:
                        count += 1
            layout.operator('fd_object.assign_verties_to_vertex_group',text="Assign to - " + vgroup.name + " (" + str(count) + ")").vertex_group_name = vgroup.name
        layout.separator()
        layout.operator('fd_assembly.connect_meshes_to_hooks_in_assembly',text='Connect Hooks',icon='HOOK').object_name = context.active_object.name
        layout.operator('fd_object.clear_vertex_groups',text='Clear All Vertex Group Assignments',icon='X').object_name = context.active_object.name
        
class MENU_right_click_menu_edit_mesh(Menu):
    bl_label = "Mesh Options"

    def draw(self, context):
        toolsettings = context.tool_settings
        obj = context.active_object
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.menu("MENU_mesh_selection",text="Selection Mode",icon='MAN_TRANS')
        layout.separator()
        layout.operator("fd_object.set_base_point",icon='SPACE2').object_name = obj.name
        layout.separator()
        layout.menu("MENU_mesh_modeling_tools",text="Modeling Tools",icon='EDITMODE_HLT')
        layout.separator()
        layout.operator('fd_object.unwrap_mesh',icon='ASSET_MANAGER',text="Unwrap Mesh")
        layout.operator('fd_general.open_new_window',icon='UV_FACESEL',text="View Texture Map").space_type = 'IMAGE_EDITOR'
        layout.separator()
        layout.prop_menu_enum(toolsettings, 'proportional_edit', "Proportional Editing", icon='META_ELLIPSOID')
        if toolsettings.proportional_edit != 'DISABLED':
            layout.prop_menu_enum(toolsettings, 'proportional_edit_falloff', "Proportional Editing Falloff", icon='SPHERECURVE')        
        layout.separator()
        layout.menu("MENU_mesh_display",text="Mesh Display Options",icon='MOD_UVPROJECT')
        layout.separator()
        if len(obj.vertex_groups) > 0:
            layout.menu("MENU_vertex_groups",text="Vertex Groups",icon='GROUP_VERTEX')
            layout.separator()
        layout.menu("MENU_delete_selection",text="Delete",icon='X')
        layout.separator()
        layout.operator("fd_object.toggle_edit_mode",text="Exit Edit Mode",icon='EDITMODE_HLT').object_name = obj.name
        
class MENU_handel_type(Menu):
    bl_label = "Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("curve.handle_type_set",icon='CURVE_PATH')
        
class MENU_right_click_menu_edit_curve(Menu):
    bl_label = "Curve Options"

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("curve.extrude_move",icon='CURVE_PATH')
        layout.operator("curve.switch_direction",icon='SCULPTMODE_HLT')
        layout.operator("curve.subdivide",icon='OUTLINER_OB_LATTICE')
        layout.prop(obj.data,'show_handles')
        layout.separator()
        layout.operator("curve.handle_type_set",icon='CURVE_PATH')
        layout.separator()
        layout.menu("MENU_delete_selection_curve",text="Delete",icon='X')
        layout.separator()
        layout.operator("fd_object.toggle_edit_mode",text="Exit Edit Mode",icon='EDITMODE_HLT').object_name = obj.name
        
class MENU_add_assembly_object(Menu):
    bl_label = "Add Assembly Object"
    
    def draw(self, context):
        layout = self.layout
        
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("fd_assembly.add_mesh_to_assembly",icon='OUTLINER_OB_MESH',text="Add Mesh")
        layout.operator("fd_assembly.add_empty_to_assembly",icon='OUTLINER_OB_EMPTY',text="Add Empty")
        layout.operator("fd_assembly.add_curve_to_assembly",icon='OUTLINER_OB_CURVE',text="Add Curve")
        layout.operator("fd_assembly.add_text_to_assembly",icon='OUTLINER_OB_FONT',text="Add Text")
        layout.separator()
        layout.operator("fd_assembly.add_text_to_assembly",icon='OUTLINER_DATA_LATTICE',text="Add Assembly From Library")
        layout.operator("fd_assembly.add_text_to_assembly",icon='OBJECT_DATA',text="Add Object From Library")

class MENU_add_grease_pencil(Menu):
    bl_label = "Grease Pencil"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("gpencil.draw", text="Draw",icon='GREASEPENCIL').mode = 'DRAW'
        layout.operator("gpencil.draw", text="Line",icon='ZOOMOUT').mode = 'DRAW_STRAIGHT'
        layout.operator("gpencil.draw", text="Poly",icon='IPO_CONSTANT').mode = 'DRAW_POLY'
        layout.operator("gpencil.draw", text="Erase",icon='X').mode = 'ERASER'
        layout.separator()
        layout.prop(context.tool_settings, "use_grease_pencil_sessions")
        
class MENU_viewport_settings(Menu):
    bl_label = "Viewport Settings"

    def draw(self, context):
        layout = self.layout
        if context.space_data.type == 'VIEW_3D':
            layout.prop(context.space_data,"show_floor",text="Show Grid Floor")
            layout.prop(context.space_data,"show_axis_x",text="Show X Axis")
            layout.prop(context.space_data,"show_axis_y",text="Show Y Axis")
            layout.prop(context.space_data,"show_axis_z",text="Show Z Axis")
            layout.prop(context.space_data,"show_only_render",text="Only Render")
            layout.prop(context.space_data,"show_relationship_lines",text="Show Relationship Lines")
            layout.prop(context.space_data,"grid_lines",text="Grid Lines")
            layout.prop(context.space_data,"grid_scale",text="Grid Scale")
            layout.separator()
            layout.prop(context.space_data,"lens",text="Viewport lens angle")
            layout.prop(context.space_data,"clip_start",text="Viewport Clipping Start")
            layout.prop(context.space_data,"clip_end",text="Viewport Clipping End")
            layout.separator()
            layout.prop(context.space_data,"lock_camera",text="Lock Camera to View")

class MENU_add_lamp(Menu):
    bl_label = "Lamp"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.lamp_add",icon='LAMP_POINT',text="Add Point Lamp").type = 'POINT'
        layout.operator("object.lamp_add",icon='LAMP_SUN',text="Add Sun Lamp").type = 'SUN'
        layout.operator("object.lamp_add",icon='LAMP_SPOT',text="Add Spot Lamp").type = 'SPOT'
        layout.operator("object.lamp_add",icon='LAMP_AREA',text="Add Area Lamp").type = 'AREA'
        layout.separator()
        layout.operator("fd_object.add_room_lamp",icon='LAMP_AREA',text="Add Room Lamp")

class MENU_active_group_options(Menu):
    bl_label = "Lamp"

    def draw(self, context):
        layout = self.layout
        obj_bp = utils.get_parent_assembly_bp(context.object)
        if obj_bp:
            for index, page in enumerate(obj_bp.mv.PromptPage.COL_MainTab):
                if page.type == 'VISIBLE':
                    props = layout.operator("fd_prompts.show_object_prompts",icon='SETTINGS',text=page.name)
                    props.object_bp_name = obj_bp.name
                    props.tab_name = page.name
                    props.index = index
                if page.type == 'CALCULATOR':
                    props = layout.operator("fd_prompts.show_object_prompts",icon='SETTINGS',text=page.name)
                    props.object_bp_name = obj_bp.name
                    props.tab_name = page.name
                    props.index = index

#------REGISTER
classes = [
           VIEW3D_HT_fluidheader,
           VIEW3D_MT_fd_menus,
           PANEL_object_properties,
           PANEL_assembly_properties,
           PANEL_wall_properties,
           PANEL_product_info,
           PANEL_insert_info,
           VIEW3D_MT_fluidview,
           VIEW3D_MT_fluidtools,
           VIEW3D_MT_grouptools,
           VIEW3D_MT_assemblytools,
           MENU_viewport_settings,
           INFO_MT_fluidaddobject,
           MENU_mode,
           MENU_cursor_tools,
           MENU_mesh_selection,
           MENU_delete_selection,
           MENU_delete_selection_curve,
           MENU_right_click_menu_edit_mesh,
           MENU_right_click_menu_edit_curve,
           MENU_add_assembly_object,
           MENU_mesh_modeling_tools,
           VIEW3D_MT_producttools,
           VIEW3D_MT_origintools,
           VIEW3D_MT_shadetools,
           VIEW3D_MT_objecttools,
           VIEW3D_MT_extrusiontools,
           VIEW3D_MT_dimensiontools,
           MENU_add_grease_pencil,
           VIEW3D_MT_transformtools,
           VIEW3D_MT_selectiontools,
           MENU_add_lamp,
           MENU_active_group_options,
#            MENU_active_group_prompts,
           MENU_mesh_display,
           MENU_vertex_groups
           ]

def register():

    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
