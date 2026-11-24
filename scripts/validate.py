#!/usr/bin/env python3
"""Checks picks.json before it goes anywhere near the app.

  python3 scripts/validate.py            # full check, including MusicBrainz
  python3 scripts/validate.py --offline  # format and dates only

Errors fail the run (and the GitHub Action). Warnings are printed but pass.

Errors:
  - anything the schema rejects (missing field, empty note, unknown tag, ...)
  - a goLive that isn't a real date, or two weeks with the same goLive
  - the same release group twice in one week
  - an MBID that MusicBrainz doesn't know

Warnings:
  - a goLive that isn't a Friday
  - fewer than six picks in a week
  - an artist or title that doesn't match what MusicBrainz has for the MBID
  - no cover art in the Cover Art Archive (the app shows a plain sleeve)
  - an exclamation mark in a note
"""

import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mb  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    offline = "--offline" in sys.argv
    errors, warnings = [], []

    try:
        data = json.loads((ROOT / "picks.json").read_text())
    except json.JSONDecodeError as e:
        print(f"FAILED: picks.json is not valid JSON: {e}")
        return 1

    try:
        import jsonschema
    except ImportError:
        print("FAILED: the jsonschema package is needed. Install it with: pip install jsonschema")
        return 1
    schema = json.loads((ROOT / "schema.json").read_text())
    for err in sorted(jsonschema.Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(top level)"
        errors.append(f"{where}: {err.message}")
    if errors:
        return report(errors, warnings)

    seen_dates = set()
    for i, week in enumerate(data["weeks"]):
        label = f"week {week['goLive']}"
        try:
            day = datetime.date.fromisoformat(week["goLive"])
        except ValueError:
            errors.append(f"weeks/{i}: goLive {week['goLive']} is not a real date")
            continue
        if week["goLive"] in seen_dates:
            errors.append(f"{label}: two weeks have this goLive date")
        seen_dates.add(week["goLive"])
        if day.weekday() != 4:
            warnings.append(f"{label}: goes live on a {day.strftime('%A')}, not a Friday")
        if len(week["picks"]) < 6:
            n = len(week["picks"])
            warnings.append(f"{label}: {n} pick{'' if n == 1 else 's'}; a week is usually six to ten")

        ids = set()
        for pick in week["picks"]:
            name = f"{label}: {pick['artist']} — {pick['title']}"
            if pick["mbid"] in ids:
                errors.append(f"{name}: appears twice in this week")
            ids.add(pick["mbid"])
            if not pick["note"].strip():
                errors.append(f"{name}: the note is empty")
            if "!" in pick["note"]:
                warnings.append(f"{name}: the note has an exclamation mark")
            if offline:
                continue
            try:
                group = mb.release_group(pick["mbid"])
            except mb.NotFound:
                errors.append(f"{name}: MusicBrainz has no release group {pick['mbid']}")
                continue
            except Exception as e:  # network trouble is not the file's fault
                warnings.append(f"{name}: couldn't reach MusicBrainz to check it ({e})")
                continue
            if not mb.matches(group, pick["artist"], pick["title"]):
                warnings.append(
                    f"{name}: MusicBrainz calls {pick['mbid']} "
                    f"{mb.credited_artist(group)} — {group['title']}")
            try:
                if not mb.has_cover(pick["mbid"]):
                    warnings.append(f"{name}: no cover art in the Cover Art Archive")
            except Exception:
                pass

    return report(errors, warnings)


def report(errors, warnings):
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    if errors:
        print(f"\nFAILED with {len(errors)} error(s). The app keeps showing the last good list until this is fixed.")
        return 1
    print("\npicks.json is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
