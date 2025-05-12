"""
By default, the Opentrons API raises an error if you try to retreve a tip that is not in the tiprack. 
This script allows you to overwrite that behavior ex. prompt you to replace the tip box.

This does this by hijacking the properties of the pipette instrumentcontext and applying them to a new
class that has the overwritten behavior for when the pipette runs out of tips. The below code is an example
of an implementation of this: instructing the robot to throw out 100 pipette tips from a rack in slot 1.

To deploy it yourself, you may need to make ajustments to the pipette class for your particular use case and
obviously you will need to tell the robot what is on the deck/integrate the rest of your protocol.

I am not responsible for any damage that may occur to your equipment.

"""

# Imports
from opentrons.protocol_api.labware import OutOfTipsError, filter_tipracks_to_start, split_tipracks, Well, Labware
from opentrons.protocol_api.instrument_context import InstrumentContext
from opentrons.types import Location
from typing import List, Optional, Union, Tuple, TYPE_CHECKING
from opentrons.protocols.api_support.instrument import validate_tiprack
from opentrons.commands.publisher import CommandPublisher, publish, publish_context
from opentrons.commands import commands as cmds
import logging

# Change to execute if you are actually running this on a machine
from opentrons import simulate


# protocol = simulate.get_protocol_api('2.12')
protocol = simulate.get_protocol_api('2.12')

# The instrumentcontext requires a logger to be set up before it is used.
logger = logging.getLogger(__name__)


# Overwrite the pipette with a custom class by coppying the contents of the class instance to a new instrumentcontext
class CustomPipette(InstrumentContext):
    def __init__(self, parent_instance):
        vars(self).update(vars(parent_instance))
        self.out_of_tips_func = self.prompt_refill_tips # Defines what happens when tips run out. In theory you can overwrite this
        
    def pick_up_tip(
        self,
        location: Optional[Union[Location, Well]] = None,
        presses: Optional[int] = None,
        increment: Optional[float] = None,
    ) -> InstrumentContext:
        """
        This is a rewrite of the pick up tip function to better handle running out of tips.
        Hijacking is on like 66.
        
        See original InstrumentContext's pick_up_tip function for propper docstring
        """

        if location and isinstance(location, types.Location):
            if location.labware.is_labware:
                tiprack = location.labware.as_labware()
                target: Well = tiprack.next_tip(self.channels)  # type: ignore
                if not target:
                    return self.out_of_tips_func()  # We're hijacking at this point. Everything else is factory.
            elif location.labware.is_well:
                target = location.labware.as_well()
                tiprack = target.parent
        elif location and isinstance(location, Well):
            tiprack = location.parent
            target = location
        elif not location:
            tiprack, target = self.next_available_tip(
                self.starting_tip, self.tip_racks, self.channels
            )
        else:
            raise TypeError(
                "If specified, location should be an instance of "
                "types.Location (e.g. the return value from "
                "tiprack.wells()[0].top()) or a Well (e.g. tiprack.wells()[0]."
                " However, it is a {}".format(location)
            )

        assert tiprack.is_tiprack, "{} is not a tiprack".format(str(tiprack))
        validate_tiprack(self.name, tiprack, logger)

        with publish_context(
            broker=self.broker,
            command=cmds.pick_up_tip(instrument=self, location=target),
        ):
            self.move_to(target.top(), publish=False)
            self._implementation.pick_up_tip(
                well=target._impl,
                tip_length=self._tip_length_for(tiprack),
                presses=presses,
                increment=increment,
            )
            # Note that the hardware API pick_up_tip action includes homing z after

        tiprack.use_tips(target, self.channels)
        self._last_tip_picked_up_from = target

        return self
    
    
    # This tiprack selection is not native to instrumentcontext its workflow throws the error, so we need to change that behavior
    def next_available_tip(self,
    starting_tip: Optional[Well], tip_racks: List[Labware], channels: int
    ) -> Tuple[Labware, Well]:
        start = starting_tip
        if start is None:
            return self.select_tiprack_from_list(tip_racks, channels)
        else:
            return self.select_tiprack_from_list(
                filter_tipracks_to_start(start, tip_racks), channels, start
            )

    # This one is called by the one above and is the second place the robot can throw the error, so we change it
    def select_tiprack_from_list(self,
        tip_racks: List[Labware], num_channels: int, starting_point: Optional[Well] = None
        ) -> Tuple[Labware, Well]:

        first, rest = None, None
        try:
            first, rest = split_tipracks(tip_racks)
        except IndexError:
            output = self.out_of_tips_func() # The other place we hijack is here
            if output:
                return output
            else: # There's some weird behavior replacing tips from this spot. This else helps with that.
                try:
                    first, rest = split_tipracks(self.tip_racks)
                except IndexError:
                    raise OutOfTipsError

        if starting_point and starting_point.parent != first:
            raise TipSelectionError(
                "The starting tip you selected " f"does not exist in {first}"
            )
        elif starting_point:
            first_well = starting_point
        else:
            first_well = first.wells()[0]

        next_tip = first.next_tip(num_channels, first_well)
        if next_tip:
            return first, next_tip
        else:
            return self.select_tiprack_from_list(rest, num_channels)
    
    def out_of_tips_error(self):
        "This is the default function called when the pipette runs out of tips" # Set this as the function to restore default behavior
        raise OutOfTipsError
        
    def prompt_refill_tips(self):
        "This function prompts the operator to refill tips"
        print('Please replace the following tip boxes:')
        for box in self.tip_racks:
            print(box)  # This script assumes you're using jupyter notebook. If you're not, you'll need to change this to pause the script
        input('Press Enter When Finished')
        for box in self.tip_racks:
            replace_tipbox(box)
        print('Done refilling tip boxes')


def replace_tipbox(tipbox, missing_tips = 0):
    '''Takes given tipbox and refills its tips, changing nothing else'''
    for well in tips.wells()[missing_tips:]:
        well.has_tip = True
        


# The end of the helper code. Now we provide an example of how to use the custom pipette
def run(protocol):
    # Generate the pipette and its tips. Adjust to your machine
    tips = protocol.load_labware("thermoscientificarttips_96_tiprack_200ul", 1)
    pipette = protocol.load_instrument("p300_single", "right", tip_racks=[tips])

    # Create the custom pipette
    custom_pipette = CustomPipette(pipette)

    # Have the pipette throw out 100 tips
    for _ in range(100):
        custom_pipette.pick_up_tip()
        custom_pipette.drop_tip()

if __name__ == "__main__":
    run(protocol)
