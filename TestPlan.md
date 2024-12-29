# Test Plan

Testing that needs to occur before a board spin:

1. __Pico W__

    1. __RP2040 UART Connection__

        1. This is a no-brainer - RX needs to go to TX, and TX to RX. Beyond that, it's all software, so no PCB issues.

    1. __PicoProbe SWD Control__

        1. This is a no-brainer - PicoW GPIOs need to connect to RP2040 SWD CLK and IO, and the rest is software, so no PCB issues.

    1. __Micro SD card operation__ Completed

        1. SD card transfers work fine in SPI mode at 20.8 MHz. That is the max speed possible that does not exceed 25 MHz.
        1. Using the RP2040 CRC sniffer and DMA unit, a 512-byte block can be transferred in about 500 uSec. That's a raw read rate of about 1 megabyte per second.

    1. __LCD operation__ (SPI port) Completed

        1. Port operation was verified as part of SD card testing.

    1. __GPS operation, including PPS interrupts__ Completed

        1. GPS serial communication is working
        1. PPS remains to be tested in software, but it is a no-brainer since it is a typical GPIO interrupt connection. The signal is verified to arrive at GPIO 28, pin 34 as a rising edge pulse with a duration of 100 mSec.
