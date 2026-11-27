#!/usr/bin/env python3
"""Writes every published week to ARCHIVE.md and picks.csv.

  python3 scripts/build_archive.py

ARCHIVE.md is a readable list, newest week first, grouped by year: ready to
copy into a newsletter or a year-end recap. picks.csv has one row per pick for
a spreadsheet. Both are rebuilt from picks.json every time, so they're never
edited by hand. Weeks whose goLive date hasn't arrived yet (Pacific time) are
left out, so a queued week can't leak into a newsletter early.
"""

import csv
import datetime
import json
import pathlib
import sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / "picks.json").read_text())
    today = datetime.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    weeks = sorted((w for w in data["weeks"] if w["goLive"] <= today),
                   key=lambda w: w["goLive"], reverse=True)

    lines = ["# Cabinet picks: every week", "",
             "Built from picks.json by scripts/build_archive.py. Don't edit by hand.", ""]
    year = None
    for w in weeks:
        day = datetime.date.fromisoformat(w["goLive"])
        if day.year != year:
            year = day.year
            count = sum(len(x["picks"]) for x in weeks if x["goLive"].startswith(str(year)))
            lines += [f"## {year}", "", f"{count} records.", ""]
        lines += [f"### {w['title']} · {day.strftime('%b')} {day.day}, {day.year}", ""]
        for p in w["picks"]:
            tag = f" · {p['tag']}" if p.get("tag") else ""
            link = f"https://musicbrainz.org/release-group/{p['mbid']}"
            lines.append(f"- **{p['artist']} — [{p['title']}]({link})** ({p['year']}{tag})  ")
            lines.append(f"  {p['note']}")
        lines.append("")
    (ROOT / "ARCHIVE.md").write_text("\n".join(lines).rstrip() + "\n")

    with open(ROOT / "picks.csv", "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(["goLive", "artist", "title", "year", "tag", "note", "musicbrainz"])
        for w in weeks:
            for p in w["picks"]:
                out.writerow([w["goLive"], p["artist"], p["title"], p["year"], p.get("tag", ""),
                              p["note"], f"https://musicbrainz.org/release-group/{p['mbid']}"])

    total = sum(len(w["picks"]) for w in weeks)
    print(f"ARCHIVE.md and picks.csv: {len(weeks)} week(s), {total} pick(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
