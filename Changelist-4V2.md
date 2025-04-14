# Changelist for 4V2 PCB

## Problems With 4V1a

None so far.

## Critical Changes for 4V2

None so far.

## Proposed Enhancements and Changes for 4V2

1) __Add a test pad to measure CPU 1.1V supply__

    There is plenty of room by C15 to add a test pad and silkscreen.

1) __Increase the size of R7__

    The new green "BSY" LED I had to spec is needlessly bright.
    Experiments will be needed to see what a suitable resistor would be.

1) __Need Bigger Drill for Keystone 4952 test points__

    The Keystone 1035 test points fit OK with their current drill size.
    The Keystone 4952 test points need a bigger hole than the 1035.
    Check if the 4952 test point has the right size drill in the library.

1) __Add GPS Module Designator to Silkscreen__

    The GPS M2 module designator is missing from the silkscreen layer.

1) __Move Spare1 and Spare2__

    Spare1 and Spare2 pads should get moved out from underneath the Pico module to be colocated with the Spare0 pad.

1) __Add a Plain LED to SpareX Pad__

    Add a normal LED (i.e. not a WS2812) to one of the SpareX pads.
    The built-in LED controlled by the WiFi module takes a considerable amount of time and CPU effort before it can be used.
    It defeats the purpose of being an early indication of life.

    Add an LED with current-limiting resistor operating in pulldown mode (GPIO output of 0 means 'on').
    Place the LED beside the WS2812 to make it more visible under the motorbike seat.
    Leave the SpareX pad in place even with the LED added.
