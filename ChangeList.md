# Changelist

Captures problems and workarounds with the existing 4V0b PCB revisions. Identifies potential improvements for future revisions.

## Power Supply Changes

At the moment, the Umod4 is powered from the PicoW, indirectly powered by switched +5V. When the key switches off, the PicoW loses power, meaning that the EP RP2040 loses power too.

Proposal

1) Add a new power supply with an active high enable, which is quite common.
1) The regulator is always powered by unswitched +12V coming in through a fuse, probably with some noise-reduction circuitry too
1) The enable signal will be powered by switched +5V arriving through a diode, then a pulldown resistor to the enable pin.
1) When the key is switched ON, the +5V signal will override the pulldown, the regulator will start, and the WP and EP will boot.
1) As each of the EP and WP boot, they will configure an IO pin that drives a shared KEEP_ALIVE signal through a diode that is wired to the pulldown resistor. By driving KEEP_ALIVE to 3.3V, the power supply remains enabled, even if +5V goes away.
    1) if +5V fails before the processor has booted to the point of configuring KEEP_ALIVE, then the umod4 power will fail. This is not a problem because the system will not yet be in a state where the power loss will harm anything.
1) When +5V fails, the WP will notice.
    1) The EP can continue to do what it wants, or it could shut down to save a few mA.
    1) when the WP decides that it has nothing to do, it programs the KEEP_ALIVE GPIO driver to be disconnected. The pulldown on KEEP_ALIVE will disable the regulator.
    1) Reasons to stay powered up:
        1) Timeout-related: like "stay alive for 5 mins in case the user connects via bluetooth to do something"
        1) stay alive if the board detects that it is home by being able to connect to the home wifi network
        1) check and see if there is anything to do because it is 'home', like check for software updates
        1) unload log data from SD card to a data log server via the home network
    1) Once everything is taken care of, it might wait for an additional 5 mins and then shut down.
    1) Another possibility would be to stay powered as long as the unswitched +12 supply showed indications of being connected to a charger, or at least to stay powered longer before shutting down due to inactivity


## V4.0b Resolved Problems

The following issues were detected and resolved during bringup:
1)	__HC11_RESET_IN circuitry is not permitting HC11 to run__
    1. Issue: ECU uses a pullup on HC11_RESET, but the voltage divider formed by R8/R9 is too much of a load to let HC11_RESET to go high enough to let the ECU run
    1. Workaround: Remove R9.
    1. The HC11_RESET_IN feature is not usable, had minimal usefulness in the first place, and will be removed in the next version.
2)	__ECU can’t operate without SW running on a PicoW to enable the bus buffers__ This was annoying during early development, and adds another point of failure if the WP/PicoW were to fail during operation.
    1. Workaround: Remove R17 and ground the resistor pad closest to the ‘7’ of the silkscreen ‘R17’. This permanently enables the bus driver instead of requiring that the PicoW must enable the bus buffers via software. 
    1. The bus buffers should be enabled whenever the ECU +5V is present.
3)	__EP RP2040 does not boot reliably__
    1. Issue: The specific crystal spec'd on the BOM does not start up as fast as the Pico bootrom expects. See [here](https://forums.raspberrypi.com/viewtopic.php?t=334143) for more information on the topic
    1. Fix: No PCB fix is required. The umod4.h board file needs to define the following symbol:

            #define PICO_XOSC_STARTUP_DELAY_MULTIPLIER 64
            
4)	__EP SWD Debugging does not work__
    1. Issue: The SWD CLK and DAT silkscreen was correct, but the wiring to the pins was swapped.
    1. Workaround: When attaching a debugger, swap the squid connections for SWD CLK and SWD DAT

## V4.1 Proposed Changes & Enhancements
1) Is it even worth adding the 10-pin JTAG and squid pins for the WP? Why not just attach squid pins to the Pico-W itself? The only reason that the EP has a 10-pin and squid pins is because it is a bare chip
    1) A Pico-W only supports squid pins
    1) Squid pins work for the PicoDebug unit, old style or CSMIS
    1) I have not seen a compelling reason to use a JLink, but it may come

1)	__HC11 XTAL hole needs to move to the left and be as tall as possible__
    1. To do: examine other ECUs to see how variable the XTAL's location is
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

13)	__Add a WS2812 to the EP RP2040__ Use color patterns to indicate things like boot/run/flash-in-progress/ECU-heartbeat.
    1. This is slightly troublesome:
        1. The WS2812 needs to be on a regular GPIO so that it can be driven by PIO. It would either require sharing a pin for DBG_BSY and WS2812 DI, or I would need to move DBG_BSY to a QSPI pin like SCK.
        1. The WS2812 needs a +5V supply, which is nowhere near the RP2040
15)	__Consider moving the parts from under the Pico W so it could be mounted directly to the board without the socket or pins__
    1. would reduce the height of the board, although it appears to not be a problem at the moment
16)	__Add a test point for GPIO24/TX so that it can be used to measure RP2040 CLKOUT__
    1. Useful during bringup
17)	__Add a test point to scope the buffered E signal__
    1. scoping this signal was beneficial during bringup
1) __Replace the MicroSD socket with a more modern one__
    1. The current version was used because I had some in stock and could hand solder it after getting the board back from JLCPCB. The old one is perfectly functional, it's just that newer MicroSD sockets are a bit smaller.

## V4.1 Implemented Changes, So Far

### Critical Changes
1)	__Delete RESET_HC11_IN__
    1.	The signal is not not necessary: the WP knows when EP is running because the EP will tell it so.
    1.	Deleted the signal along with R8 and R9. That frees up two more GPIOs for the WP.
1)	__Fix wiring connections on SWD squid pins__: CLK and DIO were swapped but the silkscreen was correct
    1. Verify that the pins are wired as desired to the other connectors, too!
    1. Moved the silkscreen up a bit to be more visible
3)	__ADDR_EN should not be driven by PicoW__
    1. Bike should run even if PicoW is dead or missing
    1. R17 has been removed and the ADDR_EN signal permanently grounded.

### V4.1 Enhancements

1)	__RP2040: Made HC11 RESET Control Permanent__  The RP2040 should be the only thing controlling HC11 RESET.
    1. Get rid of the solder jumper option
    1. Moved the GND test point to where the old SPARE testpoint was located

1) __Replaced J3 & J4 with a 10-pin 0.050 SWD Header__
    1. Do not stuff squid pins or 10-pin header pins - for SW developers only!

1)	__Changed the WS2812 package from 5050 to 2020__
    1. See WS2812C-2020

1) __Add squid pins for J3/WP for use with PicoProbe__

## Discarded Changes

The following changes were under consideration, but discarded for various reasons.

    <<None, so far>>