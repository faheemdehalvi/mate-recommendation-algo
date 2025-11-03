"""README / CLI

Offline T/E Feature Generator
----------------------------

Usage:
  Batch (flags):
    python -m te_features.cli --name "Jaden Ekbote" --dob 2003-02-11 --tob 04:35 --place "Hubli, IN" --json

  Interactive prompts:
    python -m te_features.cli --interactive

Flags:
  --json                Print pretty JSON (default).
  --raw                 Include raw/intermediate astro values (astro block is always included per schema).
  --no-hash-jitter      Disable tiny deterministic name-based jitter.

Notes & Limits:
  - No network is used. Positions come from Swiss Ephemeris if available; else a deterministic
    low-precision fallback (~±1° Sun, ~±3–5° Moon) is used, which is sufficient for coarse
    sidereal sign/nakshatra bins. Ayanamsa (Lahiri) is approximated linearly when falling back.
  - Time zones come from the bundled gazetteer data/cities_min.csv. You can add rows with fields:
      name,country,lat,lon,tz_offset_hours
    For example:
      Hubli,IN,15.3647,75.1240,5.5
      Hubballi,IN,15.3647,75.1240,5.5
  - If a place is not in the gazetteer, you may pass "lat,lon,offset" directly (e.g., "15.36,75.12,5.5").
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Sequence, Tuple
import sys

from . import compute_te
from .te_mapper import get_t_dim_meta, get_e_dim_meta


def _parser(batch_required: bool) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="te_features", add_help=True)
    p.add_argument("--interactive", action="store_true", help="Prompt for inputs interactively")
    p.add_argument("--name", required=batch_required)
    p.add_argument("--dob", required=batch_required, help="YYYY-MM-DD")
    p.add_argument("--tob", required=batch_required, help="HH:MM (24h local time)")
    p.add_argument("--place", required=batch_required, help="City[, Country] or 'lat,lon,offset'")
    p.add_argument("--json", action="store_true", help="Print pretty JSON (default in batch mode)")
    p.add_argument("--raw", action="store_true", help="Include raw/intermediate (astro is always included)")
    p.add_argument("--no-hash-jitter", action="store_true", help="Disable name-based tiny jitter")
    p.add_argument("--profile", action="store_true", help="Also print a witty profile paragraph")
    return p


def _prompt(msg: str) -> str:
    return input(msg).strip()


def _print_labeled_vectors(result: dict) -> None:
    t_meta = list(get_t_dim_meta())
    e_meta = list(get_e_dim_meta())
    T = result["T"]
    E = result["E"]

    print("\nT (Traits)")
    for i, (label, desc) in enumerate(t_meta):
        val = T[f"t{i}"]
        print(f"  t{i}  {label:22s}  {val:0.3f}  — {desc}")

    print("\nE (Engagement/Energy)")
    for i, (label, desc) in enumerate(e_meta):
        val = E[f"e{i}"]
        print(f"  e{i}  {label:22s}  {val:0.3f}  — {desc}")


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    interactive = "--interactive" in argv
    parser = _parser(batch_required=not interactive)
    args = parser.parse_args(argv)

    if interactive:
        name = args.name or _prompt("Full name: ")
        dob = args.dob or _prompt("DOB (YYYY-MM-DD): ")
        tob = args.tob or _prompt("TOB (HH:MM 24h local): ")
        place = args.place or _prompt("Place (City[, CC] or lat,lon,offset): ")
        disable_jitter = bool(args.no_hash_jitter)
        result = compute_te(name, dob, tob, place, disable_hash_jitter=disable_jitter)
        print(f"\nName: {result['name']}")
        rp = result["resolved_place"]
        print(f"Resolved place: {rp['name']}  lat={rp['lat']:.4f} lon={rp['lon']:.4f} tz={rp['tz_offset']}")
        _print_labeled_vectors(result)
        if args.profile:
            from .profile_gen import generate_witty_profile
            print("\nProfile")
            print(generate_witty_profile(result))
        return 0

    # Batch mode (flags)
    result = compute_te(
        args.name,
        args.dob,
        args.tob,
        args.place,
        disable_hash_jitter=bool(args.no_hash_jitter),
        include_raw_astro=True,
    )
    if args.json or True:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_labeled_vectors(result)
    if args.profile:
        from .profile_gen import generate_witty_profile
        print("\nProfile")
        print(generate_witty_profile(result))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
