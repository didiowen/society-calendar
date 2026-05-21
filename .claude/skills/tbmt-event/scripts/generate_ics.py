#!/usr/bin/env python3
"""
Generate events.ics from tbmt_events.json — all upcoming events, no filter.

Run:
    python scripts/generate_ics.py
"""

import io, json, re, sys, uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).parent.parent  # skill root


def load_events():
    with open(BASE / "tbmt_events.json", encoding="utf-8") as f:
        return json.load(f)


_TIME_PREFIX_RE = re.compile(r"^\s*\d{1,2}:\d{2}\s*[~\-－～]\s*\d{1,2}:\d{2}\s*")


def _norm_title(t):
    """Normalise a TBMT title for dedup: drop a leading time-range prefix and a
    leading 'TBMT' org tag, so e.g. '12:00~14:00 TBMT理監事會' and '理監事會'
    collapse to the same key."""
    t = _TIME_PREFIX_RE.sub("", t or "")
    t = re.sub(r"^TBMT\s*", "", t)
    return t.strip()


def dedup(events):
    """Drop duplicate TBMT events, keeping the entry with the richer
    location/description. The TBMT site sometimes lists the same event twice
    under different detail-page IDs and slightly different titles. Two events
    collapse when they share start date + time range + normalised title."""
    best = {}
    for e in events:
        title = e.get("full_title") or e.get("title", "")
        key = (e.get("date", ""), e.get("time_range", ""), _norm_title(title))
        score = len(e.get("location", "") or "") + len(e.get("description", "") or "")
        if key not in best or score > best[key][1]:
            best[key] = (e, score)
    deduped = [v[0] for v in best.values()]
    deduped.sort(key=lambda e: e["date"])
    return deduped


def esc(s):
    return (
        s.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def fold(name, value):
    """Fold ICS line at 75 octets per RFC 5545 §3.1."""
    line = f"{name}:{value}"
    b = line.encode("utf-8")
    chunks = []
    first = True
    while b:
        limit = 75 if first else 74
        first = False
        cut = min(limit, len(b))
        while cut > 0:
            try:
                b[:cut].decode("utf-8")
                break
            except UnicodeDecodeError:
                cut -= 1
        chunks.append(b[:cut].decode("utf-8"))
        b = b[cut:]
    result = chunks[0]
    for chunk in chunks[1:]:
        result += "\r\n " + chunk
    return result + "\r\n"


def build_desc(e):
    p = []
    if e.get("organizer"):
        p.append(f"主辦單位：{e['organizer']}")
    if e.get("location"):
        p.append(f"地點：{e['location']}")
    if e.get("detail_url"):
        p.append(f"學會頁面：{e['detail_url']}")
    if e.get("attachments"):
        p += ["", "--- 附件 ---"]
        for a in e["attachments"]:
            p.append(a)
    if e.get("description"):
        p += ["", "--- 活動內容 ---", e["description"]]
    return "\n".join(p)


def main():
    all_events = load_events()
    events = dedup(all_events)
    dropped = len(all_events) - len(events)
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = BASE / "events.ics"

    with open(out, "w", encoding="utf-8", newline="") as f:
        def w(line): f.write(line + "\r\n")
        def wf(name, value): f.write(fold(name, value))

        w("BEGIN:VCALENDAR")
        w("VERSION:2.0")
        w("PRODID:-//TBMT//Bone Marrow Transplant Events//ZH")
        w("CALSCALE:GREGORIAN")
        w("METHOD:PUBLISH")
        w("X-WR-CALNAME:學會")
        w("X-WR-TIMEZONE:Asia/Taipei")
        w("BEGIN:VTIMEZONE")
        w("TZID:Asia/Taipei")
        w("BEGIN:STANDARD")
        w("DTSTART:19700101T000000")
        w("TZOFFSETFROM:+0800")
        w("TZOFFSETTO:+0800")
        w("TZNAME:CST")
        w("END:STANDARD")
        w("END:VTIMEZONE")

        for e in events:
            uid_src = e.get("detail_url") or e["event_id"]
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL, uid_src))
            title = e.get("full_title") or e["title"]
            tr = e.get("time_range", "")

            w("BEGIN:VEVENT")
            w(f"UID:{uid}")
            w(f"DTSTAMP:{now}")
            wf("SUMMARY", esc(title))
            if e.get("location"):
                wf("LOCATION", esc(e["location"]))
            desc = build_desc(e)
            if desc:
                wf("DESCRIPTION", esc(desc))

            # time_range format from TBMT: "HH:MM-HH:MM"
            m = re.match(r"(\d{2}:\d{2})-(\d{2}:\d{2})$", tr)
            if m:
                st, et = m.group(1).replace(":", ""), m.group(2).replace(":", "")
                d = e["date"].replace("-", "")
                w(f"DTSTART;TZID=Asia/Taipei:{d}T{st}00")
                w(f"DTEND;TZID=Asia/Taipei:{d}T{et}00")
            else:
                # All-day; FullCalendar end_date is already exclusive
                sd = date.fromisoformat(e["date"])
                ed = date.fromisoformat(e["end_date"])
                if ed <= sd:
                    ed = sd + timedelta(days=1)
                w(f"DTSTART;VALUE=DATE:{sd:%Y%m%d}")
                w(f"DTEND;VALUE=DATE:{ed:%Y%m%d}")

            w("END:VEVENT")

        w("END:VCALENDAR")

    print(f"OK {len(events)} events written to: {out}  (dropped {dropped} duplicates)")


if __name__ == "__main__":
    main()
