# Umod4PCB

The [Ultramod4](https://github.com/mookiedog/umod4) project replaces the EPROM in an Aprila Gen 1 ECU with a circuit board that combines realtime ECU datalogging with GPS position and location.  This repository contains the PCB design files for the project.

![Ultramod4 PCB layout](images/pcb_image_4V1.jpg)

## Goals

### Status

This project is still evolving. The first version of the board has been fabricated and tested. It is functional, but the bringup process has already identifed a number of changes to be incorporated on any new revision. Right now, I am letting the changes stack up until such time as some change/fix/feature forces a new board revision. See the file [ChangeList.md](ChangeList.md) for the current set of changes planned for the next PCB revision.

### Design For Manufacture

This project uses a bare RP2040 chip, which is too difficult for me to place by hand for reflowing the board using my [home-brew reflow](https://github.com/mookiedog/Reflow) process. Instead, this design is set up from the get-go for fabrication at JLCPCB.com. Where possible, the BOM parts were chosen from JLCPCB's "basic" component list to avoid the fee for using an "extended" component. Even so, stocks of "basic" parts fluctuate and components become obsolete, so the BOM might change with time. 

The initial version of the design has proven it can go end-to-end through the entire JCLPCB fabrication process where the resulting boards function as designed.

## Design Tool Choice

I know this will be a problem for some, but the project is currently written using Cadsoft Eagle.  It's because I've used Eagle for the last bazillion years. I am still using an old version of Eagle (V7.6) that I own outright. These days, you are forced to forced to buy new versions of Eagle on a monthly subscription basis. That doesn't work for me, because I make no money off this stuff and can't afford the subscription fees.  Too bad, I like Eagle.

Anyway, I realize that at some point it would be worth switching the design over to something like KiCad to make it more accessible to the open source community.

Someday.
