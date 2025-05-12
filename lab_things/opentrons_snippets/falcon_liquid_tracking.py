# Liquid tracked container classes

from opentrons.protocol_api.labware import Well, Labware, Location

class tracked_container():
    minimum_volume = None #ul
    maximum_volume = None #ul
    bottom_out = None  # The remaining volume where the arm just goes to the bottom
    offset_hight = None # Pretend there is 2mL less to allow for room to withdraw liquid
    offset_rate = None # Height in mm for each milliliter
    offset_constant = None
    
    
    def __init__(self):
        if self.minimum_volume == None:
            raise NotImplementedError('Subclasses must define self.minimum_volume')
        if self.maximum_volume == None:
            raise NotImplementedError('Subclasses must define self.maximum_volume')
        if self.offset_hight == None:
            raise NotImplementedError('Subclasses must define self.offset_hight')
        if self.offset_rate == None:
            raise NotImplementedError('Subclasses must define self.offset_rate')
        if self.offset_constant == None:
            raise NotImplementedError('Subclasses must define self.offset_constant')
        if self.bottom_out == None:
            raise NotImplementedError('Subclasses must define self.bottom_out')
    
    def subtract_volume(self, volume_extracted=0):
        "Subtracts volume from current and returns new volume"
        volume_remaining = self.current_volume - volume_extracted
        if volume_remaining < self.minimum_volume:
            raise ValueError("Volume extracted is greater than minimum volume")
        elif volume_extracted <= 0:
            raise ValueError("Volume extracted must be positive")
        self.current_volume = volume_remaining 
        return volume_remaining

    def add_volume(self, volume_added=0):
        "Subtracts volume from current and returns new volume"
        volume_remaining = self.current_volume + volume_added
        if volume_remaining > self.maximum_volume:
            raise ValueError("Volume extracted is greater than minimum volume")
        elif volume_added <= 0:
            raise ValueError("Volume added must be positive")
        self.current_volume = volume_remaining 
        return volume_remaining

    def get_fluid_level(self):
        "Returns Z-offest of top of fluid in mm"
        if self.current_volume > self.maximum_volume:
            UserWarning("Falcon tube above capasity")
            return
        elif self.bottom_out <= self.current_volume:
            _delta_volume = self.current_volume - self.offset_hight
            _offset = self.offset_constant + self.offset_rate*_delta_volume/1_000
            return _offset
        elif self.minimum_volume <= self.current_volume:
            return 3
        elif self.label:
            raise ValueError(f"{self.label} is empty")
        else:
            raise ValueError(f"Container at {self.location} is empty!")
            
            
class falcon_tube_15(tracked_container):

    def __init__(self, protocol, initial_volume,
        location,
        label = None,
        namespace = None,
        version = None):

        self.current_volume = initial_volume
        self.location = location
        self.label = label
        self.namespace = namespace
        self.version = version
        
        
        self.minimum_volume = 200 #ul
        self.maximum_volume = 15_000 #ul
        self.bottom_out = 1_500  # The remaining volume where the arm just goes to the bottom
        self.offset_hight = 2_000 # Pretend there is 2mL less to allow for room to withdraw liquid
        self.offset_rate = 6.1 # Height in mm for each milliliter
        self.offset_constant = 21
        
        super().__init__()
        
        
class falcon_tube_50(tracked_container):

    def __init__(self, protocol, initial_volume,
        location,
        label = None,
        namespace = None,
        version = None):

        self.current_volume = initial_volume
        self.location = location
        self.label = label
        self.namespace = namespace
        self.version = version
        
        
        self.minimum_volume = 1_000 #ul
        self.maximum_volume = 50_000 #ul
        self.bottom_out = 5_000  # The remaining volume where the arm just goes to the bottom
        self.offset_hight = 2_000 # Pretend there is 2mL less to allow for room to withdraw liquid
        self.offset_rate = 6.1/5 # Height in mm for each milliliter
        self.offset_constant = 0
        
        super().__init__()
        
        
# Tracked Transfer Function

def tracked_transfer(source, destination, pipette, volume):

    # Remember default heights
    original_asp_clearance = pipette.well_bottom_clearance.aspirate
    original_dis_clearance = pipette.well_bottom_clearance.dispense

    # Get appropriate level for source and adjust clearance
    if type(source) == Well:  # If it is a well then use default clearance
        source_loc = source
    elif type(source) == Location:  # If it is a well then use default clearance
        source_loc = source
    else:
        source_loc = source.location

    # Get appropriate level for destination adjust clearance
    if type(destination) == Well:  # If it is a well then use default clearance
        destination_loc = destination
    elif type(destination) == Location:  # If it is a well then use default clearance
        destination_loc = destination
    else:
        destination_loc = destination.location
        
    # Do transfer, automatically adjust clearance
    max_vol = pipette.max_volume
    n_transfers = int(volume/max_vol)
    remainder = volume - n_transfers*max_vol
    for i in range(n_transfers):
        if type(source) not in [Well, Location]:
            source.subtract_volume(max_vol)
            pipette.well_bottom_clearance.aspirate = source.get_fluid_level()
        if type(destination) not in [Well, Location]:
            destination.add_volume(max_vol)
            try:
                dest_level = destination.get_fluid_level()
            except:
                dest_level = 3
            pipette.well_bottom_clearance.dispense = dest_level
        pipette.transfer(max_vol, source_loc, destination_loc,
            new_tip='never')
        
    if remainder > 0:
        if type(source) not in [Well, Location]:
            source.subtract_volume(remainder)
            pipette.well_bottom_clearance.aspirate = source.get_fluid_level()
        if type(destination) not in [Well, Location]:    
            destination.add_volume(remainder)
            try:
                dest_level = destination.get_fluid_level()
            except:
                dest_level = 3
            pipette.well_bottom_clearance.dispense = dest_level
        pipette.transfer(remainder, source_loc, destination_loc,
            new_tip='never')

    # Return to default heights
    pipette.well_bottom_clearance.aspirate = original_asp_clearance
    pipette.well_bottom_clearance.dispense = original_dis_clearance
    
    
# Example 
# Example Usage

import opentrons.simulate
import opentrons.execute

def run(protocol):
    protocol.home()
    # Define the consumables
    print('Defining consumables')
    tips300 = protocol.load_labware("opentrons_96_filtertiprack_200ul", 5)
    tube_rack = protocol.load_labware("opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical", 3)
    
    tube_1 = falcon_tube_50(protocol, 50_000, tube_rack['A3'])
    tube_2 = falcon_tube_50(protocol, 0, tube_rack['A4'])
    
    
    # Define the pipette
    print('Defining Pipette')
    pipette300 = protocol.load_instrument("p300_single", "right", tip_racks=[tips300])
    
    # Transfer liquid back and forth
    if pipette300.has_tip:
        pipette300.drop_tip()
    pipette300.pick_up_tip()
    print("Transfering from A to B")
    while True:
        try:
            tracked_transfer(tube_1, tube_2, pipette300, 200)
            # NOTE: TRACKED TRANSFER NEVER CHANGES TIPS. IF YOU TELL IT TO DO 400UL WITH A P200 IT WILL DO 2x200!
        except ValueError as e:
            break
            
    print("Transfering from B to A")
    while True:
        try:
            tracked_transfer(tube_2, tube_1, pipette300, 200)
        except ValueError as e:
            break
    pipette300.return_tip()

protocol = opentrons.simulate.get_protocol_api("2.12")
run(protocol)
