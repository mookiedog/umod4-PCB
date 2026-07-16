# Test Plan: 4V2 Bring-Up

Bench bring-up checklist for boards returned from JLCPCB. Ordered so that risk is
retired before power is applied, and full power before firmware, and firmware
before the ECU is trusted with a board.

Background/rationale for each item lives in [Changelist-4V2.md](Changelist-4V2.md)
and [Verification.md](Verification.md) — this document is the executable checklist,
those are the "why."

## Equipment Needed

- Bench PSU with adjustable current limit (for B+ / 12V input)
- USB cable/power source for PicoW VBUS
- DMM
- Oscilloscope
- ECU test harness or bare wires for B+ / E0x (GND)
- SWD debugger (for external-debug-path tests)
- Several SD cards of different brands/sizes (see [PowerSupply.md](PowerSupply.md) for brands previously tested)
- Jumper wires for JP3, TP4

---

## 1. Incoming Inspection (no power applied)

- [ ] Populated/DNP parts match the BOM. In particular confirm **Q1 is unstuffed**
      (intentional "No Stuff" per 4V2 — [Changelist-4V2.md](Changelist-4V2.md#make-fet-q1-a-no-stuff))
- [ ] Polarized parts (LEDs, WS2812s, diodes) oriented correctly — cross-check
      against JLCPCB's post-order placement confirmation images
- [ ] GPS module designator silkscreen present and matches actual GPS placement
- [ ] DVDD 1.1V test pad silkscreen label present near C15
- [ ] TP4 (BOOTSEL disaster-recovery pad) present
- [ ] JP3 (EP_SWD_DIS 0.1" jumper) present
- [ ] New 0.1" WP/EP comms header present
- [ ] SPAREn test points present and appear accessible from card edges

## 2. No-Power Continuity Checks

- [ ] Resistance GND→rail on VBUS, VSYS, VCCB, +3.3V (WP), +3.3V (EP), VDD_SD,
      VLED — confirm no shorts before applying any power
- [ ] Continuity from each SPAREn test point to its corresponding GPIO (table below)
- [ ] Continuity from new EP/WP comms header pins to their signals

| GP | 4V2 Name | Test Point |
| -- | -------- | ---------- |
| GP27 | SPARE0_ADC | yes |
| GP26 | DISK_BSY | yes |
| GP5  | EP_SWD_DIS | JP3 |
| GP16 | SPARE3 (yellow LED) | yes |
| GP17 | SPARE4 (red LED) | yes |
| GP18 | SPARE5 | yes |
| GP19 | EN_VDD_SD | — |
| GP20 | VCCB_PWR | — |
| GP21 | EP_BOOTSEL | — |
| — | RESET_HC_11 (old SPARE6) | testpoint only, WP no longer drives |

## 3. Power-Up Sequencing (current-limited PSU, no SD card inserted)

### 3.1 USB only (VBUS present, B+ absent)

- [ ] VSYS present, correct diode-drop relationship to VBUS
- [ ] VCCB = 0V (no B+ present)
- [ ] VCCB_PWR GPIO reads '0'
- [ ] DVDD test pad ≈ 1.1V once RP2040 is running

### 3.2 B+ only (12V via bench PSU, no USB)

- [ ] +5_ECU present, VSYS one diode drop below it
- [ ] VCCB ramps to 3.3V, VCCB_PWR GPIO reads '1'
- [ ] VLED ≈ 4.2V (2 Schottky drops off VSYS — must clear WS2812 3.7V min and
      RP2040 Vih margin)
- [ ] DVDD test pad ≈ 1.1V

### 3.3 Both sources present

- [ ] USB source takes priority per power-combiner design (no unexpected VSYS dip
      or glitch when B+ is applied second, or removed first)

### 3.4 ECU-off current draw — the headline regression test for this revision

This is the bug the whole VCCB regulator redesign exists to fix — treat it as the
pass/fail gate for the release, ideally reproduced on an actual bike/ECU per the
2026-04-04 baseline in [Changelist-4V2.md](Changelist-4V2.md#testing-on-2026-04-04):

- [ ] USB power only, ECU off: baseline current ~130-160 mA
- [ ] Ignition on (B+ applied): current drops to ~40 mA
- [ ] Ignition off (B+ removed, USB still powered): current returns to the
      ~130-160 mA baseline — **must not** rise to ~270 mA as it did pre-fix on 4V1
- [ ] VCCB discharges quickly on B+ removal (active-discharge feature of the
      TLV757P), VCCB_PWR reads '0' promptly

## 4. Firmware / SWD Bring-Up

- [ ] Flash WP firmware via USB/BOOTSEL
- [ ] With JP3 open, WP flashes EP firmware over SWD successfully
- [ ] With JP3 grounded, external SWD debugger attaches to EP through the 100R
      series resistors and operates reliably (confirms WP is NOT driving the bus)
- [ ] Idle SWD bus state (nothing attached, JP3 open): SWDCLK low, SWD data high
- [ ] EP_BOOTSEL: assert from WP while holding EP in reset, release, confirm EP
      enters BOOTSEL
- [ ] TP4 manual jumper-to-GND also forces BOOTSEL (last-resort path)
- [ ] EP TX/RX lines read logic '1' at idle before UART init; UART comms normal
      after boot

## 5. GPIO / Indicator Functional Tests

- [ ] Toggle SPARE3 (yellow) and SPARE4 (red) from firmware, confirm LEDs light
- [ ] Toggle SPARE5, SPARE0_ADC, SPARE6_ADC, confirm correct level at test point
- [ ] Drive both daisy-chained WS2812 LEDs independently with different colors;
      confirm chain order matches physical position on board
- [ ] Confirm WP has no path to drive RESET_HC_11 (net-level check — this signal
      is EP-only as of 4V2)
- [ ] HC11 reset behavior unchanged after reset-circuit relocation (functional
      reset test, not just visual layout check)

## 6. SD Card Subsystem

- [ ] At power-up, before firmware drives EN_VDD_SD, VDD_SD measures 0V at the
      card socket (power defaults off)
- [ ] Drive EN_VDD_SD high, confirm VDD_SD ramps and card enumerates in 4-bit SD
      mode (not SPI mode) — validates DAT3 pullup
- [ ] Toggle EN_VDD_SD off, confirm active-discharge brings VDD_SD to 0V quickly
- [ ] Re-enable and confirm card reinitializes cleanly (power-cycle recovery is
      the point of the SY6280)
- [ ] Repeat across multiple SD card brands/sizes for compatibility

## 7. GPS

- [ ] GPS acquires and produces PPS/TX/RX data as on 4V1 (unchanged GPIOs)
- [ ] Confirm connector/hole spacing is workable in practice (flagged as a soft
      concern in [Changelist-4V2.md](Changelist-4V2.md#verify-gps-hole-spacing))

## 8. Integration Test in ECU

- [ ] Install in ECU, connect B+/GND harness, USB, GPS antenna, SD card
- [ ] Fake-EPROM operation confirmed on scope per the E-clock/read/write trace
      method in [README.md](README.md)
- [ ] End-to-end datalogging pipeline (ECU stream + GPS + SD write) matches 4V1
      behavior
- [ ] Re-check known 4V1 bring-up issues do not reappear (see
      [ChangeList.md](ChangeList.md) "V4.0b Resolved Problems"): EP RP2040 boot
      reliability (confirm firmware still sets `PICO_XOSC_STARTUP_DELAY_MULTIPLIER`)
- [ ] Repeat the §3.4 ECU-off current-draw test on the actual bike as the final
      confirmation

## 9. Sign-off

- [ ] All items above pass
- [ ] Results recorded with date in [Changelist-4V2.md](Changelist-4V2.md)
- [ ] Any deviations documented and triaged (fab defect vs. design issue vs. new
      4V3 changelist item)
