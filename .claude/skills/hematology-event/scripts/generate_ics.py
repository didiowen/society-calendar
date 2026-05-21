#!/usr/bin/env python3
"""
Generate events.ics from events.json — no API credentials needed.

Run:
    python scripts/generate_ics.py

Then import events.ics into Google Calendar:
    Settings (⚙) → Import & export → Import → select events.ics → choose 學會 calendar
"""

import json
import re
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).parent.parent  # skill root (.claude/skills/hematology-event)

TAINAN_KW    = ["台南", "臺南"]
KAOHSIUNG_KW = ["高雄", "義大", "嘉義"]


def load_events():
    with open(BASE / "events.json", encoding="utf-8") as f:
        return json.load(f)


def credits_value(credits_str):
    m = re.search(r"(\d+(?:\.\d+)?)", credits_str or "")
    return float(m.group(1)) if m else 0.0


def passes_filter(e):
    loc = e.get("location", "") + e.get("organizer", "")
    cred = credits_value(e.get("credits", ""))
    if any(kw in loc for kw in TAINAN_KW):
        return True
    if any(kw in loc for kw in KAOHSIUNG_KW):
        return cred > 2
    return cred > 3


def parse_time_range(tr):
    """Return (start_date, start_time, end_date, end_time) strings, or None."""
    tr = tr.replace("\n", " ")
    m = re.match(
        r"(\d{4}-\d{2}-\d{2})的(\d{2}:\d{2})至\s*(?:(\d{4}-\d{2}-\d{2})的)?(\d{2}:\d{2})",
        tr,
    )
    if m:
        sd, st, ed, et = m.groups()
        return sd, st, ed or sd, et
    return None


def esc(s):
    """Escape ICS special characters."""
    return (
        s.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def fold(name, value):
    """Fold ICS property line at 75 octets per RFC 5545 §3.1."""
    line = f"{name}:{value}"
    b = line.encode("utf-8")
    chunks = []
    first = True
    while b:
        limit = 75 if first else 74  # continuation lines get a leading space (1 byte)
        first = False
        cut = min(limit, len(b))
        # Avoid splitting in the middle of a multi-byte UTF-8 sequence
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
    if e.get("subtitle"):
        p.append(e["subtitle"])
    if e.get("organizer"):
        p.append(f"主辦單位：{e['organizer']}")
    if e.get("category"):
        p.append(f"分類：{e['category']}")
    if e.get("credits"):
        p.append(f"積分：{e['credits']}")
    if e.get("url"):
        p.append(f"學會頁面：{e['url']}")
    if e.get("links"):
        p += ["", "--- 相關連結 ---"]
        for lk in e["links"]:
            text = lk.get("text", "").replace("\r\n", " ").replace("\n", " ").strip()
            p.append(f"{text}：{lk['url']}")
    if e.get("registration_program"):
        p += ["", "--- 報名/節目表 ---", e["registration_program"]]
    return "\n".join(p)


def main():
    all_events = load_events()
    events = [e for e in all_events if passes_filter(e)]
    skipped = len(all_events) - len(events)
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out = BASE / "events.ics"

    with open(out, "w", encoding="utf-8", newline="") as f:

        def w(line):
            f.write(line + "\r\n")

        def wf(name, value):
            f.write(fold(name, value))

        w("BEGIN:VCALENDAR")
        w("VERSION:2.0")
        w("PRODID:-//HST//Hematology Society Events//ZH")
        w("CALSCALE:GREGORIAN")
        w("METHOD:PUBLISH")
        w("X-WR-CALNAME:學會")
        w("X-WR-TIMEZONE:Asia/Taipei")
        # VTIMEZONE
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
            is_allday = e["time"] == "00:00"
            tr = parse_time_range(e.get("time_range", ""))
            uid = str(uuid.uuid5(uuid.NAMESPACE_URL, e["url"]))

            w("BEGIN:VEVENT")
            w(f"UID:{uid}")
            w(f"DTSTAMP:{now}")
            wf("SUMMARY", esc(e["title"]))
            if e.get("location"):
                wf("LOCATION", esc(e["location"]))
            d = build_desc(e)
            if d:
                wf("DESCRIPTION", esc(d))

            if tr:
                sd, st, ed, et = tr
                if is_allday and st == "00:00" and et == "00:00":
                    # All-day: ICS DTEND is exclusive, so add 1 day
                    sd_d = date.fromisoformat(sd)
                    ed_d = date.fromisoformat(ed) + timedelta(days=1)
                    w(f"DTSTART;VALUE=DATE:{sd_d:%Y%m%d}")
                    w(f"DTEND;VALUE=DATE:{ed_d:%Y%m%d}")
                else:
                    w(f"DTSTART;TZID=Asia/Taipei:{sd.replace('-','')}T{st.replace(':','')}00")
                    w(f"DTEND;TZID=Asia/Taipei:{ed.replace('-','')}T{et.replace(':','')}00")
            else:
                # Fallback: single all-day event
                sd_d = date.fromisoformat(e["date"])
                w(f"DTSTART;VALUE=DATE:{sd_d:%Y%m%d}")
                w(f"DTEND;VALUE=DATE:{(sd_d + timedelta(days=1)):%Y%m%d}")

            w("END:VEVENT")

        w("END:VCALENDAR")

    print(f"OK {len(events)}/{len(all_events)} events written to: {out}  (filtered out {skipped})")
    print()
    print("Import into Google Calendar:")
    print("  1. Open calendar.google.com on desktop")
    print("  2. Settings ⚙ → Import & export → Import")
    print("  3. Choose events.ics")
    print("  4. Select '學會' calendar")
    print("  5. Click Import")


if __name__ == "__main__":
    main()
