# ChatBI (智慧记) Competitive Analysis Report

> **Scope of Analysis:** Direct competitors — same target users (Chinese individual business owners / micro-merchants in China), same use case (querying business data via natural language within an inventory management app or similar mobile app)

---

## I. Criteria for Defining Direct Competitors

**Three conditions required to qualify as a direct competitor (all must be met):**

- **Same target users** — Individual business owners (个体工商户) / wholesale & retail micro-merchants
- **Same use case** — Embedded within an inventory management app, or a standalone app targeting the same user group
- **Substitutability** — A real possibility that users would choose one product over the other

---

## II. Competitor Overview

| Dimension | Haoshengyi (好生意) / Changjietong (畅捷通) / Yonyou (用友) | Qinsi Shengyi (秦丝生意通) | Guanjiapo (管家婆) |
|---|---|---|---|
| **Target Users** | Wholesale & retail micro-merchants, SMB | Apparel / footwear / electronics physical stores | Individual business owners + micro-enterprises |
| **Deployment** | Standalone app | Standalone app, mobile-first | Desktop-primary, weak mobile |
| **Market Scale** | Mid-size wholesale & retail user base | 750,000+ free users | Deep legacy user base |
| **Pricing** | ¥1,298/year/user; ¥2,999/5 years/unlimited users | Owner app + printer ¥1,899/year (cloud); then ¥300/year renewal | — |

---

## III. Core Feature Comparison

### 3.1 Feature 1: Natural Language Query (NLQ)

**Pain Point:** Users want to quickly retrieve business numbers, but don't know SQL, don't know what the data tables are called, and don't want to click through multiple menus.

| Dimension | Haoshengyi (好生意) | Qinsi Shengyi (秦丝生意通) | Guanjiapo (管家婆) |
|---|---|---|---|
| **NLQ Support** | Partial (filter-based) | ❌ Not supported | ❌ Not supported |
| **Query Method** | Report tab + filters | Extensive reports, but fixed templates | Fixed report templates |
| **Supported Query Style** | Requires dimension selection: open "Sales Report" → set date range → view | Fixed templates — users see only what's pre-built | Fixed templates, cumbersome on PC |
| **AI Depth** | AI assistant for operations, AI data query, AI data entry, AI feature discovery, AI business insights | AI photo-based order entry — input side only, not query side | AI customer service only |
| **Data Source Limitation** | Haoshengyi (好生意) platform data only | Qinsi (秦丝) data only | Guanjiapo (管家婆) data only |

**Featured Example — Haoshengyi (好生意):** After asking the AI a question, it can generate a chart or table.

---

### 3.2 Feature 2: Auto Chart Generation

**Pain Point:** After getting numbers, users want to "see the trend" — but don't know how to use any charting tools.

| Dimension | Haoshengyi (好生意) | Qinsi Shengyi (秦丝生意通) | Guanjiapo (管家婆) |
|---|---|---|---|
| **Support** | Fixed dashboard charts + auto chart generation after AI query | Basic sales / inventory charts | Text tables only — no visual charts |
| **Chart Generation Method** | Pre-set templates, fixed dimensions | Pre-set templates, fixed dimensions | Pre-set reports, fixed dimensions |
| **Mobile Experience** | Decent mobile experience | Mobile-first | Primarily PC |
| **User Effort** | Open "Xiaochang AI Assistant", ask revenue question | 2–3 steps: go to report → view | 4+ steps: deep menu hierarchy |

**Featured Example — Qinsi Shengyi (秦丝生意通)**

---

### 3.3 Feature 3: Session Memory

**Pain Point:** Users don't ask all their questions at once — they pick up their phone between sales, ask something, put it down, then come back with another question.

| Dimension | Haoshengyi (好生意) | Qinsi Shengyi (秦丝生意通) | Guanjiapo (管家婆) |
|---|---|---|---|
| **Support** | ❌ None | ❌ None | ❌ None |
| **Memory Type** | N/A | N/A | N/A |
| **User Behavior Pattern** | Fixed report mode, no need for follow-up queries | N/A | N/A |

---

## IV. Target User Comparison

| Dimension | Haoshengyi (好生意) | Qinsi Shengyi (秦丝生意通) | Guanjiapo (管家婆) |
|---|---|---|---|
| **Typical User** | Wholesalers, small chain store owners | Apparel / footwear / electronics shop owners | Traditional individual business owners across industries |
| **Tech Literacy** | Slightly higher, willing to learn the system | Low, primarily mobile users | Low, accustomed to desktop |
| **Business Size** | 5–50 people | 1–10 people | 1–20 people |
| **Device Preference** | Phone + PC | Phone-primary | PC-primary |
| **Usage Timing** | Opens app intentionally to review data | Checks anytime throughout the day | Reviews accounts at fixed times |
| **Core Need** | "I need to manage inventory and reconcile accounts" | "I need to manage products and members" | "I need to keep my accounts clear" |

---

## V. Indirect Competitor / Reference Competitor Analysis

### Three-Product Comparison

| Dimension | DataFocus | Jingdouyun (精斗云) / Kingdee (金蝶) | SwiftAgent / Shushi Tech (数势科技) |
|---|---|---|---|
| **Positioning** | Search-based BI — "Make data analysis as simple as search" | Cloud inventory + cloud accounting all-in-one, from ¥698/year | LLM + metric semantic layer + Agent architecture — enterprise-grade ChatBI |
| **Target Users** | Mid-size enterprise ops, marketing, sales, PMs — business-metric-savvy, non-SQL users | Micro-enterprises (5–50 people), with a dedicated finance person and basic digital literacy | Large enterprise data analysts, data teams, C-level executives |
| **Company Type** | Independent company | Under Kingdee Group (金蝶集团) | Shushi Tech (数势科技), independent company |
| **Deployment** | Standalone SaaS — requires separate registration, data source import, schema configuration | Standalone app — requires account setup, product catalog config; data not interoperable with Zhihuiji (智慧记) | Enterprise on-premise or cloud — requires IT implementation, rollout takes weeks |
| **NLQ Capability** | Strong — keyword + natural language search, bilingual (CN/EN), NL2DSL2SQL architecture | Navigation bot only — not a data query engine | Very strong — semantic layer guarantees ~99% accuracy, NL2DSL2SQL + multi-step Agent reasoning |
| **Query Style** | Analyst-style: "Show Q3 2024 user retention rate", "Rank ROI by channel" | Ask "What are today's sales?" → Gets: "You can go to 【Sales Report】→ select date → view" — no actual number returned; user still needs to complete the lookup manually | Analyst-style: "Q3 YTD revenue change in Yangtze Delta region", "Root cause of this month's profit decline" |
| **Chart Capability** | Rich — large-screen visualization, multiple chart types, custom dashboards, desktop-first | Fixed dashboard, drag-and-drop customization available, mobile accessible | Rich — supports attribution analysis, trend forecasting, multi-dimensional drill-down, desktop-first |
| **Session Memory** | None (search-based, each query is independent) | None (no conversational interface) | Supports multi-turn in-session follow-up queries |
| **Setup Cost** | Need to understand data table structure and know where to find data | Requires account setup, product catalog, and user permissions | Very high — data engineering + semantic layer modeling + permission system; requires dedicated IT |
| **Pricing** | SaaS subscription, per-user billing | Basic inventory from ¥1,298/year | Enterprise custom pricing, tens of thousands to hundreds of thousands of RMB/year |
| **Applicable Scale** | 50–500 people | 5–50 people | 500+ people |

**References:**
- DataFocus AI feature demo: https://www.zhihu.com/zvideo/1680956516390363136
- Jingdouyun (精斗云) AI Assistant

---

## Conclusion

The real gap in today's market is not whether a product exists — it is **whether a product can directly answer real business questions in natural language and return accurate data within seconds.**

Existing competitors either focus only on the input side (order entry, bookkeeping), don't support natural language queries at all, or act as "navigation AI" — they teach users where to click, but never return the answer directly. This means the core problem — **"the boss wants a number and gets it immediately"** — has never truly been solved. This is an experience gap that has been validated through real user behavior.

### Zhihuiji's (智慧记) Opportunity

| Advantage | Explanation |
|---|---|
| **Existing distribution** | Users are already active — no additional download or re-education needed; ChatBI just needs to be embedded at the right moment |
| **Strong data foundation** | Core data (orders, inventory, receivables/payables) is already stored in the system — no external data source integration needed |
| **Shortest path to value** | The chain from "asking a question" to "getting the answer" is the shortest possible, with the fastest response |
| **Query experience is still unoptimized** | Existing products are optimized for analyst-style questions — no one has solved the everyday conversational query style of small business owners. This is the key breakthrough opportunity |
| **Clear gap in the micro-merchant segment** | In the target market of micro-merchants, virtually no product can end-to-end solve this problem |