# [AI Reports] Personalized Interactive Data Analysis Reports Generated from Zhihuiji Data — Value Definition Document

---

## I. Core Pain Points of External Customers & Real User Personas

### 1.1 Core Pain Points

Data pulled from the operations backend shows **87 support tickets** related to reports from real user feedback, with **55 valid tickets from 2024 onward**, covering **five core pain points** — proving this is a genuinely existing and validated problem.

---

### Pain Point #1: The reports users want simply don't exist in the system

This is the most common category, with **17 tickets**. Customers repeatedly encounter the issue of "there's no dedicated report for this data" across different business scenarios.

Missing reports include: store summary reports, purchase order statistics, sales pre-order statistics, sales return standalone reports, assembly/disassembly reports, prepayment deposit statistics, inventory alert reports, full-document reconciliation reports, monthly sales/receivables/overdue statistics, annual profit reports, shipping cost statistics, invoicing record reports, lost customer reports, key account pricing reports — **14 report types in total**.

The common logic behind these requests: customers' businesses involve multiple document types and scenarios, but the system only provides a few core reports. **A large number of real but edge-case business questions have nowhere to be answered.** Every time a business decision needs to be made, another missing report is discovered.

---

### Pain Point #2: The report exists, but missing fields make exports useless

**9 tickets** in total, focused on the problem of missing fields in exported data.

Specific issues include:
- Sales statistics exports missing cost price and product category
- Sales/purchase/pre-order exports missing the creator field (only salesperson field exists, making it impossible to trace who created the order)
- Inventory reports missing spec attributes and custom product attributes (e.g. color codes)
- Sales statistics missing quantity columns and discount amount
- Accounts payable details mixing cash and goods in the same column with no separation

The fact that customers need to export data at all proves that the system's reporting function cannot meet their needs — they require secondary processing after export. **Due to insufficient system fields, even when a corresponding report exists, it still fails to meet customers' analysis needs.**

---

### Pain Point #3: The report exists, but can't be filtered by the desired dimension

**11 tickets** in total, reflecting limitations in query dimensions and operational experience.

Specific issues include:
- No sorting function in reports (e.g. can't view inventory or sales volume from high to low)
- Cannot filter by sales staff
- Sales statistics don't support unit switching (roll/piece), with different needs for domestic vs. overseas
- Inflexible time range settings (preset date spans too large, can't remember last query conditions, missing "current year" option, month switching requires full reset)
- Report content fully collapsed — must expand each item one by one to view

Customers want to analyze their business from multiple angles, but **reports only offer a single fixed perspective — any slight change in dimension makes the data inaccessible.**

---

### Pain Point #4: Data exists, but isn't visual — users want charts and graphs

**7 tickets** in total, spanning from 2017 all the way to early 2026 — proving this is a long-standing need that has never been addressed.

Specific feedback: requests to add bar charts, trend lines, comparison curves, chart analysis types, and graphical display modes.

The scenario behind this need is very concrete: a business owner wants to see at a glance whether sales revenue has been rising or falling over the past few months, or whether the share of each product category is shifting — but right now **everything is dense tables of numbers**, requiring manual row-by-row comparison just to sense any change, making it very hard to form quick judgments. For small business owners who aren't naturally comfortable reading numbers, charts aren't a nice-to-have — they are the threshold for whether users can truly "understand" their data at all.

---

### Pain Point #5: Data exists, but users can't tell where the problem is

**6 tickets** in total. This type of need is often expressed unclearly by customers — the ticket descriptions are vague — but they all point in the same direction.

Specific issues include:
- Two tickets directly requesting a "lost customer report" with pop-up alerts
- One ticket explicitly mentioning "reports lack slow-moving inventory and purchasing functions"
- One ticket requesting the ability to query customers who haven't made a purchase recently
- One ticket asking sales order reports to show the pre-order total per product to help decide how much to reorder
- One ticket requesting that negative inventory be highlighted in red (essentially: visualization of abnormal inventory states)

All of these point to the same gap: **the system only provides raw statistical numbers, without defining any business status.** Questions like "which products are slow-moving?", "which customers are churning quickly?", "is inventory abnormal?" — all of these judgments require building **[status indicator tags]** on top of **[raw data]**, but the current system has no such layer at all. Customers receive a pile of numbers, can't derive conclusions themselves, and end up submitting tickets asking for a "dedicated" report — when what they actually need is not more reports, but for the system to help them **translate numbers into business insights.**

---

## Summary & Strategic Conclusion

✏️ In summary, users' reporting needs are **highly personalized, long-tail, and fragmented**. Developing them one by one would not only be time-consuming and costly, but would also **never be able to fully cover users' individualized long-tail scenarios.**

Therefore, instead of patching gaps one by one, it makes more sense to **build an AI report tool** that lets users independently generate the reports they need by **customizing fields, dimensions, chart types, and business metrics** — fundamentally solving the personalized long-tail demand.

---

## 1.2 User Personas

### 1) Core User Persona — One-Line Summary

> **"Ages 35–55. Makes decisions solo. Manages inventory and cash. No time for — and can't read — reports. Just wants to hear the bottom line."**

| Trait | Description |
|---|---|
| 👤 Decision-maker | Calls all the shots themselves |
| 📦 Manages inventory | Responsible for stock |
| 💰 Manages cash flow | Controls finances |
| 📊 Low data literacy | Not comfortable with complex data |
| ⏰ Busy, time-scarce | Little bandwidth for analysis |

They can't read complex Excel reports, don't know terms like "MoM" or "YoY" — but they will ask: *"How did sales go this month?" "Which products sell best?" "Do we have enough stock?"*

---

### 2) Segmented Role Personas

#### 🧑‍💼 Zhang (Boss) — Hardware store owner, county town · Age 42
- *"Don't show me Excel. I just want to know if I made money today."*
- *"Which products sell best? Which customers still owe me money?"*
- **Pain tags:** ⏰ Time-poor · 💸 Fears losses · 📣 Chasing overdue payments

---

#### 🏭 Li (Warehouse Manager) — Warehouse manager + buyer · Age 35
- *"Which products are expiring soon?"*
- *"Which items haven't moved in a month? What's out of stock?"*
- **Pain tags:** ⚠️ Fears stockouts · 📉 Fears slow-movers · 📅 Fears expiry

---

#### 👩‍💼 Wang (Finance) — Wholesale company finance staff · Age 28
- *"What's this month's gross margin?"*
- *"Which customers have been overdue more than 30 days? How much do we need to pay next week?"*
- **Pain tags:** 📋 Reconciliation fatigue · 📊 Complex calculations · 🌙 Month-end overtime

---

**✏️ Summary:** The primary users are bosses, store owners, warehouse managers, buyers, finance staff, and clerks at small and micro enterprises. They **lack professional analytical skills**, but have a strong need for business data. They want to **quickly query core business metrics** — sales, inventory, purchasing, profit, and accounts — **using natural language**, and receive results in visual/chart form.