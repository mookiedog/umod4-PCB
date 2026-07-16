# Verification Checklist

## New Parts

### TLV75733

The bus transceiver gets its own 3.3V VCCB power supply derived from +5_ECU. This means that the bus transceiver will only be powered when the ECU is powered. It eliminates the possibility of backpowering the ECU if VCCB is present, but VCCA is not.

* Pinout checked
* Cap sizing checked
* GND checked

TEST RESULTS:

* LED lights when VCCB is present
* When plugging into a powered supply (instant ON), the powerup rise time seems a bit slow (200 uSec). Regardless, the VCCB 3.3V output lags 5V slightly, which is the desired sequence for powering the bus tranceiver.
* Powerdown has correct sequence too: 3.3V falls at same rate as 5V

### VLED

Derived from VSYS, where VSYS is always 1 diode drop from +5_ECU or VBUS.
THis means that VLED is 2 Schottky drops from nominal +5V, or about 0.8V, so VLED will be 4.2V.
This is well above the min spec of 3.7V for the WS2812.
In addition, Vih (min) will be 0.7 * 4.2V, or 2.94V, well within the ability of the RP2350 to drive it to 3.3V.

TEST RESULTS:

* VLED is 4.5V, which is a bit higher than expected, probably due to low Vf at very low current draw and 5.1V VSYS. RP2350 needs to drive it to 3.15V to meet the Vh (Min) spec. That is close to the 3.3V VDDio voltage level, but in spec. The old system powered VLED at 5.1V with a Vh of 3.57V (Min), which violated the official spec.

### New RGB LED #2

TEST RESULTS:

* Works. Inits to OFF, can be set to various colors without affecting LED #1

### SY6280 High-Side Switch for SD Power

* 20 uF of capacitance on input, as per data sheet.
* EN default is GND, meaning 'OFF'. WP will need to drive EN_VDD_SD to '1' to power the SD card.

R16 is the ISET pin.
The value 10K was chosen because it is common on the board. It works out to approximately 0.68A current limit, which is not really useful for this application, but better than nothing.

TEST RESULTS:

* ENABLE/DISABLE works
* When enabling power, the input does not ring above 3.3V so the input capacitance must be sufficient
* ISET not tested (current limit is too high to be useful anyway)

### EP BOOTSEL

* The button was replaced by TP4, a pad that can be shorted to GND with a jumper wire. This is a disaster recovery feature, never to be used.

* EP_BOOTSEL was added as a signal driven by the WP that pulls BOOTSEL to GND through a 1K resistor.
It forms a resistor divider that will pull bootsel to about 0.5V, plently low enough to be a logic '0'.

TEST RESULTS:

* BOOTSEL measured at 0.32V when asserted by WP. This is well under 0.8V Vil limit.

### EP External SWD Pin Protection

As per RPi doc, 100R resistors were added (R1/R2) to protect the RP2040 from electrical transients that might show up on the squid pin wiring.

The WP drives the signals directly without going through the 100R resistors.

TEST RESULTS:

* WP can drive the EP SWD to reflash it
* Debug unit is able to drive the EP after WP SWD disable jumper is inserted

### EP SWD Resistors

R3/R4 were added to put the SWD pins in a known state at all times. Clock is pulled to GND, Data is pulled up via 4K7 resistor.

TEST RESULTS:

* Pullup/pulldown are present, do not cause any trouble, and the WP debugging of EP via SWD interface continues to function

### RESET_HC_11 disconnected from WP

This signal is only allowed to be driven by the EP from now on.
The WP never used it before, so no big deal.

TEST RESULTS:

* Tested by design: the connection was removed from the schematic

### JP3 0.1 Jumper Pins Added

This allows a developer to easily short EP_SWD_DIS to GND. This tells the WP to NOT use the SWD interface so that an external debugger can be attached to the EP.

TEST RESULTS:

* Works, detected by WP firmware

### 10K Pullups on GP0/1 (EP 32-bit TX, FLOW)

Again, these were not totally required, but 10K resistors are totally cheap and just solve the problem.

### SPAREn Pins

SPARE0 renamed to SPARE0_ADC, drives a testpoint
SPARE1 is officially DISK_BSY, which it always was after the bodge LED was added to all 4V1 boards (WORKS)
SPARE2 is officially EP_BOOTSEL, which it always was in 4V1 firmware
SPARE3 drives a yellow LED and a testpoint (WORKS)
SPARE4 drives a red LED and a testpoint (WORKS)
SPARE5 drives a testpoint
SPARE6_ADC is the old RESET_HC_11 signal, not used by WP anymore, drives a testpoint

GP20 is now VCCB_PWR, tied to VCCB through a pullup for VCCB power detection (NOT TESTED)
GP21 is the EP_BOOTSEL driver (TESTED, works: pulls BOOTSEL down to 0.32V)

### SD Card Pullups

Pullups were added so that all 4 DATn signals have pullups now.

### SD Card Powered by VDD_SD

The SD card is powered by the new high-side switch.
Default is OFF.
Drive VDD_SD_EN to '1' to power the SD card.

TEST RESULTS:

* power control works

## No Stuff Parts

### Q1: +5_ECU FET to VSYS

## Deleted Parts

### Old U7 is removed

+5 ECU power detection is now performed via resistor pullup to VCCB to a WP GPIO.

### EP USB Connector & 27R Resitors Removed

The WP control of the EP via SWD works perfectly.
The connector is expensive and just not required anymore.

The WP now has the ability to drive EP BOOTSEL, EP RESET, and the SWD interface. These mechanisms mean that the WP is always able to take control of the EP and install new firmware.
