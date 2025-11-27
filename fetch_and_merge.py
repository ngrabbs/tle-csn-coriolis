#!/usr/bin/env python3
import urllib.request
from pathlib import Path

CSN_URL = "http://www.csntechnologies.net/SAT/csnbare.txt"
CORIOLIS_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR=27640&FORMAT=tle"
OUTPUT_FILE = Path("csn_plus_coriolis.tle")


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=200) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_norad_from_line1(line1: str) -> str:
    # TLE line 1: columns 3–7 are the catalog number in classic TLE format
    # Example: "1 27640U 03001A ..."
    return line1[2:7].strip()


def main():
    print("Fetching CSN base list...")
    csn_text = fetch_text(CSN_URL)

    print("Fetching Coriolis TLE...")
    coriolis_text = fetch_text(CORIOLIS_URL).strip()

    # Normalize Coriolis block to exactly 3 lines (name + 2 TLE lines)
    coriolis_lines = [ln.rstrip() for ln in coriolis_text.splitlines() if ln.strip()]
    if len(coriolis_lines) < 2:
        raise RuntimeError("Coriolis TLE response doesn’t look valid")

    # If it’s only 2 lines (no name), fabricate a name line
    if len(coriolis_lines) == 2:
        coriolis_lines.insert(0, "CORIOLIS")

    coriolis_name, coriolis_l1, coriolis_l2 = coriolis_lines[:3]
    coriolis_norad = extract_norad_from_line1(coriolis_l1)
    print(f"Detected Coriolis NORAD ID: {coriolis_norad}")

    # Walk CSN file in 3-line groups and drop any entry with the same NORAD
    lines = [ln.rstrip("\n") for ln in csn_text.splitlines() if ln.strip()]
    merged_blocks = []

    i = 0
    while i + 2 < len(lines):
        name = lines[i]
        l1 = lines[i + 1]
        l2 = lines[i + 2]

        # Basic sanity check: this looks like a TLE block
        if not (l1.strip().startswith("1 ") and l2.strip().startswith("2 ")):
            # If the format is weird, just keep the line and move on cautiously
            merged_blocks.append("\n".join([name, l1, l2]))
            i += 3
            continue

        norad = extract_norad_from_line1(l1)
        if norad == coriolis_norad:
            print(f"Skipping existing Coriolis entry from CSN (NORAD {norad})")
            # Skip this block, we’ll replace with fresh CelesTrak one
        else:
            merged_blocks.append("\n".join([name, l1, l2]))
        i += 3

    # Append Coriolis block at the end
    merged_blocks.append("\n".join([coriolis_name, coriolis_l1, coriolis_l2]))

    output_text = "\n\n".join(merged_blocks) + "\n"
    OUTPUT_FILE.write_text(output_text, encoding="utf-8")
    print(f"Wrote merged file to {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()