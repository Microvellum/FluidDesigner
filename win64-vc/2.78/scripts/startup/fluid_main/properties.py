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

from bpy.types import PropertyGroup

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       BoolVectorProperty,
                       PointerProperty,
                       CollectionProperty,
                       EnumProperty)

from bpy.app.handlers import persistent
import os
import inspect
import bpy_extras.image_utils as img_utils
from mv import utils, fd_types, unit

enum_library_types = [('SCENE',"Scenes","Scenes"),
                      ('PRODUCT',"Products","Products"),
                      ('INSERT',"Inserts","Inserts"),
                      ('ASSEMBLY',"Assemblies","Assemblies"),
                      ('OBJECT',"Objects","Objects"),
                      ('MATERIAL',"Materials","Materials"),
                      ('WORLD',"Worlds","Worlds")]

enum_object_tabs = [('INFO',"","Show the Main Information"),
                    ('DISPLAY',"","Show Options for how the Object is Displayed"),
                    ('MATERIAL',"","Show the materials assign to the object"),
                    ('CONSTRAINTS',"","Show the constraints assigned to the object"),
                    ('MODIFIERS',"","Show the modifiers assigned to the object"),
                    ('MESHDATA',"","Show the Mesh Data Information"),
                    ('CURVEDATA',"","Show the Curve Data Information"),
                    ('TEXTDATA',"","Show the Text Data Information"),
                    ('EMPTYDATA',"","Show the Empty Data Information"),
                    ('LIGHTDATA',"","Show the Light Data Information"),
                    ('CAMERADATA',"","Show the Camera Data Information"),
                    ('DRIVERS',"","Show the Drivers assigned to the Object"),
                    ('TOKENS',"","Show the Tokens that are assigned to the Object")]

enum_group_tabs = [('INFO',"Main","Show the Main Info Page"),
                   ('SETTINGS',"","Show the Settings Page"),
                   ('PROMPTS',"Prompts","Show the Prompts Page"),
                   ('OBJECTS',"Objects","Show Objects"),
                   ('DRIVERS',"Drivers","Show the Driver Formulas")]

enum_calculator_type = [('XDIM',"X Dimension","Calculate the X Dimension"),
                        ('YDIM',"Y Dimension","Calculate the Y Dimension"),
                        ('ZDIM',"Z Dimension","Calculate the Z Dimension")]

enum_prompt_tab_types = [('VISIBLE',"Visible","Visible tabs are always displayed"),
                         ('HIDDEN',"Hidden","Hidden tabs are not shown in the right click menu"),
                         ('CALCULATOR',"Calculator","Use to calculate sizes of opening")]

enum_prompt_types = [('NUMBER',"Number","Number"),
                     ('QUANTITY',"Quantity","Quantity"),
                     ('COMBOBOX',"Combo Box","Combo Box"),
                     ('CHECKBOX',"Check Box","Check Box"),
                     ('TEXT',"Text","Text"),
                     ('DISTANCE',"Distance","Distance"),
                     ('ANGLE',"Angle","Angle"),
                     ('PERCENTAGE',"Percentage","Percentage"),
                     ('PRICE',"Price","Enter Price Prompt")]

enum_object_types = [('NONE',"None","None"),
                     ('CAGE',"CAGE","Cage used to represent the bounding area of an assembly"),
                     ('VPDIMX',"Visible Prompt X Dimension","Visible prompt control in the 3D viewport"),
                     ('VPDIMY',"Visible Prompt Y Dimension","Visible prompt control in the 3D viewport"),
                     ('VPDIMZ',"Visible Prompt Z Dimension","Visible prompt control in the 3D viewport"),
                     ('EMPTY1',"Empty1","EMPTY1"),
                     ('EMPTY2',"Empty2","EMPTY2"),
                     ('OBSTACLE',"Obstacle","Obstacle"),
                     ('BPWALL',"Wall Base Point","Parent object of a wall"),
                     ('BPASSEMBLY',"Base Point","Parent object of an assembly"),
                     ('VISDIM_A', "Visual Dimension A", "Anchor Point for Visual Dimension"),
                     ('VISDIM_B', "Visual Dimension B", "End Point for Visual Dimension")]

enum_group_drivers_tabs = [('LOC_X',"Location X","Location X"),
                           ('LOC_Y',"Location Y","Location Y"),
                           ('LOC_Z',"Location Z","Location Z"),
                           ('ROT_X',"Rotation X","Rotation X"),
                           ('ROT_Y',"Rotation Y","Rotation Y"),
                           ('ROT_Z',"Rotation Z","Rotation Z"),
                           ('DIM_X',"Dimension X","Dimension X"),
                           ('DIM_Y',"Dimension Y","Dimension Y"),
                           ('DIM_Z',"Dimension Z","Dimension Z"),
                           ('PROMPTS',"Prompts","Prompts")]

enum_render_type = [('PRR','Photo Realistic Render','Photo Realistic Render'),
                    ('NPR','Line Drawing','Non-Photo Realistic Render')]    


preview_collections = {}

def update_scene_index(self,context): 
    space_data = context.space_data
    v3d = space_data.region_3d
    scene = context.screen.scene
    
    if not scene.mv.elevation_scene:
        scene.mv.initial_view_location = v3d.view_location.copy()
        scene.mv.initial_view_rotation = v3d.view_rotation.copy()
        scene.mv.initial_shade_mode = space_data.viewport_shade
    
    context.screen.scene = bpy.data.scenes[self.elevation_scene_index]
    scene = context.screen.scene
    
    if scene.mv.elevation_scene or scene.mv.plan_view_scene:
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA' 
                space_data.viewport_shade = 'WIREFRAME'        
                
    else:
        v3d.view_location = scene.mv.initial_view_location
        v3d.view_rotation = scene.mv.initial_view_rotation  
        space_data.viewport_shade = scene.mv.initial_shade_mode
    
def update_text_editor_outline_index(self,context):    
    wm = context.window_manager.cabinetlib
    selected_member = wm.module_members[wm.module_members_index]
    
    for area in  bpy.data.screens['Default'].areas:
        if area.type == 'TEXT_EDITOR':
            for space in area.spaces:
                if space.type == 'TEXT_EDITOR':
                    space.find_text = "class " + selected_member.name + "("
                    space.use_find_wrap = True
  
    bpy.ops.text.find()
    
def assign_default_libraries(self,context):
    library_tabs = self.id_data.mv.ui.library_tabs
    lib_name = "" 

    if library_tabs == 'PRODUCT':
        for lib in context.window_manager.cabinetlib.lib_products:
            if os.path.exists(lib.lib_path):
                # This was causing errors if the library path wasn't created yet
#                 lib = context.window_manager.cabinetlib.lib_products[0]
                bpy.ops.fd_general.change_library(library_name=lib.name)
                return
    if library_tabs == 'INSERT':
        for lib in context.window_manager.cabinetlib.lib_inserts:
            if os.path.exists(lib.lib_path):
                bpy.ops.fd_general.change_library(library_name=lib.name)
                return
    if library_tabs == 'ASSEMBLY':
        path = utils.get_library_dir("assemblies")
        dirs = os.listdir(path)
        for directory in dirs:
            if os.path.exists(os.path.join(path,directory)):
                bpy.ops.fd_general.change_library(library_name=directory)
                return
    if library_tabs == 'OBJECT':
        path = utils.get_library_dir("objects")
        dirs = os.listdir(path)
        for directory in dirs:
            if os.path.exists(os.path.join(path,directory)):
                bpy.ops.fd_general.change_library(library_name=directory)
                return
    if library_tabs == 'MATERIAL':
        path = utils.get_library_dir("materials")
        dirs = os.listdir(path)
        for directory in dirs:
            if os.path.exists(os.path.join(path,directory)):
                bpy.ops.fd_general.change_library(library_name=directory)
                return
    if library_tabs == 'WORLD':
        path = utils.get_library_dir("worlds")
        dirs = os.listdir(path)
        for directory in dirs:
            if os.path.exists(os.path.join(path,directory)):
                bpy.ops.fd_general.change_library(library_name=directory)
                return

def update_library_paths(self,context):
    """ EVENT: saves an XML file to disk to store the path
               of the library data.
    """
    bpy.ops.fd_general.update_library_xml()

class library_items(PropertyGroup):
    is_selected = BoolProperty(name="Is Selected")
    name = StringProperty(name="Library Item Name")
    
bpy.utils.register_class(library_items)

class blend_file(PropertyGroup):
    is_selected = BoolProperty(name="Is Selected")
    items = CollectionProperty(name="Library Objects",type=library_items)
    show_expanded = BoolProperty(name="Show Objects",default=False)

bpy.utils.register_class(blend_file)

class fd_tab(bpy.types.PropertyGroup):
    type = EnumProperty(name="Type",items=enum_prompt_tab_types,default='VISIBLE')
    index = IntProperty(name="Index")
    calculator_type = EnumProperty(name="Calculator Type",items=enum_calculator_type)
    calculator_deduction = FloatProperty(name="Calculator Deduction",subtype='DISTANCE')
    
bpy.utils.register_class(fd_tab)
    
class fd_tab_col(bpy.types.PropertyGroup):
    col_tab = CollectionProperty(name="Collection Tab",type=fd_tab)
    index_tab = IntProperty(name="Index Tab",min=-1)

    def add_tab(self, name):
        tab = self.col_tab.add()
        tab.name = name
        tab.index = len(self.col_tab)
        return tab
    
    def delete_tab(self, index):
        for index, tab in enumerate(self.col_tab):
            if tab.index == index:
                self.col_tab.remove(index)

    def draw_tabs(self,layout):
        layout.template_list("FD_UL_specgroups", " ", self, "col_tab", self, "index_tab", rows=3)

bpy.utils.register_class(fd_tab_col)

#TODO: implement the standard collections or remove this and add to RNA Structure
class mvPrompt(bpy.types.PropertyGroup):
    Type = EnumProperty(name="Type",items=enum_prompt_types)
    TabIndex = IntProperty(name="Tab Index",default = 0)
    lock_value = BoolProperty(name="lock value")
    export = BoolProperty(name="Export",default = False,description="This determines if the prompt should be exported")
    equal = BoolProperty(name="Equal",description="Used in calculators to calculate remaining size")
    columns = IntProperty(name="Columns",description="Used for Combo Boxes to determine how many columns should be displayed",min=1,default=1)
    COL_EnumItem = bpy.props.CollectionProperty(name="COL_Enum Items",type=fd_tab)
    EnumIndex = IntProperty(name="EnumIndex")
    
    CheckBoxValue = BoolProperty(name="Check Box Values")
    
    QuantityValue = IntProperty(name="Quantity Value",min=0)
    
    TextValue = StringProperty(name="Text Value")
    
    NumberValue = FloatProperty(name="Number Value",precision=4,step=10)
    
    DistanceValue = FloatProperty(name="Distance Value",precision=4,step=10,subtype='DISTANCE')
    
    AngleValue = FloatProperty(name="Rotation Value",subtype='ANGLE')
    
    PriceValue = FloatProperty(name="Price Value",precision=2,step=10)
    
    PercentageValue = FloatProperty(name="Percentage Value",subtype='PERCENTAGE',min=0,max=1)
    
    TypeName = {'NUMBER':"NumberValue",'QUANTITY':"QuantityValue",'COMBOBOX':"EnumIndex",\
                'CHECKBOX':"CheckBoxValue",'TEXT':"TextValue",'DISTANCE':"DistanceValue",\
                'ANGLE':"AngleValue",'PERCENTAGE':"PercentageValue",'PRICE':"PriceValue"} #DELETE
    
    def draw_prompt(self,layout,allow_edit=False,text="",split_text=True):
        row = layout.row()
        if text != "":
            prompt_text = text
        else:
            prompt_text = self.name
        
        if split_text:
            row.label(prompt_text)
            prompt_text = ""
            
        if self.Type == 'NUMBER':
            if self.lock_value:
                row.label(str(self.NumberValue))
            else:
                row.prop(self,"NumberValue",text=prompt_text)
            
        if self.Type == 'ANGLE':
            if self.lock_value:
                row.label(str(self.AngleValue))
            else:
                row.prop(self,"AngleValue",text=prompt_text)
            
        if self.Type == 'DISTANCE':
            if self.lock_value:
                row.label(str(unit.meter_to_active_unit(self.DistanceValue)))
            else:
                row.prop(self,"DistanceValue",text=prompt_text)
            
        if self.Type == 'PERCENTAGE':
            if self.lock_value:
                row.label(str(self.PercentageValue))
            else:
                row.prop(self,"PercentageValue",text=prompt_text)
            
        if self.Type == 'PRICE':
            if self.lock_value:
                row.label(str(self.PriceValue))
            else:
                row.prop(self,"PriceValue",text=prompt_text)
            
        if self.Type == 'QUANTITY':
            if self.lock_value:
                row.label(str(self.QuantityValue))
            else:
                row.prop(self,"QuantityValue",text=prompt_text)
            
        if self.Type == 'COMBOBOX':
            if self.lock_value:
                row.label(self.COL_EnumItem[self.EnumIndex].name)
            else:
                if allow_edit:
                    prop = row.operator("fd_prompts.add_combo_box_option",icon='ZOOMIN',text="")
                    prop.prompt_name = self.name
                    prop.data_name = self.id_data.name
                col = layout.column()
                col.template_list("FD_UL_combobox"," ", self, "COL_EnumItem", self, "EnumIndex",rows=len(self.COL_EnumItem)/self.columns,type='GRID',columns=self.columns)
        
        if self.Type == 'CHECKBOX':
            if self.lock_value:
                row.label(str(self.CheckBoxValue))
            else:
                row.prop(self,"CheckBoxValue",text=prompt_text)
            
        if self.Type == 'SLIDER':
            row.prop(self,"NumberValue",text=prompt_text,slider=True)
            
        if self.Type == 'TEXT':
            row.prop(self,"TextValue",text=prompt_text)
            
        if allow_edit:
            props = row.operator("fd_prompts.show_prompt_properties",text="",icon='INFO')
            props.prompt_name = self.name
            props.data_name = self.id_data.name
            
            props = row.operator("fd_prompts.delete_prompt",icon='X',text="")
            props.prompt_name = self.name
            props.data_name = self.id_data.name
        
    def draw_calculation_prompt(self,layout,data,allow_edit=True):
        row = layout.row()
        row.label(self.name)
        if self.equal:
            row.label(str(unit.meter_to_active_unit(self.DistanceValue)))
            row.prop(self,'equal',text='')
        else:
            row.prop(self,'DistanceValue',text="")
            row.prop(self,'equal',text='')
        if allow_edit:
            props = row.operator("fd_prompts.delete_prompt",icon='X',text="")
            props.prompt_name = self.name
            props.data_name = data.name
        
    def add_enum_item(self,Name):
        Item = self.COL_EnumItem.add()
        Item.name = Name
        
    def Update(self):
        self.NumberValue = self.NumberValue
        self.TextValue = self.TextValue
        self.QuantityValue = self.QuantityValue
        self.CheckBoxValue = self.CheckBoxValue
        self.EnumIndex = self.EnumIndex
        
    def draw_prompt_properties(self,layout,object_name):
        row = layout.row()
        row.label(self.name)
        props = row.operator('fd_prompts.rename_prompt',text="Rename Prompt",icon='GREASEPENCIL')
        props.data_name = object_name
        props.old_name = self.name
        row = layout.row()
        row.label('Type:')
        row.prop(self,"Type",text="")
        typeUpdate = row.operator('fd_prompts.update_formulas_w_new_prompt_type',text="",icon='FILE_REFRESH')
        typeUpdate.data_name = object_name
        typeUpdate.name = self.name
        row = layout.row()
        row.label('Lock Value:')
        row.prop(self,"lock_value",text="")
        row = layout.row()
        row.label('Tab Index:')
        row.prop(self,"TabIndex",expand=True,text="")
        if self.Type == 'COMBOBOX':
            row = layout.row()
            row.label('Columns:')
            row.prop(self,"columns",text="")
        
    def show_prompt_tabs(self,layout):
        layout.template_list("FD_UL_prompttabs"," ", self, "COL_MainTab", self, "MainTabIndex",rows=len(self.COL_MainTab),type='DEFAULT')
        
    def value(self):
        if self.Type == 'NUMBER':
            return self.NumberValue
            
        if self.Type == 'ANGLE':
            return self.AngleValue
            
        if self.Type == 'DISTANCE':
            return self.DistanceValue
            
        if self.Type == 'PERCENTAGE':
            return self.PercentageValue
            
        if self.Type == 'PRICE':
            return self.PriceValue
            
        if self.Type == 'QUANTITY':
            return self.QuantityValue
            
        if self.Type == 'COMBOBOX':
            return self.COL_EnumItem[self.EnumIndex].name

        if self.Type == 'CHECKBOX':
            return self.CheckBoxValue
            
        if self.Type == 'SLIDER':
            return self.NumberValue
        
        if self.Type == 'TEXT':
            return self.TextValue
        
    def set_value(self,value):
        if self.Type == 'NUMBER':
            self.NumberValue = value
            
        if self.Type == 'ANGLE':
            self.AngleValue = value
            
        if self.Type == 'DISTANCE':
            self.DistanceValue = value
            
        if self.Type == 'PERCENTAGE':
            self.PercentageValue = value
            
        if self.Type == 'PRICE':
            self.PriceValue = value
            
        if self.Type == 'QUANTITY':
            self.QuantityValue = value
            
        if self.Type == 'COMBOBOX':
            for index, item in enumerate(self.COL_EnumItem):
                if item.name == value:
                    self.EnumIndex = index
                    break

        if self.Type == 'CHECKBOX':
            self.CheckBoxValue = value
            
        if self.Type == 'SLIDER':
            self.NumberValue = value
        
        if self.Type == 'TEXT':
            self.TextValue = value
        
    @property
    def prompt_type(self):
        if self.Type == 'NUMBER':
            return "NumberValue"
            
        if self.Type == 'ANGLE':
            return "AngleValue"
            
        if self.Type == 'DISTANCE':
            return "DistanceValue"
            
        if self.Type == 'PERCENTAGE':
            return "PercentageValue"
            
        if self.Type == 'PRICE':
            return "PriceValue"
            
        if self.Type == 'QUANTITY':
            return "QuantityValue"
            
        if self.Type == 'COMBOBOX':
            return "EnumIndex"

        if self.Type == 'CHECKBOX':
            return "CheckBoxValue"
            
        if self.Type == 'SLIDER':
            return "NumberValue"
        
        if self.Type == 'TEXT':
            return "TextValue"
        
    def get_type_as_string(self, prompt_type):
        return self.TypeName[prompt_type]
        
bpy.utils.register_class(mvPrompt)

#TODO: implement the standard collections or remove this and add to RNA Structure
class mvPromptPage(bpy.types.PropertyGroup):
    COL_MainTab = CollectionProperty(name="COL_MainTab",type=fd_tab)
    MainTabIndex = IntProperty(name="Main Tab Index")
    COL_Prompt = CollectionProperty(name="COL_Prompt",type=mvPrompt)
    PromptIndex = IntProperty(name="Prompt Index")

    def add_tab(self,Name,tab_type):
        Tab = self.COL_MainTab.add()
        Tab.name = Name
        Tab.type = tab_type
    
    def add_prompt(self,name,type,data_name):
        Prompt = self.COL_Prompt.add()
        Prompt.name = name
        Prompt.Type = type
        return Prompt

    def delete_prompt(self,Name):
        for index, Prompt in enumerate(self.COL_Prompt):
            if Prompt.name == Name:
                self.COL_Prompt.remove(index)

    def delete_selected_tab(self):
        self.COL_MainTab.remove(self.MainTabIndex)

    def rename_selected_tab(self,Name):
        self.COL_MainTab[self.MainTabIndex].name = Name

    #TODO: MAYBE DELETE THIS
    def Update(self):
        for Prompt in self.COL_Prompt:
            Prompt.Update()

    def run_calculators(self,obj):
        for index, tab in enumerate(obj.mv.PromptPage.COL_MainTab):
            if tab.type == 'CALCULATOR':
                bpy.ops.fd_prompts.run_calculator(data_name=obj.name,tab_index=index)

    def draw_prompts_list(self,layout):
        Rows = len(self.COL_Prompt)
        if Rows > 8:
            Rows = 10
        layout.template_list("MV_UL_default"," ", self, "COL_Prompt", self, "PromptIndex",rows=Rows)
        Prompt = self.COL_Prompt[self.PromptIndex]
        Prompt.DrawPrompt(layout,obj=None,AllowEdit=False)

    def draw_prompt_page(self,layout,allow_edit=True):

        row = layout.row(align=True)
        if allow_edit:
            props = row.operator("fd_prompts.add_main_tab",text="Add Tab",icon='SPLITSCREEN')
            props.data_name = self.id_data.name
        if len(self.COL_MainTab) > 0:
            if allow_edit:
                props1 = row.operator("fd_prompts.rename_main_tab",text="Rename Tab",icon='GREASEPENCIL')
                props1.data_name = self.id_data.name
                props2 = row.operator("fd_prompts.delete_main_tab",text="Delete Tab",icon='X')
                props2.data_name = self.id_data.name
                
            layout.template_list("FD_UL_prompttabs"," ", self, "COL_MainTab", self, "MainTabIndex",rows=len(self.COL_MainTab),type='DEFAULT')
            box = layout.box()
            tab = self.COL_MainTab[self.MainTabIndex]
            if tab.type == 'CALCULATOR':
                row = box.row()
                row.prop(tab,'calculator_type',text='')
                row.prop(tab,'calculator_deduction',text='Deduction')
                props3 = box.operator("fd_prompts.add_calculation_prompt",text="Add Calculation Variable",icon='UI')
                props3.data_name = self.id_data.name
                for prompt in self.COL_Prompt:
                    if prompt.TabIndex == self.MainTabIndex:
                        prompt.draw_calculation_prompt(box,self.id_data,allow_edit)
                props3 = box.operator("fd_prompts.run_calculator",text="Calculate")
                props3.data_name = self.id_data.name
                props3.tab_index = self.MainTabIndex
            else:
                props3 = box.operator("fd_prompts.add_prompt",text="Add Prompt",icon='UI')
                props3.data_name = self.id_data.name
                for prompt in self.COL_Prompt:
                    if prompt.TabIndex == self.MainTabIndex:
                        prompt.draw_prompt(box,allow_edit)

    def show_prompts(self,layout,obj,index,tab_name=""):
        #If the tab_name is passed in set the index
        if tab_name != "":
            for i, tab in enumerate(self.COL_MainTab):
                if tab.name == tab_name:
                    index = i
                    break
        
        tab = self.COL_MainTab[index]
        if tab.type == 'CALCULATOR':
            for Prompt in self.COL_Prompt:
                if Prompt.TabIndex == index:
                    row = layout.row()
                    row.label(Prompt.name)
                    row.prop(Prompt,"DistanceValue",text="")
                    row.prop(Prompt,"equal",text="")
        else:
            for Prompt in self.COL_Prompt:
                if Prompt.TabIndex == index:
                    Prompt.draw_prompt(layout,allow_edit=False)
                    
bpy.utils.register_class(mvPromptPage)

class opengl_dim(PropertyGroup):
    
    hide = BoolProperty(name="Hide Dimension",
                        description="Show/Hide Dimension",
                        default=False)
    
    gl_color = IntProperty(name="gl_color",
                           default=0,
                           description="Color for the measure")  
    
    gl_default_color = FloatVectorProperty(name="Default color",
                                           description="Default Color",
                                           default=(0.8, 0.8, 0.8, 1.0),
                                           min=0.1,
                                           max=1,
                                           subtype='COLOR',
                                           size=4)
    
    gl_width = IntProperty(name='gl_width', 
                           min=1, 
                           max=10, 
                           default=1,
                           description='line width')
    
    show_label = BoolProperty(name="Show Label",
                              description="Display label for this measure",
                              default=True)    
    
    gl_label = StringProperty(name="Label", 
                              maxlen=256,
                              description="Short description (use | for line break)")
    
    gl_font_size = IntProperty(name="Text Size",
                               description="Text size",
                               default=14, 
                               min=6, 
                               max=150)
    
    gl_text_x = IntProperty(name="gl_text_x",
                            description="Change font position in X axis",
                            default=0, 
                            min=-3000, 
                            max=3000)
    
    gl_text_y = IntProperty(name="gl_text_y",
                            description="Change font position in Y axis",
                            default=0, 
                            min=-3000, 
                            max=3000)
    
    gl_arrow_type = EnumProperty(items=(('99', "--", "No arrow"),
                                       ('1', "Line", "The point of the arrow are lines"),
                                       ('2', "Triangle", "The point of the arrow is triangle"),
                                       ('3', "TShape", "The point of the arrow is a T")),
                                 name="Arrow Type",
                                 description="Dimension Arrow Type",
                                 default='99')
     
    gl_arrow_size = IntProperty(name="Size",
                                description="Arrow size",
                                default=15, 
                                min=6, 
                                max=500)
    
    gl_dim_units = EnumProperty(items=(('1', "Automatic", "Use scene units"),
                                       ('2', "Meters", ""),
                                       ('3', "Centimeters", ""),
                                       ('4', "Milimiters", ""),
                                       ('5', "Feet", ""),
                                       ('6', "Inches", "")),
                                name="Units",
                                default="6",
                                description="Units")        
        
    gl_precision = IntProperty(name='Precision', 
                               min=0, 
                               max=5, 
                               default=2,
                               description="Number of decimal precision")        

bpy.utils.register_class(opengl_dim)

class Project_Property(PropertyGroup):
    value = StringProperty(name="Value")
    global_variable_name = StringProperty(name="Global Variable Name")
    project_wizard_variable_name = StringProperty(name="Project Wizard Variable Name")
    specification_group_name = StringProperty(name="Specification Group Name")
    
bpy.utils.register_class(Project_Property)
    
class Library_Pointer(PropertyGroup):
    index = IntProperty(name="Index")
    
    type = EnumProperty(name="Type",
                        items=[('NONE',"None","No Grain"),
                               ('WIDTH',"Width","Width"),
                               ('LENGTH',"Length","Length")])
    
    library_name = StringProperty(name="Library Name")
    
    category_name = StringProperty(name="Category Name")
    
    item_name = StringProperty(name="Item Name")
    
    pointer_value = FloatProperty(name="Pointer Value")
    
    assign_material = BoolProperty(name="Assign Material",default=False) # USED TO Assign Materials with drag and drop
    
bpy.utils.register_class(Library_Pointer)

class Material_Slot(PropertyGroup):
    index = IntProperty(name="Index")
    material_path = StringProperty(name="Material Path")
    pointer_name = StringProperty(name="Pointer Name")
    library_name = StringProperty(name="Library Name")
    category_name = StringProperty(name="Category Name")
    item_name = StringProperty(name="Item Name")

bpy.utils.register_class(Material_Slot)

class List_Library_Item(PropertyGroup):
    """ Class to put products, inserts, and parts in a list view
        Used to show all library items
    """
    bp_name = StringProperty(name='BP Name')
    class_name = StringProperty(name='Class Name')
    library_name = StringProperty(name='Library Name')
    category_name = StringProperty(name='Category Name')
    selected = BoolProperty(name="Selected")
    has_thumbnail = BoolProperty(name="Has Thumbnail")
    has_file = BoolProperty(name="Has File")

bpy.utils.register_class(List_Library_Item)

class List_Library(PropertyGroup):
    package_name = StringProperty(name="Package Name")
    module_name = StringProperty(name="Module Name")
    lib_path = StringProperty(name="Library Path")
    items = CollectionProperty(name="Items",type=List_Library_Item)
    index = IntProperty(name="Index")

bpy.utils.register_class(List_Library)    

class List_Module_Members(bpy.types.PropertyGroup):
    index = bpy.props.IntProperty(name="Index")      
    
bpy.utils.register_class(List_Module_Members)       
    
class Library_Package(bpy.types.PropertyGroup):
    lib_path = StringProperty(name="Library Path",subtype='DIR_PATH',update=update_library_paths)
    enabled = BoolProperty(name="Enabled",default=True,update=update_library_paths)
    
bpy.utils.register_class(Library_Package)       
    
class Category(PropertyGroup):
    path = StringProperty(name="Path")

bpy.utils.register_class(Category)
    
class Library(PropertyGroup):
    path = StringProperty(name="Path")
    
    lib_type = EnumProperty(name="Library Type",items=[('NONE','None','None'),
                                                       ('PRODUCT','Product','Product'),
                                                       ('INSERT','Insert','Insert')],
                            default='NONE')

    categories = CollectionProperty(name="Categories",
                                    type=Category)
    
    active_category_name = StringProperty(name="Active Category Name")
    
    def get_categories(self):
        for lib_cat in self.categories:
            self.categories.remove(0)
            
        if not os.path.exists(self.path): os.makedirs(self.path)
        
        categories = os.listdir(self.path)
        for category in categories:
            category_path = os.path.join(self.path,category)
            if os.path.isdir(category_path):
                lib_category = self.categories.add()
                lib_category.name = category
                lib_category.path = category_path
                
        if len(self.categories) > 0:
            self.active_category_name = self.categories[0].name

    def get_active_category(self):
        return self.categories[self.active_category_name]

bpy.utils.register_class(Library)
    
class Cutpart(PropertyGroup):
    thickness = FloatProperty(name="Thickness",
                              unit='LENGTH',
                              precision=5)
    
    mv_pointer_name = StringProperty(name="MV Pointer Name")
    
    core = StringProperty(name="Core")
    
    top = StringProperty(name="Top")
    
    bottom = StringProperty(name="Bottom")
    
bpy.utils.register_class(Cutpart)
    
class Edgepart(PropertyGroup):
    thickness = FloatProperty(name="Thickness",
                              unit='LENGTH',
                              precision=5)
    
    mv_pointer_name = StringProperty(name="MV Pointer Name")
    
    material = StringProperty(name="Material")
    
bpy.utils.register_class(Edgepart)
    
class Sheet_Size(PropertyGroup):
    width = FloatProperty(name="Width",
                          unit='LENGTH')
    
    length = FloatProperty(name="Length",
                           unit='LENGTH')
    
    leading_length_trim = FloatProperty(name="Leading Length Trim",
                                        unit='LENGTH')
    
    leading_width_trim = FloatProperty(name="Leading Width Trim",
                                       unit='LENGTH')
    
    trailing_length_trim = FloatProperty(name="Trailing Length Trim",
                                         unit='LENGTH')
    
    trailing_width_trim = FloatProperty(name="Trailing Width Trim",
                                        unit='LENGTH')
    
    comment = StringProperty(name="Comment")

bpy.utils.register_class(Sheet_Size)

class Sheet_Stock(PropertyGroup):
    thickness = FloatProperty(name="Thickness",
                              unit='LENGTH')
    
    grain = EnumProperty(name="Grain",
                         items=[('NONE',"None","No Grain"),
                                ('WIDTH',"Width","Width"),
                                ('LENGTH',"Length","Length")])
    
    core_material = StringProperty(name="Core Material")
    
    top_material = StringProperty(name="Top Material")
    
    bottom_material = StringProperty(name="Bottom Material")
    
    size_index = IntProperty(name="Size Index")
    
    sizes = CollectionProperty(name="Sizes",
                                type=Sheet_Size)
    
bpy.utils.register_class(Sheet_Stock)

class Specification_Group(PropertyGroup):
    
    materials = CollectionProperty(name="Materials",
                                   type=Library_Pointer)
    
    material_index = IntProperty(name="Material Index",
                                 default=0)
    
    cutparts = CollectionProperty(name="Cutparts",
                                  type=Cutpart)
    
    cutpart_index = IntProperty(name="Cutpart Index",
                                default=0)

    edgeparts = CollectionProperty(name="Edgeparts",
                                  type=Edgepart)
    
    edgepart_index = IntProperty(name="Edgepart Index",
                                default=0)

    def draw_materials(self,layout):
        box = layout.box()
        row = box.row()
        col = row.column(align=True)
        col.template_list("LIST_material_pointers", " ", self, "materials", self, "material_index")
        
        if self.material_index + 1 <= len(self.materials):
            pointer = self.materials[self.material_index]
            box = col.box()
            box.label('Library Name: ' + pointer.library_name,icon='EXTERNAL_DATA')
            box.label('Category Name: ' + pointer.category_name,icon='FILE_FOLDER')
            box.label('Material Name: ' + pointer.item_name,icon='MATERIAL')
            
    def draw_cutparts(self,layout):
        box = layout.box()
        row = box.row()
        
        col = row.column(align=True)
        col.template_list("LIST_cutparts", " ", self, "cutparts", self, "cutpart_index")
        if self.cutpart_index + 1 <= len(self.cutparts):
            pointer = self.cutparts[self.cutpart_index]
            box = col.box()
            box.prop_search(pointer,'core',self,'materials',text="Core Material",icon='FULLSCREEN')
            box.prop_search(pointer,'top',self,'materials',text="Top Material (Exterior)",icon='NODE')
            box.prop_search(pointer,'bottom',self,'materials',text="Bottom Material (Interior)",icon='NODE_SEL')

    def draw_edgeparts(self,layout):
        box = layout.box()
        row = box.row()
        
        col = row.column(align=True)
        col.template_list("LIST_edgeparts", " ", self, "edgeparts", self, "edgepart_index")
        if self.edgepart_index + 1 <= len(self.edgeparts):
            pointer = self.edgeparts[self.edgepart_index]
            box = col.box()
            box.prop_search(pointer,'material',self,'materials',text="Material",icon='EDGESEL')

bpy.utils.register_class(Specification_Group)

class Machine_Token(PropertyGroup):
    show_expanded = BoolProperty(name="Show Expanded",default=False)
    type_token = EnumProperty(name="Mesh Type",
                              items=[('NONE',"None","None"),
                                     ('CORNERNOTCH',"CORNERNOTCH","CORNERNOTCH"),
                                     ('CHAMFER',"CHAMFER","CHAMFER"),
                                     ('CONST',"CONST","CONST"),
                                     ('HOLES',"HOLES","HOLES"),
                                     ('SHLF',"SHLF","SHLF"),
                                     ('SHELF',"SHELF","SHELF"),
                                     ('SHELFSTD',"SHELFSTD","SHELFSTD"),
                                     ('DADO',"DADO","DADO"),
                                     ('SAW',"SAW","SAW"),
                                     ('SLIDE',"SLIDE","SLIDE"),
                                     ('CAMLOCK',"CAMLOCK","CAMLOCK"),
                                     ('MITER',"MITER","MITER"),
                                     ('BORE',"BORE","BORE")],
                              description="Select the Machine Token Type.",
                              default='NONE')
    
    face = EnumProperty(name="Face",
                        items=[('1',"1","1"),
                               ('2',"2","2"),
                               ('3',"3","3"),
                               ('4',"4","4"),
                               ('5',"5","5"),
                               ('6',"6","6")],
                        description="Select the face to assign the machine token to.",
                        default='1')
    
    edge = EnumProperty(name="Edge",
                        items=[('1',"1","1"),
                               ('2',"2","2"),
                               ('3',"3","3"),
                               ('4',"4","4"),
                               ('5',"5","5"),
                               ('6',"6","6"),
                               ('7',"7","7"),
                               ('8',"8","8")],
                        description="Select the edge to assign the machine token to.",
                        default='1')
    
    dim_to_first_const_hole = FloatProperty(name="Dim to First Construction Hole",unit='LENGTH')
    dim_to_last_const_hole = FloatProperty(name="Dim to Last Construction Hole",unit='LENGTH')
    edge_bore_depth = FloatProperty(name="Edge Bore Depth",unit='LENGTH')
    edge_bore_dia = FloatProperty(name="Edge Bore Diameter")
    face_bore_depth = FloatProperty(name="Face Bore Depth",unit='LENGTH')
    face_bore_depth_2 = FloatProperty(name="Face Bore Depth 2")
    face_bore_dia = FloatProperty(name="Face Bore Diameter")
    face_bore_dia_2 = FloatProperty(name="Face Bore Diameter 2")
    drill_from_opposite_side = BoolProperty(name="Drill From Opposite Side")
    second_hole_at_32mm = BoolProperty(name="Second Hole at 32mm")
    distance_between_holes = FloatProperty(name="Distance Between Holes",unit='LENGTH')
    hole_locations = FloatVectorProperty(name="Hole Locations",size=15,unit='LENGTH')
    z_value = FloatProperty(name="Z Value",unit='LENGTH')
    
    dim_in_x = FloatProperty(name="Dim In X",unit='LENGTH')
    dim_in_y = FloatProperty(name="Dim In Y",unit='LENGTH')
    dim_in_z = FloatProperty(name="Dim In Z",unit='LENGTH')
    end_dim_in_x = FloatProperty(name="End Dim In X",unit='LENGTH')
    end_dim_in_y = FloatProperty(name="End Dim In Y",unit='LENGTH')
    associative_dia = FloatProperty(name="Associative Diameter")
    associative_depth = FloatProperty(name="Associative Depth",unit='LENGTH')
    
    lead_in = FloatProperty(name="Lead In",unit='LENGTH')
    lead_out = FloatProperty(name="Lead Out",unit='LENGTH')
    reverse_direction = BoolProperty(name="Reverse Direction")
    beginning_depth = FloatProperty(name="Beginning Depth",unit='LENGTH')
    double_pass = FloatProperty(name="Double Pass",unit='LENGTH')
    lock_joint = FloatProperty(name="Lock Joint",unit='LENGTH')
    panel_penetration = FloatProperty(name="Panel Penetration",unit='LENGTH')
    
    backset = FloatProperty(name="Backset",unit='LENGTH')
    cam_face = EnumProperty(name="Cam Face",
                            items=[('5',"5","5"),
                                   ('6',"6","6")],
                            description="The face number the cam is assigned to.",
                            default='5')
    
    angle = FloatProperty(name="Angle",unit='ROTATION')
    
    tool_number = StringProperty(name="Tool Number")
    tongue_tool_number = StringProperty(name="Tongue Tool Number")
    
    space_from_bottom = FloatProperty(name="Space From Bottom",unit='LENGTH')
    space_from_top = FloatProperty(name="Space From Top",unit='LENGTH')
    dim_to_first_row = FloatProperty(name="Dim to First Row",unit='LENGTH')
    dim_to_second_row = FloatProperty(name="Dim to Second Row",unit='LENGTH')
    shelf_hole_spacing = FloatProperty(name="Shelf Hole Spacing",unit='LENGTH')
    shelf_clip_gap = FloatProperty(name="Shelf Clip Gap",unit='LENGTH')
    
    #SLIDE
    dim_from_drawer_bottom = FloatProperty(name="Dimension from Drawer Bottom",unit='LENGTH')
    dim_to_first_hole = FloatProperty(name="Dimension to First Hole",unit='LENGTH')
    dim_to_second_hole = FloatProperty(name="Dimension to Second Hole",unit='LENGTH')
    dim_to_third_hole = FloatProperty(name="Dimension to Third Hole",unit='LENGTH')
    dim_to_fourth_hole = FloatProperty(name="Dimension to Fourth Hole",unit='LENGTH')
    dim_to_fifth_hole = FloatProperty(name="Dimension to Fifth Hole",unit='LENGTH')
    drawer_slide_clearance = FloatProperty(name="Drawer Slide Clearance",unit='LENGTH')
    
    def get_hole_locations(self):
        locations = ""
        for x in range(0,len(self.hole_locations) - 1):
            if self.hole_locations[x] != 0:
                locations += str(unit.meter_to_active_unit(self.hole_locations[x])) + ","
        return locations[:-1] #Remove last comma
    
    def create_parameter_dictionary(self):
        param_dict = {}
        if self.type_token == 'CONST':
            param_dict['Par1'] = str(unit.meter_to_active_unit(self.dim_to_first_const_hole))
            param_dict['Par2'] = str(unit.meter_to_active_unit(self.dim_to_last_const_hole))
            param_dict['Par3'] = str(unit.meter_to_active_unit(self.edge_bore_depth))
            param_dict['Par4'] = str(self.edge_bore_dia)
            param_dict['Par5'] = str(unit.meter_to_active_unit(self.face_bore_depth))
            param_dict['Par6'] = str(self.face_bore_dia)
            param_dict['Par7'] = "1" if self.drill_from_opposite_side else "0"
            param_dict['Par8'] = "1" if self.second_hole_at_32mm else "0"
            param_dict['Par9'] = str(unit.meter_to_active_unit(self.distance_between_holes))
            
        if self.type_token == 'HOLES':
            param_dict['Par1'] = self.get_hole_locations()
            param_dict['Par2'] = str(self.edge_bore_dia)
            param_dict['Par3'] = str(unit.meter_to_active_unit(self.edge_bore_depth))
            param_dict['Par4'] = ""
            param_dict['Par5'] = str(unit.meter_to_active_unit(self.face_bore_depth))
            param_dict['Par6'] = str(self.face_bore_dia)
            param_dict['Par7'] = str(self.drill_from_opposite_side)
            param_dict['Par8'] = str(self.second_hole_at_32mm)
            param_dict['Par9'] = str(unit.meter_to_active_unit(self.distance_between_holes))
            
        if self.type_token in {'DADO','SAW'}:
            param_dict['Par1'] = str(unit.meter_to_active_unit(self.lead_in))
            param_dict['Par2'] = "1" if self.reverse_direction else "0"
            param_dict['Par3'] = str(unit.meter_to_active_unit(self.beginning_depth))
            param_dict['Par4'] = str(unit.meter_to_active_unit(self.lead_out))
            param_dict['Par5'] = str(unit.meter_to_active_unit(self.double_pass))
            param_dict['Par6'] = "0"
            param_dict['Par7'] = str(self.tool_number)
            param_dict['Par8'] = str(unit.meter_to_active_unit(self.panel_penetration))
            param_dict['Par9'] = str(self.tongue_tool_number)
            
        if self.type_token == 'CAMLOCK':
            param_dict['Par1'] = self.get_hole_locations()
            param_dict['Par2'] = str(self.edge_bore_dia)
            param_dict['Par3'] = str(unit.meter_to_active_unit(self.edge_bore_depth))
            param_dict['Par4'] = str(unit.meter_to_active_unit(self.z_value)) if self.z_value != 0 else ""
            param_dict['Par5'] = str(self.face_bore_dia) + "," + str(self.face_bore_dia_2)
            param_dict['Par6'] = str(unit.meter_to_active_unit(self.face_bore_depth)) + "," + str(unit.meter_to_active_unit(self.face_bore_depth_2))
            param_dict['Par7'] = str(unit.meter_to_active_unit(self.backset))
            param_dict['Par8'] = str(self.cam_face)
            param_dict['Par9'] = "1" if self.drill_from_opposite_side else "0"
            
        if self.type_token in {'SHLF','SHELF','SHELFSTD'}:
            param_dict['Par1'] = str(unit.meter_to_active_unit(self.space_from_bottom))
            param_dict['Par2'] = str(unit.meter_to_active_unit(self.dim_to_first_row))
            param_dict['Par3'] = str(unit.meter_to_active_unit(self.face_bore_depth))
            param_dict['Par4'] = str(unit.meter_to_active_unit(self.space_from_top))
            param_dict['Par5'] = str(unit.meter_to_active_unit(self.dim_to_second_row))
            param_dict['Par6'] = str(self.face_bore_dia)
            param_dict['Par7'] = str(unit.meter_to_active_unit(self.shelf_hole_spacing))
            param_dict['Par8'] = str(unit.meter_to_active_unit(self.shelf_clip_gap))
            param_dict['Par9'] = "1" if self.reverse_direction else "0"
            
        if self.type_token == 'BORE':
            param_dict['Par1'] = str(unit.meter_to_active_unit(self.dim_in_x))
            param_dict['Par2'] = str(unit.meter_to_active_unit(self.dim_in_y))
            param_dict['Par3'] = str(unit.meter_to_active_unit(self.dim_in_z))
            param_dict['Par4'] = str(self.face_bore_dia)
            param_dict['Par5'] = str(unit.meter_to_active_unit(self.end_dim_in_x))
            param_dict['Par6'] = str(unit.meter_to_active_unit(self.end_dim_in_y))
            param_dict['Par7'] = str(unit.meter_to_active_unit(self.distance_between_holes))
            param_dict['Par8'] = str(self.associative_dia)
            param_dict['Par9'] = str(unit.meter_to_active_unit(self.associative_depth))
            
        if self.type_token == 'CORNERNOTCH':
            param_dict['Par1'] = str(unit.meter_to_active_unit(self.dim_in_x))
            param_dict['Par2'] = str(unit.meter_to_active_unit(self.dim_in_y))
            param_dict['Par3'] = str(unit.meter_to_active_unit(self.dim_in_z))
            param_dict['Par4'] = str(unit.meter_to_active_unit(self.lead_in))
            param_dict['Par5'] = ""
            param_dict['Par6'] = ""
            param_dict['Par7'] = str(self.tool_number)
            param_dict['Par8'] = ""
            param_dict['Par9'] = ""
            
        if self.type_token == 'CHAMFER':
            param_dict['Par1'] = str(unit.meter_to_active_unit(self.dim_in_x))
            param_dict['Par2'] = str(unit.meter_to_active_unit(self.dim_in_y))
            param_dict['Par3'] = str(unit.meter_to_active_unit(self.dim_in_z))
            param_dict['Par4'] = str(unit.meter_to_active_unit(self.lead_in))
            param_dict['Par5'] = ""
            param_dict['Par6'] = ""
            param_dict['Par7'] = str(self.tool_number)
            param_dict['Par8'] = ""
            param_dict['Par9'] = ""            
            
        if self.type_token == 'SLIDE':
            param_dict['Par1'] = str(unit.meter_to_active_unit(self.dim_from_drawer_bottom))
            param_dict['Par2'] = str(unit.meter_to_active_unit(self.dim_to_first_hole))
            param_dict['Par3'] = str(unit.meter_to_active_unit(self.dim_to_second_hole))
            param_dict['Par4'] = str(unit.meter_to_active_unit(self.dim_to_third_hole))
            param_dict['Par5'] = str(unit.meter_to_active_unit(self.dim_to_fourth_hole))
            param_dict['Par6'] = str(unit.meter_to_active_unit(self.dim_to_fifth_hole))
            param_dict['Par7'] = str(unit.meter_to_active_unit(self.face_bore_depth)) + "|" + str(self.face_bore_dia)
            param_dict['Par8'] = str(unit.meter_to_active_unit(self.drawer_slide_clearance))
            param_dict['Par9'] = ""
            
        return param_dict
    
    def draw_properties(self,layout):
        col = layout.column(align=True)
        box = col.box()
        row = box.row()
        
        if self.show_expanded:
            row.prop(self,'show_expanded',text='',icon='TRIA_DOWN',emboss=False)
        else:
            row.prop(self,'show_expanded',text="",icon='TRIA_RIGHT',emboss=False)
        row.prop(self,"name",text="",icon='SCULPTMODE_HLT')
        row.operator('cabinetlib.delete_machine_token',text="",icon='X',emboss=False).token_name = self.name

        if self.show_expanded:
            box = col.box()
            row = box.row()
            row.prop(self,'type_token',text="")
            row.prop(self,'face',text="Face")
            if self.type_token == 'CONST':
                col = box.column(align=True)
                col.prop(self,'dim_to_first_const_hole')
                col.prop(self,'dim_to_last_const_hole')
                box.prop(self,'distance_between_holes')
                row = box.row(align=True)
                row.label('Edge:')
                row.prop(self,'edge_bore_depth',text="Depth")
                row.prop(self,'edge_bore_dia',text="Dia")
                row = box.row(align=True)
                row.label('Face:')
                row.prop(self,'face_bore_depth',text="Depth")
                row.prop(self,'face_bore_dia',text="Dia")
                
                row = box.row(align=True)
                row.prop(self,'drill_from_opposite_side')
                row.prop(self,'second_hole_at_32mm')
                
            if self.type_token == 'HOLES':
                box.prop(self,'hole_locations')
                box.prop(self,'edge_bore_dia')
                box.prop(self,'edge_bore_depth')
                box.prop(self,'face_bore_depth')
                box.prop(self,'face_bore_dia')
                box.prop(self,'drill_from_opposite_side')
                box.prop(self,'z_value')
            if self.type_token in {'SHLF','SHELF'}:
                col = box.column(align=True)
                col.prop(self,'space_from_top')
                col.prop(self,'space_from_bottom')
                row = box.row(align=True)
                row.prop(self,'dim_to_first_row')
                row.prop(self,'dim_to_second_row')
                row = box.row(align=True)
                row.label("Drilling:")
                row.prop(self,'face_bore_dia',text="Dia")
                row.prop(self,'face_bore_depth',text="Depth")
                row.prop(self,'shelf_hole_spacing',text="Spacing")
                box.prop(self,'shelf_clip_gap')
                box.prop(self,'drill_from_opposite_side')
            if self.type_token == 'SHELFSTD':
                box.label('Not Available at this time')
            if self.type_token in {'DADO','SAW'}:
                row = box.row(align=True)
                row.label('Router Lead:')
                row.prop(self,'lead_in',text="In")
                row.prop(self,'lead_out',text="Out")
                box.prop(self,'beginning_depth')
                box.prop(self,'double_pass')
                box.prop(self,'lock_joint')
                box.prop(self,'panel_penetration')
                box.prop(self,'tool_number')
                box.prop(self,'tongue_tool_number')
                box.prop(self,'reverse_direction')
            if self.type_token == 'SLIDE':
                row.prop(self,'dim_from_drawer_bottom')
                row.prop(self,'dim_to_first_hole')
                box.prop(self,'dim_to_second_hole')
                box.prop(self,'dim_to_third_hole')
                box.prop(self,'dim_to_fourth_hole')
                box.prop(self,'dim_to_fifth_hole')
                box.prop(self,'face_bore_depth')
                box.prop(self,'face_bore_dia')
                box.prop(self,'drawer_slide_clearance')
            if self.type_token == 'CAMLOCK':
                box.prop(self,'hole_locations')
                box.prop(self,'edge_bore_dia')
                box.prop(self,'edge_bore_depth')
                row = box.row()
                row.prop(self,'face_bore_dia')
                row.prop(self,'face_bore_depth')
                row = box.row()
                row.prop(self,'face_bore_dia_2')
                row.prop(self,'face_bore_depth_2')      
                box.prop(self,'z_value')
                box.prop(self,'backset')
                box.prop(self,'cam_face')
                box.prop(self,'drill_from_opposite_side')
            if self.type_token == 'MITER':
                box.prop(self,'edge')
                box.prop(self,'angle')
                box.prop(self,'lead_out')
                box.prop(self,'tool_number')
            if self.type_token == 'BORE':
                box.prop(self,'dim_in_x')
                box.prop(self,'dim_in_y')
                box.prop(self,'dim_in_z')
                box.prop(self,'face_bore_dia')
                box.prop(self,'end_dim_in_x')
                box.prop(self,'end_dim_in_y')
                box.prop(self,'distance_between_holes')
                box.prop(self,'associative_dia')
                box.prop(self,'associative_depth')
            if self.type_token == 'CORNERNOTCH':
                box.prop(self,'dim_in_x')
                box.prop(self,'dim_in_y')
                box.prop(self,'dim_in_z')
                box.prop(self,'lead_in')
                box.prop(self,'tool_number')
            if self.type_token == 'CHAMFER':
                box.prop(self,'dim_in_x')
                box.prop(self,'dim_in_y')
                box.prop(self,'dim_in_z')
                box.prop(self,'lead_in')
                box.prop(self,'tool_number')
                                
    def add_driver(self,obj,token_property,expression,driver_vars,index=None):
        data_path = 'mv.mp.machine_tokens.["' + self.name + '"].' + token_property
        
        if data_path != "":
            if index:
                driver = obj.driver_add(data_path,index)
            else:
                driver = obj.driver_add(data_path)
            utils.add_variables_to_driver(driver,driver_vars)
            driver.driver.expression = expression
        else:
            print("Error: '" + self.name + "' not found while setting expression '" + expression + "'")
        
bpy.utils.register_class(Machine_Token)

class Machine_Point(PropertyGroup):

    machine_tokens = CollectionProperty(name="Machine Tokens",
                                        description="Collection of machine tokens ",
                                        type=Machine_Token)
    
    machine_token_index = IntProperty(name="Machine Token Index")
    
    def add_machine_token(self,name,token_type,face,edge="1"):
        token = self.machine_tokens.add()
        token.name = name
        token.type_token = token_type
        token.face = face
        token.edge = edge
        return token
    
    def draw_machine_tokens(self,layout):
        for token in self.machine_tokens:
            token.draw_properties(layout)

bpy.utils.register_class(Machine_Point)

class OBJECT_PROPERTIES(PropertyGroup):
    #KEEP FOR NOW
    type_mesh = EnumProperty(name="Mesh Type",
                             items=[('NONE',"None","None"),
                                    ('CUTPART',"Cut Part","Cut Part"),
                                    ('EDGEBANDING',"Edgebanding","Edgebanding"),
                                    ('SOLIDSTOCK',"Solid Stock","Solid Stock"),
                                    ('HARDWARE',"Hardware","Hardware"),
                                    ('BUYOUT',"Buyout","Buyout"),
                                    ('MACHINING',"Machining","Machining")],
                             description="Select the Mesh Type.",
                             default='NONE')
    
    spec_group_name = StringProperty(name="Specification Group Name",
                                     description="Current name of the specification group that is assigned to the group.")
    
    spec_group_index = IntProperty(name="Specification Group Index")
    
    material_slots = CollectionProperty(name="Material Slot Collection",
                                        description="Collection of material slots used ",
                                        type=Material_Slot)    
    
    #MOVE
    cutpart_name = StringProperty(name="Cutpart Name")
    edgepart_name = StringProperty(name="Edgepart Name")

bpy.utils.register_class(OBJECT_PROPERTIES)
    
class SCENE_PROPERTIES(PropertyGroup):
#     libraries = CollectionProperty(name="Libraries",
#                                    type=Library)
    
    sheets = CollectionProperty(name="Materials",
                                type=Sheet_Stock)

    edgebanding = CollectionProperty(name="Edgebanding",
                                     type=Cutpart)
    
#     products = CollectionProperty(name="Products",
#                                   type=List_Library_Item)
#     
#     product_index = IntProperty(name="Product Index",
#                                 default=0)
    
bpy.utils.register_class(SCENE_PROPERTIES)

class WM_PROPERTIES(PropertyGroup):

    library_types = EnumProperty(name="Library Types",items=[('PRODUCT',"Product","Product"),
                                                             ('INSERT',"Insert","Insert")],
                                                            default = 'PRODUCT')  
    
    lib_products = CollectionProperty(name="Library Products",
                                      type=List_Library)
    
    lib_product_index = IntProperty(name="Library Product Index",
                                    default=0)
    
    lib_inserts = CollectionProperty(name="Library Inserts",
                                     type=List_Library)
     
    lib_insert_index = IntProperty(name="Library Insert Index",
                                   default=0)
    
    lib_insert = PointerProperty(name="Library Insert",type=List_Library)

    #USED FOR THE LIBRARY BUILD PROGRESS BAR
    current_item = IntProperty(name="Current Item",
                               default = 0)
    
    total_items = IntProperty(name="Total Items",
                              default = 0)

    #TEXT EDITOR
    module_members = bpy.props.CollectionProperty(name="Module Members", 
                                                  type=List_Module_Members)    
    
    module_members_index = bpy.props.IntProperty(name="Module Member Index", 
                                                 default=0,
                                                 update=update_text_editor_outline_index)   
    
    library_module_tabs = bpy.props.EnumProperty(name="Library Module Tabs",
                                             items=[('LIBRARY_DEVELOPMENT',"Library Development","Library Development"),
                                                    ('FIND',"Find","Find"),
                                                    ('PROPERTIES',"Properties","Properties")],
                                             default='LIBRARY_DEVELOPMENT')

    def draw_inserts(self,layout):
        pass
    
    def draw_library_items(self,layout,library_type):
        col = layout.column(align=True)
        box = col.box()
        row = box.row(align=True)
        row.prop_enum(self, "library_types", 'PRODUCT', icon='LATTICE_DATA', text="Products")
        row.prop_enum(self, "library_types", 'INSERT', icon='STICKY_UVS_LOC', text="Inserts")
        if self.library_types == 'PRODUCT':
            if len(self.lib_products) < 1:
                box.operator('fd_general.load_library_modules',text="Load Library Modules",icon='FILE_REFRESH')
            else:
                row = box.row(align=True)
                row.scale_y = 1.3
                row.operator("fd_general.load_library_modules",text="",icon='FILE_REFRESH')
                props = row.operator('fd_general.brd_library_items',text="Build",icon='FILE_BLEND')
                props.operation_type = 'BUILD'
                props.library_type = 'PRODUCT'
                props = row.operator('fd_general.brd_library_items',text="Render",icon='RENDER_RESULT')
                props.operation_type = 'RENDER'
                props.library_type = 'PRODUCT'
                props = row.operator('fd_general.brd_library_items',text="Draw",icon='GREASEPENCIL')
                props.operation_type = 'DRAW'
                props.library_type = 'PRODUCT'
                row.menu('MENU_Product_Library_Options',text="",icon='DOWNARROW_HLT')
                col.template_list("LIST_lib", " ", self, "lib_products", self, "lib_product_index")
                lib = self.lib_products[self.lib_product_index]
                col.template_list("LIST_lib_productlist", " ", lib, "items", lib, "index")
                
        if self.library_types == 'INSERT':
            if len(self.lib_inserts) < 1:
                box.operator('fd_general.load_library_modules',text="Load Library Modules",icon='FILE_REFRESH')
            else:
                row = box.row(align=True)
                row.scale_y = 1.3
                row.operator("fd_general.load_library_modules",text="",icon='FILE_REFRESH')
                props = row.operator('fd_general.brd_library_items',text="Build",icon='FILE_BLEND')
                props.operation_type = 'BUILD'
                props.library_type = 'INSERT'
                props = row.operator('fd_general.brd_library_items',text="Render",icon='RENDER_RESULT')
                props.operation_type = 'RENDER'
                props.library_type = 'INSERT'
                props = row.operator('fd_general.brd_library_items',text="Draw",icon='GREASEPENCIL')
                props.operation_type = 'DRAW'
                props.library_type = 'INSERT'
                row.menu('MENU_Insert_Library_Options',text="",icon='DOWNARROW_HLT')
                col.template_list("LIST_lib", " ", self, "lib_inserts", self, "lib_insert_index")
                lib = self.lib_inserts[self.lib_insert_index]
                col.template_list("LIST_lib_insertlist", " ", lib, "items", lib, "index")
                
bpy.utils.register_class(WM_PROPERTIES)

class fd_object(PropertyGroup):

    type = EnumProperty(name="type",
                        items=enum_object_types,
                        description="Select the Object Type.",
                        default='NONE')

    type_group = EnumProperty(name="Group Type",
                             items=[('NONE',"None","None"),
                                    ('PRODUCT',"Product","Product"),
                                    ('INSERT',"Insert","Insert"),
                                    ('SPLITTER',"Splitter","Splitter"),
                                    ('OPENING',"Opening","Opening")],
                             description="Stores the Group Type.",
                             default='NONE')

    item_number = IntProperty(name="Item Number")

    property_id = StringProperty(name="Property ID",
                                 description="This property allows objects to display a custom property page. This is the operator bl_id.")

    plan_draw_id = StringProperty(name="Plan Draw ID",
                                  description="This property allows products to have a custom 2D plan view drawing. This is the operator bl_id.")

    update_id = StringProperty(name="Update ID",
                             description="This property allows a product to be updated after drawing. This is the operator bl_id.")

    drop_id = StringProperty(name="Drop ID",
                             description="This property allows a product to have a custom drop operator. This is the operator bl_id.")

    name_object = StringProperty(name="Object Name",
                                 description="This is the readable name of the object")
    
    use_as_mesh_hook = BoolProperty(name="Use As Mesh Hook",
                                    description="Use this object to hook to deform a mesh. Only for Empties",
                                    default=False)
    
    use_as_bool_obj = BoolProperty(name="Use As Boolean Object",
                                   description="Use this object cut a hole in the selected mesh",
                                   default=False)

    use_sma = BoolProperty(name="Use Part Boarder Algorithm",
                           description="Use Solid Model Analyzer to read geometry",
                           default=False)

    PromptPage = bpy.props.PointerProperty(name="Prompt Page",
                                           description="Custom properties assigned to the object. Only access from base point object.",
                                           type=mvPromptPage)
    
    product_type = StringProperty(name="Product Type",
                                  description="This is the type of the product")    
    
    product_sub_type = StringProperty(name="Product Sub Type",
                                      description="This is the sub type of the product")      
    
    product_shape = StringProperty(name="Product Shape",
                                   description="This is the shape of the product")          
    
    is_wall_mesh = BoolProperty(name="Is Wall Mesh",
                                description="Determines if the object is a wall mesh.",
                                default=False)
    
    is_cabinet_door = BoolProperty(name="Is Cabinet Door",
                                   description="Determines if the object is a cabinet door.",
                                   default=False)
    
    is_cabinet_drawer_front = BoolProperty(name="Is Cabinet Drawer Front",
                                           description="Determines if the object is a cabinet drawer front.",
                                           default=False)
    
    is_cabinet_drawer_box = BoolProperty(name="Is Cabinet Drawer Box",
                                         description="Determines if the object is a drawer box.",
                                         default=False)    
    
    is_cabinet_pull = BoolProperty(name="Is Cabinet Pull",
                                   description="Determines if the object is a cabinet pull.",
                                   default=False)

    mirror_z = BoolProperty(name="Flip Z",default = False,description = "Used in an product assembly to determine if the z dim is mirrored")
    mirror_y = BoolProperty(name="Flip Y",default = True,description = "Used in an product assembly to determine if the y dim is mirrored")

    edge_w1 = StringProperty(name="Edge Width 1",description="Name of the edgebanding applied to Width 1")
    edge_l1 = StringProperty(name="Edge Length 1",description="Name of the edgebanding applied to Length 1")
    edge_w2 = StringProperty(name="Edge Width 2",description="Name of the edgebanding applied to Width 2")
    edge_l2 = StringProperty(name="Edge Length 2",description="Name of the edgebanding applied to Length 2")
    solid_stock = StringProperty(name="Solid Stock",description="Name of the solid stock material applied to the obj")    
    
    opening_name = StringProperty(name="Opening Name",description="Name of the opening")   
    
    mp = PointerProperty(name="Machine Point",
                         description="Machining Point",
                         type=Machine_Point)    
    
    placement_type = StringProperty(name="Placement Type",
                                    description="Type of placement for products and inserts 'STANDARD','CORNER','INTERIOR','EXTERIOR','SPLITTER'")    
    
    interior_open = BoolProperty(name="Interior Open",description="Used for inserts to determine if an opening has an interior assembly",default=True)
    
    exterior_open = BoolProperty(name="Exterior Open",description="Used for inserts to determine if an opening has an exterior assembly",default=True)    
    
    library_name = StringProperty(name="Library Name",
                                  description="Name of the library that this product is assigned.")    
    
    package_name = StringProperty(name="Package Name",
                                  description="This is the python package the assembly is from")
    
    module_name = StringProperty(name="Module Name",
                                description="This is the python module name the assembly is from")
    
    class_name = StringProperty(name="Class Name",
                                description="This is the python class name the assembly is from")    
    
    comment = StringProperty(name="Comment",
                             description="Comment to store information for reporting purposes.")    
    
    price = FloatProperty(name="Price",
                          description="Stores the price for an object. This it only used for hardware.")    
    
    opengl_dim = PointerProperty(type=opengl_dim)

bpy.utils.register_class(fd_object)

class fd_interface(PropertyGroup):
    
    show_debug_tools = BoolProperty(name="Show Debug Tools",
                                    default = False,
                                    description="Show Debug Tools")
    
    use_default_blender_interface = BoolProperty(name="Use Default Blender Interface",
                                                 default = False,
                                                 description="Show Default Blender interface")
    
    interface_object_tabs = EnumProperty(name="Interface Object Tabs",
                                         items=enum_object_tabs,
                                         default = 'INFO')
    
    interface_group_tabs = EnumProperty(name="Interface Group Tabs",
                                        items=enum_group_tabs
                                        ,default = 'INFO')
    
    group_tabs = EnumProperty(name="Group Tabs",
                              items=enum_group_tabs,
                              description="Group Tabs",
                              default='INFO')
    
    group_driver_tabs = EnumProperty(name="Group Driver Tabs",
                                     items=enum_group_drivers_tabs,
                                     default = 'LOC_X')

    render_type_tabs = EnumProperty(name="Render Type Tabs",
                                    items=enum_render_type,
                                    default='PRR')
    
    enum_library_types = [('SCENE',"Scenes","Scenes"),
                          ('PRODUCT',"Products","Products"),
                          ('INSERT',"Inserts","Inserts"),
                          ('ASSEMBLY',"Assemblies","Assemblies"),
                          ('OBJECT',"Objects","Objects"),
                          ('MATERIAL',"Materials","Materials"),
                          ('WORLD',"Worlds","Worlds")]
    
    library_tabs = EnumProperty(name="Library Tabs",
                                items=[('SCENE',"Scenes","Scenes"),
                                       ('PRODUCT',"Products","Products"),
                                       ('INSERT',"Inserts","Inserts"),
                                       ('ASSEMBLY',"Assemblies","Assemblies"),
                                       ('OBJECT',"Objects","Objects"),
                                       ('MATERIAL',"Materials","Materials"),
                                       ('WORLD',"Worlds","Worlds")],
                                default='PRODUCT',
                                update=assign_default_libraries)
    
bpy.utils.register_class(fd_interface)

class fd_image(PropertyGroup):
    image_name = StringProperty(name="Image Name",
                                description="The Image name that is assign to the image view")
    
    is_plan_view = BoolProperty(name="Is Plan View",
                                default = False,
                                description="This determines if the image is a 2D Plan View")
    
    use_as_cover_image = BoolProperty(name="Use as Cover Image",
                                      default = False,
                                      description="This determines if the image should be printed on the first page")
    
    is_elv_view = BoolProperty(name="Is Elv View",
                               default = False,
                               description="This determines if the image is a 2D Elevation View")
    
bpy.utils.register_class(fd_image)

class fd_item(PropertyGroup):
    pass

bpy.utils.register_class(fd_item)

class fd_scene(PropertyGroup):
    scene_library_name = StringProperty(name="Scene Library Name",description="Used to determine what scene library is active.")
    scene_category_name = StringProperty(name="Scene Category name",description="Used to determine what scene category is active.")
    
    product_library_name = StringProperty(name="Product Library name",description="Used to determine what product library is active.")
    product_category_name = StringProperty(name="Product Category name",description="Used to determine what product category is active.")
    
    insert_library_name = StringProperty(name="Insert Library name",description="Used to determine what insert library is active.")
    insert_category_name = StringProperty(name="Insert Category name",description="Used to determine what insert category is active.")
    
    assembly_library_name = StringProperty(name="Assembly Library name",description="Used to determine what assembly library is active.")
    assembly_category_name = StringProperty(name="Assembly Category name",description="Used to determine what assembly category is active.")
    
    object_library_name = StringProperty(name="Object Library name",description="Used to determine what object library is active.")
    object_category_name = StringProperty(name="Object Category name",description="Used to determine what object category is active.")
    
    material_library_name = StringProperty(name="Material Library name",description="Used to determine what material library is active.")
    material_category_name = StringProperty(name="Material Category name",description="Used to determine what material category is active.")
    
    world_library_name = StringProperty(name="World Library name",description="Used to determine what world library is active.")
    world_category_name = StringProperty(name="World Category name",description="Used to determine what world category is active.")

    active_addon_name = StringProperty(name="Active Addon Name",description="Used to determine what the addon is active.")
    
    ui = PointerProperty(name="Interface",type= fd_interface)

    spec_group_tabs = EnumProperty(name="Library Tabs",
                                   items=[('GLOBALS',"Globals","Global Variable Options"),
                                          ('MATERIALS',"Materials","Rendering Materials"),
                                          ('CUTPARTS',"Cut Parts","Cut Parts for cabinets"),
                                          ('EDGEPARTS',"Library Builder","Edge banding for cabinets")],
                                   default = 'MATERIALS')

    spec_groups = CollectionProperty(name="Spec Groups",
                                     type=Specification_Group)
    
    spec_group_index = IntProperty(name="Spec Group Index",
                                   default=0)

    #These properties are used to view the children objects in a group
    active_object_name = StringProperty(name="Active Object Name",
                                        description="Used to make sure that the correct collection is being displayed this is set in the load child objects operator.")
    
    active_object_index = IntProperty(name="Active Object Index",
                                      description="Used is list views to select an object in the children_objects collection")
    
    children_objects = CollectionProperty(name="Children Objects",
                                          type=fd_item,
                                          description="Collection of all of the children objects of a group. Used to display in a list view.")

    opengl_dim = PointerProperty(type=opengl_dim)
    
    name_scene = StringProperty(name="Scene Name",
                                description="This is the readable name of the scene")    
    
    plan_view_scene = BoolProperty(name="Plan View Scene",
                                   description="Scene used for rendering project plan view",
                                   default=False) 
    
    elevation_scene = BoolProperty(name="Elevation Scene",
                                   description="Scene used for rendering elevations",
                                   default=False)    
    
    elevation_selected = BoolProperty(name="Selected for Elevation Rendering")   
    
    elevation_img_name = StringProperty(name="Rendered Elevation Image Name")
    
    initial_shade_mode = StringProperty(name="Initial Shade Mode")   
    
    initial_view_location =  FloatVectorProperty(name="Initial View Location",
                                                 size=3)
    
    initial_view_rotation =  FloatVectorProperty(name="Initial View Rotation",
                                                 size=4)      
    
    project_properties = CollectionProperty(name="Project Properties",
                                            type=Project_Property,
                                            description="Collection of all of the User Defined Project Properties")

    default_wall_height = FloatProperty(name="Default Wall Height",
                                        description="Enter the default height when drawings walls",
                                        default=unit.inch(108),
                                        unit='LENGTH')
    
    default_wall_depth = FloatProperty(name="Default Wall Depth",
                                        description="Enter the default depth when drawings walls",
                                        default=unit.inch(6),
                                        unit='LENGTH')

    job_name = StringProperty(name="Job Name")
    
    designer_name = StringProperty(name="Designer Name")
    
    client_name = StringProperty(name="Client Name")

    client_phone = StringProperty(name="Client Phone")
    
    client_email = StringProperty(name="Client Email")
    
bpy.utils.register_class(fd_scene)

class fd_window_manager(PropertyGroup):
    use_opengl_dimensions = BoolProperty(name="Use OpenGL Dimensions",
                                         description="Use OpenGL Dimensions",
                                         default=False)  
    
    elevation_scene_index = IntProperty(name="2d Elevation Scene Index",
                                        default=0,
                                        update=update_scene_index)    
    
    data_from_libs = CollectionProperty(name="Blend Files",type=blend_file)
    
    library_packages = CollectionProperty(name="Library Packages",type=Library_Package)
    
    library_module_path = StringProperty(name="Library Module Path",default="",subtype='DIR_PATH',update=update_library_paths)
    assembly_library_path = StringProperty(name="Assembly Library Path",default="",subtype='DIR_PATH',update=update_library_paths)
    object_library_path = StringProperty(name="Object Library Path",default="",subtype='DIR_PATH',update=update_library_paths)
    material_library_path = StringProperty(name="Material Library Path",default="",subtype='DIR_PATH',update=update_library_paths)
    world_library_path = StringProperty(name="World Library Path",default="",subtype='DIR_PATH',update=update_library_paths)
    
    image_views = CollectionProperty(name="Image Views",
                                     type=fd_image,
                                     description="Collection of all of the views to be printed.")

    image_view_index = IntProperty(name="Image View Index",
                                   default=0)    
    
bpy.utils.register_class(fd_window_manager)
    
class extend_blender_data():
    bpy.types.Object.mv = PointerProperty(type = fd_object)
    bpy.types.Scene.mv = PointerProperty(type = fd_scene)
    bpy.types.WindowManager.mv = PointerProperty(type = fd_window_manager)
    bpy.types.Object.cabinetlib = PointerProperty(type = OBJECT_PROPERTIES)
    bpy.types.Scene.cabinetlib = PointerProperty(type = SCENE_PROPERTIES)
    bpy.types.WindowManager.cabinetlib = PointerProperty(type = WM_PROPERTIES)
    bpy.types.Image.mv = PointerProperty(type = fd_image)
    
def register():
    extend_blender_data()
    
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    pcoll.my_previews_dir = ""
    pcoll.my_previews = ()
 
    preview_collections["main"] = pcoll
    
def unregister():
    pass
