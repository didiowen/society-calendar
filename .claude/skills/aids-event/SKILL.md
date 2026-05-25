---
name: aids-event
description: Fetches upcoming events from 台灣愛滋病學會 (Taiwan AIDS Society), generates a filtered ICS, and pushes to the subscribable calendar. Use when the user asks to update or sync AIDS society events.
allowed-tools: [Bash, Read, Write]
---

# AIDS Society Event Sync

Scrapes the 台灣愛滋病學會 event list, enriches with detail pages, generates a filtered ICS, and publishes to notes-not-scandal.

## Subscribe URL (auto-refreshes monthly on the 21st)

```
https://didiowen.github.io/notes-not-scandal/cal/aids-events.ics
```

In Google Calendar: **Other calendars → + → From URL** → paste the URL above.

To refresh manually (also runs IDSROC + hematology):

```sh
python3 X/scripts/refresh_calendars.py
```

## Filter (always applied)

Events are included if **any** condition is true:

| Condition | Value |
|-----------|-------|
| 台南 | 全部納入 |
| 高雄, 嘉義, 台北 | > 4 學分 |
| 其他地區 | 排除 |

To change the filter, edit `TAINAN_KW` and `PRIORITY_KW` and `passes_filter()` in `scripts/generate_ics.py`.

## Quick Start (manual one-off)

```sh
cd .claude/skills/aids-event
python3 scripts/fetch_aids_events.py   # scrape → events.json
python3 scripts/generate_ics.py        # filter + events.json → events.ics
```

## Workflow

- [ ] Step 1: Fetch events → `events.json`
- [ ] Step 2: Generate filtered ICS → `events.ics`
- [ ] Step 3: Push to notes-not-scandal (done by `refresh_calendars.py`)

## Source

- **List page**: `https://www.aids-care.org.tw/events/index.php`
- **Detail pages**: `https://www.aids-care.org.tw/events/content.php?id={id}&pageno=1&continue=Y`
- Detail pages require a session cookie from the list page (handled automatically by the script).

## Event fields

| Field | Source |
|-------|--------|
| date | `<time class="events-list__date">` |
| title | `<a href="content.php?...">` |
| location | `<div class="events-list__place">` |
| credits | `<span class="events-list__socre">` (typo on site) |
| time_range | detail page `活動日期：` |
| organizer | detail page `主辦單位` |
| speaker | detail page `主講人` |
| fee | detail page `活動收費` |
| program_url | detail page `下載檔案` link |
| contact / email / phone | detail page `聯絡資訊` |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Detail page returns 資料讀取有誤 | Script must visit list page first to get a session cookie — already handled |
| 0 events found | Check `events-list__item` class in `index.php` HTML |
| 台北 events not showing | Confirm "台北"/"臺北" is in `PRIORITY_KW` |
