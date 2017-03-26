"""
Microvellum 
Exteriors
Stores the logic and insert defs for all exterior components for cabinets and closets.
Doors, Drawers, Hampers
"""

import bpy
from mv import fd_types, unit, utils
from os import path
from . import cabinet_properties

ROOT_PATH = path.join(path.dirname(__file__),"Cabinet Components")
DOOR = path.join(ROOT_PATH,"Part with Edgebanding.blend")
PULL = path.join(ROOT_PATH,"Bar Pull 3.blend")

VERTICAL_GAP = unit.inch(.125)
REVEALS = unit.inch(.0625)
DOOR_TO_CABINET_GAP = unit.inch(.125)
DRAWER_FRONT_HEIGHT = unit.inch(6)
STACKED_TOP_DOOR_HEIGHT = unit.inch(10)

#---------FUNCTIONS

def add_prompt_tabs(assembly):
    assembly.add_tab(name='Door Options',tab_type='VISIBLE')
    assembly.add_tab(name='Formulas',tab_type='HIDDEN')
    
def add_common_door_prompts(assembly):
    door_type = 0 #SET DEFAULT
    if assembly.door_type == 'BASE':
        door_type = 0
    if assembly.door_type == 'TALL':
        door_type = 1     
    if assembly.door_type == 'UPPER':
        door_type = 2
    
    assembly.add_prompt(name="Door Thickness",prompt_type='DISTANCE',value=unit.inch(.75),tab_index=1)
    assembly.add_prompt(name="Pull Location",prompt_type='COMBOBOX',items=['BASE','TALL','UPPER'],value=door_type,tab_index=1,columns=3)
    assembly.add_prompt(name="Pull From Edge",prompt_type='DISTANCE',value=unit.inch(1.5),tab_index=0)
    assembly.add_prompt(name="Pull From Top",prompt_type='DISTANCE',value=unit.inch(1.5),tab_index=0)
    assembly.add_prompt(name="Pull From Bottom",prompt_type='DISTANCE',value=unit.inch(1.5),tab_index=0)
    assembly.add_prompt(name="Pull From Floor",prompt_type='DISTANCE',value=unit.inch(40),tab_index=0)
    
def add_common_pull_prompts(assembly):
    props = cabinet_properties.get_scene_props()
    
    assembly.add_prompt(name="No Pulls",prompt_type='CHECKBOX',value=props.exterior_defaults.no_pulls,tab_index=0)
    assembly.add_prompt(name="Pull Length",prompt_type='DISTANCE',value=0,tab_index=0)
    
def add_overlay_prompts(assembly):
    props = cabinet_properties.get_scene_props()
    
    assembly.add_prompt(name="Front Thickness",prompt_type='DISTANCE',value=unit.inch(.75),tab_index=0)
    assembly.add_prompt(name="Inset Front",prompt_type='CHECKBOX',value=props.exterior_defaults.inset_door,tab_index=0)
    assembly.add_prompt(name="Door to Cabinet Gap",prompt_type='DISTANCE',value=DOOR_TO_CABINET_GAP,tab_index=0)
    assembly.add_prompt(name="Half Overlay Top",prompt_type='CHECKBOX',value=False,tab_index=0)
    assembly.add_prompt(name="Half Overlay Bottom",prompt_type='CHECKBOX',value=False,tab_index=0)
    assembly.add_prompt(name="Half Overlay Left",prompt_type='CHECKBOX',value=False,tab_index=0)
    assembly.add_prompt(name="Half Overlay Right",prompt_type='CHECKBOX',value=False,tab_index=0)
    
    assembly.add_prompt(name="Vertical Gap",prompt_type='DISTANCE',value=VERTICAL_GAP,tab_index=0)
    assembly.add_prompt(name="Top Reveal",prompt_type='DISTANCE',value=unit.inch(.25),tab_index=0)
    assembly.add_prompt(name="Bottom Reveal",prompt_type='DISTANCE',value=0,tab_index=0)
    assembly.add_prompt(name="Left Reveal",prompt_type='DISTANCE',value=REVEALS,tab_index=0)
    assembly.add_prompt(name="Right Reveal",prompt_type='DISTANCE',value=REVEALS,tab_index=0)
    assembly.add_prompt(name="Inset Reveal",prompt_type='DISTANCE',value=unit.inch(0.125),tab_index=0) 
    
    #CALCULATED
    assembly.add_prompt(name="Top Overlay",prompt_type='DISTANCE',value=unit.inch(.6875),tab_index=1)
    assembly.add_prompt(name="Bottom Overlay",prompt_type='DISTANCE',value=unit.inch(.6875),tab_index=1)
    assembly.add_prompt(name="Left Overlay",prompt_type='DISTANCE',value=unit.inch(.6875),tab_index=1)
    assembly.add_prompt(name="Right Overlay",prompt_type='DISTANCE',value=unit.inch(.6875),tab_index=1)
    
    #INHERITED
    assembly.add_prompt(name="Extend Top Amount",prompt_type='DISTANCE',value=0,tab_index=1)
    assembly.add_prompt(name="Extend Bottom Amount",prompt_type='DISTANCE',value=0,tab_index=1)
    assembly.add_prompt(name="Top Thickness",prompt_type='DISTANCE',value=unit.inch(.75),tab_index=1)
    assembly.add_prompt(name="Bottom Thickness",prompt_type='DISTANCE',value=unit.inch(.75),tab_index=1)
    assembly.add_prompt(name="Left Side Thickness",prompt_type='DISTANCE',value=unit.inch(.75),tab_index=1)
    assembly.add_prompt(name="Right Side Thickness",prompt_type='DISTANCE',value=unit.inch(.75),tab_index=1)
    assembly.add_prompt(name="Division Thickness",prompt_type='DISTANCE',value=unit.inch(.75),tab_index=1)
    
    inset = assembly.get_var("Inset Front",'inset')
    ir = assembly.get_var("Inset Reveal",'ir')
    tr = assembly.get_var("Top Reveal",'tr')
    br = assembly.get_var("Bottom Reveal",'br')
    lr = assembly.get_var("Left Reveal",'lr')
    rr = assembly.get_var("Right Reveal",'rr')
    vg = assembly.get_var("Vertical Gap",'vg')
    hot = assembly.get_var("Half Overlay Top",'hot')
    hob = assembly.get_var("Half Overlay Bottom",'hob')
    hol = assembly.get_var("Half Overlay Left",'hol')
    hor = assembly.get_var("Half Overlay Right",'hor')
    tt = assembly.get_var("Top Thickness",'tt')
    lst = assembly.get_var("Left Side Thickness",'lst')
    rst = assembly.get_var("Right Side Thickness",'rst')
    bt = assembly.get_var("Bottom Thickness",'bt')
    
    assembly.prompt('Top Overlay','IF(inset,-ir,IF(hot,(tt/2)-(vg/2),tt-tr))',[inset,ir,hot,tt,tr,vg])
    assembly.prompt('Bottom Overlay','IF(inset,-ir,IF(hob,(bt/2)-(vg/2),bt-br))',[inset,ir,hob,bt,br,vg])
    assembly.prompt('Left Overlay','IF(inset,-ir,IF(hol,(lst/2)-(vg/2),lst-lr))',[inset,ir,hol,lst,lr,vg])
    assembly.prompt('Right Overlay','IF(inset,-ir,IF(hor,(rst/2)-(vg/2),rst-rr))',[inset,ir,hor,rst,rr,vg])
    
def add_common_drawer_prompts(assembly):
    g = bpy.context.scene.lm_basic_cabinets.exterior_defaults

    assembly.add_prompt(name="Center Pulls on Drawers",prompt_type='CHECKBOX',value=g.center_pulls_on_drawers,tab_index=0)
    assembly.add_prompt(name="Drawer Pull From Top",prompt_type='DISTANCE',value=g.drawer_pull_from_top,tab_index=0)
    assembly.add_prompt(name="Pull Double Max Span",prompt_type='DISTANCE',value=unit.inch(30),tab_index=0)

def add_pull(assembly):
    Height = assembly.get_var("dim_z","Height")
    Door_to_Cabinet_Gap = assembly.get_var("Door to Cabinet Gap")
    No_Pulls = assembly.get_var("No Pulls")
    Front_Thickness = assembly.get_var("Front Thickness")
    PL = assembly.get_var("Pull Location","PL")
    Pull_Length = assembly.get_var("Pull Length")
    Pull_From_Top = assembly.get_var("Pull From Top")
    Pull_From_Bottom = assembly.get_var("Pull From Bottom")
    Pull_From_Floor = assembly.get_var("Pull From Floor")
    World_Z = assembly.get_var('world_loc_z','World_Z',transform_type='LOC_Z')
    Inset_Front = assembly.get_var("Inset Front")
    
    base_pull_loc = 'Height-Pull_From_Top-Pull_Length/2'
    tall_pull_loc = 'Pull_From_Floor+(Pull_Length/2)-World_Z'
    upper_pull_loc = 'Pull_From_Bottom+Pull_Length/2'
    
    z_loc_vars = [PL,Height,Pull_From_Top,Pull_From_Floor,Pull_From_Bottom,Pull_Length,World_Z]
    
    pull = assembly.add_object(PULL)
    pull.obj.mv.is_cabinet_pull = True
    pull.set_name("Cabinet Pull")
    pull.y_loc('IF(Inset_Front,0,-Door_to_Cabinet_Gap-Front_Thickness)',[Inset_Front,Door_to_Cabinet_Gap,Front_Thickness])
    pull.z_loc('IF(PL==0,' + base_pull_loc +',IF(PL==1,' + tall_pull_loc + ',IF(PL==2,' + upper_pull_loc + ',0)))',z_loc_vars)
    pull.x_rot(value = -90)
    pull.y_rot(value = 90)
    pull.z_rot(value = -90)
    pull.material("Cabinet_Pull_Finish")
    pull.hide('IF(No_Pulls,True,False)',[No_Pulls])
    return pull
    
def add_door(assembly):
    Front_Thickness = assembly.get_var("Front Thickness")
    Bottom_Overlay = assembly.get_var("Bottom Overlay")
    Door_to_Cabinet_Gap = assembly.get_var("Door to Cabinet Gap")
    Inset_Front = assembly.get_var("Inset Front")
    
    door = assembly.add_assembly(DOOR)
    door.obj_bp.mv.is_cabinet_door = True
    door.set_name("Cabinet Door")
    door.y_loc('IF(Inset_Front,Front_Thickness,-Door_to_Cabinet_Gap)',[Inset_Front,Front_Thickness,Door_to_Cabinet_Gap])
    door.z_loc('-Bottom_Overlay',[Bottom_Overlay])
    door.x_rot(value = 0)
    door.y_rot(value = -90)
    door.z_rot(value = 90)
    door.z_dim('Front_Thickness',[Front_Thickness])
    door.set_material_pointers("Exposed_Exterior_Surface")  
    door.edgebanding('Cabinet_Door_Edges',l1 = True, w1 = True, l2 = True, w2 = True)
    return door
    
class Single_Door(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    door_type = "" # {BASE, TALL, UPPER}
    
    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        self.add_prompt(name="Door Swing",prompt_type='COMBOBOX',items=['LEFT','RIGHT'],value=0,tab_index=0,columns=2)
        
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Pull_From_Edge = self.get_var("Pull From Edge")
        Door_Swing = self.get_var("Door Swing")
        
        door = add_door(self)
        door.set_name("Cabinet Door")
        door.x_loc('-Left_Overlay',[Left_Overlay])
        door.x_dim('Height+Top_Overlay+Bottom_Overlay',[Height,Top_Overlay,Bottom_Overlay])
        door.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])
        
        pull = add_pull(self)
        pull.x_loc('IF(Door_Swing==1,Width-Pull_From_Edge,Pull_From_Edge)',[Width,Pull_From_Edge,Door_Swing])
        
        self.prompt("Pull Length",value=pull.obj.dimensions.x)
        
        self.update()

class Single_Door_Double_Stack(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    door_type = "" # {BASE, TALL, UPPER}
    
    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        self.add_prompt(name="Door Swing",prompt_type='COMBOBOX',items=['LEFT','RIGHT'],value=0,tab_index=0,columns=2)
        self.add_prompt(name="Top Door Height",prompt_type='DISTANCE',value=STACKED_TOP_DOOR_HEIGHT,tab_index=0)
        
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Pull_From_Edge = self.get_var("Pull From Edge")
        Door_Swing = self.get_var("Door Swing")
        Top_Door_Height = self.get_var("Top Door Height")
        Vertical_Gap = self.get_var("Vertical Gap")
        Pull_From_Bottom = self.get_var("Pull From Bottom")
        Pull_Length = self.get_var("Pull Length")
        
        top_door = add_door(self)
        top_door.set_name("Cabinet Door")
        top_door.x_loc('-Left_Overlay',[Left_Overlay])
        top_door.z_loc('Height+Top_Overlay-Top_Door_Height',[Height,Top_Overlay,Top_Door_Height])
        top_door.x_dim('Top_Door_Height',[Top_Door_Height])
        top_door.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])
        
        top_pull = add_pull(self)
        top_pull.x_loc('IF(Door_Swing==1,Width-Pull_From_Edge,Pull_From_Edge)',[Width,Pull_From_Edge,Door_Swing])
        top_pull.z_loc('Height+Top_Overlay-Top_Door_Height+Pull_From_Bottom+(Pull_Length/2)',
                       [Height,Top_Overlay,Top_Door_Height,Pull_From_Bottom,Pull_Length])
        
        bottom_door = add_door(self)
        bottom_door.set_name("Cabinet Door")
        bottom_door.x_loc('-Left_Overlay',[Left_Overlay])
        bottom_door.x_dim('Height+Top_Overlay+Bottom_Overlay-Top_Door_Height-Vertical_Gap',[Height,Top_Overlay,Bottom_Overlay,Top_Door_Height,Vertical_Gap])
        bottom_door.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])        
        
        bottom_pull = add_pull(self)
        bottom_pull.x_loc('IF(Door_Swing==1,Width-Pull_From_Edge,Pull_From_Edge)',[Width,Pull_From_Edge,Door_Swing]) 
        
        self.prompt("Pull Length",value=bottom_pull.obj.dimensions.x)
        
        self.update()

class Double_Door(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    door_type = "" # {BASE, TALL, UPPER}
    
    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Pull_From_Edge = self.get_var("Pull From Edge")
        Vertical_Gap = self.get_var("Vertical Gap")
        
        left_door = add_door(self)
        left_door.set_name("Cabinet Door")
        left_door.x_loc('-Left_Overlay',[Left_Overlay])
        left_door.x_dim('Height+Top_Overlay+Bottom_Overlay',[Height,Top_Overlay,Bottom_Overlay])
        left_door.y_dim('((Width/2)+Left_Overlay-(Vertical_Gap/2))*-1',[Width,Left_Overlay,Vertical_Gap])
        
        right_door = add_door(self)
        right_door.set_name("Cabinet Door")
        right_door.x_loc('Width+Left_Overlay',[Width,Left_Overlay])
        right_door.x_dim('Height+Top_Overlay+Bottom_Overlay',[Height,Top_Overlay,Bottom_Overlay])
        right_door.y_dim('(Width/2)+Right_Overlay-(Vertical_Gap/2)',[Width,Vertical_Gap,Right_Overlay])        
        
        left_pull = add_pull(self)
        left_pull.x_loc('(Width/2)-Pull_From_Edge',[Width,Pull_From_Edge])
        
        right_pull = add_pull(self)
        right_pull.x_loc('(Width/2)+Pull_From_Edge',[Width,Pull_From_Edge])        
        
        self.prompt("Pull Length",value=left_pull.obj.dimensions.x)
        
        self.update()
        
class Double_Door_Double_Stack(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    door_type = "" # {BASE, TALL, UPPER}
    
    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        self.add_prompt(name="Top Door Height",prompt_type='DISTANCE',value=STACKED_TOP_DOOR_HEIGHT,tab_index=0)
        
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Pull_From_Edge = self.get_var("Pull From Edge")
        Vertical_Gap = self.get_var("Vertical Gap")
        Top_Door_Height = self.get_var("Top Door Height")
        Pull_From_Bottom = self.get_var("Pull From Bottom")
        Pull_Length = self.get_var("Pull Length")
        
        top_left_door = add_door(self)
        top_left_door.set_name("Cabinet Door")
        top_left_door.x_loc('-Left_Overlay',[Left_Overlay])
        top_left_door.z_loc('Height+Top_Overlay-Top_Door_Height',[Height,Top_Overlay,Top_Door_Height])
        top_left_door.x_dim('Top_Door_Height',[Top_Door_Height])
        top_left_door.y_dim('((Width/2)+Left_Overlay-(Vertical_Gap/2))*-1',[Width,Left_Overlay,Vertical_Gap])
        
        top_right_door = add_door(self)
        top_right_door.set_name("Cabinet Door")
        top_right_door.x_loc('Width+Right_Overlay',[Width,Right_Overlay])
        top_right_door.z_loc('Height+Top_Overlay-Top_Door_Height',[Height,Top_Overlay,Top_Door_Height])
        top_right_door.x_dim('Top_Door_Height',[Top_Door_Height])
        top_right_door.y_dim('(Width/2)+Right_Overlay-(Vertical_Gap/2)',[Width,Vertical_Gap,Right_Overlay])        
        
        bottom_left_door = add_door(self)
        bottom_left_door.set_name("Cabinet Door")
        bottom_left_door.x_loc('-Left_Overlay',[Left_Overlay])
        bottom_left_door.x_dim('Height+Top_Overlay+Bottom_Overlay-Top_Door_Height-Vertical_Gap',
                               [Height,Top_Overlay,Bottom_Overlay,Top_Door_Height,Vertical_Gap])
        bottom_left_door.y_dim('((Width/2)+Left_Overlay-(Vertical_Gap/2))*-1',[Width,Left_Overlay,Vertical_Gap])
        
        bottom_right_door = add_door(self)
        bottom_right_door.set_name("Cabinet Door")
        bottom_right_door.x_loc('Width+Right_Overlay',[Width,Right_Overlay])
        bottom_right_door.x_dim('Height+Top_Overlay+Bottom_Overlay-Top_Door_Height-Vertical_Gap',
                                [Height,Top_Overlay,Bottom_Overlay,Top_Door_Height,Vertical_Gap])
        bottom_right_door.y_dim('(Width/2)+Right_Overlay-(Vertical_Gap/2)',[Width,Vertical_Gap,Right_Overlay])          
        
        top_left_pull = add_pull(self)
        top_left_pull.x_loc('(Width/2)-Pull_From_Edge',[Width,Pull_From_Edge])
        top_left_pull.z_loc('Height+Top_Overlay-Top_Door_Height+Pull_From_Bottom+(Pull_Length/2)',
                            [Height,Top_Overlay,Top_Door_Height,Pull_From_Bottom,Pull_Length])
        
        top_right_pull = add_pull(self)
        top_right_pull.x_loc('(Width/2)+Pull_From_Edge',[Width,Pull_From_Edge])             
        top_right_pull.z_loc('Height+Top_Overlay-Top_Door_Height+Pull_From_Bottom+(Pull_Length/2)',
                             [Height,Top_Overlay,Top_Door_Height,Pull_From_Bottom,Pull_Length])
        
        bottom_left_pull = add_pull(self)
        bottom_left_pull.x_loc('(Width/2)-Pull_From_Edge',[Width,Pull_From_Edge])
        
        bottom_right_pull = add_pull(self)
        bottom_right_pull.x_loc('(Width/2)+Pull_From_Edge',[Width,Pull_From_Edge])        
        
        self.prompt("Pull Length",value=bottom_right_pull.obj.dimensions.x)
        
        self.update()
        
class Flip_Up_Door(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    door_type = "" # {BASE, TALL, UPPER}
    
    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")

        door = add_door(self)
        door.set_name("Cabinet Door")
        door.x_loc('-Left_Overlay',[Left_Overlay])
        door.x_dim('Height+Top_Overlay+Bottom_Overlay',[Height,Top_Overlay,Bottom_Overlay])
        door.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])
        
        pull = add_pull(self)
        pull.x_loc('Width/2',[Width])
        pull.z_loc('Pull_From_Bottom',[])
        pull.x_rot(value = 0)
        pull.y_rot(value = 0)
        pull.z_rot(value = 0)
        
        self.prompt("Pull Length",value=pull.obj.dimensions.x)
        
        self.update()
        
class Flip_Up_Door_Double_Stack(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    door_type = "" # {BASE, TALL, UPPER}

    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        self.add_prompt(name="Top Door Height",prompt_type='DISTANCE',value=STACKED_TOP_DOOR_HEIGHT,tab_index=0)
        
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Top_Door_Height = self.get_var("Top Door Height")
        Vertical_Gap = self.get_var("Vertical Gap")
        
        top_door = add_door(self)
        top_door.set_name("Cabinet Door")
        top_door.x_loc('-Left_Overlay',[Left_Overlay])
        top_door.z_loc('Height+Top_Overlay-Top_Door_Height',[Height,Top_Overlay,Top_Door_Height])
        top_door.x_dim('Top_Door_Height',[Top_Door_Height])
        top_door.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])
        
        top_pull = add_pull(self)
        top_pull.x_loc('Width/2',[Width])
        top_pull.z_loc('Height+Top_Overlay-Top_Door_Height+Pull_From_Bottom',
                       [Height,Top_Overlay,Top_Door_Height])
        top_pull.x_rot(value = 0)
        top_pull.y_rot(value = 0)
        top_pull.z_rot(value = 0)
        
        bottom_door = add_door(self)
        bottom_door.set_name("Cabinet Door")
        bottom_door.x_loc('-Left_Overlay',[Left_Overlay])
        bottom_door.x_dim('Height+Top_Overlay+Bottom_Overlay-Top_Door_Height-Vertical_Gap',
                          [Height,Top_Overlay,Bottom_Overlay,Top_Door_Height,Vertical_Gap])
        bottom_door.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])
        
        bottom_pull = add_pull(self)
        bottom_pull.x_loc('Width/2',[Width])
        bottom_pull.z_loc('Pull_From_Bottom',[])
        bottom_pull.x_rot(value = 0)
        bottom_pull.y_rot(value = 0)
        bottom_pull.z_rot(value = 0)        
        
        self.prompt("Pull Length",value=bottom_pull.obj.dimensions.x)
        
        self.update()        
        
        
class Single_Door_Drawer(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    door_type = "" # {BASE, TALL, UPPER}
    
    use_false_front = False
    
    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_common_drawer_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        self.add_prompt(name="Door Swing",prompt_type='COMBOBOX',items=['LEFT','RIGHT'],value=0,tab_index=0,columns=2)
        self.add_prompt(name="Drawer Front Height",prompt_type='DISTANCE',value=DRAWER_FRONT_HEIGHT,tab_index=0)
        
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Pull_From_Edge = self.get_var("Pull From Edge")
        Door_Swing = self.get_var("Door Swing")
        Vertical_Gap = self.get_var("Vertical Gap")
        Drawer_Front_Height = self.get_var("Drawer Front Height")
        Pull_Length = self.get_var("Pull Length")
        Pull_From_Top = self.get_var("Pull From Top")
        Center_Pulls_on_Drawers = self.get_var("Center Pulls on Drawers")
        Drawer_Pull_From_Top = self.get_var("Drawer Pull From Top")
        
        door = add_door(self)
        door.set_name("Cabinet Door")
        door.x_loc('-Left_Overlay',[Left_Overlay])
        door.x_dim('Height+Top_Overlay+Bottom_Overlay-Drawer_Front_Height-Vertical_Gap',
                   [Height,Top_Overlay,Bottom_Overlay,Drawer_Front_Height,Vertical_Gap])
        door.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])
        
        drawer = add_door(self)
        drawer.set_name("Cabinet Drawer")
        drawer.x_loc('-Left_Overlay',[Left_Overlay])
        drawer.z_loc('Height-Drawer_Front_Height+Top_Overlay',[Height,Drawer_Front_Height,Top_Overlay])
        drawer.x_dim('Drawer_Front_Height',[Drawer_Front_Height])
        drawer.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])        
        
        door_pull = add_pull(self)
        door_pull.x_loc('IF(Door_Swing==1,Width-Pull_From_Edge,Pull_From_Edge)',[Width,Pull_From_Edge,Door_Swing])
        door_pull.z_loc('Height+Top_Overlay-Drawer_Front_Height-Pull_From_Top-(Pull_Length/2)',
                        [Height,Top_Overlay,Drawer_Front_Height,Pull_From_Top,Pull_Length])
        
        if not self.use_false_front:
            drawer_pull = add_pull(self)
            drawer_pull.x_rot(value=0)
            drawer_pull.y_rot(value=0)
            drawer_pull.z_rot(value=0)
            drawer_pull.x_loc('Width/2',[Width])
            drawer_pull.z_loc('Height+Top_Overlay-IF(Center_Pulls_on_Drawers,Drawer_Front_Height/2,Drawer_Pull_From_Top)',
                              [Height,Top_Overlay,Center_Pulls_on_Drawers,Drawer_Front_Height,Drawer_Pull_From_Top])        
            
        self.prompt("Pull Length",value=door_pull.obj.dimensions.x)
        
        self.update()
        
class Double_Door_Drawer(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    door_type = "" # {BASE, TALL, UPPER}
    
    use_false_front = False
    
    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_common_drawer_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        self.add_prompt(name="Drawer Front Height",prompt_type='DISTANCE',value=DRAWER_FRONT_HEIGHT,tab_index=0)
        
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Pull_From_Edge = self.get_var("Pull From Edge")
        Vertical_Gap = self.get_var("Vertical Gap")
        Drawer_Front_Height = self.get_var("Drawer Front Height")
        Pull_Length = self.get_var("Pull Length")
        Pull_From_Top = self.get_var("Pull From Top")
        Center_Pulls_on_Drawers = self.get_var("Center Pulls on Drawers")
        Drawer_Pull_From_Top = self.get_var("Drawer Pull From Top")
        
        left_door = add_door(self)
        left_door.set_name("Cabinet Door")
        left_door.x_loc('-Left_Overlay',[Left_Overlay])
        left_door.x_dim('Height+Top_Overlay+Bottom_Overlay-Drawer_Front_Height-Vertical_Gap',
                   [Height,Top_Overlay,Bottom_Overlay,Drawer_Front_Height,Vertical_Gap])
        left_door.y_dim('((Width/2)+Left_Overlay-(Vertical_Gap/2))*-1',[Width,Left_Overlay,Vertical_Gap])
        
        right_door = add_door(self)
        right_door.set_name("Cabinet Door")
        right_door.x_loc('Width+Right_Overlay',[Width,Right_Overlay])
        right_door.x_dim('Height+Top_Overlay+Bottom_Overlay-Drawer_Front_Height-Vertical_Gap',
                   [Height,Top_Overlay,Bottom_Overlay,Drawer_Front_Height,Vertical_Gap])
        right_door.y_dim('(Width/2)+Right_Overlay-(Vertical_Gap/2)',[Width,Right_Overlay,Vertical_Gap])
        
        left_drawer = add_door(self)
        left_drawer.set_name("Cabinet Drawer")
        left_drawer.x_loc('-Left_Overlay',[Left_Overlay])
        left_drawer.z_loc('Height-Drawer_Front_Height+Top_Overlay',[Height,Drawer_Front_Height,Top_Overlay])
        left_drawer.x_dim('Drawer_Front_Height',[Drawer_Front_Height])
        left_drawer.y_dim('((Width/2)+Left_Overlay-(Vertical_Gap/2))*-1',[Width,Left_Overlay,Vertical_Gap])      
        
        right_drawer = add_door(self)
        right_drawer.set_name("Cabinet Drawer")
        right_drawer.x_loc('Width+Right_Overlay',[Width,Right_Overlay])
        right_drawer.z_loc('Height-Drawer_Front_Height+Top_Overlay',[Height,Drawer_Front_Height,Top_Overlay])
        right_drawer.x_dim('Drawer_Front_Height',[Drawer_Front_Height])
        right_drawer.y_dim('(Width/2)+Right_Overlay-(Vertical_Gap/2)',[Width,Right_Overlay,Vertical_Gap])         
        
        left_door_pull = add_pull(self)
        left_door_pull.x_loc('(Width/2)-Pull_From_Edge',[Width,Pull_From_Edge])
        left_door_pull.z_loc('Height+Top_Overlay-Drawer_Front_Height-Pull_From_Top-(Pull_Length/2)',
                             [Height,Top_Overlay,Drawer_Front_Height,Pull_From_Top,Pull_Length])
        
        right_door_pull = add_pull(self)
        right_door_pull.x_loc('(Width/2)+Pull_From_Edge',[Width,Pull_From_Edge])
        right_door_pull.z_loc('Height+Top_Overlay-Drawer_Front_Height-Pull_From_Top-(Pull_Length/2)',
                              [Height,Top_Overlay,Drawer_Front_Height,Pull_From_Top,Pull_Length])        
        
        if not self.use_false_front:
            left_drawer_pull = add_pull(self)
            left_drawer_pull.x_rot(value=0)
            left_drawer_pull.y_rot(value=0)
            left_drawer_pull.z_rot(value=0)
            left_drawer_pull.x_loc('Width/4',[Width])
            left_drawer_pull.z_loc('Height+Top_Overlay-IF(Center_Pulls_on_Drawers,Drawer_Front_Height/2,Drawer_Pull_From_Top)',
                                   [Height,Top_Overlay,Center_Pulls_on_Drawers,Drawer_Front_Height,Drawer_Pull_From_Top])        
            
            left_drawer_pull = add_pull(self)
            left_drawer_pull.x_rot(value=0)
            left_drawer_pull.y_rot(value=0)
            left_drawer_pull.z_rot(value=0)
            left_drawer_pull.x_loc('(Width/4)*3',[Width])
            left_drawer_pull.z_loc('Height+Top_Overlay-IF(Center_Pulls_on_Drawers,Drawer_Front_Height/2,Drawer_Pull_From_Top)',
                                   [Height,Top_Overlay,Center_Pulls_on_Drawers,Drawer_Front_Height,Drawer_Pull_From_Top])           
            
        self.prompt("Pull Length",value=left_door_pull.obj.dimensions.x)
        
        self.update()        
        
class Double_Door_Single_Drawer(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    door_type = "" # {BASE, TALL, UPPER}
    
    use_false_front = False
    
    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_common_drawer_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        self.add_prompt(name="Drawer Front Height",prompt_type='DISTANCE',value=DRAWER_FRONT_HEIGHT,tab_index=0)
        
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Pull_From_Edge = self.get_var("Pull From Edge")
        Vertical_Gap = self.get_var("Vertical Gap")
        Drawer_Front_Height = self.get_var("Drawer Front Height")
        Pull_Length = self.get_var("Pull Length")
        Pull_From_Top = self.get_var("Pull From Top")
        Center_Pulls_on_Drawers = self.get_var("Center Pulls on Drawers")
        Drawer_Pull_From_Top = self.get_var("Drawer Pull From Top")
        
        left_door = add_door(self)
        left_door.set_name("Cabinet Door")
        left_door.x_loc('-Left_Overlay',[Left_Overlay])
        left_door.x_dim('Height+Top_Overlay+Bottom_Overlay-Drawer_Front_Height-Vertical_Gap',
                   [Height,Top_Overlay,Bottom_Overlay,Drawer_Front_Height,Vertical_Gap])
        left_door.y_dim('((Width/2)+Left_Overlay-(Vertical_Gap/2))*-1',[Width,Left_Overlay,Vertical_Gap])
        
        right_door = add_door(self)
        right_door.set_name("Cabinet Door")
        right_door.x_loc('Width+Right_Overlay',[Width,Right_Overlay])
        right_door.x_dim('Height+Top_Overlay+Bottom_Overlay-Drawer_Front_Height-Vertical_Gap',
                   [Height,Top_Overlay,Bottom_Overlay,Drawer_Front_Height,Vertical_Gap])
        right_door.y_dim('(Width/2)+Right_Overlay-(Vertical_Gap/2)',[Width,Right_Overlay,Vertical_Gap])        
        
        left_door_pull = add_pull(self)
        left_door_pull.x_loc('(Width/2)-Pull_From_Edge',[Width,Pull_From_Edge])
        left_door_pull.z_loc('Height+Top_Overlay-Drawer_Front_Height-Pull_From_Top-(Pull_Length/2)',
                             [Height,Top_Overlay,Drawer_Front_Height,Pull_From_Top,Pull_Length])
        
        right_door_pull = add_pull(self)
        right_door_pull.x_loc('(Width/2)+Pull_From_Edge',[Width,Pull_From_Edge])
        right_door_pull.z_loc('Height+Top_Overlay-Drawer_Front_Height-Pull_From_Top-(Pull_Length/2)',
                              [Height,Top_Overlay,Drawer_Front_Height,Pull_From_Top,Pull_Length])        
        
        drawer = add_door(self)
        drawer.set_name("Cabinet Drawer")
        drawer.x_loc('-Left_Overlay',[Left_Overlay])
        drawer.z_loc('Height-Drawer_Front_Height+Top_Overlay',[Height,Drawer_Front_Height,Top_Overlay])
        drawer.x_dim('Drawer_Front_Height',[Drawer_Front_Height])
        drawer.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])          
        
        if not self.use_false_front:
            drawer_pull = add_pull(self)
            drawer_pull.x_rot(value=0)
            drawer_pull.y_rot(value=0)
            drawer_pull.z_rot(value=0)
            drawer_pull.x_loc('Width/2',[Width])
            drawer_pull.z_loc('Height+Top_Overlay-IF(Center_Pulls_on_Drawers,Drawer_Front_Height/2,Drawer_Pull_From_Top)',
                              [Height,Top_Overlay,Center_Pulls_on_Drawers,Drawer_Front_Height,Drawer_Pull_From_Top])             
            
        self.prompt("Pull Length",value=left_door_pull.obj.dimensions.x)
        
        self.update()                
        
class Drawers(fd_types.Assembly):
    library_name = "Cabinet Exteriors"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    
    drawer_qty = 1
    
    front_heights = []
    
    def add_drawer_front(self,i,prev_drawer):
        Drawer_Front_Height = self.get_var("Drawer Front " + str(i) + " Height","Drawer_Front_Height")
        Height = self.get_var("dim_z","Height")
        Width = self.get_var("dim_x","Width")
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Vertical_Gap = self.get_var("Vertical Gap")
        
        Center_Pulls_on_Drawers = self.get_var("Center Pulls on Drawers")
        Drawer_Pull_From_Top = self.get_var("Drawer Pull From Top")
        
        drawer = add_door(self)
        drawer.set_name("Cabinet Drawer " + str(i))
        drawer.x_loc('-Left_Overlay',[Left_Overlay])
        if prev_drawer:
            prev_drawer_z_loc = prev_drawer.get_var('loc_z','prev_drawer_z_loc')
            drawer.z_loc('prev_drawer_z_loc-Drawer_Front_Height-Vertical_Gap',[prev_drawer_z_loc,Drawer_Front_Height,Vertical_Gap])
        else:
            drawer.z_loc('Height-Drawer_Front_Height+Top_Overlay',[Height,Drawer_Front_Height,Top_Overlay])
        drawer.x_dim('Drawer_Front_Height',[Drawer_Front_Height])
        drawer.y_dim('(Width+Left_Overlay+Right_Overlay)*-1',[Width,Left_Overlay,Right_Overlay])        
        
        drawer_z_loc = drawer.get_var('loc_z','drawer_z_loc')
        
        drawer_pull = add_pull(self)
        drawer_pull.x_rot(value=0)
        drawer_pull.y_rot(value=0)
        drawer_pull.z_rot(value=0)
        drawer_pull.x_loc('Width/2',[Width])
        drawer_pull.z_loc('drawer_z_loc+Drawer_Front_Height-IF(Center_Pulls_on_Drawers,Drawer_Front_Height/2,Drawer_Pull_From_Top)',
                          [drawer_z_loc,Drawer_Front_Height,Center_Pulls_on_Drawers,Drawer_Front_Height,Drawer_Pull_From_Top])    
        
        return drawer
    
    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_drawer_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        Vertical_Gap = self.get_var("Vertical Gap")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        
        self.add_tab(name='Drawer Front Heights',tab_type='CALCULATOR',calc_type="ZDIM")
        
        drawer = None
        for i in range(self.drawer_qty):
            equal = True
            height = 0
            if len(self.front_heights) >= i + 1:
                equal = True if self.front_heights[i] == 0 else False
                height = self.front_heights[i]
            self.add_prompt(name="Drawer Front " + str(i+1) + " Height",
                            prompt_type='DISTANCE',
                            value=height,
                            tab_index=2,
                            equal=equal)
            drawer = self.add_drawer_front(i+1,drawer)
            
        self.calculator_deduction("Vertical_Gap*(" + str(self.drawer_qty) +"-1)-Top_Overlay-Bottom_Overlay",
                                  [Vertical_Gap,Top_Overlay,Bottom_Overlay])
        
        self.update()
        
class Pie_Cut_Doors(fd_types.Assembly):
    
    library_name = "Frameless Cabinet Inserts"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    door_type = "" # {Base, Tall, Upper}
    door_swing = "" # {Left Swing, Right Swing, Double Door, Flip up}

    def draw(self):
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_common_drawer_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        self.add_prompt(name="Door Swing",prompt_type='COMBOBOX',items=['LEFT','RIGHT'],value=0,tab_index=0,columns=2)
        
        Width = self.get_var('dim_x','Width')
        Depth = self.get_var('dim_y','Depth')
        Height = self.get_var('dim_z','Height')
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Door_Swing = self.get_var("Door Swing")
        Door_to_Cabinet_Gap = self.get_var("Door to Cabinet Gap")
        Door_Thickness = self.get_var("Door Thickness")
        Pull_From_Edge = self.get_var("Pull From Edge")

        left_door = add_door(self)
        left_door.set_name("Cabinet Door")        
        left_door.z_rot(value=0)
        left_door.x_loc('Door_Thickness+Door_to_Cabinet_Gap',[Door_Thickness,Door_to_Cabinet_Gap])
        left_door.y_loc('Depth-Left_Overlay',[Depth,Left_Overlay])
        left_door.x_dim('Height+Top_Overlay+Bottom_Overlay',[Height,Top_Overlay,Bottom_Overlay])
        left_door.y_dim('fabs(Depth)+Left_Overlay-Door_to_Cabinet_Gap',[Depth,Left_Overlay,Door_to_Cabinet_Gap])
        
        right_door = add_door(self)
        right_door.set_name("Cabinet Door")
        right_door.x_loc('Door_to_Cabinet_Gap',[Door_to_Cabinet_Gap])
        right_door.x_dim('Height+Top_Overlay+Bottom_Overlay',[Height,Top_Overlay,Bottom_Overlay])
        right_door.y_dim('(Width+Right_Overlay-Door_to_Cabinet_Gap)*-1',[Width,Right_Overlay,Door_to_Cabinet_Gap])     
        
        pull = add_pull(self)
        pull.x_loc('IF(Door_Swing==0,Door_Thickness+Door_to_Cabinet_Gap,Width+Left_Overlay-Pull_From_Edge)',
                   [Door_Swing,Width,Left_Overlay,Pull_From_Edge,Door_Thickness,Door_to_Cabinet_Gap])
        pull.y_loc('IF(Door_Swing==0,Depth-Left_Overlay+Pull_From_Edge,-Door_Thickness-Door_to_Cabinet_Gap)',
                   [Door_Swing,Depth,Left_Overlay,Pull_From_Edge,Door_Thickness,Door_to_Cabinet_Gap])
        pull.z_rot('IF(Door_Swing==0,radians(0),radians(-90))',[Door_Swing])
        
        self.prompt("Pull Length",value=pull.obj.dimensions.x)
        
        self.update()
        
class Diagonal_Single_Door(fd_types.Assembly):
    
    library_name = "Frameless Cabinet Inserts"
    type_assembly = 'INSERT'
    placement_type = "EXTERIOR"
    property_id = "exteriors.door_prompts"
    door_type = "" # {Base, Tall, Upper}
    door_swing = "" # {Left Swing, Right Swing, Double Door, Flip up}

    def draw(self):
        #TODO: Set Drivers Correctly for Diagonal Doors
        self.create_assembly()
        add_prompt_tabs(self)
        add_common_door_prompts(self)
        add_common_drawer_prompts(self)
        add_overlay_prompts(self)
        add_common_pull_prompts(self)
        
        self.add_prompt(name="Door Swing",prompt_type='COMBOBOX',items=['LEFT','RIGHT'],value=0,tab_index=0,columns=2)
        
        Width = self.get_var('dim_x','Width')
        Depth = self.get_var('dim_y','Depth')
        Height = self.get_var('dim_z','Height')
        Left_Overlay = self.get_var("Left Overlay")
        Right_Overlay = self.get_var("Right Overlay")
        Top_Overlay = self.get_var("Top Overlay")
        Bottom_Overlay = self.get_var("Bottom Overlay")
        Door_Swing = self.get_var("Door Swing")
        Door_to_Cabinet_Gap = self.get_var("Door to Cabinet Gap")
        Door_Thickness = self.get_var("Door Thickness")
        Pull_From_Edge = self.get_var("Pull From Edge")

        # Z ROT atan((fabs(Depth)-Left_Side_Thickness-Cabinet_Depth_Right)/(fabs(Width)-Right_Side_Thickness-Cabinet_Depth_Left))
        # X DIM sqrt(((fabs(Depth)-Left_Side_Thickness-Cabinet_Depth_Right)**2)+((fabs(Width)-Right_Side_Thickness-Cabinet_Depth_Left)**2))
        
        left_door = add_door(self)
        left_door.set_name("Cabinet Door")        
        left_door.z_rot('atan(Width/Depth)',[Depth,Width])
        left_door.x_loc('Door_Thickness+Door_to_Cabinet_Gap',[Door_Thickness,Door_to_Cabinet_Gap])
        left_door.y_loc('Depth-Left_Overlay',[Depth,Left_Overlay])
        left_door.x_dim('Height+Top_Overlay+Bottom_Overlay',[Height,Top_Overlay,Bottom_Overlay])
        left_door.y_dim('sqrt((fabs(Depth)**2)+(fabs(Width)**2))',[Depth,Width])
        
#         right_door = add_door(self)
#         right_door.set_name("Cabinet Door")
#         right_door.z_rot(value=-45)
#         right_door.x_loc('Door_to_Cabinet_Gap',[Door_to_Cabinet_Gap])
#         right_door.x_dim('Height+Top_Overlay+Bottom_Overlay',[Height,Top_Overlay,Bottom_Overlay])
#         right_door.y_dim('Width+Right_Overlay-Door_to_Cabinet_Gap',[Width,Right_Overlay,Door_to_Cabinet_Gap])     
        
        pull = add_pull(self)
        pull.x_loc('IF(Door_Swing==0,Door_Thickness+Door_to_Cabinet_Gap,Width+Left_Overlay-Pull_From_Edge)',
                   [Door_Swing,Width,Left_Overlay,Pull_From_Edge,Door_Thickness,Door_to_Cabinet_Gap])
        pull.y_loc('IF(Door_Swing==0,Depth-Left_Overlay+Pull_From_Edge,-Door_Thickness-Door_to_Cabinet_Gap)',
                   [Door_Swing,Depth,Left_Overlay,Pull_From_Edge,Door_Thickness,Door_to_Cabinet_Gap])
        pull.z_rot(value = -45)
        
        self.prompt("Pull Length",value=pull.obj.dimensions.x)
        
        self.update()        
        