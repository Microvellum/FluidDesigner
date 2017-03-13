"""
Microvellum 
Countertops
Stores the logic and product defs for counertops
# TODO: Create Diagonal Corner CT, Create Transition CT, Create Island CT
"""

from mv import fd_types, unit, utils
from os import path

ROOT_DIR = path.dirname(__file__)
COUNTERTOP_PARTS_DIR = path.join(ROOT_DIR,"Countertop Parts")
BACKSPLASH_PART = path.join(COUNTERTOP_PARTS_DIR,"Backsplash.blend")
CTOP = path.join(COUNTERTOP_PARTS_DIR,"Straight Countertop Square.blend")
NOTCHED_CTOP = path.join(COUNTERTOP_PARTS_DIR,"Corner Notched Countertop Square.blend")
DIAGONAL_CTOP = path.join(COUNTERTOP_PARTS_DIR,"Corner Diagonal Countertop Square.blend")

#---------PRODUCT: COUNTERTOPS

class Straight_Countertop(fd_types.Assembly):
    
    def __init__(self):
        self.library_name = "Countertops"
        self.category_name = "Countertops"
        self.assembly_name = "Straight Countertop"
        self.width = unit.inch(30)
        self.height = unit.inch(5.5)
        self.depth = unit.inch(24)
        self.height_above_floor = unit.inch(34.1)
        
    def draw(self):
        self.create_assembly()

        self.add_tab(name='Countertop Options',tab_type='VISIBLE')
        self.add_tab(name='Material Thickness',tab_type='HIDDEN')
        self.add_prompt(name="Add Backsplash",prompt_type='CHECKBOX',value=True,tab_index=0)
        self.add_prompt(name="Add Left Backsplash",prompt_type='CHECKBOX',value=False,tab_index=0)
        self.add_prompt(name="Add Right Backsplash",prompt_type='CHECKBOX',value=False,tab_index=0)
        self.add_prompt(name="Side Splash Setback",prompt_type='DISTANCE',value=unit.inch(2.75),tab_index=0)
#         self.add_prompt(name="Edge Type",
#                               prompt_type='COMBOBOX',
#                               value=0,
#                               tab_index=0,
#                               items=['Full Bull-Nose',
#                                      'Half Bull-Nose',
#                                      '1/2 inch Bevel',
#                                      '1/4 inch Bevel',
#                                      'Double Bevel',
#                                      'Ogee',
#                                      'Cove',
#                                      'Dupont'],
#                               columns=3)
        self.add_prompt(name="Deck Thickness",prompt_type='DISTANCE',value=unit.inch(1.5),tab_index=1)
        self.add_prompt(name="Splash Thickness",prompt_type='DISTANCE',value=unit.inch(.75),tab_index=1)
        
        #VARS
        Product_Width = self.get_var('dim_x','Product_Width')
        Product_Height = self.get_var('dim_z','Product_Height')
        Product_Depth =  self.get_var('dim_y','Product_Depth')
        Add_Backsplash = self.get_var('Add Backsplash')
        Add_Left_Backsplash = self.get_var('Add Left Backsplash')
        Add_Right_Backsplash = self.get_var('Add Right Backsplash')
        Side_Splash_Setback = self.get_var('Side Splash Setback')
        Deck_Thickness = self.get_var('Deck Thickness')
        Splash_Thickness = self.get_var('Splash Thickness')
        
        deck = self.add_assembly(CTOP) 
        deck.set_name("Countertop Deck")
        deck.x_loc(value = 0)
        deck.y_loc(value = 0)
        deck.z_loc(value = 0)
        deck.x_rot(value = 0)
        deck.y_rot(value = 0)
        deck.z_rot(value = 0)
        deck.x_dim("Product_Width",[Product_Width])
        deck.y_dim("Product_Depth",[Product_Depth])
        deck.z_dim("Deck_Thickness",[Deck_Thickness])
        deck.material("Countertop_Surface")

        splash = self.add_assembly(BACKSPLASH_PART)
        splash.set_name("Backsplash")
        splash.x_loc(value = 0)
        splash.y_loc(value = 0)
        splash.z_loc('Deck_Thickness',[Deck_Thickness])
        splash.x_rot(value = 90)
        splash.y_rot(value = 0)
        splash.z_rot(value = 0)
        splash.x_dim("Product_Width",[Product_Width]) 
        splash.y_dim("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness]) 
        splash.z_dim("Splash_Thickness",[Splash_Thickness]) 
        splash.prompt("Hide","IF(Add_Backsplash,False,True)",[Add_Backsplash])
        splash.material("Countertop_Surface")

        left_splash = self.add_assembly(BACKSPLASH_PART)  
        left_splash.set_name("Left Backsplash")
        left_splash.x_loc(value = 0)
        left_splash.y_loc("IF(Add_Backsplash,-Splash_Thickness,0)",[Splash_Thickness,Add_Backsplash])
        left_splash.z_loc('Deck_Thickness',[Deck_Thickness])
        left_splash.x_rot(value = 90) 
        left_splash.y_rot(value = 0) 
        left_splash.z_rot(value = -90)
        left_splash.x_dim("fabs(Product_Depth)-Side_Splash_Setback-Splash_Thickness",[Product_Depth,Side_Splash_Setback,Splash_Thickness])
        left_splash.y_dim("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness]) 
        left_splash.z_dim("-Splash_Thickness",[Splash_Thickness])
        left_splash.prompt("Hide","IF(Add_Left_Backsplash,False,True)",[Add_Left_Backsplash])
        left_splash.material("Countertop_Surface")

        right_splash = self.add_assembly(BACKSPLASH_PART)  
        right_splash.set_name("Rear Backsplash")
        right_splash.x_loc("Product_Width",[Product_Width])
        right_splash.y_loc("IF(Add_Backsplash,-Splash_Thickness,0)",[Splash_Thickness,Add_Backsplash])
        right_splash.z_loc('Deck_Thickness',[Deck_Thickness])
        right_splash.x_rot(value = 90)
        right_splash.z_rot(value = 0)
        right_splash.z_rot(value = -90)
        right_splash.x_dim("fabs(Product_Depth)-Side_Splash_Setback-Splash_Thickness",[Product_Depth,Side_Splash_Setback,Splash_Thickness])
        right_splash.y_dim("Product_Height-Deck_Thickness",[Product_Height,Deck_Thickness]) 
        right_splash.z_dim("Splash_Thickness",[Splash_Thickness])
        right_splash.prompt("Hide","IF(Add_Right_Backsplash,False,True)",[Add_Right_Backsplash])
        right_splash.material("Countertop_Surface")
        
        self.update()
                
