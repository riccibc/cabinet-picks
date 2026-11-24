#!/usr/bin/env python3
"""Adds a record to a week in picks.json, looked up in MusicBrainz.

  python3 scripts/add_pick.py --week 2026-11-20 --artist "Nick Drake" --title "Pink Moon"
  python3 scripts/add_pick.py --week 2026-11-20 --artist "..." --title "..." --tag reissue
  python3 scripts/add_pick.py --week 2026-11-20 --artist "..." --title "..." --note "In my words."
  python3 scripts/add_pick.py --week 2026-11-20 --mbid <release-group id>

Artist, title and year are written as MusicBrainz has them. The week is
created if it doesn't exist. The note is left empty unless --note is given,
and validate.py fails until it's written, so a pick can't go live without one.

If more than one album matches, they're listed and nothing is written. Run
again with --mbid to choose. It never guesses.
"""

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mb  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
TAGS = ["new", "reissue", "new pressing"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--week", required=True, help="goLive date, YYYY-MM-DD (usually a Friday)")
    p.add_argument("--artist")
    p.add_argument("--title")
    p.add_argument("--mbid", help="release-group ID, to choose between matches")
    p.add_argument("--tag", choices=TAGS)
    p.add_argument("--note", default="")
    p.add_argument("--week-title", default="Picks", help="heading for a new week (default: Picks)")
    args = p.parse_args()

    import datetime
    try:
        datetime.date.fromisoformat(args.week)
    except ValueError:
        sys.exit(f"--week {args.week} is not a date in the form YYYY-MM-DD")

    if args.mbid:
        try:
            group = mb.release_group(args.mbid)
        except mb.NotFound:
            sys.exit(f"MusicBrainz has no release group {args.mbid}")
    else:
        if not (args.artist and args.title):
            sys.exit("Give --artist and --title, or --mbid")
        found = [g for g in mb.search(args.artist, args.title) if mb.matches(g, args.artist, args.title)]
        if not found:
            sys.exit(f"Nothing in MusicBrainz matches {args.artist} — {args.title}. Check the spelling, "
                     "or find the release group on musicbrainz.org and pass --mbid.")
        albums = [g for g in found if g.get("primary-type") == "Album"] or found
        if len(albums) > 1:
            print(f"More than one match for {args.artist} — {args.title}. Nothing written. Choose one with --mbid:\n")
            for g in albums:
                kind = " / ".join(filter(None, [g.get("primary-type")] + (g.get("secondary-types") or [])))
                print(f"  --mbid {g['id']}   {mb.credited_artist(g)} — {g['title']} "
                      f"({mb.year(g) or '?'}, {kind or 'type unknown'})"
                      f"{'  · ' + g['disambiguation'] if g.get('disambiguation') else ''}")
            return 2
        group = albums[0]

    pick = {
        "mbid": group["id"],
        "artist": mb.credited_artist(group),
        "title": group["title"],
        "year": mb.year(group) or 0,
        "note": args.note,
    }
    if args.tag:
        pick["tag"] = args.tag
    if not pick["year"]:
        sys.exit(f"MusicBrainz has no release date for {pick['artist']} — {pick['title']}; add it by hand with the year.")

    path = ROOT / "picks.json"
    data = json.loads(path.read_text())
    week = next((w for w in data["weeks"] if w["goLive"] == args.week), None)
    if week is None:
        week = {"goLive": args.week, "title": args.week_title, "picks": []}
        data["weeks"].append(week)
        data["weeks"].sort(key=lambda w: w["goLive"])
    if any(x["mbid"] == pick["mbid"] for x in week["picks"]):
        sys.exit(f"{pick['artist']} — {pick['title']} is already in the week of {args.week}")
    if len(week["picks"]) >= 10:
        sys.exit(f"The week of {args.week} already has ten picks")
    week["picks"].append(pick)

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Added {pick['artist']} — {pick['title']} ({pick['year']}) to the week of {args.week}"
          f"{'' if pick['note'] else '. Write its note before pushing.'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
