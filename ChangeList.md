# Changelist

Captures problems and workarounds with the existing 4V0b PCB revisions. Identifies potential improvements for future revisions.


## V4.0b Problems

The following issues needed to be dealt with during bringup:
1)	HC11_RESET_IN is not permitting HC11 to run
    1. Issue: ECU uses a pullup on HC11_RESET, but the voltage divider formed by R8/R9 is too much of a load to let HC11_RESET to go high enough to let the ECU run
    1. Workaround: Remove R9.
    1. The HC11_RESET_IN feature is not usable, had minimal usefulness in the first place, and will be removed in the next version.
2)	ECU can’t operate without SW running on a PicoW to enable the bus buffers. This was annoying during early development, and adds another point of failure if the WP/PicoW were to fail during operation.
    1. Workaround: Remove R17 and ground the resistor pad closest to the ‘7’ of the silkscreen ‘R17’. This permanently enables the bus driver instead of requiring that the PicoW must enable the bus buffers via software. 
    1. The bus buffers should be enabled whenever the ECU +5V is present.
3)	RP2040 does not boot reliably
    1. Issue: The specific crystal spec'd on the BOM does not start up as fast as the Pico bootrom expects. See [here](https://forums.raspberrypi.com/viewtopic.php?t=334143) for more information on the topic
    1. Fix: No PCB fix is required. The umod4.h board file needs to define the following symbol:

            #define PICO_XOSC_STARTUP_DELAY_MULTIPLIER 64
4)	SWD Debugging does not work
    1. Issue: The SWD CLK and DAT silkscreen was correct, but the wiring to the pins was swapped.
    1. Workaround: When attaching a debugger, swap the squid connections for SWD CLK and SWD DAT

## V4.1 Proposed Changes

1) __Add squid pins for J3/WP for use with PicoProbe__
1) __Add a 10-pin 0.050 SWD connector for both the EP and WP__
    1. Do not stuff squid pins or 10-pin header pins – they would only be for people developing firmware needing a debugger, and it would require a hand-soldering step during JLCPCP fabrication
1)	__HC11 XTAL hole needs to move to the left and be as tall as possible__
    1. examine other ECUs to see how the XTAL's location is kind of variable
7)	__A little more clearance is needed for the capacitor near the silkscreen “od 4V”__
8)	__More clearance for mainboard cap by the GND test point near JP4__
9)	__GPS mounting hole does not line up very well__
10)	__It looks like the series termination resistor on E is not required__
    1. It makes the signal a bit cleaner, but the ADDR signals are not much worse.
11)	__Consider adding a Power Supply__
    1. Power the PW from unswitched +12
        1. PW needs to be able to remain powered after ignition is switched off
        1. PW needs to be able to switch itself off when desired
        1. PW should always switch itself ON when the ECU gets powered
    1.	RP2040 should be powered from diode-combined ECU +5 or PW 3.3V
        1. With bike off, the RP2040 needs to be powered so that the PW can reflash it
        1. When ECU +5 is present, the FE should be powered even if the PW has no power for some reason
    1.	This would require a 5V to 3.3V converter, perhaps with a diode combiner on the +5 source

13)	__Add a WS2812 to the RP2040 using one of the QSPI pins (probably SCK)__ Use color patterns to indicate things like boot/run/flash-in-progress/ECU-heartbeat.
    1. Using a QSPI pin would imply that either:
        1. The entire EP program would need to be RAM-resident, or
        1. At a minimum, the WS2812 driver would need to be RAM-resident while locking out interrupts (this choice seems like a bad idea though)
14)	__Change the WS2812 package from 5050 to 2020__
    1. See WS2812B-2020
15)	__Consider moving the parts from under the Pico W so it could be mounted directly to the board without the socket or pins__
    1. would reduce the height of the board, although it appears to not be a problem at the moment
16)	__Add a test point for GPIO24/TX so that it can be used to measure RP2040 CLKOUT__
    1. Useful during bringup
17)	__Add a test point to scope the buffered E signal__
    1. scoping this signal was beneficial during bringup
1) __Replace the MicroSD socket with a more modern one__
    1. The current version was used because I had some in stock and could hand solder it after getting the board back from JLCPCB. The old one is perfectly functional, it's just that newer MicroSD sockets are a bit smaller.

## V4.1 Implemented Changes, So Far

### V4.0 Critical Changes
1)	__Delete RESET_HC11_IN__
    1.	The signal is not not necessary: the WP knows when EP is running.
    1.	Deleted the signal along with R8 and R9. That frees up two more GPIOs for the WP.
1)	__Fix wiring connections on SWD squid pins__: CLK and DIO were swapped but the silkscreen was correct
    1. Verify that the pins are wired as desired to the other connectors, too!
    1. Moved the silkscreen up a bit to be more visible
3)	__ADDR_EN should not be driven by PicoW__
    1. Bike should run even if PicoW is dead or missing
    1. R17 has been removed and the ADDR_EN signal permanently grounded.

### V4.1 Implemented Enhancements

1)	__RP2040: Make HC11 RESET Control Permanent__  The RP2040 should be the only thing controlling HC11 RESET.
    1. Get rid of the solder jumper option
    1. Moved the GND test point to where the old SPARE testpoint was located

## Discarded Changes

The following changes were under consideration, but discarded for various reasons.

    <<None, so far>>