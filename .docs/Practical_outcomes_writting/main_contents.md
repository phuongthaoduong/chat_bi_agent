Here is your complete writing plan for the Feasibility Demonstration Report.

---

## Feasibility Demonstration Report — Writing Plan
**Project: ChatBI Data Analytics Agent | Platform: 智慧记 (Zhihuiji) by Kingdee**

---

### How to Read This Plan

Each section below tells you three things: **what to write**, **why it matters** to the reviewer, and **what evidence or content to pull from your existing work**.

---

### Section 1 — Engineering Background & Significance

**What to write:**
Describe the real-world problem landscape that makes this project necessary. Frame it at two levels — the macro industry level (rise of SaaS for micro-enterprises in China, data illiteracy among small merchants) and the micro product level (merchants in 智慧记 cannot act on their own business data without analyst help).

**Why it matters:**
This section answers *"why does this project deserve to exist?"* Reviewers need to see that you identified a genuine engineering gap, not just built a feature for its own sake.

**Content to draw from:**
Your four validated pain points (P1–P4), your market overview section, and the target customer analysis of 小微 wholesale/retail merchants.

---

### Section 2 — Review of Current Development Status & Trends (Domestic & International)

**What to write:**
A structured literature/market review in two halves:
- **International:** Text-to-SQL evolution, LLM-powered analytics agents (e.g., OpenAI, Tableau AI, Microsoft Copilot for BI)
- **Domestic (China):** Yonghe BI, Alibaba Quick BI, Hengshi Technology, NetEase Youdata — what they do and where they fall short for 小微 users

End with a synthesis: the gap that ChatBI fills (conversational + chart-enriched + session memory, all in one lightweight embedded agent).

**Why it matters:**
This proves you understand the field, not just your own product. It also justifies your technical choices by showing what alternatives exist and why they're insufficient.

**Content to draw from:**
Your competitive landscape section from the product report.

---

### Section 3 — Demand Analysis & Technical Specification Requirements

**What to write:**
Two subsections:
- **Demand analysis:** Who needs this, what they try to do, where they get blocked. Use your three personas (Owner/Store Manager, Warehouse/Procurement, Finance Clerk) with their trigger → decision-blocked → root-cause structure.
- **Technical specifications:** Concrete, measurable requirements — e.g., Query Success Rate ≥85% (your chosen PoC metric), response latency target, supported query types, chart output formats.

**Why it matters:**
This bridges the problem and the solution. Reviewers want to see that your design is driven by requirements, not guesswork. The measurable specs show engineering rigor.

**Content to draw from:**
Your PRD pain points and personas section, your PoC exit conditions, and your MVP roadmap metrics.

---

### Section 4 — Scheme Design

**What to write:**
The technical architecture and product design of ChatBI. Cover:
- Overall system design (how user query flows from input → NLP → SQL generation → chart rendering → response)
- Key technical components: DeepSeek LLM, Text-to-SQL layer, Chart.js/Recharts visualization, session memory module
- How it integrates into 智慧记's existing SaaS environment

Include a simple flow diagram if possible.

**Why it matters:**
This is the engineering core of the report. It shows *how* you solved the problem, not just *that* you solved it. Reviewers assess technical depth here.

**Content to draw from:**
Your Technical Architecture section from the product report.

---

### Section 5 — Expected Objectives & Forms of Achievements

**What to write:**
Be specific about what you will produce and how success is measured. Structure it as:

- **Objectives by stage:** PoC → V1 → Closed Beta (your 13-week roadmap), with hard exit conditions at each stage
- **Forms of achievement:** List the tangible deliverables — e.g., a working embedded agent prototype, a PRD document, a product report, query success rate benchmarks, user testing results
- **Final outcome statement:** What the completed project demonstrates as an engineering achievement

**Why it matters:**
"Forms of achievements" is a required field for degree-by-achievement applications. Reviewers need concrete, verifiable outputs — not vague goals.

**Content to draw from:**
Your three-stage roadmap (PoC → V1 → Closed Beta), your 13-week timeline, your PoC metric (Query Success Rate ≥85%).

---

### Section 6 — Conditions for Carrying Out Practical Work

**What to write:**
Demonstrate that you have everything needed to execute:
- **Technical resources:** Access to DeepSeek API, 智慧记 platform environment, development tools
- **Data resources:** Access to representative merchant transaction data for testing
- **Human resources:** Your role as PM intern, collaboration with engineering team at Kingdee
- **Institutional support:** Kingdee as the supporting enterprise providing guidance and infrastructure

**Why it matters:**
This section de-risks the project in the reviewer's eyes. It answers *"can this actually be done?"* by showing you're not starting from zero.

---

### Section 7 — Progress Schedule & Key Milestones

**What to write:**
A clear timeline mapped to your 13-week, 3-stage roadmap:

| Stage | Weeks | Key Milestone |
|---|---|---|
| PoC | 1–4 | Core query→SQL→chart pipeline working; QSR ≥85% |
| V1 | 5–9 | Session memory, persona-tuned responses, internal testing |
| Closed Beta | 10–13 | Real merchant testing, feedback loop, final benchmarks |

Add 2–3 key risk checkpoints and what triggers a stage gate review.

**Why it matters:**
Shows planning maturity. A milestone-based schedule signals that you think like an engineer and a PM — you know what done looks like at each step.

**Content to draw from:**
Your existing 3-stage roadmap with hard exit conditions.

---

### Section 8 — Review Opinions from Supporting Unit (Kingdee)

**What to write:**
This is typically a short formal statement (half to one page) from Kingdee that:
- Confirms the project is real and conducted within their platform
- Affirms the technical and business relevance of the work
- Endorses the applicant's contribution and role
- Is signed and stamped by an authorized representative

**What you need to do:**
Ask your internship supervisor or HR contact at Kingdee to provide this. You can draft a template for them to review and sign — I can help you write that template when you're ready.

---

### Suggested Writing Order

Because sections depend on each other, write in this sequence for efficiency:

1. Section 3 (Demand & Specs) — grounds everything in user evidence
2. Section 4 (Scheme Design) — your core technical answer
3. Section 1 (Background & Significance) — now you can frame the problem sharply
4. Section 2 (Literature Review) — position your work in context
5. Section 5 (Objectives & Achievements) — define what you're claiming
6. Section 6 (Conditions) — straightforward once the above is clear
7. Section 7 (Schedule) — pull from your roadmap
8. Section 8 (Supporting Unit) — coordinate with Kingdee separately