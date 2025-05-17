# Changelist for 4V2 PCB

## Problems With 4V1a

None so far.

## Critical Changes for 4V2

None so far.

Note that 4-bit SD card operations have not been implemented yet.
A 4V2 PCB should not be built until the feature is proven to work or not.

## Proposed Enhancements and Changes for 4V2

1) __Replace RP2040 with RP2354A__

    One problem that has been annoying to this point is that I would have really liked to add a WS2812 LED for status reporting, but there is no spare GPIO on the standard package.
    The RP2350 is available in a larger package with more GPIO.

    Upsides:

    * The Hazard RISC-V core has 16 registers available for the fake EPROM code.
        Essentially doubling the number of general purpose CPU registers compared to the Cortex should make it easier to write more complicated versions of the fake EPROM, should additional features be required.
    * The RP2354A has 2 megabytes of flash built into it.
This wold allow me to delete my own 16 megabyte SPI flash and decoupling cap.
The smaller capacity should not be a huge problem.

    Downsides:

    * Swapping the package represents a very big change to hardware and software:
      * Rewriting the fake EPROM code in RISC-V would take some effort.
      The Cortex M33 is not really suitable for use in a cycle-counting firmware.
      * There is not a lot of spare real estate in that location on the PCB for a larger package.

    Ultimately, it seems like a lot of work to get a status LED.
    The simpler solution might be to parallel the original DBG_BSY LED with a WS2812 and accept that both features will not be available at the same time.
    See "Consider Adding WWS2812 LED", below.

    At the moment, the RP2040 is totally capable of doing everything it needs to do.
    If future features require a faster processor, the RP2040 could be up-clocked from its current 125 MHz to as much as 200 MHz.
    If the future required more RAM, then an RP2350 becomes more viable, at least in its small package.

    At the moment, this feature seems unlikely to survive the cut.

1) __Add a test pad to measure CPU 1.1V supply__

    There is plenty of room by C15 to add a test pad and silkscreen.

1) __Need Bigger Drill for Keystone 4952 test points__

    The Keystone 1035 test points fit OK with their current drill size.
    The Keystone 4952 test points need a bigger hole than the 1035.
    Check if the 4952 test point has the right size drill in the library.

1) __Add GPS Module Designator to Silkscreen__

    The GPS M2 module designator is missing from the silkscreen layer.

1) __Move Spare1 and Spare2__

    Spare1 and Spare2 pads should get moved out from underneath the Pico module to be co-located with the Spare0 pad.

1) __Add Footprints to Drive Plain LEDs to all SpareX Pads__

    Reasoning: The built-in LED controlled by the WiFi module takes a considerable amount of time and CPU effort before it can be used.
    It defeats the purpose of being an early indication of life.

    Add footprints to allow installing a normal LED (i.e. not a WS2812) to all SpareX pads in addition to the wire attachment pad.
    The new LEDs could be used for debugging purposes or get integrated into the operation of the system, if needed.

    Add an LED with current-limiting resistor operating in pulldown mode (GPIO output of 0 means 'on').
    Place the new LEDs beside the WS2812 to make it more visible under the motorbike seat.

1) __Add More WS2812 LEDs__

    In addition to the WS2812 used to display WP status, daisy chain a couple more WS2812 RGB LEDs to display:
    * SD card status
    * GPS status
    * EP data stream status (could flash it like a hard disk activity light)

1) __Consider Using 2mm WS2812C Parts__

    Last time I looked, JLCPCB was not real happy if I spec'd the smaller parts.
    I believe the issue was that they felt they needed to bake the parts before soldering them, which I'm sure would be an annoying manual problem for them.
    Since then: it appears that JLCPCB also wants to bake the 5050 parts.
    This means that any WS2818 parts regardless of package need to be manually soldered after receiving assembled boards from JLCPCB.
    If that's the case, there is no benefit in spec'ing 5050 parts.
    The only remaining issue is whether or not the 2020 parts can be hand-soldered.
    The 5050 parts are easy to hand solder.
    The 2020 parts look more difficult to place, but given that the pads are castelleated and have only 2 pads per side, it should be doable.

1) __Consider WS2812 Status LED For EP__

    In normal use on the bike, the DBG_BSY LED has two purposes:
    * to flicker a 'hello' indication at boot time to prove to a human being that the EP is alive
    * to drive the memory cycle timing information so an o'scope can see it

    I would really like to give the EP a mechanism to display some basic status information using an RGB LED.
    For example, things like this:

    * Booting
    * Loading EPROM image
    * HC11 out of RESET
    * HC11 operating properly
    * panic situation

    If I just parallel a WS2812C with the DBG_BSY LED, I run into trouble because the frequency of the EPROM operations in conjunction with DBG_BSY changing state looks enough like a data stream to the WS2812 that it will experience unexpected color state changes.

    The simplest solution is to build the code so that it either drives DBG_BSY for scope timing verification, or it uses the same IO to drive a WS2812 for status info.
    If set up to drive scope timing, then the WS2812 will not be able to show status because the scope timing signals will corrupt the WS2812 lighting data.

    If the GPIO unit controls the DBG_BSY pad, then it will show code timing info.
    If the PIO unit controls the DBG_BSY pad, then it will show WS2812 status info.
