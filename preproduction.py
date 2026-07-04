#!/usr/bin/env python3
"""Pre-production verification and BOM generation for Eagle PCB projects.

Run from the project root after running the Eagle CAM processor:
    python3 preproduction.py

Auto-discovers the .sch/.brd pair in the script's directory, or pass a
schematic path explicitly:
    python3 preproduction.py path/to/board.sch

Reads gerbers from build/cam/, generates BOM files, and packages
everything for JLCPCB upload into build/jlcpcb/.

DNP convention:
    LCSC_PART non-empty     → assembled by JLCPCB
    DNP_LCSC_PART non-empty → excluded from assembly; part number preserved
                              for reference and easy re-enable in future
    neither attribute       → excluded (connectors, test points, frames, etc.)
"""

import csv
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

GERBER_EXTS = ['.GBL', '.GBO', '.GBP', '.GBS', '.GKO',
               '.GTL', '.GTO', '.GTP', '.GTS', '.XLN']

EAGLE_EXE  = r'C:\Program Files\Eagle\bin\eagle.exe'
BAT_FILE   = r'C:\Users\robin\AppData\Local\Temp\eagle-cpl.bat'


def _open_for_write(path, retries=8, delay=0.4, **kwargs):
    """Open a file for writing, retrying on transient PermissionError.

    Files inside an OneDrive-synced directory can be briefly locked while
    OneDrive reacts to a directory cleanup (rmtree). A few short retries
    are enough to outlast that lock without any perceptible delay.
    """
    kwargs.setdefault('mode', 'w')
    for attempt in range(retries):
        try:
            return open(path, **kwargs)
        except PermissionError:
            if attempt == retries - 1:
                raise PermissionError(
                    f"Cannot write {path.name} after {retries} attempts — "
                    "close any application that has this file open (e.g. Excel) and try again.")
            time.sleep(delay)


def find_schematic(start_dir):
    """Return the single .sch file in start_dir, or raise if ambiguous/missing."""
    candidates = list(start_dir.glob('*.sch'))
    if not candidates:
        raise FileNotFoundError(f"No .sch file found in {start_dir}")
    if len(candidates) == 1:
        return candidates[0]
    # Multiple .sch files — prefer the one with a matching .brd
    for sch in candidates:
        if sch.with_suffix('.brd').exists():
            return sch
    raise FileNotFoundError(
        f"Multiple .sch files in {start_dir}; pass the path explicitly")


def _nat_key(s):
    """Natural sort key: C1 < C2 < C10."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s or '')]


def parse_schematic(sch_path):
    """Parse Eagle .sch XML. Returns (pcba_rows, dnp_rows, other_rows).

    Each row: (value, package, lcsc_or_dnp_lcsc, [sorted_designators])
    """
    tree = ET.parse(sch_path)
    sch  = tree.getroot().find('drawing/schematic')

    # Eagle .sch embeds full library data including package names
    pkg_map = {}
    for lib in sch.find('libraries').findall('library'):
        lname      = lib.get('name')
        devicesets = lib.find('devicesets')
        if devicesets is None:
            continue
        for ds in devicesets.findall('deviceset'):
            devices = ds.find('devices')
            if devices is None:
                continue
            for dev in devices.findall('device'):
                key = (lname, ds.get('name'), dev.get('name', ''))
                pkg_map[key] = dev.get('package', '')

    pcba_map  = {}
    dnp_map   = {}
    other_map = {}

    for part in sch.find('parts').findall('part'):
        pkg = pkg_map.get(
            (part.get('library'), part.get('deviceset'), part.get('device', '')), '')
        if not pkg:
            continue  # supply symbols, frames — no physical package

        value    = part.get('value', '')
        pname    = part.get('name')
        attrs    = {a.get('name'): a.get('value', '') for a in part.findall('attribute')}
        lcsc     = attrs.get('LCSC_PART',     '').strip()
        dnp_lcsc = attrs.get('DNP_LCSC_PART', '').strip()

        if lcsc:
            pcba_map.setdefault((value, pkg, lcsc), []).append(pname)
        elif dnp_lcsc:
            dnp_map.setdefault((value, pkg, dnp_lcsc), []).append(pname)
        else:
            other_map.setdefault((value, pkg, ''), []).append(pname)

    def to_rows(d):
        rows = []
        for (value, pkg, lcsc), refs in d.items():
            refs.sort(key=_nat_key)
            rows.append((value, pkg, lcsc, refs))
        rows.sort(key=lambda r: (_nat_key(r[0]), _nat_key(r[1])))
        return rows

    return to_rows(pcba_map), to_rows(dnp_map), to_rows(other_map)


def write_csv(pcba_rows, path):
    """Write JLCPCB-format BOM CSV."""
    with _open_for_write(path, newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for value, pkg, lcsc, refs in pcba_rows:
            w.writerow([value, ', '.join(refs), pkg, lcsc])


_CSS = """\
<style>
body { font-family: sans-serif; margin: 2em; color: #222; }
h1   { font-size: 1.3em; }
h2   { font-size: 1.05em; margin-top: 2em; color: #444; }
table { border-collapse: collapse; width: 100%; margin-bottom: 1.5em; }
th { background: #444; color: #fff; text-align: left; padding: 6px 10px; }
td { padding: 5px 10px; border-bottom: 1px solid #ddd; vertical-align: top; }
tr:nth-child(even) { background: #f6f6f6; }
.qty  { text-align: center; width: 3em; }
.lcsc   { color: #0055cc; font-family: monospace; }
.lcsc a { color: #0055cc; }
.dnp    { color: #999;    font-family: monospace; }
.dnp  a { color: #999; }
.meta { font-size: .85em; color: #888; }
</style>"""


def write_html(pcba_rows, dnp_rows, other_rows, sch_path, path):
    """Write two-section human-readable BOM HTML."""
    now         = datetime.now().strftime('%Y-%m-%d %H:%M')
    pcba_count  = sum(len(r[3]) for r in pcba_rows)
    other_count = sum(len(r[3]) for r in dnp_rows) + sum(len(r[3]) for r in other_rows)

    def tr(value, pkg, refs, lcsc_cell):
        return (f'<tr><td class="qty">{len(refs)}</td>'
                f'<td>{value or "<em>—</em>"}</td>'
                f'<td>{pkg}</td>'
                f'<td>{", ".join(refs)}</td>'
                f'{lcsc_cell}</tr>')

    out = [
        '<!DOCTYPE html><html><head><meta charset="utf-8">',
        f'<title>BOM — {sch_path.name}</title>',
        _CSS,
        '</head><body>',
        f'<h1>BOM: {sch_path.stem}</h1>',
        f'<p class="meta">Generated {now}'
        f' &nbsp;&bull;&nbsp; {pcba_count} JLCPCB'
        f' &nbsp;&bull;&nbsp; {other_count} other/DNP</p>',
        '<h2>JLCPCB Assembly</h2>',
        '<table><tr>'
        '<th class="qty">Qty</th><th>Value</th>'
        '<th>Package</th><th>Designators</th><th>LCSC Part #</th>'
        '</tr>',
    ]
    def lcsc_link(part_no, css_class):
        url = f'https://jlcpcb.com/parts/componentSearch?searchTxt={part_no}'
        return f'<td class="{css_class}"><a href="{url}" target="_blank">{part_no}</a></td>'

    for value, pkg, lcsc, refs in pcba_rows:
        out.append(tr(value, pkg, refs, lcsc_link(lcsc, 'lcsc')))
    out.append('</table>')

    out += [
        '<h2>Other / DNP / Hand-solder</h2>',
        '<table><tr>'
        '<th class="qty">Qty</th><th>Value</th>'
        '<th>Package</th><th>Designators</th><th>DNP LCSC #</th>'
        '</tr>',
    ]
    for value, pkg, dnp_lcsc, refs in dnp_rows:
        out.append(tr(value, pkg, refs, lcsc_link(dnp_lcsc, 'dnp')))
    for value, pkg, _, refs in other_rows:
        out.append(tr(value, pkg, refs, '<td></td>'))
    out += ['</table>', '</body></html>']

    with _open_for_write(path, encoding='utf-8') as f:
        f.write('\n'.join(out))


def main():
    # Resolve schematic path
    if len(sys.argv) > 1:
        sch_path = Path(sys.argv[1]).resolve()
        if not sch_path.exists():
            print(f"Error: {sch_path} not found", file=sys.stderr)
            return 1
    else:
        try:
            sch_path = find_schematic(Path(__file__).parent.resolve())
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    proj     = sch_path.parent
    stem     = sch_path.stem
    brd      = sch_path.with_suffix('.brd')
    builddir = proj / 'build'
    camdir   = builddir / 'cam'
    jlcdir   = builddir / 'jlcpcb'
    html_out = jlcdir / f'{stem}-bom.html'
    csv_out  = jlcdir / 'bom.csv'
    zip_out  = jlcdir / f'{stem}.zip'

    issues = []
    lines  = []
    now    = datetime.now().strftime('%Y-%m-%d %H:%M')

    print(f'\n{"="*60}')
    print(f' Pre-Production Check: {stem}  ({now})')
    print(f'{"="*60}')

    # Ensure build/cam/ exists so Eagle can write there on the next CAM run
    camdir.mkdir(parents=True, exist_ok=True)

    jlcdir.mkdir(parents=True, exist_ok=True)

    # --- Gerber freshness ---
    src_mt  = max(brd.stat().st_mtime, sch_path.stat().st_mtime)
    missing = [f'{stem}{e}' for e in GERBER_EXTS
               if not (camdir / f'{stem}{e}').exists()]
    stale   = [f'{stem}{e}' for e in GERBER_EXTS
               if (camdir / f'{stem}{e}').exists()
               and (camdir / f'{stem}{e}').stat().st_mtime < src_mt]

    if missing:
        msg = f"Missing gerbers ({len(missing)}) — run CAM processor in Eagle"
        issues.append(msg)
        lines.append(f'[FAIL] {msg}')
    elif stale:
        msg = f"Stale gerbers ({len(stale)} files) — run CAM processor in Eagle"
        issues.append(msg)
        lines.append(f'[FAIL] {msg}')
    else:
        lines.append('[PASS] Gerbers are current')

    # --- BOM generation ---
    pcba_rows, dnp_rows, other_rows = parse_schematic(sch_path)
    pcba_count  = sum(len(r[3]) for r in pcba_rows)
    other_count = sum(len(r[3]) for r in dnp_rows) + sum(len(r[3]) for r in other_rows)

    write_csv(pcba_rows, csv_out)
    write_html(pcba_rows, dnp_rows, other_rows, sch_path, html_out)
    lines.append(f'[PASS] BOM: {pcba_count} PCBA parts, {other_count} other/DNP')
    lines.append(f'[PASS] CSV:  {csv_out.relative_to(proj)}')
    lines.append(f'[PASS] HTML: {html_out.relative_to(proj)}')

    # --- CPL generation via Eagle + modified ULP ---
    # Copy the board to a temp directory using the original filename so the ULP
    # derives the correct output name (it uses filename(B.name) as the stem).
    # Using a temp *directory* rather than a temp *file* avoids a random name
    # that would make the ULP write e.g. tmp12345_top_cpl.csv instead of
    # umod4_top_cpl.csv.
    tmp_dir  = Path(tempfile.mkdtemp(dir='/mnt/c/Users/robin/AppData/Local/Temp'))
    tmp_brd  = tmp_dir / f'{stem}.brd'
    shutil.copy2(brd, tmp_brd)
    try:
        brd_win  = subprocess.check_output(['wslpath', '-w', str(tmp_brd)]).decode().strip()
        ulp_path = proj / 'jlcpcb_smta_exporter_v7.ulp'
        ulp_win  = subprocess.check_output(['wslpath', '-w', str(ulp_path)]).decode().strip()
        jlc_win  = subprocess.check_output(['wslpath', '-w', str(jlcdir)]).decode().strip()

        bat_wsl  = subprocess.check_output(['wslpath', '-u', BAT_FILE]).decode().strip()
        with open(bat_wsl, 'w', newline='\r\n') as f:
            f.write('@echo off\r\n')
            f.write('cd /d C:\\Users\\robin\r\n')
            f.write(f'start /wait "" "{EAGLE_EXE}" "{brd_win}" '
                    f'-C "RUN \'{ulp_win}\' \'{jlc_win}\'; QUIT;"\r\n')

        ret = subprocess.call(['cmd.exe', '/c', BAT_FILE],
                              cwd='/mnt/c/Users/robin')
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    cpl_out = jlcdir / f'{stem}_top_cpl.csv'
    ulp_bom = jlcdir / f'{stem}_top_bom.csv'
    ulp_bom.unlink(missing_ok=True)  # ULP BOM has a bug; we use our own bom.csv
    if ret == 0 and cpl_out.exists():
        # Filter CPL to PCBA designators only. The ULP includes anything with an
        # SMD pad (test pads, fiducials, etc.) — we only want assembled parts.
        pcba_designators = {ref for _, _, _, refs in pcba_rows for ref in refs}
        with open(cpl_out, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            all_rows = list(reader)
        kept     = [r for r in all_rows if r and r[0].strip() in pcba_designators]
        stripped = sorted(
            [r[0].strip() for r in all_rows if r and r[0].strip() and r[0].strip() not in pcba_designators],
            key=_nat_key)
        with _open_for_write(cpl_out, newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(kept)
        if stripped:
            with _open_for_write(jlcdir / 'cpl-stripped.txt', encoding='utf-8') as f:
                f.write('\n'.join(stripped) + '\n')
        suffix = f' ({len(kept)} parts'
        if stripped:
            suffix += f', {len(stripped)} stripped'
        suffix += ')'
        lines.append(f'[PASS] CPL:  {cpl_out.relative_to(proj)}{suffix}')
        if stripped:
            lines.append(f'       Stripped from CPL: {", ".join(stripped)}')
    else:
        msg = "CPL generation failed — run jlcpcb_smta_exporter_v7.ulp manually"
        issues.append(msg)
        lines.append(f'[FAIL] {msg}')

    # --- ZIP (only if gerbers are current) ---
    if not missing and not stale:
        with zipfile.ZipFile(zip_out, 'w', zipfile.ZIP_DEFLATED) as zf:
            for ext in GERBER_EXTS:
                zf.write(camdir / f'{stem}{ext}', f'{stem}{ext}')
        kb = zip_out.stat().st_size // 1024
        lines.append(f'[PASS] ZIP:  {zip_out.relative_to(proj)} ({kb} KB)')
    else:
        lines.append('[SKIP] ZIP skipped — gerbers not current')

    for line in lines:
        print(f' {line}')

    if issues:
        print(f'{"-"*60}')
        print(' Action required:')
        for issue in issues:
            print(f'   → {issue}')
    print(f'{"="*60}\n')

    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
