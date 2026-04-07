# Changelist Tracker for 4V2 PCB

## Critical Changes for 4V2

None so far.

## Outstanding 4V1a Issues

None.

## Resolved 4V1a Issues

### Issue: Excessive Power Draw from WP USB when ECU is Powered Off

Resolved: fixed in firmware. The EP was depending on falling-E to disable the HC11 bus drivers. When power is lost, there may be a situation where the final bus cycle looks like a read so the drivers are enabled, but there is no subsequent bus cycle to disable the drivers. The drivers continue to back-power the now-unpowered bus transceiver causing excessive current consumption.

Fix: add a PIO state machine to handle driving read data to the transceiver. On an HC11 read operation, instead of writing the read data directly to the GPIO output drivers, the firmware now puts the read data in a PIO FIFO. A PIO SM wakes up, puts the data on the bus, and starts a bus timer. The timeout value is chosen so that the data is only driven until such time as we satisfy the data hold time after the E clock falls. At that point, the bus drivers are unconditionally disabled. This prevents driving IO pins into an unpowered bus transceiver.

#### Testing on 2026-04-04

Tuono using old firmware that exhibits the issue:

1) power ECU via USB: current 130-160mA
2) ignition on: USB power drops to 40 mA
3) ignition off: USB power rises to 270 mA instead of the previous 130-160mA.

Tuono using new firmware that uses PIO to always disable bus writes:
1) power ECU via USB: current 130-160mA
2) ignition on: USB power drops to 40 mA
3) ignition off: USB power drops back to same current as before

## Proposed Enhancements and Changes for 4V2

1) Backup Power
    LitteFS has some issues regarding the time to perform a write/sync operation as the SD card fills. One possible way to deal with that is to use something like FAT FS instead. However, FAT FS has its own terrible problems that random power cuts can destroy the integrity of the file system. But if LittleFS proves troublesome enough, it might be a consideratation to move to FAT FS, but with a backup power system to guard against data corruption issues.

    One possible method of dealing with unexpected power cuts (ignition key off events) would be to enable some sort of short-term power backup option before beginning a SD Card write, then turning the backup power off after the write completes.
    If the power failed during the write, the backup source would ensure that the write completed.
    After completing and disabling the backup power, the system power would fail immediately but the filesystem would not be corrupted.


    * LiPo battery backup

        The little RC quadcoptor 50 mAH LiPo batteries should work fine to power the PicoW while it is doing a write operation for 1 second or so.

        Note: These connectors are advertised on Aliexpress and ebay as JST 1.25, but they are __not__ JST connectors, they are Molex Picoblade.

        Mating through-hole socket is part number 5304702XX, where XX=60 means gold plated.

        See [molex catalog](https://www.molex.com/content/dam/molex/molex-dot-com/en_us/pdf/datasheets/987651-3691.pdf?inline) for more info on Picoblade series.

1) __Add Pullups/downs to SWD Bus__

    The EP-reflash via SWD has shown that the SWD data needs a pullup of 4.7K.
    Without it, the loading of a scope probe was enough that SWD operation became unreliable.
    The internal pullup is not good enough.
    A 10K was reliable, but the 4K7 is a lot faster and would potentially allow for faster SWD bus operation.
    Web advice recomments a 10K pulldown on SWDCK just so that noise does not cause false clock edges.

1) __Add Series Resistors to SWD CK and IO__

    Hmmm. This is pretty much in opposition to 1, above. Figure this out.


1) __Add pullups to SD Card Signals__

    DAT1 and DAT2 have pullups already.
    The SD card needs pullup resistors added to:

    * DAT0/MISO This one is probably harmless since it is master input, but resistors are cheap
    * DAT3/CS This one is critical! If not pulled high, the card will go into SPI mode. SPI mode can only be exited via power-cycle.

1) __Decide on Removing FET Q1__

    It gets rid of the Schottkey diode drop on D1 if VBUS is not applied (the normal case).
    It saves a small amount of power on the ECU power supply.
    This might be important for a battery-powered device, but the ECU is not.

1) __POWER_GOOD on VCCB Regulator__

    The VCCB regulator should have a POWER_GOOD output.
    The WP should monitor POWER_GOOD so it knows if the ECU is powered or not.
    If POWER_GOOD is false:

    * should the WP assert HC11_RESET? Or disable EP_RUN and reboot the EP?
    * If USB VBUS power is present and ECU_5V (or VCCB 3.3V) is not present, the WP should turn on WiFi module and enable WiFi control mode for downloading logs or performing OTA updates.

    1) __Add an ECU_PWR_GOOD signal into the WP__

        The original ECU_PWR signal was used to control an !OE on the 4245 bus tranceiver.
        It was never driven into the WP.
        Since then, the need for detecting the ECU power state has become clearer as part of WP WiFi operation, among other things.
        If this feature is not added via a VCCB regulator "power good" feature (as described above), it should be added via a simple voltage divider into a WP GPIO.

1) __Power Switch for SD Card__

    It is clear that SD cards can get into states where they need a power-cycle to recover.
    The current 4-bit driver seems very reliable, but adding a power switch would take care of the issue completely.

1) __Identify LEDs for SPARE0/1__

    Need colors, LCSC part numbers, resistor values.
    Should also mark PCB silkscreen for SPARE1 as being a disk activity light (see below)

1) __Rework GND Plane For Separate GND Regimes__

    It might be beneficial to separate the one giant GND plane on the back into a couple of GND planes.
    Perhaps one for the EPROM and voltage conversion, one for GPS/SD, one for CPU.
    These would connect in a star fashion down at the SIP connector.


1) __Add Backup Power To Guarantee Completion of Disk IO__

    _What is the goal here?
    One possibility is that disk write operation is not permitted to begin if the WP is on backup power.
    Another possibility is that the WP could enable backup power before starting a disk operation and disable it after completion.
    If power died while the write was happening, the WP would power-fail immediately after completing the write operation.
    This approach would not require a special power control for GPS._


    The Aprilia ECU is not designed to avoid uncontrolled power shutdown.
    When the ignition key turns off, power vanishes.

    LittleFS is tolerant of these situations, and in theory, avoids filesystem corruption due to uncontrolled power loss, though not data data loss from those same events.
    Unfortunatly, LittleFS has its own problems in that can be __extremely__ slow to perform writes to a SD card containing large filesets.
    Slow, like on the order of minutes to perform a single write of a small 512-ish bytes.
    In contrast, filesystems like ExFat are much higher performance, at the cost not not being at all tolerant of interrupted write operations.
    It is very easy for ExFat to end up in an inconsistent state if power is lost during some disk IO operation.

    If it is determined that the larger problem is the lack of performance from LittleFS, then using ExFat only makes sense if the umod4 board can guarantee that it can always complete an exfat operation.
    One possibility would be to add a backup power supply of sufficient capability that ExFat disk operations can be guaranteed to complete once begun.
    The backup supply probably only needs to guarantee that the WP continues to operate for maybe a couple of seconds after the ignition turns off.
    This means that the backup power could possibly be based on a supercap instead of a battery.
    Both supercaps and batteries need charging circuits, but a supercap can probably be charged using a resistor instead of a specialty IC.

    Once the WP completes any disk operation in flight after power was lost, it might also be useful if the WP was able to disable the backup power immediately.
    The point would be that supercap power would not be enabled until such time as a disk operation began.
    Once completed, the WP could power itself down cleanly if it noticed that ECU power had disappeared during the disk operation.


1) __Need Bigger Drill for Keystone 4952 test points__

    The Keystone 1035 test points fit OK with their current drill size.
    The Keystone 4952 test points need a bigger hole than the 1035.
    Check if the 4952 test point has the right size drill in the library.

1) __Verify GPS Hole Spacing__

    I'm not sure that the hole spacing is quite right.
    It is close enough to force things to work, but it could be better.

## Deferred from 4V2

The following features were considered, but deferred from the 4V2 implementation.

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

    Ultimately, it seems like way too much work to get a status LED.
    The simpler solution might be to parallel the original DBG_BSY LED with a WS2812 and accept that both features will not be available at the same time.
    See "Consider Adding WWS2812 LED", below.

    At the moment, the RP2040 is totally capable of doing everything it needs to do.
    If future features require a faster processor, the RP2040 could be up-clocked from its current 125 MHz to as much as 200 MHz.
    If the future required more RAM, then an RP2350 becomes more viable, at least in its small package.

    At the moment, this feature seems unlikely to survive the cut.

1) __Consider Using 2mm WS2812C Parts__

    _I am going to skip this, at least this time.
    The 5050 parts are easy to solder after the fact, and now there is room for 3 of them on the back edge with the revised layout.
    If 2020 LED get too close together, they become hard to distinguish._

    Last time I looked, JLCPCB was not real happy if I spec'd the smaller parts.
    I believe the issue was that they felt they needed to bake the parts before soldering them, which I'm sure would be an annoying manual problem for them.
    Since then: it appears that JLCPCB also wants to bake the 5050 parts.
    This means that any WS2818 parts regardless of package need to be manually soldered after receiving assembled boards from JLCPCB.
    If that's the case, there is no benefit in spec'ing 5050 parts.
    The only remaining issue is whether or not the 2020 parts can be hand-soldered.
    The 5050 parts are easy to hand solder.
    The 2020 parts look more difficult to place, but given that the pads are castelleated and have only 2 pads per side, it should be doable.


## Changes Completed for 4.2

### 1. Add +3V3 VCCB Regulator for Voltage Conversion ICs

The 4V1 board has issues where the board would draw excessive current if the ECU was powered off while the umod4 remained powered from a USB supply.
That specific issue was due in part to the RP2040 driving the HC11 data bus into the bus transceiver although it seemed like the transceiver should have handled that OK with VCCB being present.
Regardless: it appears that the bus buffer is behaving badly when VCCB is present without VCCA, in spite of what the Nexperia data sheet says.

The solution is to make sure that none of the ICs involved with address translation are powered at all if the ECU +5V is not present.
Those ICs are:

* Two 8-bit address buffers
* 8-bit Bidirectional data bus buffer
* U6 dual inverter

If we add a linear regulator powered off +5_ECU which outputs 3.3V, then use this specific supply to power the voltage translation ASICs, then they will only be powered when +5_ECU is present (ignition ON).

This new 3V3 supply is named VCCB, as per the naming convention of the 74LVC4245.

Having those ASICs be unpowered should not be an issue:

* The address buffers (and E signal) drivers are always inputs to the RP2040, with pulldowns activated.
Losing power causes no issues at all.
* The inverted versions of the HC11 bus signals (W/!R and CE) arriving at the RP2040 are also input only
to the RP2040, with pulldowns activated.
Losing power causes no problems.
* The data bus transceiver has two supplies.
The spec for the chip indicates that VCCB (+3V3) should be applied either at the same time, or after VCCA.
Since the new linear regulator creates VCCB from VCCA, VCCB will be generated slightly after VCCA appears due to the delay in recognizing the regulator 'enable' signal and then the soft-start after 'enable' is recognized.

The EP firmware has been modified so that if the RP2040 ever sees what it thinks is a read cycle begin just as VCCB power fails, the RP2040 is guaranteed to stop driving the bus via a failsafe time delay. This gets rid of all problems where the RP2040 might backpower the bus buffer.

### 2. Delete ECU Power Present Signal

Discuss why this signal is not needed anymore.

Getting rid of this signal allows us to delete U7.
U7 only used one of its two inverters.
By deleting the ECU power present signal from U6, we can move the remaining signal from U7 to U6 and delete U7.

### 3. Add 100R Protection Resistors for DBG Signals

The Pi documentation suggests putting 100R resistors in series with SWD clk and SWD data.
This serves as protection for various situations, including ESD events.
Having blown up a Pi Pico board set up as a debugger, this would appear to be a real situation.

Series resistors have been added.

### 4. Add Pullups to EP TX/RX Lines

The TX line that the EP uses to send to the WP should have a pullup on it.
I believe that this is causing a false 0 byte to be received when the WP boots.

Pullups have been added to both RX and TX lines.

### 5. Delete U7 (!ECU_PWR Signal)

Inverter U7 was fed with a signal derived from a voltage divided and filtered version of +5_ECU.
The output of this signal was used to drive one of the !OE signals on the 4245 data bus tranceiver.
The other half of U7 was unused.

U7 has been deleted, and that !OE signal is not tied to GND.
Given that the 4245 tranceiver is now powered by VCCB, there is no need for an !OE driven by the presence of +5_ECU.

### 8. Move Reset Control Circuitry

Goal: leave more room for adding 3 more indicater LEDs and access to the SPAREx pads at the edge of the board.

### 9. Move Spare0/1/2 To Card Edge

The three SPARE0/1/2 pads got moved to be accessable on the rear card edge.

### 10. Add Official Test Point for SPARE2

Added a real testpoint instead of a via.

Spare2 currently is used to tell the WP that it is NOT allowed to use SWD to talk to the EP. Spare2 must be grounded whenever a debugger is connected to the EP or else the WP and the debugger will fight over the SWD pins.

### 11. Add Simple LEDs to Spare0 and Spare1

Reasoning: The built-in LED controlled by the WiFi module takes a considerable amount of time and CPU effort before it can be used.
It defeats the purpose of being an early indication of life.

Having LEDs is fine, even if the signals end up being used for something else, like a scope trigger.
The signals will default to '1' due to the pullup resistor.
LEDs will turn on via active low GPIO.

NOTE: Current firmware has redefined SPARE1 as a "disk activity" indicator light. The LED is lit while LittleFS accesses the file system for reads or writes.

SPARE0 is still 'spare'.

### 12. Daisy Chain 1 more WS2812 LED for WP

An extra WS2812 has been added in a daisy chain for WP use.
Conceivably, the existing LED could continue to be used for SD Card status.
The new LED could display some other form or status, yet to be determined.

### 13. Added 0.1 Spacing Test Points for EP/WP Comms

The holes and spacing of the pins up by the RP2040 are too small for general use.
A new pinheader was added over by the WP.

### 14. Add a Test Pad For CPU DVDD 1.1V Supply

There is plenty of room by C15 to add a test pad and silkscreen for the CPU DVDD 1.1V supply.

### 15. Add WS2812 Status LED For EP

In normal use on the bike, the DBG_BSY LED has two purposes:
* to flicker a 'hello' indication at boot time to prove to a human being that the EP is alive
* to drive the memory cycle timing information so an o'scope can see it

I would really like to give the EP a mechanism to display some basic status information using an RGB LED:

* EP Booting
* Loading EPROM image
* HC11 out of RESET
* HC11 operating properly
* panic situation

Given that the EP has no spare GPIOs, the simplest solution is to wire a WS2812 in parallel with the DBG_BSY LED.
Code would be set up with a build-time flag so that it uses SIO to drive DBG_BSY for scope timing verification, or it uses a PIO engine to drive the same GPIO with WS2812 status color info.

Both WS2812 and DBG_BSY timing code would drive the LED constantly, with knowledge of each other.
At boot time, the 'hello' blink of the DBG_BSY LED would still occur.

After the hello blink, the softare would be built to do one of two things:

* Assign control of the DBG_BSY GPIO to the PIO for status info.
* Leave control with SIO for DBG_BSY timing tests.
    While being used for timing tests, the WS2812 lighting colors will go crazy from the data stream on DBG_BSY

It would be possible to write software for certain status indications like panic() to force control of the WS2812 to the PIO, even if the software was built for timing tests.
That way, panic situations would be obvious even when set up for timing tests.

### 16. Add FET Power Control for SD Card

Add a control mechanism so that the WP can power cycle the SD Card.

At reset, the SD Card is powered OFF by default.
The WP must drive the 3V3_SD_EN signal to '1' to power the SD Card.

During testing, I have seen SD cards that fail spectacularly after bad commands were issued to them.
In particular, if you asked to read 1 block off the end of the card, some cards would hang to the point that they needed a power-cycle to recover.

Having power control would also make the whole hot-plug thing a bit safer because the hotPlug manager would keep power off until card was physically present for some amount of time, as opposed to powering it up while it is being inserted if the socket is always hot.

There are lots of commodity USB power switch controllers, but I decided to go with a simple PFET solution.

If that decision needs to be revisited, here are some power switch ICs available at LCSC:

* SY6280
* TPS22918
* MT9700

There are lots more, but this gives the flavor of what is out there.


### 17. Add FET Power Control for GPS

In case the board ever gets a supercap backup, it would be advantageous to disable power to the GPS if it was determined that the WP was running on supercap backup power.

At reset, the default is that the GPS is powered ON by default.
If desired, the WP can disable power to the GPS by driving the 3V3_GPS_EN signal to '0'.

### 18. Add GPS Module Designator to Silkscreen

The GPS has now been marked on the silkscreen layer.

