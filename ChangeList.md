# Changelist for 4V1

## Version 4V1a PCB is Being Fabricated

The final 4V1a changes:

* Added an indicator LED to show when +5_ECU was present
* Added indicator marks for the LEDs on the board to aid in parts placement at JLCPCB
* Changed the WS2812 LED from a 2020 package back to the 5050 package.
JLCPCB said that the 2020 package was "difficult" for them to manage.
In contrast, the 5050 package is easy to hand solder.

As far as fabrication goes, the following parts will get hand soldered after receiving the boards:
* WS2812-5050
* Hirose SD Card holder

The SD card holders were out of stock.
The WS2812 5050 cannot be installed using the PCBA economic process because they need to be baked before installation.
Since both parts are JLCPCB extended parts, leaving them off saves $6 in extended parts fees.
The total cost at JCLPCB was just over $10 per board, including parts and assembly, not including shipping.



Captures problems and workarounds with the existing 4V0b PCB revisions. Identifies potential improvements for future revisions.

## Note: Power Supply Simplification

The power supply changes from the previous interim checkin have been deleted.
To get umod4 power and the resulting wifi connection, it turns out that a much simpler solution is to just use a USB extension cable that plugs into the Pico W.
If the extension cable gets plugged into a USB charger while parked, the umod4 will be active
while the rest of the ECU remains powered off.

## V4.0b Resolved Problems

The following issues were detected and resolved during bringup:

1) __HC11_RESET_IN circuitry is not permitting HC11 to run__

    Issue: ECU uses a pullup on HC11_RESET, but the voltage divider formed by R8/R9 is too much of a load to let HC11_RESET to go high enough to let the ECU run
    The HC11_RESET_IN feature is not usable, had minimal usefulness in the first place, and will be removed in the next version.

    Workaround: Remove R9.

1) __ECU can’t operate without SW running on a PicoW to enable the bus buffers via ADDR_EN__

    This was annoying during early development, and adds another point of failure if the WP/PicoW were to fail during operation.

    Workaround: Remove R17 and ground the resistor pad closest to the ‘7’ of the silkscreen ‘R17’.
    This permanently enables the bus driver instead of requiring that the PicoW must enable the bus buffers via software.

    The bus buffers will be enabled whenever the ECU +5V is present.

1) __EP RP2040 does not boot reliably__

    Issue: The specific crystal spec'd on the BOM does not start up as fast as the Pico bootrom expects.
    See [here](https://forums.raspberrypi.com/viewtopic.php?t=334143) for more information on the topic.

    Fix: No PCB fix is required. The umod4.h board file needs to define the following symbol:

            #define PICO_XOSC_STARTUP_DELAY_MULTIPLIER 64

1) __EP SWD Debugging does not work__

    Issue: The SWD CLK and DAT silkscreen was correct, but the wiring to the pins was swapped.

    Workaround: When attaching a debugger, swap the squid connections for SWD CLK and SWD DAT.

1) __GPS would disable UART during debug sessions__

    Fixed by adding a pullup resistor to the PicoW GPS TX pin to hold the TX pin high by default after RESET.
    A GPIO pullup controlled by firmware is not suitable because the debugger will not let firmware run after RESET.

    See below for more details.

## V4.1 Proposed Changes & Enhancements

Closed.

## V4.1 Implemented Changes, So Far

### Critical Changes

1) __Delete RESET_HC11_IN__

    The signal is not not necessary: the WP knows when EP is running because the EP will tell it so.

    Fix: Deleted the signal along with R8 and R9.

    Note: This fix frees up two more GPIOs for the WP.

1) __Fix wiring connections on SWD squid pins__

    CLK and DIO were swapped but the silkscreen was correct.

    Fix: Fix silksreen, also moved the silkscreen up a bit to be more visible.

1) __ADDR_EN should not be driven by PicoW__

    Reasoning: Bike should run even if PicoW is dead or missing.

    Fix: R17 has been removed and the ADDR_EN signal permanently grounded.

1) __GPS Disables UART During Debug Sessions__

    It turns out that a NEO-8 GPS will disable its UART interface if it sees too many framing errors on its RX pin within 1 second.
    This can happen if the RX pin is held to '0' for some reason.
    This should not be a problem in a real system, but while debugging, when the system is stopped at the initial breakpoint in main(), the RX pin will be at '0' until the system boots enough to init the serial interface to its idle state of '1'.

    Fix: Added a 10K pullup to the UART0_TX signal that drives the GPS RX pin

### V4.1 Changes and Enhancements

1) __Added Indicator LED for +5_ECU__

    An indicator light was added to show when +5 ECU power is present.
    This light would be off when the umod4 is powered from a USB cable attached to the Pico board and it would be on whenever the ignition key is on.

1) __Allow For SD Card Access Using 4-bit SPI Mode__

    The 4V0 PCB accessed the SD card using the 1-bit SPI mode subset built into all SD cards.
    The 4V0 wiring scheme used the R2040 SPI1 silicon unit to perform SPI transfers.
    It could have also used a PIO program to perform the transfers, but using the silicon block works just fine.

    The 4V1 board adds additional wiring to allow for 4-bit IO to the SD Card using PIO libraries that can be found on the web.
    The 4-bit mode should greatly increase the transfer rate from the SD card when uploading log files via WiFi.

    The wiring has been added in a fashion that allows the SD card to be accessed via 1-bit mode and using silicon SPI unit #1, or in 4-bit mode via PIO.
    A requirement of the PIO code is that DAT0 through DAT3 must occupy 4 consecutive GP pins where DAT0 is the lowest numbered GP pin of the four.

    If for some reason, the 4-bit PIO code cannot be made to work, 1-bit SPI mode will work as before.

    The table below shows how the wiring will be done so that the SD card can be accessed via RP2040 hardware SPI unit #1, as well as a PIO implementation of 4-bit mode:

| GP | SPI Unit 1 | SD Card in 1-Bit SPI Mode | SD Card in 4-Bit Mode |
|--|--|--|--|
| GP10 | SCK | CLK | CLK |
| GP11 | TX | CMD/MOSI | CMD |
| GP12 | RX | MISO | DAT0 |
| GP13 | N/A | N/A | DAT1 |
| GP14 | N/A | N/A | DAT2 |
| GP15 | N/A | CS | DAT3 |

1) __Changed C27 Part Number__

    The previous part number C368809 is a JCLPCB extended part.
    The new part number C23733 is still a Samsung capacitor 4.7 uF, 10V, X5R but is available as a JCLPCB basic part.

1) __Changed DBG_BSY LED Package__

    The package for the LED connected to DBG_BSY was changed from 0603 to 0805.
    The original 0603 LED is not available anymore.
    The selection of basic LED parts is quite limited.
    The only emerald green LED available as a basic part comes in an 0805 package: [C2297](https://jlcpcb.com/partdetail/Hubei_KentoElec-KT0805G/C2297).

1) __Swapped Pico W End-for-End__

    This change allows a mini USB cable be plugged into the Pico W even with the ECU lid attached.
    The other end of the USB cable can be plugged into a standard 5V USB charger while the bike is parked.
    When connected to a charger, the Pico W and its WiFi connection will be active even when the key is off.

    This change had the happy side effect of making the wiring flow much simpler by getting the LCD and SD Card closer to SPI pins after swapping their SPI units.
    The LCD is now driven by SPI0 and the SD Card by SPI1.
    It also made sense to swap the GPS Uart and the RP2040 Uart connections at the same time, for the same reasons.
    The GPS now uses UART 1, and the RP2040 serial connection uses UART 0.

    Other connections got moved around.
    The umod4 software will need to be updated for the pin changes.

1) __RP_RUN signal was renamed EP_RUN__

    This happened at some point in the past, just documenting the change here.

1) __RP2040: Made HC11 RESET Control Permanent__

    Under normal circumstances, the RP2040 should be the only thing controlling HC11 RESET.
    This has the benefit that an ECU with a malfunctioning Pico W would still be rideable as long as the RP2040 was able to boot.

    Note that the HC11 RESET signal *can* still be controlled by PicoW software, but it is expected that the PicoW would only do that under exceptional circumstances.
    For example, if the PicoW was to use the SWD debug interface to reflash the RP2040, the PicoW would want to assert HC11 RESET before taking control of the RP2040 via the debug unit.

    1. Get rid of the solder jumper option
    1. Moved the GND test point to where the old SPARE testpoint was located

1) __Deleted SWD debug access via J3 & J4__

    J3 and J4 were 4-pin JST connectors that connected to RP2040 and PicoW debug ports.
    A decision was made that squid pins are fine, especially in conjunction with the Raspberry Pi debugger unit.

    1. Do not stuff squid pins during assembly - they can easily be added after the fact.
    Normal users will not need them, only SW developers.

1) __Added a Real Footprint for EP SWD Squid Pins__

    The original squid pin connections were just vias on the board, carefully named & placed.
    They are now a real 1x3 pinheader.

1) __WS2812 Moved for Better Visibility__

    Moved the package to the front edge of the PCB for better visibility.
    As mentioned earlier, the 5050 package is still being used because JCLPCB says that the 2020 package is 'difficult' for them.
    The 5050 package cannot be sent through the economic PCB assembly service because it needs to be baked.
    These LEDs will be hand soldered.

1) __Add squid pins for J3/WP for use with PicoProbe__

1) __Add a test point to scope the buffered E signal__

    Scoping this signal was beneficial during bringup so a testpoint would make it easier.

    1. Added a 0.028 via as a test point.
    The size 0.028 matches the DIP socket and is large enought to not be tented.

1) __Add a test point for EP GPIO24/TX so that it can be used to measure RP2040 CLKOUT__

    Having access to CLKOUT was useful during bringup.

    1. Used a 0.028 via so it would not be tented. Also made the corresponding RX uart signal the same drill size so both signals could be scoped at these test points
    1. I'm not bothering with adding a test pad for the PicoW because a scope can attach directly to the GPIO24 pin if desired.

1) __HC11 XTAL hole needs to move to the left and be as tall as possible__

    The crystal is not in a particularly fixed location according to my collection of ECUs.
    There is benefit in making the XTAL hole a bit bigger to tolerate placement issues.

    1. Moved the left side of the hole to add an additional 0.050 inch.
    1. Increased the hole size by 0.010 on top and bottom

1) __GPS mounting hole does not line up very well__

    The problem was the drawing did not spec the distance between the solder holes and the mounting hole.
    Measuring the real parts added about 0.7mm to the distance from the original footprint.
    Note that fixing this required rotating the board so that the cable heads off towards
    the ignition transistors.
    It was either that, or make the board slightly taller.

1) __Delete S2__

    Never used. Since it is an analog pin, it is probably better reserved for future use.

1) __Flipped JST Socket J5 (The auxiliary/LCD SPI port)__

    This makes it way easier to hand solder if anyone wants to add it.

1) __Make decoupling capacitance match SD card spec__

    As defined in the SD card spec specification 3.01, section E.2: use a 4.7uF cap followed by a 0.1 uF cap.

1) __Moved HC11 reset control parts from under the Pico W__

    This allows the module to be soldered down without a socket, although it seems unlikely that this would happen.
    For example, the Pico W could be replaced with a Pico 2 W (or whatever comes after that) if the module is socketed.

1) __More clearance for mainboard capacitor by the GND test point near JP4__

    Made a small notch in the side to allow for the capacitor a bit of extra room.

1) __Added TP2 GND Testpoint__

   Somehow, TP2 GND testpoint got left off the original PCB.
   Bringup confirmed that it would be handy to have one on the lower right for attaching scope probes.

## Deferred Changes

These changes might be reconsidered in the future, but are not going to be included on the next revision.

1) __Replace the MicroSD socket with something more modern from LCSC__

    The current Hirose DM3AT-SF-PEJ was used because I had some in stock and could hand solder it after getting the board back from JLCPCB.
    That Hisrose part is just barely available from LCSC, but it is available from Digikey in great quantity.
    If JLCPCB runs out of them, I can always get them from Digikey and then hand solder them.

    The main issue with designing in a new part is that the footprints are all unique, complicated, and weird.
    My Hirose footprint is a known quantity and works great.

1) __Add the ability to power-control the SD card__

    During testing, I have seen cards that fail spectacularly after bad commands to the point that they need a power-cycle to continue. It would also make the whole hot-plug thing a bit safer because the hotPlug manager would keep power off while a socket was empty, only powering it up after a card had been inserted for some amount of time. It should only need a logic-level PFET to implement it.

    1) There are lots of commodity USB power switch controllers that would do perfectly. They are logic-level controlled, have ESD protection, surge management, etc and cost 10 cents at LCSC.

1) __Add a WS2812 to the EP RP2040__

    Use color patterns to indicate things like boot/run/flash-in-progress/ECU-heartbeat.

    This might be handy, but is slightly troublesome:

    1. The WS2812 needs to be on a regular GPIO so that it can be driven by PIO.
    It would either require sharing a pin for DBG_BSY and WS2812 DI, or I would need to move DBG_BSY to a QSPI pin like SCK.

## Discarded Changes

The following changes were under consideration, but discarded for various reasons.

1) __Series termination resistor on E is not required__

    It makes the signal a bit cleaner, but the ADDR signals are not much worse.

    Determination: The resistor is essentially free and everything works, so I'm leaving it alone.

1) __Add 10-pin debug header for WP__

    Determination: Not required.

    Use a cheap, standard Raspberry Pi debug unit and attach it using the squid pins built right on top of the PicoW.

    The 10-pin connector was convenient if using a Segger J-Link debug unit, but the RPi debugger is cheaper and much easier to source.

1) __Power Measurements__
    1) __Add ability to measure SD Card Current Draw__
    1) __Add ability to measure total 3V3 consumption__
    1) __Add ability to measure VSYS current__

    Determination: I can't measure 3.3V accurately anyway because it will not reflect the 3.3V consumed by the PicoW itself.
    I already know that modern SD cards consume almost nothing at idle.
    The GPS power is interesting, but I can easily get just that because it is on a connector.
    It might be nice to measure VSYS, but I can pretty much calculate it from the input supply and assume an 80% to 90% efficient power conversion process.
