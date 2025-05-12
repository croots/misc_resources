"""
By default, expects tip racks to be full of tips.
If you want to start with an empty tip rack, you can use the following snippet.

The snippet does this by flagging 'wells' in the tip box as empty based on
either the number of tips missing or the coordinate of the tip you want to start
using from.

I am not responsible for any damage done to your labware.
"""

from opentrons import simulate  # Replace with execute if you want to run this on the robot

def drop_tips(tipbox, number_of_tips):
    """Removes the first n number of tips from the rack, so that it starts on the next one"""
    for well in tipbox.wells()[:number_of_tips]:
        well.has_tip = False

def starting_tip(tipbox, coordinates: str):
    """Drops all tips before the starting tip, so that the robot starts at the given tip coordinate"""
    wells = list(tips.wells_by_name().keys())
    coord_value = wells.index(coordinates)
    drop_tips(tipbox, coord_value)

# Example of how to use the above functions

protocol = simulate.get_protocol_api('2.12')
tips = protocol.load_labware("thermoscientificarttips_96_tiprack_200ul", 1)

starting_tip(tips, "B4")

print(f"tips[B3]: {tips['B3'].has_tip}")
print(f"tips[B4]: {tips['B4'].has_tip}")
print(f"tips[B5]: {tips['B5'].has_tip}")