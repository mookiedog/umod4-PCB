# Changelist Tracker for 4V3 PCB

## Outstanding Critical Issues

None

## Outstand Major Issues

None

## Outstanding Minor Issues

1) U8 is Missing P1 Indicator

    Needs a silkscreen indication of P1. Not critical because the package is unidirectional, but still.

## Completed Issues

1) LED5/6 Orientation Indicators

    The non-standard WS2812 pinout marking continues to cause trouble at JLCPCB when getting the parts oriented for placement. The JLCPCB engineers seem to want it marked like a diode with + for VCC (pin 1) and - for GND (pin 3)
    I added "+" signs to mark pin 1 in the fashion that JCLPCB seems to want.

2) 4V2 DISK_BSY LED is active LOW (4V1 was active HIGH).

    Fixed in firmware, plus a bodge on all 4V1 boards.

    Added another 3K3 bodge pulldown resistor that parallels the 4V1 DISK_BSY LED and current limiting resistor to GND. This allows a 4V1 board to identify itself via the new bodge pulldown: A 4V2 board does not implement this pulldown. Putting the identification burden on the 4V1 boards makes sense because there will only ever be the 5 of them. The 4V2, 4V3 boards require no changes.

3) Add a test point for VDD_SD (Switched SD card power)

    Allows for verification of power state changes, as well making it easier to see weird things like the card getting backpowered via the SDIO signal pins.

4) Resized all 0402/0603/0805 pads

    JLCPCB was complaining that the 0402 and 0603 pads were too large. Indeed, they were pretty big. They have all been replaced with standard-sized pads. As part of the fix, library robins-v7 has been updated with generic RES and CAP parts available in packages SMD-0402-NOM, SMD-0603-NOM, SMD-0805-NOM. These parts should be used from now on.

5) Resistors are all changed from 0402 to 0603

    As part of the pad size changes (above), all resistors were resized to be 0603. The 0603 parts can take almost double the power dissipation, not that it really matters. It would make them easier to be replaced, if needed. The new 0603 footprint is barely bigger than the old 0402 footprint so it caused no problems.
