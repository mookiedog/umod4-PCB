# Umod4 Power Supply

This doc is for capturing thoughts about how the umod4 should be powered.

In the big picture, there are really just two situations:

1) Normal operation: ECU and umod4 both power on and off with the key

2) Data transfer mode: key off, but umod4 gets powered while ECU remains unpowered

The point of data transfer mode is to allow the umod4 board wifi access with the bike turned off and parked. This mode allows logs to be uploaded or OTA firmware updates to be performed.

The simplest way to do this is to attach a USB power cable to the PicoW VBUS pin and snake it out
of the ECU to a location where a rider could plug in a USB charger, much as they might also connect
a battery charger after a ride.

The more complicated solution adds a power supply to the umod4 that is connected to the motorbike
battery. The umod4 could detect when the engine stops and remain powered for a while, or perhaps
even remain powered for as long as it detects a charger connected to the battery.

## Outstanding Questions

1. How much current can a JST connector take?

   Answer: the SR/SZ 1mm pitch JST connectors are rated at 700 mA.

It would be simplest if the USB power connector used a 2-pin JST connector like LiIon batteries use.
That connector should be able to fit through one of the 4 holes already present in the ECU lid.

## Current Plan

The simplest solution would be to just add a USB power port on an extension cable soldered to the umod4 board.
It is not a big hardship to attach USB power to the bike after parking.

As of now, I have a power supply designed and in place, but I don't need to stuff it with parts.
I could just add a could of pads that would allow me to attach a USB cable to the PCB.
It would probably be best to cut the umod4 end of the cable off and just solder the wires to the PCB.

Getting the wire out of the ECU will be an issue in either case.


## Design Requirements
The Umod4 power supply is designed to support a number of use cases:

  1. Software development and testing
      1. Bench testing of a bare Umod4 PCB board, not plugged into an ECU
          1. Power to be supplied via the PicoW USB connector
      1. Bench testing of a Umod4 PCB installed in an ECU
          1. Power could be supplied via PicoW USB connector
          1. Power could be supplied via ECU +5
              1. ECU needs +12 on its B+ pin
  1. General usage on a motorbike
      1. Power to be supplied via a fused, unswitched supply connected directly to the motorbike battery
          1. If the ignition is ON, the Umod4 is always powered
          1. If the ignition is OFF, and the Umod4 detects that the battery is on a battery charger, the Umod4 will remain powered so that it can respond to WiFi/Bluetooth control
          1. If the ignition is OFF and the Umod4 is not on a charger, it will remain powered for as long as it takes to download ride logs to a server and then power itself off.

Note1 : The system _could_ be installed on a motorbike without connecting the unswitched supply to the battery. This is **NOT** recommended. Under these circumstances, whenever the ignition is turned OFF, the Umod4 will be powered off immediately without allowing it to shut down gracefully. Abrupt shutdown events can cause corruption of the SD Flash memory.

Note 2: When bench-testing in an ECU, if no USB power is supplied, the Umod4 will take its power from the ECU 5V supply. This is not a huge problem in that the ECU power supply appears to be over-designed and can handle the extra load, but to avoid stressing the ECU 5V supply in any way, a USB power supply is recommended during test and development on a bench.

## Outstanding Issues
The real question is whether or not the selected voltage regulator can supply the 5V requirements of the Pico W, which is also powering the entire Umod4 board. In theory, 600 mA at 5V output is 3W available to the Pico W. If the PicoW can convert power at 90% efficiency, that would correspond to 2.7W of power at 3.3V. That is 800 mA of current at 3.3V.

With my current setup (GPS, flash card idling, LEDs on, PicoW not doing any wireless activity), plugging in the USB power reduces power supply current to the ECU by less than 90 mA. Since the ECU is a linear supply, it means that the Umod4 must be drawing no more than 90 mA.

## Background
The Pico W has an [RT6154](https://www.richtek.com/assets/product_file/RT6154A=RT6154B/DS6154AB-03.pdf) switchmode power supply. The ASIC is capable of supplying 3A when it is generating 3.3V from a 5V input.

The Umod4 board combines a pair of 5V sources (USB or ECU 5V on the 4V0 design) that feeds the Pico W VSYS input. The power combiner prioritizes the USB source of +5. If the USB +5 exists, it disables the 5V source from the 12V unswitched supply. This means that a Umod 4 board can be powered permanently by plugging in a USB cable, even if the Umod4 is inserted in an unpowered ECU.

The RT6154 converts the 5V VSYS supply to the 3.3V output used by the Pico W.  In addition to its own 3.3V power requirements, the Pico W is capable of supplying up to 300 mA to power the Umod4 board.

In the 4V1 power supply, the USB 5V input remains strictly for bench testing. If 5V USB is present, the Umod4 will remain powered permanently. The other power source is a +12 unswitched supply that generates 5V. That +5 output would replace the 5V_ECU input.

## Power Requirements
The potentially biggest power consumer looks like the SD card. It is a transient power requirement though only when accessing flash, especially when erasing or writing flash. If we were writing 10K bytes/sec, that would be 20 writes per second, or 50 mSec per write. They don't take that long to write, so the average power consumption would be a lot less than 163 mA.

The Umod4 hardware being powered by the Pico W would be:
* 67 mA Neo8 GPS
* 80 mA Micro SD (various manufacturers), this is a total worst case guess
* 50 mA RP2040 and serial flash
* 15 mA DS2812C LED

If everything except the Micro SD totals 130 mA, that leaves 170 mA for the Micro SD card. There is [some data](https://electronics.stackexchange.com/questions/33472/how-much-current-does-a-microsd-card-use) to indicate that when operating in SPI mode at the default 25 MHz, a card is limited to .36W at 3.3V, or 163 mA. That would seem to be right where we need to be.

### GPS
The Neo-8 data sheet says to size the power supply for a max draw of 67 mA. My measurements show that it draws between 44mA and 54mA during normal operation. I do not know how much power the active antenna is taking.

### Micro SD Card
Crude card measurements follow:

#### Samsung 32G
  1) Reads take about 500 uSec, power increases by 20 mA

  1) Writes take about 900 uSec, power increases by 40 mA

#### Netac 64G
  1) Reads take about 380 uSec, power increases by 20 mA

  1) Writes take about 900 uSec, power increases by 30 mA

#### Transcend 128G
  1) Reads take about 320 uSec, power increases by 20 mA

  1) Writes take about 1200 uSec, power increases by 30 mA.  That's slow but still over 300K bytes/sec.




### EP RP2040
I measured the RP2040 power consumption at about 25 mA when servicing HC11 memory requests. The W25Q128 SPI flash indicates that its worst-case power consumption is 25 mA max. Max power occurs during programming or erasing.

### DS2812C
I'm not sure what the actual power requirement is. The spec sheet says 5 mA, but I'm not clear if that is 5 mA total, or 5 mA per color, so 15 mA total. The ASIC itself draws 0.6 mA.


## Version 4V0

As is, the Umod4 is powered by 5V_ECU. The 5V_ECU supply is present when the ignition key is ON, derived from the B+ (nominal 12V) supply into the ECU. This also means that the ECU 5V supply is responsible for powering the entire Umod4 board, which has not-insignificant power requirements due to the GPS, the EP RP2040, the micro SD, and of course, the PicoW running WiFi.

The drawback is that when the ignition is switched OFF, power is unexpectedly cut off to the Umod4 which could be in the middle of a disk write.

## Proposed 4V1

The Umod4 power supply has a number of design considerations. Even though the Umod4 lives inside the ECU, it may be powered when the ECU is not powered. This allows for use cases like arriving home from a ride. The Umod4 would remain running after the ignition key is turned off so that it could dump ride logs to a server on the wifi network. Once all logs were dumped, and some time after the last user interaction with the Umod4 user interface, the Umod4 will power itself down.

The Umod4 will detect if it is attached to a battery charger, even if it was powered down when the charger was connected. As long as the system is on a charger, the Umod4 will keep its wifi connection alive. This allows a user to do things like push a Umod4 firmware update from inside the house knowing that the Umod4 will be powered out in the garage.

For development and testing, it needs to operate on a bench in situations where the ECU itself may or may not be powered. In operation, the power supply operates outside of the ignition key control. The basic idea is that if the ignition key ever turns on, the Umod4 comes to life. When the ignition key turns off, the ECU will power down immediately, but the Umod4 will remain powered until it decides to power down.

The Umod4 never needs to know what is happening on B+. The 5V_ECU power supply is derived from the B+ supply by ECU power supply circuitry, so if 5V_ECU is present, it means that B+ is present.

## Battery Charger Detection
The ECU needs to know what is happening on 12V_UNSW. The Umod4 power supply is derived from 12V_UNSW. The Umod4 needs to know if the voltage on 12V_UNSW rises enough to indicate that there is a battery charger present.

For any sort of active solution, I need a power supply. The power supply could be as simple as a voltage divider of perhaps divide by 4. This would mean that a part that could handle as much as 6V on its input would tolerate 24V on 12V_UNSW.

I would need a reset chip that is powered from the 12V_UNSW supply through the voltage divider. It really would be best if the chip only drew a few uA. When the supply rose to a point indicating that a charger was present, reset would be allowed to go HIGH, perhaps after a delay.


## Powering for Bench Testing
Bench testing is most easily accomplished with an ECU connector cut from an old wiring harness. The nominal +12V arrives on the B+ pin, and GND is supplied via the E01/E02/E03 pins. Without access to an ECU connector, it is also easy to solder wires directly to the B+ and E0x pins inside the ECU before they attach to the PCB.