# Umod4PCB

This project represents the design of the UltraMod4 PCB board. The [Ultramod4](https://github.com/mookiedog/umod4) project replaces the EPROM in an Aprila Gen 1 ECU with a circuit board that combines realtime ECU datalogging with GPS position and location.

![Ultramod4 PCB layout](images/pcb_image_4V1.jpg)

## Goals

### Status

This project is still evolving. The first version of the board has been fabricated and tested. It is functional, but the bringup process has already identifed a number of changes to be incorporated on any new revision. Right now, I am letting the changes stack up until such time as some change/fix/feature forces a new board revision. See the file [ChangeList.md](ChangeList.md) for the current set of changes planned for the next PCB revision.

### Design For Manufacture

This project uses a bare RP2040 chip, which is too difficult for me to place by hand for my [home-brew reflow](https://github.com/mookiedog/Reflow) process. So instead, this design is set up for fabrication at JCLPCB.com. The parts on the BOM are chosen from JCLPCB's parts supplier LSCS.com. I stayed away from oddball parts and only selected components that seemed to be extremely well-stocked at LCSC. Even so, stocks flutuate and parts come and go. Nonetheless, this project has proven its ability to go through the entire JCLPCB/LCSC process and deliver PCBs loaded with parts that function as designed.

## Design Tool Choice

I know this will be a problem for some, but the project is currently written using Cadsoft Eagle.  It's because I've used Eagle for the last bazillion years. I am still using an old version of Eagle (V7.6) that I own outright. These days, you are forced to forced to buy new versions of Eagle on a monthly subscription basis. That doesn't work for me, because I make no money off this stuff and can't afford the subscription fees.  Too bad, I like Eagle.

Anyway, I realize that at some point it would be worth switching over to something like KiCad.

Someday.
