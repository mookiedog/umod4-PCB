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

1) __GPS would disable UART during debug sessions__ Fixed by adding a pullup resistor to the PicoW GPS TX pin to hold the TX pin high by default after RESET. See below for more details.

## V4.1 Proposed Changes & Enhancements
1) __Broken Power Supply Plan__ I think the power supply plan is broken. The requirements are:
    1) Bench testing:
        1) Everything on Umod4 board should be powered whenever USB power is plugged into the PicoW, regardless of presence of +12 unswitched or ECU 5V
    2) In system:
        1) When +12 unswitched is present, the board can decide if it wants to be powered or not
            1) it should stay powered if it has work to do, like transfer a file via wifi or finish writing data to SD card
        1) If the voltage level on +12 unswitched indicates that it is on a battery charger, then the system could decide to remain powered indefintely so that firmware updates could be pushed at anytime via wifi without having to walk out to the garage and turn the ignition on or something like that

        1) if +5_ECU is present, the ignition is on and the system must remain powered Because keep_alive is driven through a diode, there is no way for the WP to screw up and drive keep_alive low when +5_ECU is present. The WP can't accidentally turn the power off. 
            1) during bench testing, if the ECU is powered via +12V switched (the normal 12V input wiring into the ECU), it's as though the ignition key is ON because +5_ECU will be present due.

        1) If +5_ECU is NOT present, as might happen if a bare Umod4 board was powered on a bench, not in an ECU, we would still like the system to run. This could be accomplished via a diode from VSYS

1) __Add ability to measure +12 Unswitched voltage__ Note: The Pico only has 4 A/D inputs located on GPIOs [26..29].
    1) This will require moving the pushbutton off GPIO26(currently SPARE1)
    1) Should consider moving some of the other signals to different GPIOs so that the analog pins remain free
        1) GPS_PPS
        1) EP_RUN
        1) SPARE0
        1) GPIO29 cannot be used by Umod4: it is used by PICO_W to measure VSYS and does not have a wiring connection off the PicoW PCB
1) __Add ability to measure SD Card Current Draw__
1) __Add ability to measure total 3V3 consumption__
1) __Add ability to measure VSYS current__
1) __Add the ability to power-control the SD card__ During testing, I have seen cards that fail spectacularly after bad commands to the point that they need a power-cycle to continue. It would also make the whole hot-plug thing a bit safer because the hotPlug manager would keep power off while a socket was empty, only powering it up after a card had been inserted for some amount of time. It should only need a logic-level PFET to implement it.
    1) There are lots of commodity USB power switch controllers that would do perfectly. They are logic-level controlled, have ESD protection, surge management, etc and cost 10 cents at LCSC.
1) __Add decoupling capacitance to the SD card power__ Meed the spec as defined in the SD card spec specification 3.01, section E.2. Basically, use a 47 uF cap on the unswitched (incoming power) side of the PFET and a 4.7uF cap followed by a 0.1 uF cap on the switched side of the PFET.
7)	__A little more clearance is needed for the mainboard capacitor near the silkscreen “od 4V”__
8)	__More clearance for mainboard capacitor by the GND test point near JP4__
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

1) __Replace the MicroSD socket with something from LCSC__
    1. The current version was used because I had some in stock and could hand solder it after getting the board back from JLCPCB. The old one is perfectly functional, it's just that if I get something from LCSC, it will be cheaper and JLCPCB will be able to include it in their assembly process

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

1) __GPS Disables UART During Debug Sessions__
    1) It turns out that a NEO-8 GPS will disable its UART interface if it sees too many framing errors on its RX pin within 1 second. This can happen if the RX pin is held to '0' for some reason. This should not be a problem in a real system, but while debugging, when the system is stopped at the initial breakpoint in main(), the RX pin will be at '0' until the system boots enough to init the serial interface to its idle state of '1'.
    1) Fix: Added a 10K pullup to the UART0_TX signal that drives the GPS RX pin. 

### V4.1 Enhancements

1)	__RP2040: Made HC11 RESET Control Permanent__  The RP2040 should be the only thing controlling HC11 RESET.
    1. Get rid of the solder jumper option
    1. Moved the GND test point to where the old SPARE testpoint was located

1) __Replaced J3 & J4 with a 10-pin 0.050 SWD Header__
    1. Do not stuff squid pins or 10-pin header pins - for SW developers only!

1)	__Changed the WS2812 package from 5050 to 2020__
    1. See WS2812C-2020

1) __Add squid pins for J3/WP for use with PicoProbe__

1)	__Add a test point to scope the buffered E signal__
    1. scoping this signal was beneficial during bringup
    1. Added a 0.028 via as a test point. The size 0.028 matches the DIP socket and is large enought to not be tented.

1)	__Add a test point for EP GPIO24/TX so that it can be used to measure RP2040 CLKOUT__
    1. Useful during bringup
    1. Used a 0.028 via so it would not be tented. Also made the corresponding RX uart signal the same drill size so both signals could be scoped at these test points
    1. I'm not bothering with adding a test pad for the PicoW because a scope can attach directly to the GPIO24 pin if desired.

1)	__HC11 XTAL hole needs to move to the left and be as tall as possible__
    1. Moved the left side of the hole to add an additional 0.050 inch.
    1. Increased the hole size by 0.010 on top and bottom

9)	__GPS mounting hole does not line up very well__
    1. The problem was the drawing did not spec the distance between the solder holes and the mounting hole. Measuring the real parts added about 0.7mm to the distance from the original footprint. Note that fixing this required extending the board upwards by 0.050 to get enough clearance between the mounting hole and the edge of the board.

1) __Delete S2__
    1. Never used. Since it is an analog pin, it is better served for a different purpose

## Discarded Changes

The following changes were under consideration, but discarded for various reasons.

1)	__Series termination resistor on E is not required__
    1. It makes the signal a bit cleaner, but the ADDR signals are not much worse.
    1. Determination: The resistor is essentially free and everything works, so I'm leaving it alone.

2) __Add 10-pin debug header for WP__
    1) Determination: just use the squid pins built right on top of the PicoW where they can be accessed with right angle header pins.
