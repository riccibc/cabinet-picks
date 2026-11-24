# Cabinet weekly picks

The hand-chosen records shown under **New this week** in Cabinet's Crate tab.
Six to ten records a week, like a record shop's staff-picks wall. A new list
goes live on Friday, when new records come out.

Everything lives in `picks.json`. Edit it, push, and the app picks it up.

## How a week goes live

- Each week has a `goLive` date. The app shows **the most recent week whose
  `goLive` date has arrived**, on Pacific time.
- Queue as many future weeks as you like. A week with a future date changes
  nothing until its day.
- With no new week, the app keeps showing the last one, headed with its date
  ("Picks · Nov 20"), so a missed week never claims to be new.
- If a push breaks the file, the GitHub check fails and the app keeps showing
  the last good list. Nothing empties.

The app checks for a new list at most once a day, and again soon after a
queued week's date arrives.

## Adding a week

1. Add each record. This looks it up in MusicBrainz and writes artist, title,
   year and ID exactly as MusicBrainz has them:

   ```bash
   python3 scripts/add_pick.py --week 2026-11-20 --artist "Nick Drake" --title "Pink Moon"
   ```

   - `--tag new`, `--tag reissue` or `--tag "new pressing"` adds a tag.
   - `--note "..."` writes the note at the same time.
   - If more than one album matches, it lists them with their IDs and writes
     nothing. Run it again with `--mbid <id>` for the right one.
   - If nothing matches, check the spelling, or find the release group on
     musicbrainz.org and pass `--mbid`.

2. Write a note for every pick in `picks.json`: one or two lines, in your own
   words. A pick without a note fails the check, so nothing goes live without one.

3. Check, then push:

   ```bash
   python3 scripts/validate.py
   git add picks.json && git commit -m "Picks for Nov 20" && git push
   ```

The check needs `pip install jsonschema` once.

## The format

```json
{
  "weeks": [
    {
      "goLive": "2026-11-20",
      "title": "Picks",
      "picks": [
        {
          "mbid": "740ec10a-e887-38a6-a04d-fe2069c9e2a7",
          "artist": "Nick Drake",
          "title": "Pink Moon",
          "year": 1972,
          "note": "One or two lines, in my words.",
          "tag": "reissue"
        }
      ]
    }
  ]
}
```

| Field | Rules |
|---|---|
| `goLive` | `YYYY-MM-DD`, a real date, one week per date. Usually a Friday (other days give a warning). |
| `title` | The heading before the date. Normally `Picks`. |
| `picks` | 1–10 records. Fewer than six gives a warning. |
| `mbid` | The MusicBrainz **release-group** ID. Cover art comes from it. |
| `artist`, `title`, `year` | As on MusicBrainz. `add_pick.py` fills these in. |
| `note` | Required. Up to 280 characters. |
| `tag` | Optional: `new`, `reissue` or `new pressing`. |

`schema.json` is the formal version of this table.

## What the check does

`scripts/validate.py` runs on every push (GitHub Actions) and fails loudly on:

- anything the schema rejects: a missing field, an empty note, an unknown tag
- a `goLive` that isn't a real date, or two weeks on the same date
- the same record twice in one week
- an ID MusicBrainz doesn't know

It warns, but passes, when:

- a week isn't on a Friday, or has fewer than six picks
- the artist or title doesn't match what MusicBrainz has for that ID
- there's no cover art in the Cover Art Archive (the app shows a plain sleeve)
- a note has an exclamation mark

`python3 scripts/validate.py --offline` checks the format and dates without
MusicBrainz.

## Why this repository is public

The picks are shown to everyone who uses the app, so there's nothing to hide,
and the Worker can read the file without a token. A token could leak, and
worse, it could quietly expire and leave the app stuck on an old list. The
one cost is that anyone could see queued weeks before their Friday.
