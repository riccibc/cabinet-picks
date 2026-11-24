# Working in cabinet-picks

This repository holds `picks.json`, the weekly record picks for the Cabinet
app. Read `README.md` first; it is the whole procedure.

When asked to add picks for a week:

1. Use `scripts/add_pick.py` for every record. Never type an MBID, artist,
   title or year by hand, and never guess between matches. If the script lists
   several, show them to the person and ask which one.
2. The person writes the notes. If they gave notes, pass them with `--note`
   exactly as given. If they didn't, ask for them. Don't write notes yourself.
3. `goLive` is the Friday of the week they mean ("the week of the 20th" is
   Friday the 20th if the 20th is a Friday; otherwise ask).
4. Run `python3 scripts/validate.py` and fix every error before committing.
   Mention any warnings.
5. Commit with a message like "Picks for Nov 20" and push.

Don't change `schema.json`, the scripts or the workflow unless asked. The
Cabinet app and its Worker depend on this exact format.
