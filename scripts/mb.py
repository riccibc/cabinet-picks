"""Small MusicBrainz and Cover Art Archive client shared by the scripts.

MusicBrainz asks for a descriptive User-Agent and at most one request a
second, and sometimes sheds load with 503. This keeps to both and retries.
"""

import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "CabinetPicks/1.0 ( connect@attunelabspro.com )"
BASE = "https://musicbrainz.org/ws/2"
_last = [0.0]


class NotFound(Exception):
    pass


def _get(url, method="GET"):
    for attempt in range(3):
        wait = 1.1 - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        req = urllib.request.Request(url, method=method, headers={
            "User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, (r.read() if method == "GET" else b"")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise NotFound(url)
            if e.code != 503 or attempt == 2:
                raise
        except (urllib.error.URLError, ConnectionError):
            if attempt == 2:
                raise
        time.sleep(3)


def release_group(mbid):
    """The release group with this ID. Raises NotFound."""
    _, body = _get(f"{BASE}/release-group/{mbid}?inc=artist-credits&fmt=json")
    return json.loads(body)


def has_cover(mbid):
    """True if the Cover Art Archive has a front cover for the release group."""
    try:
        _get(f"https://coverartarchive.org/release-group/{mbid}/front-250", method="HEAD")
        return True
    except NotFound:
        return False


def _escape(s):
    return "".join("\\" + c if c in '+-&|!(){}[]^"~*?:\\/' else c for c in s)


def search(artist, title):
    """Release groups matching artist and title, best first."""
    q = f'releasegroup:"{_escape(title)}" AND artist:"{_escape(artist)}"'
    _, body = _get(f"{BASE}/release-group?" + urllib.parse.urlencode({"query": q, "limit": 10, "fmt": "json"}))
    return json.loads(body).get("release-groups", [])


def credited_artist(group):
    return "".join(c.get("name", "") + c.get("joinphrase", "") for c in group.get("artist-credit") or [])


def year(group):
    raw = (group.get("first-release-date") or "")[:4]
    return int(raw) if raw.isdigit() else None


# Matching, the same rules the app uses: ignore case, accents, punctuation,
# a leading "The" on the artist, and edition suffixes on the title.

def fold(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^\w]+", " ", s).split())


def fold_title(s):
    s = re.sub(r"[(\[][^)\]]*[)\]]", " ", s)
    s = re.sub(r"\s*[-–—:]\s*(remaster(ed)?|deluxe|expanded|anniversary|special|bonus|mono|stereo)\b.*$", "", s, flags=re.I)
    noise = {"remaster", "remastered", "deluxe", "edition", "expanded", "version", "anniversary", "reissue"}
    return " ".join(w for w in fold(s).split() if w not in noise)


def fold_artist(s):
    f = fold(s)
    return f[4:] if f.startswith("the ") else f


def similarity(a, b):
    if a == b:
        return 1.0
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    dice = 2 * len(ta & tb) / (len(ta) + len(tb))
    return max(dice, 0.9) if (ta <= tb or tb <= ta) else dice


def matches(group, artist, title):
    return (similarity(fold_title(group["title"]), fold_title(title)) >= 0.9
            and similarity(fold_artist(credited_artist(group)), fold_artist(artist)) >= 0.85)
