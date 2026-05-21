# Society Calendar

> 用 AI 自動抓取台灣醫學會行事曆，一鍵同步到 Google Calendar

_Originally created by [htlin222](https://github.com/htlin222/society-calendar)._

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill%20Based-blueviolet?logo=anthropic)](https://claude.ai/claude-code)
[![Google Calendar](https://img.shields.io/badge/Google%20Calendar-ICS%20%2F%20MCP-4285F4?logo=google-calendar&logoColor=white)](#兩種使用方式擇一)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero_(stdlib_only)-brightgreen)](#tech-stack)
[![Made in Taiwan](https://img.shields.io/badge/Made%20in-Taiwan%20%F0%9F%87%B9%F0%9F%87%BC-red)](https://github.com/htlin222/society-calendar)

---

## 為什麼需要這個？

身為醫師，每個月要追蹤好幾個學會的繼續教育活動、研討會、年會。每個學會網站長得不一樣，有些用民國年，有些有 CAPTCHA，有些 SSL 壞掉。

**手動做法**：逐一開學會網站 → 翻頁找活動 → 手動建 Google Calendar 事件 → 每月重複

**自動化做法**：給 Claude Code 一個 URL → 自動探索、抓取、產生 `.ics` 或直接建立日曆事件

```
你：/distill-events https://www.hematology.org.tw/...
AI：找到 37 筆活動，要建立 skill 嗎？
你：好
AI：skill 建好了，活動已同步 ✓
```

---

## 兩種使用方式（擇一）

抓取後，每個學會都會產生一份 `.ics`。你可以**訂閱檔案**，或讓 **Claude Code 直接寫入** Google Calendar。

### 方式 A — 訂閱 `.ics`（最簡單，任何行事曆 App 皆可）

`.ics` 檔發佈於 [`ics/`](ics/)，唯讀、零設定、自動更新：

| 學會 | 訂閱網址（Google Calendar → 其他日曆 → 透過網址加入） |
|------|------|
| 🦠 感染症 | `https://raw.githubusercontent.com/didiowen/society-calendar/main/ics/idsroc-events.ics` |
| 🩸 血液病 | `https://raw.githubusercontent.com/didiowen/society-calendar/main/ics/hematology-events.ics` |
| 🎗️ 愛滋病 | `https://raw.githubusercontent.com/didiowen/society-calendar/main/ics/aids-events.ics` |
| 🦴 骨髓移植 | `https://raw.githubusercontent.com/didiowen/society-calendar/main/ics/tbmt-events.ics` |

### 方式 B — 透過 Google Calendar MCP 直接寫入

搭配 Claude Code + Google Calendar MCP，將過濾後的活動以 `create_event` 直接寫入你指定的日曆（依「標題＋開始日期」去重，可重複執行而不重複建立）。可自訂日曆、可加學會標籤（`[感染症]`/`[血液病]`/`[愛滋]`/`[骨髓移植]`），但需授權連接器具備 **Google Calendar 寫入權限**。

> **差異**：訂閱 `.ics` 唯讀、自動更新、零設定；MCP 寫入可自訂、可分類，但需寫入授權。

---

## 目前支援的學會

| 學會 | Skill | 產出 | 特性 |
|------|-------|------|------|
| 🩸 [血液病學會](https://www.hematology.org.tw) | `/hematology-event` | `.ics`（過濾） | Bootstrap table，全年活動 |
| 🦠 [感染症醫學會](https://www.idsroc.org.tw) | `/idsroc-event` | `.ics`（過濾） | PDF 課程表，多分頁，可自訂過濾 |
| 🎗️ [愛滋病學會](https://www.aids-care.org.tw) | `/aids-event` | `.ics`（過濾） | 詳細頁需 session cookie，可自訂過濾 |
| 🦴 [骨髓移植學會 (TBMT)](https://www.tbmt.org.tw) | `/tbmt-event` | `.ics`（去重） | FullCalendar JSON API，certifi SSL，自動去重 |
| 🧬 [癌症醫學會](https://www.taiwanoncologysociety.org.tw) | `/oncology-event` | JSON | POST 分頁，民國年，SSL 壞掉 |
| 🏥 [內科醫學會](https://www.tsim.org.tw) | `/tsim-event` | JSON | 日期嵌在標題中，SSL 壞掉 |

---

## 快速開始

### 1. 抓取活動 → 產生 `.ics`

`hematology` / `idsroc` / `aids` / `tbmt` 皆採 **fetch → generate_ics** 兩階段：

```bash
# 血液病學會（過濾）
cd .claude/skills/hematology-event
python3 scripts/fetch_events.py
python3 scripts/generate_ics.py

# 感染症醫學會（過濾）
cd .claude/skills/idsroc-event
python3 scripts/fetch_idsroc_events.py
python3 scripts/generate_ics.py

# 愛滋病學會（過濾）
cd .claude/skills/aids-event
python3 scripts/fetch_aids_events.py
python3 scripts/generate_ics.py

# 骨髓移植學會（去重）
cd .claude/skills/tbmt-event
python3 scripts/fetch_tbmt_events.py
python3 scripts/generate_ics.py
```

> 過濾型（aids / idsroc / hematology）的地點／學分過濾規則可自訂，詳見下方〔[自訂過濾規則](#自訂過濾規則)〕。TBMT 不套用過濾，但會依「日期＋時段＋正規化標題」自動去除重複列出的同一活動。

### 2. 同步到 Google Calendar

- **訂閱**：見上方〔方式 A〕，貼上 `ics/` 的 raw 網址。
- **MCP 寫入**：在 Claude Code 中執行對應 skill（`/hematology-event` 等），或解析 `.ics` 後以 `create_event` 寫入。

### 3. 新增學會

給 Claude Code 任何學會網站的 URL：

```
/distill-events https://www.some-society.org.tw/events
```

Claude 會自動找到行事曆頁面、分析 HTML、建立 scraper、詢問是否打包成 skill。

---

## 自訂過濾規則

`aids` / `idsroc` / `hematology` 在產生 `.ics` 時會套用**地點＋學分**過濾，邏輯都在各自的 `scripts/generate_ics.py`，三者規則相同：

| 比對對象 | 條件 | 結果 |
|----------|------|------|
| `TAINAN_KW`（台南／臺南） | 命中 | 一律納入 |
| `KAOHSIUNG_KW`（高雄／義大／嘉義） | 命中且學分 > 2 | 納入 |
| 其他地區 | 學分 > 3 | 納入 |

比對的文字是活動的「地點＋主辦單位」（`location + organizer`），學分取自 `credits` 欄位。

**怎麼改**（編輯該 skill 的 `scripts/generate_ics.py`）：

1. **改地點名單** — 修改檔案上方的 `TAINAN_KW` / `KAOHSIUNG_KW` 兩個 list，加入想「一律納入」或「低門檻納入」的關鍵字（地名或主辦單位皆可）。
2. **改學分門檻** — 修改 `passes_filter()` 內的數字（預設 `> 2`、`> 3`）。
3. **全部納入（不過濾）** — 讓 `passes_filter()` 直接 `return True`。
4. 改完重跑 `python3 scripts/generate_ics.py` 即可，**不需重新抓資料**。

> TBMT 不套用地點／學分過濾（收錄所有近期活動），僅自動去除重複列出的同一場活動。

## Tech Stack

| 元件 | 技術 | 說明 |
|------|------|------|
| Scraper | Python 3 (stdlib) | `urllib` + `re`，零外部依賴 |
| SSL | `certifi`（若可用） | TBMT 需驗證憑證；Windows 上以 certifi 憑證庫建立 context |
| 日曆同步 | `.ics` 訂閱 / Google Calendar MCP | 二擇一 |
| Skill 系統 | Claude Code Skills | `.claude/skills/` 結構化技能 |
| 探索引擎 | `/distill-events` | 自動化新學會流程 |

### 為什麼用 stdlib？

- 醫院電腦通常不能 `pip install`
- 零依賴 = 任何有 Python 3 的環境都能跑
- `urllib` + `re` 處理這些簡單 HTML 綽綽有餘（`certifi` 為唯一選用相依，缺少時自動退回系統憑證庫）

---

## 專案結構

```
society-calendar/
├── ics/                         # 發佈的 .ics（可直接訂閱）
│   ├── idsroc-events.ics
│   ├── hematology-events.ics
│   ├── aids-events.ics
│   └── tbmt-events.ics
├── LICENSE                      # MIT
└── .claude/skills/
    ├── distill-events/          # 通用探索 skill（給新學會用）
    ├── hematology-event/        # 血液病學會（fetch + generate_ics，過濾）
    ├── idsroc-event/            # 感染症醫學會（fetch + generate_ics，過濾）
    ├── aids-event/              # 愛滋病學會（fetch + generate_ics，過濾）
    ├── tbmt-event/              # 骨髓移植學會（fetch + generate_ics，去重）
    ├── oncology-event/          # 癌症醫學會（fetch → JSON）
    └── tsim-event/              # 內科醫學會（fetch → JSON）
```

---

## 處理過的網站特性

這些 scraper 已經處理了台灣學會網站常見的坑：

| 問題 | 解法 |
|------|------|
| HTTP 406 (User-Agent blocked) | 加 `Mozilla/5.0` header |
| SSL 憑證壞掉 | `ssl.CERT_NONE`（AIDS）或 `certifi` 憑證庫（TBMT，Windows 相容、不停用驗證） |
| Windows `cp950` 主控台崩潰 | 強制 UTF-8 stdout（`sys.stdout.reconfigure`） |
| 同一活動重複列出（不同 detail ID） | `generate_ics.py` 依日期＋時段＋正規化標題去重 |
| 列表頁日期 `YYYY/MM/DD` vs `YYYY-MM-DD` | 比對前統一正規化（修正 AIDS 抓到 0 筆的 bug） |
| 民國年日期 `115/04/18` | `year + 1911` 轉換 |
| POST 分頁 | 帶完整 hidden fields |
| CAPTCHA 保護 | 改用其他頁面（如活動訊息） |
| Word HTML 嵌入 | strip `<style>` blocks |
| 日期嵌在標題中 | regex 從標題提取日期 |

---

## 更新紀錄

最新釋出：**[v1.0.0](https://github.com/didiowen/society-calendar/releases/tag/v1.0.0)** — Windows 修復（cp950 / SSL）、AIDS 日期過濾修正、TBMT 去重，並提供 `.ics` 訂閱與 Google Calendar MCP 兩種使用方式。

---

## License

[MIT](LICENSE)
