'''
Common Unit Conversion Functions
'''
import bpy
from decimal import *

def inch(inch):
    """ Converts inch to meter
    """
    return round(inch / 39.3700787,6) #METERS

def millimeter(millimeter):
    """ Converts millimeter to meter
    """
    return millimeter * .001 #METERS

def meter_to_feet(meter):
    """ Converts meter to feet
    """
    return round(meter * 3.28084,4)

def meter_to_inch(meter):
    """ Converts meter to inch
    """
    return round(meter * 39.3700787,4)

def meter_to_millimeter(meter):
    """ Converts meter to millimeter
    """
    return meter * 1000

def meter_to_active_unit(meter):
    """ Converts meter to active unit
    """
    if bpy.context.scene.unit_settings.system == 'METRIC':
        return meter_to_millimeter(meter)
    else:
        return meter_to_inch(meter)
    
def inch_to_millimeter(inch):
    """ Converts inch to millimeter
    """
    return inch * 25.4

def decimal_inch_to_millimeter(inch):
    """ Converts inch to millimeter returned as a decimal object
    """
    return Decimal(str(inch)) * Decimal(str(25.4))

def draw_dollar_price(value):
    return  "$" + str(round(value,2))
