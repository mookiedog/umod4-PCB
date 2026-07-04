# Changelist Tracker for 4V2 PCB

## Dicking With Parts due to LCSC Supply Issues

* Changed the 100R resistors protecting SWD signals to be 0603 for availablity reasons
* Changed the E series resistor to be 100R/0603 to take advantage of above. AI indicates that 100R will be overdamped, but will be to my benefit at a slow 2 MHz clock.
* The 1K 0402 resistors R1, R4, R10 will be a minimum charge of $9. Changing the package does not help, and R1 needs to be 0402 anyway.
* The 470R resistors (R7,R11,R20,R21) can all be 0402 C25117 as per the 4V1
* The 4K7 R26 (SWD pullup) is converted to 0603
* Oddly, the GRN C2297 and YEL C2296 LEDs are basic parts, but the RED C2295 is an extended part. I think I will have the 470R resistors added for the SPARE3/4 LEDs, but the LEDs themselves left unstuffed.

## Outstanding 4V1a Issues

All known 4V1 issues have been resolved as below.

## GPIO Assignment Changes from 4V1 to 4V2

The SPARE1 and SPARE2 signals were used by the 4V1 software for various purposes.
The usage for these pins becomes official on the 4V2 PCB.

The LCD connector has been retired with 4V2 and the connector pins are assigned new functionality with 4V2.

| GP | 4V1 PCB Name | 4V2 PCB Name | Function |
| -- | ------------ | ------------ | -------- |
| GP27 | SPARE0 | SPARE0_ADC | spare, renamed to reflect ADC capability |
| GP26 | SPARE1 | DISK_BSY | SD card disk activity and "hello" notification |
| GP5  | SPARE2 | EP_SWD_DIS | Disable WP control of EP SWD |
| GP16 | SPI0_MISO | SPARE3 | spare (footprint for LED exists) |
| GP17 | SPI0_CS   | SPARE4 | spare (footprint for LED exists) |
| GP18 | SPI0_SCK  | SPARE5 | spare |
| GP19 | SPI0_MOSI | EN_VDD_SD | Enable SD card power |
| GP20 | SPI0_DC   | VCCB_PWR | test if VCCB is present |
| GP21 | SPI0_BKLT | EP_BOOTSEL | can drive EP_BOOTSEL to '0' during EP RESET |

All other signals and their GPIO assignments remain the same:

* RP2040 U0_TX, U0_RX
* RP_SWCLK, RP_SWD
* EP_RUN
* GPS: PPS, TX, RX
* SD Card: !CARD, SCK, MOSI, MISO, DAT1, DAT2, CS
* WS2812: DI

## Changes Completed for 4V2

### Resolve Excessive Power Draw At ECU Power-Off

__Problem:__ The 4V1 board draws excessive current if the ECU is powered off while the umod4 remains powered from a USB supply. It would appear that the bus buffer behaves badly when VCCB is present without VCCA, in spite of what the Nexperia data sheet says. The RP2040 can end up driving the HC11 data bus into the bus transceiver, backpowering it.

__Change:__ There were 2 changes made to resolve this issue.

The first was a firmware change. Existing firmware would disable the read-cycle bus drivers at the start of the next E cycle. When power failed, the 'next' E cycle would never come, and drivers (if enabled) would remain enabled. To fix this, a PIO state machine was added to drive the read data. A failsafe PIO timer mechanism would unconditionally disable the bus drivers if the firmware failed to do so because the next E clock never came.

The PIO mechanism resolved the issue for 4V1 PCBs. For 4V2, an additional change has been made. The 4V1 required using a Nexperia 74LVC4245 because it purported to deal with the issues that arise when one bus was powered, but the other was not. However, it would appear that there were perhaps more subtleties resulting in the excessive current draw. To fully resolve the issue and allow other manufacturer's versions of the 74LVC4245 which were stated as being fussier with power sequencing, a new power supply was added so that the +5 and +3.3V supplies to the bus transceiver would both be derived from +5 ECU supply.

A [TLV757P](https://www.lcsc.com/product-detail/C485517.html) linear regulator was added to power all voltage translation ICs:

* Two 8-bit address buffers (U1, U3)
* 8-bit bidirectional data bus buffer (U2)
* U6 dual inverter

These ICs are now completely unpowered when +5_ECU is absent (ignition OFF). The supply is named VCCB, per the 74LVC4245 naming convention.

This is safe because:

* Address buffers and E signal are always inputs to the RP2040, with pulldowns activated. Losing power causes no issues.
* Inverted HC11 bus signals (W/!R and CE) are also input only to the RP2040, with pulldowns activated.
* The 74LVC4245 spec requires VCCB to be applied at the same time or after VCCA. Since the regulator creates VCCB from VCCA, the soft-start delay guarantees this ordering.
* EP firmware uses a failsafe PIO timer to stop driving the bus if VCCB power fails mid-cycle.

The TLV757P features active output discharge when not enabled, making VCCB_PWR detection reliable.

__Verification:__ With USB power only (no ECU), confirm VCCB is 0V and current draw matches pre-4V1 baseline (~130-160 mA). With ECU powered, confirm VCCB is 3.3V and VCCB_PWR GPIO reads '1'. Turn ECU off and confirm VCCB discharges quickly and VCCB_PWR reads '0'.

#### Testing on 2026-04-04

The PIO timer-based read cycle failsafe drive disable has been verified.

On the motorbike using old firmware that exhibits the issue:

1) power ECU via USB: current 130-160mA
2) ignition on: USB power drops to 40 mA
3) ignition off: USB power rises to 270 mA instead of the previous 130-160mA.

Tuono using new firmware that uses PIO to always disable bus writes:
1) power ECU via USB: current 130-160mA
2) ignition on: USB power drops to 40 mA
3) ignition off: USB power drops back to same current as before

### Delete U7 & 4V1 ECU Power Present Signal

__Problem:__ U7 (dual inverter used as +5V ECU power detector) is no longer needed now that the VCCB regulator provides a simpler way to detect ECU power.

__Change:__ Deleted U7. The WP now monitors ECU power via GPIO VCCB_PWR, a pullup direct to the VCCB regulator output. A logic '1' means the regulator is powered and operating. The active discharge feature ensures the signal drops to GND quickly when power is removed. This simplifies the board and frees up area.

__Verification:__ Covered by VCCB regulator verification above.

### Add Pullups to EP TX/RX Lines

__Problem:__ The EP TX line to the WP can float during reset or before UART initialization, potentially causing framing errors.

__Change:__ Added pullups to both the EP TX and RX lines to hold them at idle state.

__Verification:__ After EP reset, confirm TX and RX lines are at logic '1' before UART initialization. Confirm UART communication works normally after boot.

### Move Reset Control Circuitry

__Problem:__ The reset control components occupied space needed for indicator LEDs at the rear edge of the board where they are more easily visible under the rear seat.

__Change:__ Relocated the reset control circuitry to free up rear card edge space for LEDs.

__Verification:__ Visual inspection of layout. Confirm HC11 reset behavior is unchanged.

### Upgrade SPAREn Accessibility

__Problem:__ The SPARE0/1/2 pads were in locations that were difficult to access for probing or attaching jumper wires.

__Change:__ Moved SPAREn pads to be accessible from the card edges. Added test points for every SPAREn signal to make wire attachment easier.

__Verification:__ Visual inspection that pads are accessible from card edges. Confirm continuity from test points to their respective GPIOs.

### Add Monocolor LEDs to Some Spare Signals

__Problem:__ During development, it would be useful to have visual indicators on spare GPIO lines, but the 4V1 board had none.

__Change:__ Added LEDs to spare signals. This is trivial to do, costs basically nothing, and has proven useful in the past.

__Verification:__ Toggle spare GPIOs in firmware and confirm corresponding LEDs illuminate.

### Daisy Chain 1 More WS2812 LED for WP

__Problem:__ A single WS2812 LED limits the WP's ability to indicate multiple statuses (e.g., SD activity, EP status) simultaneously.

__Change:__ Added a second WS2812 in a daisy chain for the WP to drive. The LEDs are separated by a good distance to make them easy to distinguish at a glance. Usage (SD status, EP status, etc.) is yet to be determined.

__Verification:__ Drive both WS2812 LEDs with different colors from WP firmware and confirm both are independently controllable.

### Add Test Points for EP/WP Comms

__Problem:__ The existing test points up by the RP2040 had holes and spacing too small for general use with standard probes or jumper wires.

__Change:__ Added a new 0.1 inch pinheader to provide easier access to EP/WP communication signals.

__Verification:__ Confirm 0.1" header pins fit and signals are accessible with standard probes.

### Add a Test Pad for CPU DVDD 1.1V Supply

__Problem:__ No easy way to probe the RP2040 core voltage during bringup or debugging.

__Change:__ Added a test pad and silkscreen label near C15 for the CPU DVDD 1.1V supply.

__Verification:__ Measure DVDD at the test pad and confirm it reads ~1.1V when the RP2040 is powered and running.

### Add Power Control IC for SD Card

__Problem:__ SD cards can get into states where they need a power-cycle to recover. The 4V1 board has no way to cycle SD card power without removing the card.

__Change:__ Added a SY6280 high-side power switch (SOT23-5) controlled by EN_VDD_SD (GP19). The SY6280 actively discharges the load when disabled, ensuring a clean power cycle. The SOT23-5 package/pinout is shared by many alternative switches in case a replacement for the SY6280 is ever needed.

__Verification:__ Toggle EN_VDD_SD from WP firmware. Confirm SD card power drops to 0V when disabled (measure at card socket VDD). Confirm active discharge brings voltage down quickly. Confirm SD card initializes correctly after power is re-enabled.

### Add GPS Module Designator to Silkscreen

__Problem:__ The GPS module had no silkscreen marking on the 4V1 board, making it harder to identify during assembly or debugging.

__Change:__ Added GPS module designator to the silkscreen layer.

__Verification:__ Visual inspection of silkscreen.

### Make FET Q1 a "No Stuff"

__Problem:__ Q1 bypasses the Schottky diode drop on D1 when VBUS is absent, saving a small amount of power on the ECU supply. This optimization is not meaningful for a non-battery-powered device like the ECU.

__Change:__ Left the footprint for Q1 but marked it as "no stuff" in the BOM. If Q1 is ever needed, the FET can be hand-soldered after the fact.

__Verification:__ Confirm the board operates correctly with Q1 unpopulated. Measure voltage drop across D1 and confirm it is within acceptable limits for the ECU power budget.

### Add WP Control of EP BOOTSEL

__Problem:__ If the EP goes fully rogue, the WP has no way to force it into BOOTSEL mode for recovery without physical intervention.

__Change:__ Added an EP_BOOTSEL signal driven by the WP through a 1K series resistor. Combined with the existing 10K pullup, this forms a divider that pulls QSPI_SS to ~0.3V, well below the 0.8V logic '0' threshold. A testpoint via is also provided to allow a jumper wire to GND BOOTSEL through a 1K resistor as a last-resort manual override.

__Verification:__ With EP running normally, confirm QSPI_SS is high. Assert EP_BOOTSEL from WP while holding EP in reset, then release reset and confirm EP enters BOOTSEL mode. Also verify the testpoint via can force BOOTSEL with a jumper wire.

### Add Pullups/Pulldowns to EP SWD Bus

__Problem:__ EP reflash via SWD showed that the internal pullup on SWD data is insufficient. A scope probe's loading alone was enough to make SWD operation unreliable. Additionally, an undriven SWDCLK line can pick up noise and cause false clock edges.

__Change:__ Added a 4.7K pullup on SWD data (stronger than 10K, allows faster SWD bus operation). Added a 10K pulldown on SWDCLK per standard recommendations to prevent noise-induced false clocking.

__Verification:__ Perform EP SWD reflash via WP and confirm reliable operation. Attach a scope probe to SWD data and confirm operation remains stable. Confirm SWDCLK is low when idle.

### Add Series Resistors to EP SWD CK and IO

__Problem:__ The EP SWD pins are exposed when attaching an external debugger. The RPi documentation recommends series protection resistors.

__Change:__ Added 100R series resistors on the external debugger path only. The WP-to-EP SWD wiring remains a direct connection so that the WP can reflash the EP without the resistors degrading signal integrity.

__Verification:__ Attach an external SWD debugger to the EP (with EP_SWD_DIS grounded) and confirm reliable debug operation through the 100R resistors.

### Add Pullups to SD Card MISO and DAT3 Signals

__Problem:__ DAT1 and DAT2 already have pullups, but DAT0/MISO and DAT3/CS do not. The DAT3/CS pullup is critical: if DAT3 is not pulled high at power-up, the SD card will enter SPI mode, which can only be exited via power-cycle.

Note that this issue became a non-issue with the addition of power control of the SD card. By leaving the card powered off, it would give the WP time to drive appropriate GPIO pullup/pulldowns on the signals. That said, 10K resistors are essentially free, so this hardware solution has been added.

__Change:__ Added pullup resistors to:

* DAT0/MISO — probably harmless since it is master input, but resistors are cheap insurance
* DAT3/CS — critical pullup to prevent unintended SPI mode entry

__Verification:__ Power-cycle the SD card (via SY6280) and confirm the card initializes in 4-bit SD mode, not SPI mode. Measure DAT3 at power-up and confirm it is pulled high before the WP drives it.

### Add a 0.1" Jumper for EP_SWD_DIS

__Problem:__ The WP controls the EP SWD bus for reflashing. When an external debugger is attached to the EP, the WP must be prevented from driving the SWD lines or it will conflict with the debugger.

__Change:__ Added a 0.1" jumper header on EP_SWD_DIS (GP5). Installing a shorting plug or jumper wire to ground tells the WP that it must not drive the SWD connection to the EP.

__WARNING: EP_SWD_DIS must be grounded before connecting an external SWD debugger to the EP!__

__Verification:__ With jumper installed, confirm WP does not drive EP SWD lines. With jumper removed, confirm WP can reflash EP via SWD normally.

### Delete WP Ability to Drive HC11 RESET

__Problem:__ The original board design allowed either the WP or EP to assert HC11 RESET signal. This has been determined to be both not useful, and potentially problematic. The EP should be the ONLY device that controls HC11 RESET. A malfunctioning WP should not be able to accidentally assert HC11 RESET, preventing a rider from getting home home.

## Deferred from 4V2

The following features were considered, but deferred from the 4V2 implementation.

### Replace RP2040 with RP2354A

One problem that has been annoying to this point is that I would have really liked to add a WS2812 LED for status reporting, but there is no spare GPIO on the standard package.
The RP2350 is available in a larger package with more GPIO.

Upsides:

* The Hazard RISC-V core has 16 registers available for the fake EPROM code.
    Essentially doubling the number of general purpose CPU registers compared to the Cortex should make it easier to write more complicated versions of the fake EPROM, should additional features be required.
* The RP2354A has 2 megabytes of flash built into it.
    This would allow me to delete my own 16 megabyte SPI flash and decoupling cap.
    The smaller capacity should not be a huge problem.

Downsides:

* Swapping the package represents a very big change to hardware and software:
    * Rewriting the fake EPROM code in RISC-V would take some effort.
    The Cortex M33 is not really suitable for use in a cycle-counting firmware.
    * There is not a lot of spare real estate in that location on the PCB for a larger package.

Ultimately, it seems like way too much work to get a status LED.
The simpler solution might be to parallel the original DBG_BSY LED with a WS2812 and accept that both features will not be available at the same time.
See "Consider Adding WS2812 LED", below.

At the moment, the RP2040 is totally capable of doing everything it needs to do.
If future features require a faster processor, the RP2040 could be up-clocked from its current 125 MHz to as much as 200 MHz.
If the future required more RAM, then an RP2350 becomes more viable, at least in its small package.

At the moment, this feature seems unlikely to survive the cut.

### Consider Using 2mm WS2812C Parts

_I am going to skip this, at least this time.
The 5050 parts are easy to solder after the fact, and now there is room for 3 of them on the back edge with the revised layout.
If 2020 LED get too close together, they become hard to distinguish._

Last time I looked, JLCPCB was not real happy if I spec'd the smaller parts.
I believe the issue was that they felt they needed to bake the parts before soldering them, which I'm sure would be an annoying manual problem for them.
Since then: it appears that JLCPCB also wants to bake the 5050 parts.
This means that any WS2812 parts regardless of package need to be manually soldered after receiving assembled boards from JLCPCB.
If that's the case, there is no benefit in spec'ing 5050 parts.
The only remaining issue is whether or not the 2020 parts can be hand-soldered.
The 5050 parts are easy to hand solder.
The 2020 parts look more difficult to place, but given that the pads are castellated and have only 2 pads per side, it should be doable.

### Add EP-driven WS2812 for EP Status

Now that the WP can forward the EP RTT output all the way to a phone, the RTT output serves as a much better indication of problems than a status LED.

### Backup Power To Guarantee Completion of SD Writes

_The backup power issue has been resolved due to the addition of the LogStore class to drive LittleFS.
The LogStore write performance improvements have made the proposal to support FAT for performance reasons a complete non-issue._

LittleFS has some issues regarding the time to perform a write/sync operation as the SD card fills. One possible way to deal with that is to use something like FAT FS instead. However, FAT FS has its own terrible problems that random power cuts can destroy the integrity of the file system. But if LittleFS proves troublesome enough, it might be a consideration to move to FAT FS, but with a backup power system to guard against data corruption issues.

One possible method of dealing with unexpected power cuts (ignition key off events) would be to enable some sort of short-term power backup option before beginning a SD Card write, then turning the backup power off after the write completes.
If the power failed during the write, the backup source would ensure that the write completed.
After completing and disabling the backup power, the system power would fail immediately but the filesystem would not be corrupted.

* LiPo battery backup

    The little RC quadcoptor 50 mAH LiPo batteries should work fine to power the PicoW while it is doing a write operation for 1 second or so.

    Note: These connectors are advertised on Aliexpress and ebay as JST 1.25, but they are __not__ JST connectors, they are Molex Picoblade.

    Mating through-hole socket is part number 5304702XX, where XX=60 means gold plated.

    See [molex catalog](https://www.molex.com/content/dam/molex/molex-dot-com/en_us/pdf/datasheets/987651-3691.pdf?inline) for more info on Picoblade series.

### Need Bigger Drill for Keystone 4952 test points

Don't bother changing anything: just use the 1035 test points.

The Keystone 1035 test points fit OK with their current drill size.
The Keystone 4952 test points need a bigger hole than the 1035.
Check if the 4952 test point has the right size drill in the library.

### Verify GPS Hole Spacing

I'm not sure that the hole spacing is quite right.
It is close enough to force things to work, but it could be better.
