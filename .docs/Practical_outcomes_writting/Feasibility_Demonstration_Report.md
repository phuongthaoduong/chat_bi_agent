# Feasibility Demonstration Report

**Project:** ChatBI — AI-Powered Conversational Data Analytics Agent
**Platform:** Zhihuiji (智慧记) by Kingdee (金蝶)
**Author:** Duong Phuong Thao
**Date:** April 2026

---

## Abstract

Micro and small enterprises in China have rapidly adopted cloud-based Software-as-a-Service (SaaS) platforms for operational management, encompassing inventory tracking, sales invoicing, and accounts receivable management. Nevertheless, a persistent gap remains between data recording and data comprehension: although business owners routinely input transactional data into digital systems, they frequently lack the technical proficiency required to extract actionable insights from that data. This report presents ChatBI, an AI-powered conversational data analytics agent designed to be embedded within Zhihuiji, Kingdee's cloud-based business management platform serving China's micro-merchant segment. The proposed system enables non-technical users to query their business data using natural language and to receive responses in the form of automatically generated chart visualizations. Central to the system is a two-call large language model (LLM) architecture, termed the Classify–Compute–Narrate pattern, in which the LLM first generates a structured analysis plan from the user's question, a deterministic engine then executes the plan against the full dataset, and the LLM subsequently narrates the computed results. This architectural separation is designed to ensure that all numerical outputs are grounded in real computations rather than model-generated approximations. A proof-of-concept evaluation conducted on a standardized test set of 50 business questions yielded a Query Success Rate (QSR) of 88% (44/50), thereby meeting the pre-defined exit threshold of 85%. The present work contributes a replicable architectural pattern for hallucination-resistant data analytics agents, a validated product design for conversational analytics in the micro-enterprise segment, and empirical evidence suggesting that LLM-based natural language querying is feasible within the constraints of lightweight, embedded SaaS modules.

**Keywords:** conversational analytics, natural language querying, large language models, micro-enterprise SaaS, text-to-analysis, data visualization

---

## Table of Contents

1. [Engineering Background and Significance](#1-engineering-background-and-significance)
2. [Literature Review and Current Development Status](#2-literature-review-and-current-development-status)
3. [Demand Analysis and Technical Specification Requirements](#3-demand-analysis-and-technical-specification-requirements)
4. [System Design](#4-system-design)
5. [Expected Objectives and Forms of Achievements](#5-expected-objectives-and-forms-of-achievements)
6. [Evaluation Design and Results](#6-evaluation-design-and-results)
7. [Conditions for Carrying Out Practical Work](#7-conditions-for-carrying-out-practical-work)
8. [Progress Schedule and Key Milestones](#8-progress-schedule-and-key-milestones)
9. [Limitations and Future Work](#9-limitations-and-future-work)
10. [Review Opinions from Supporting Unit (Kingdee)](#10-review-opinions-from-supporting-unit-kingdee)
11. [References](#references)

---

## 1. Engineering Background and Significance

### 1.1 Industry Context

Over the past decade, China's SaaS market for micro and small enterprises has undergone significant expansion. Platforms such as Kingdee's Zhihuiji (智慧记), Yonyou's Haoshengyi (好生意), Qinsi Shengyitong (秦丝生意通), and Guanjiapo (管家婆) have digitized the core operational workflows of millions of individual business owners, spanning inventory tracking, purchasing, sales invoicing, and accounts receivable and payable management. According to the Ministry of Industry and Information Technology (MIIT, 2023), the digitization rate among China's small and micro enterprises has surpassed 50% in first-tier cities, with cloud-based SaaS platforms serving as the primary vehicle for this transformation. While these platforms have succeeded in structuring and storing transactional data, a critical asymmetry persists between data input and data utilization. Specifically, although the recording layer of business operations has been effectively digitized, the understanding layer, defined here as the capacity for non-technical users to interrogate their own data and derive actionable insights, remains largely absent.

The typical user of these platforms is a wholesale or retail merchant aged 35 to 55, managing a business of 1 to 20 employees. These individuals function as primary decision-makers responsible for inventory allocation and cash flow management; however, they generally possess neither formal data analysis training nor familiarity with analytical tools such as SQL, pivot tables, or statistical terminology. Despite this limitation, they encounter daily business questions that inherently require data-driven responses, including which products are generating the strongest sales, whether current stock levels are adequate, which customers carry outstanding balances, and how the current month's revenue compares to the preceding period.

This gap between data availability and data accessibility constitutes the central problem addressed by the present work.

### 1.2 Product Context: The Zhihuiji Reporting Gap

Zhihuiji is Kingdee's cloud-based inventory and business management platform targeting China's micro-merchant segment. The platform serves individual business owners across wholesale, retail, hardware, apparel, and other physical goods industries, enabling them to record daily transactions including sales orders, purchase orders, inventory movements, and customer balances.

To characterize the nature and prevalence of reporting-related user difficulties, an analysis of the Zhihuiji operations backend was conducted. This analysis identified 87 support tickets related to reporting functionality, of which 55 constituted valid tickets submitted from 2024 onward. Through thematic coding of these tickets (Braun & Clarke, 2006), five recurring pain point categories emerged, as summarized in Table 1.

_Table 1_

_Classification of Reporting-Related Pain Points from Zhihuiji Support Tickets (N = 55)_

| Pain Point Category | Ticket Count | Description |
|---|---|---|
| P1: Absent report types | 17 | Users require 14 distinct report types that the system does not currently provide |
| P2: Incomplete report fields | 9 | Existing reports lack critical data columns (e.g., cost price, product category, order creator), necessitating data export and manual processing |
| P3: Insufficient filtering dimensions | 11 | Reports offer fixed analytical perspectives; users cannot sort, switch measurement units, or filter flexibly by staff member, date range, or product category |
| P4: Absence of data visualization | 7 | Users receive dense numerical tables but require charts to perceive trends; this need has been documented in tickets dating back to 2017 |
| P5: Absence of business status indicators | 6 | Raw numerical values are presented without contextual interpretation (e.g., identification of slow-moving inventory, customer churn patterns, or abnormal stock levels) |

These five categories share a common structural root: users' reporting requirements are highly personalized, long-tail, and fragmented. The combinatorial space of fields, dimensions, filters, and visualization types is too expansive to address through pre-built report templates. Consequently, constructing individual reports in response to each request is neither scalable nor sustainable as a product strategy.

### 1.3 Engineering Significance and Innovation

In light of the challenges identified above, the present project proposes a fundamentally different approach to the long-tail reporting problem. Rather than constructing additional static reports, the proposed system provides an AI-powered conversational analytics agent (ChatBI) that enables users to generate the analyses they require on demand, through natural language input, with automatic chart visualization.

The engineering significance and contributions of this work are threefold.

First, at the architectural level, the present work introduces the Classify–Compute–Narrate pattern, a two-call LLM architecture in which the language model functions as a planner and narrator but never as a calculator. In this pattern, the LLM generates a structured analysis plan (classification), a deterministic engine executes the plan against the full dataset (computation), and the LLM then narrates the computed results (narration). This architectural separation is intended to ensure that every numerical value in the system's response is grounded in real computation, thereby mitigating the hallucination problem that arises when LLMs are asked to produce data-derived answers directly (Ji et al., 2023). This pattern is distinct both from code-generation approaches such as OpenAI's Code Interpreter (OpenAI, 2023) and from direct-answer approaches employed by general-purpose chatbots.

Second, at the design level, the present work introduces structured analysis plans as an intermediate representation between natural language input and data operations. Rather than generating executable code, the LLM produces a JSON-formatted plan drawn from a finite vocabulary of analytical operations. The execution engine validates and executes these plans deterministically. This design deliberately trades expressiveness for safety, predictability, and debuggability, a tradeoff that is justified by the security requirements and operational constraints of the target deployment environment, as discussed further in Section 4.2.3.

Third, at the domain level, the present work provides empirical evidence suggesting that conversational data analytics is technically viable for the micro-enterprise SaaS segment, where users characteristically lack technical literacy and budgets for enterprise-grade business intelligence tools. The embedding strategy, which places the analytics capability within the platform where the user's data already resides, eliminates the setup barriers (separate registration, data import, schema configuration) that render products such as DataFocus or Alibaba Quick BI (阿里云 Quick BI) inaccessible to this user segment. To the author's knowledge, no existing product combines natural language querying, automatic chart visualization, and session memory for the micro-merchant segment in China.

---

## 2. Literature Review and Current Development Status

This section situates the present work within the relevant academic literature and the current commercial landscape, identifying the theoretical foundations, technological precedents, and market gap that motivate the proposed system.

### 2.1 Text-to-SQL and Natural Language Querying

The core technical challenge underlying conversational data analytics, that of converting natural language questions into structured data queries, has been an active area of research for over two decades. Early systems relied on rule-based parsing and keyword matching, approaches that proved brittle when confronted with linguistic variability (Androutsopoulos et al., 1995). The emergence of neural sequence-to-sequence models marked a significant advancement; Zhong et al. (2017) introduced Seq2SQL, which employed reinforcement learning to generate SQL queries from natural language on the WikiSQL benchmark.

The subsequent introduction of the Spider benchmark (Yu et al., 2018) substantially raised the complexity threshold by requiring cross-database generalization over multi-table schemas. Subsequent research has progressively improved accuracy on Spider through increasingly sophisticated architectures. The advent of large language models further transformed the field: Pourreza and Rafiei (2023) demonstrated with DIN-SQL that decomposing the text-to-SQL task into sub-problems and leveraging in-context learning with GPT-4 could achieve state-of-the-art results, while Gao et al. (2023) showed with DAIL-SQL that carefully selected few-shot examples significantly improve LLM-based SQL generation.

However, a persistent gap remains between benchmark performance and real-world deployment. Academic benchmarks typically employ clean, well-documented schemas, whereas production business databases feature inconsistent naming conventions, ambiguous column semantics, and domain-specific terminology. The present work addresses this gap not through text-to-SQL per se, but through what may be termed text-to-analysis-plan, a higher-level abstraction that constrains the output space to a validated set of analytical operations, thereby reducing the failure modes associated with free-form SQL generation.

### 2.2 LLM-Based Agents and Tool Use

The capacity of large language models to function as autonomous agents that plan and execute multi-step tasks has been explored extensively in recent literature. Yao et al. (2023) proposed the ReAct framework, which interleaves reasoning and action steps, enabling LLMs to interact with external tools and environments. Schick et al. (2023) introduced Toolformer, demonstrating that language models can learn to invoke external APIs autonomously. Wei et al. (2022) established that chain-of-thought prompting substantially improves LLM performance on complex reasoning tasks by eliciting intermediate reasoning steps.

These developments bear direct relevance to the architecture proposed in the present work. The Classify–Compute–Narrate pattern may be understood as a constrained instance of the ReAct paradigm: the LLM reasons about the user's question (classification), generates an action specification (the analysis plan), and the system executes that action deterministically before the LLM produces a final response (narration). The critical distinction lies in the fact that ChatBI's action space is deliberately constrained to a finite set of validated operations, rather than permitting arbitrary tool invocation or code execution.

With regard to the safety implications of LLM-generated code, Chen et al. (2021) demonstrated with Codex that while language models can generate functional code, they may also produce insecure or incorrect outputs. This finding provides further motivation for ChatBI's design decision to avoid code generation entirely in favor of structured plans, a choice that prioritizes correctness and security over the flexibility of arbitrary code execution.

### 2.3 International Commercial Developments

In the commercial domain, major technology companies have integrated LLM capabilities into their analytics products, thereby demonstrating the viability of conversational analytics at scale. Microsoft Copilot for Power BI enables natural language queries over enterprise datasets, generating charts and summaries within the Power BI ecosystem (Microsoft, 2023). Tableau AI, developed by Salesforce, embeds generative AI to assist with data exploration, visualization recommendations, and natural language question answering (Salesforce, 2024). Code Interpreter, developed by OpenAI and subsequently renamed Advanced Data Analysis, demonstrates that LLMs can perform end-to-end data analysis when provided with access to code execution environments (OpenAI, 2023).

These products validate the commercial viability of conversational analytics. However, they share a common structural limitation: they are designed for enterprise users who possess existing data infrastructure, technical literacy, and enterprise subscription budgets. None of these products targets the micro-merchant segment, and none is embedded within an inventory management platform where the user's transactional data already resides.

### 2.4 Domestic Market Analysis

Within the Chinese market, several products occupy distinct segments of the business intelligence and analytics landscape. This subsection examines both enterprise-grade platforms and direct competitors in the micro-merchant segment.

Among enterprise-grade BI platforms, FineBI by Fanruan (帆软) is the leading domestic offering for mid-to-large enterprises, providing drag-and-drop dashboard creation with extensive visualization capabilities; however, it requires dedicated data analysts to configure and maintain (Fanruan, 2024). Alibaba Quick BI provides cloud-based BI services integrated with Alibaba Cloud, supporting natural language queries to a limited degree, though it targets enterprise customers with structured data warehouses (Alibaba Cloud, 2024). Hengshi Technology (衡石科技) offers an embedded analytics platform for SaaS vendors, providing white-label BI components that are architecturally relevant but not designed as user-facing tools for micro-merchants. NetEase Youdata (网易有数) provides data visualization and dashboard capabilities oriented toward enterprise deployments with substantial setup requirements.

Among direct competitors in the micro-merchant segment, a feature comparison is presented in Table 2.

_Table 2_

_Feature Comparison of Direct Competitors in the Micro-Merchant Segment_

| Product | Natural Language Querying | Automatic Charts | Session Memory | Principal Limitation |
|---|---|---|---|---|
| Haoshengyi (好生意) by Yonyou | Partial: AI assistant can generate charts from questions | Fixed dashboard supplemented with AI-generated charts | Not supported | AI assistant lacks multi-turn conversation capability; queries reset with each session |
| Qinsi Shengyitong (秦丝生意通) | Not supported | Basic pre-configured charts only | Not supported | AI capabilities restricted to photo-based order entry; no data querying functionality |
| Guanjiapo (管家婆) | Not supported | Not supported; text tables only | Not supported | Desktop-primary deployment with minimal mobile experience and no visualization layer |

Several technically advanced reference products also warrant consideration. DataFocus provides search-based BI with robust natural language querying capabilities, but requires separate registration, data import, and schema configuration, representing a level of setup complexity that is prohibitive for micro-merchants. Jingdouyun (精斗云), a Kingdee Group product, employs a navigation-oriented AI assistant that directs users to existing report screens but does not itself return computed data answers. SwiftAgent, developed by Shushi Technology (数势科技), represents the most technically advanced domestic offering, employing a semantic layer combined with an agent architecture to achieve approximately 99% accuracy; however, it is an enterprise-grade product requiring IT implementation at a cost of tens of thousands of RMB annually (Shushi Technology, 2024).

### 2.5 Synthesis: The Positioning of ChatBI

The foregoing analysis reveals a clear gap in the current market that ChatBI is positioned to address. No existing product in the micro-merchant segment delivers true natural language data querying combined with automatic visualization and session memory. Enterprise-grade solutions remain inaccessible to the target users owing to technical setup requirements and cost. Navigation-based AI approaches, as exemplified by Jingdouyun, fail to resolve the fundamental problem; they direct users to existing reports rather than providing the answer itself.

ChatBI is situated at the intersection of three capabilities that no existing product combines for the micro-merchant segment: (a) conversational natural language querying, (b) automatic chart visualization, and (c) session memory supporting multi-turn follow-up questions. Moreover, the proposed system is designed to be embedded within Zhihuiji, where the user's business data already resides, thereby eliminating setup barriers entirely. This positioning is illustrated through the competitive analysis and further validated by the empirical evaluation presented in Section 6.

---

## 3. Demand Analysis and Technical Specification Requirements

Building upon the industry context and literature review presented in the preceding sections, this section characterizes the target users, analyzes their information needs, and defines the technical specifications that the proposed system must satisfy.

### 3.1 Demand Analysis

#### 3.1.1 User Segmentation

The primary users of ChatBI are owners, managers, and operational staff at micro and small enterprises who employ Zhihuiji for daily business operations. Based on analysis of the 55 valid support tickets identified in Section 1.2 and consultation with the Zhihuiji product team, three distinct user segments were identified, each representing different analytical needs and usage contexts.

The first segment (Segment A) comprises business owners who serve as primary decision-makers, typically aged 35 to 55, with full authority over their enterprises. Their analytical needs center on revenue performance, product profitability, and accounts receivable status. Characteristic queries from this segment include sales performance summaries, identification of top-performing products, and outstanding customer balances. These users are notably time-constrained, typically accessing the platform in brief intervals between customer interactions, and they require immediate, comprehensible answers without the need for technical navigation.

The second segment (Segment B) includes operations and warehouse managers responsible for inventory oversight. Their analytical needs focus on stock status monitoring, encompassing the identification of slow-moving inventory, low-stock items, and products approaching expiration. Users in this segment typically access the platform during operational activities such as goods receiving or inventory counts, and they require rapid status assessments for specific product categories or stock conditions.

The third segment (Segment C) encompasses finance and administrative staff responsible for financial reporting and reconciliation. Their analytical needs involve gross margin calculations, overdue payment identification, and payment scheduling. These users experience peak demand at month-end or week-end reporting periods and require the ability to aggregate data across multiple dimensions simultaneously.

#### 3.1.2 User Journey Analysis

Across all three segments, the current user journey follows a consistent pattern when a business question arises. The user opens Zhihuiji, attempts to locate the answer within existing reports, and encounters one or more of the five pain points identified in Section 1.2 (absent report types, incomplete fields, insufficient dimensions, absent visualization, or absent status indicators). At this point, the user either abandons the inquiry, exports data for manual processing in external tools, or submits a support ticket. In each scenario, the business decision is either delayed or made without adequate data support.

The proposed system intervenes at this point of blockage by providing an alternative path. The user opens the ChatBI module within Zhihuiji, inputs a question in natural language, and receives an immediate response accompanied by chart visualization. Should further exploration be required, the user may pose follow-up questions within the same session, drawing upon the retained conversational context.

#### 3.1.3 Functional Requirements Summary

The demand analysis yields three primary functional requirements, as summarized in Table 3.

_Table 3_

_Functional Requirements Derived from Demand Analysis_

| Requirement | Description | Pain Points Addressed |
|---|---|---|
| Natural Language Querying | Users input questions in plain language; the system interprets intent and returns computed data | P1 (absent reports), P3 (insufficient dimensions) |
| Automatic Visualization | The system generates appropriate chart types (bar, line, pie, scatter) for query results | P4 (absent visualization), P5 (absent status indicators) |
| Session Memory | The system maintains conversational context, enabling multi-turn follow-up questions within a session | All five pain points, by enabling iterative data exploration without re-specification of context |

### 3.2 Technical Specification Requirements

On the basis of the demand analysis and the constraints of the target deployment environment, the following technical specifications define the scope and quality requirements for the proposed system.

#### 3.2.1 Functional Specifications

| Spec ID | Requirement | Target |
|---|---|---|
| F-01 | Accept natural language questions in Chinese and English | Bilingual support |
| F-02 | Classify questions as computational (requiring data query) or conversational (interpretive) | Automatic classification by LLM |
| F-03 | Generate structured analysis plans from computational questions | JSON-formatted plans; no raw code generation |
| F-04 | Execute analysis plans against uploaded datasets | Full dataset computation without sampling |
| F-05 | Produce chart visualizations for data-driven responses | Support for bar, line, pie, and scatter chart types |
| F-06 | Maintain session context for multi-turn conversation | Chat history preserved within session |
| F-07 | Support file upload in .xlsx, .xls, and .csv formats | Three format parsers with automatic encoding detection |
| F-08 | Auto-generate an initial dashboard overview upon file upload | One chart with key insights generated automatically |
| F-09 | Support cross-sheet queries for multi-file uploads | Join specification parsed from LLM response |

#### 3.2.2 Performance Specifications

| Spec ID | Requirement | Target |
|---|---|---|
| P-01 | Query Success Rate (QSR) | ≥ 85% at PoC exit |
| P-02 | Response latency for computational queries | < 15 seconds (inclusive of LLM API calls) |
| P-03 | Response latency for conversational queries | < 8 seconds |
| P-04 | File upload and parsing latency | < 5 seconds for files up to 5 MB |
| P-05 | Concurrent session capacity | 50 sessions (MVP constraint) |
| P-06 | Session inactivity timeout | 30 minutes |
| P-07 | Maximum file size per upload | 5 MB |

#### 3.2.3 Quality Specifications

| Spec ID | Requirement | Target |
|---|---|---|
| Q-01 | Answer accuracy | All numerical values in computational responses must be grounded in real computed data; no LLM-generated approximations permitted |
| Q-02 | Error transparency | All errors (file parsing, LLM failure, invalid queries) must produce user-comprehensible messages |
| Q-03 | Data completeness | All analysis operations must execute on the full dataset; display caps apply only to API response serialization |

---

## 4. System Design

This section describes the technical architecture and principal components of the proposed system. Design decisions are discussed in relation to the requirements established in Section 3 and the theoretical foundations reviewed in Section 2.

### 4.1 Overall Architecture

ChatBI adopts a monolith-first architecture consisting of three layers: a React/Vite single-page application (SPA) as the client layer, a Python FastAPI server as the backend layer, and the DeepSeek LLM API as the intelligence layer. The high-level system architecture is illustrated in Figure 1.

_Figure 1_

_High-Level System Architecture of ChatBI_

```
┌─────────────────────────────────┐
│      Client Layer (React/Vite)  │
│                                 │
│  ┌───────────┐  ┌────────────┐  │
│  │ Upload UI │  │ Chat View  │  │
│  └─────┬─────┘  └─────┬──────┘  │
│        │               │        │
│  ┌─────▼───────────────▼─────┐  │
│  │  Dashboard / Charts       │  │
│  │  (ECharts)                │  │
│  └───────────┬───────────────┘  │
└──────────────┼──────────────────┘
               │ HTTP (REST API)
┌──────────────▼──────────────────┐
│     Server Layer (FastAPI)      │
│                                 │
│  ┌──────────┐  ┌─────────────┐  │
│  │  File    │  │   Chat /    │  │
│  │  Parser  │  │   Query     │  │
│  │  Module  │  │   Engine    │  │
│  └────┬─────┘  └──────┬──────┘  │
│       │               │        │
│  ┌────▼────┐  ┌───────▼──────┐  │
│  │Profiler │  │  Analysis    │  │
│  │         │  │  Engine      │  │
│  └─────────┘  └───────┬──────┘  │
│                       │        │
│  ┌────────────────────▼──────┐  │
│  │  Intelligence Layer       │  │
│  │  (DeepSeek LLM Client)   │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

The selection of a monolithic architecture was motivated by the MVP constraints of the current phase, which involve small file sizes, the absence of authentication requirements, and ephemeral sessions. Under these conditions, a monolithic design represents the most straightforward architecture to implement, deploy, and debug. FastAPI's built-in asynchronous support provides efficient handling of concurrent LLM API calls. Importantly, the architecture incorporates extensibility through abstraction; for example, the `SessionStore` base class can be substituted from an in-memory implementation to a Redis-backed store without necessitating modifications to dependent components, consistent with the Dependency Inversion Principle (Martin, 2003).

### 4.2 Core Technical Components

#### 4.2.1 File Parser Module

The parser module is responsible for the ingestion of user-uploaded data files and comprises two functional layers.

The parsing layer reads raw file bytes into structured DataFrames. Three format-specific parsers have been implemented: `XlsxParser` (utilizing openpyxl for modern Excel files), `XlsParser` (utilizing xlrd for legacy Excel formats), and `CsvParser` (utilizing pandas with chardet for automatic character encoding detection). File format is determined by extension and dispatched through a parser registry, following the Strategy design pattern (Gamma et al., 1994).

The profiling layer generates a `SheetProfile` for each sheet in the uploaded file. Each profile contains row count, column count, and column-level metadata including data type, null count, unique value count, sample values, and summary statistics. The profile serves as the primary context provided to the LLM; notably, the model never receives the full dataset, only the structured profile. This design decision serves to limit token consumption while providing sufficient schema and distributional information for accurate analysis plan generation, a consideration that aligns with established practices for grounding LLM outputs in structured context (Wei et al., 2022).

A data completeness guarantee is maintained throughout: all rows are parsed and profiled without truncation. The complete DataFrame is stored in the session and used for all analysis computations. A display cap of 10,000 rows is applied exclusively during API response serialization and does not affect computation.

#### 4.2.2 LLM Integration: The Classify–Compute–Narrate Pattern

The proposed system employs a two-call LLM pattern for computational questions that constitutes the central mechanism for ensuring answer accuracy. The control flow of this pattern is illustrated in Figure 2.

_Figure 2_

_Control Flow of the Classify–Compute–Narrate Pattern_

```
User Question
  │
  ▼
LLM Call 1: Classification and Plan Generation
  │
  ├── COMPUTATIONAL ──► Analysis Engine executes plan on full dataset
  │                       │
  │                       ▼
  │                   Concrete AnalysisResult (computed numbers)
  │                       │
  │                       ▼
  │                   LLM Call 2: Narrate computed results
  │                       │
  │                       ▼
  │                   Response: narrative text + chart data
  │
  └── CONVERSATIONAL ──► LLM generates interpretive response
                          based on profiles and chat history
                          │
                          ▼
                      Response: narrative text only
```

The rationale for employing two LLM calls on the computational path is as follows. Were the LLM to generate the answer prior to computation, it could only approximate on the basis of schema metadata and sample values, thereby producing hallucinated numerical outputs (Ji et al., 2023). By interposing deterministic computation between classification and narration, every number in the response is grounded in actual data. The additional API call cost is considered negligible relative to the potential consequences of incorrect answers for business users making financial decisions.

For the conversational path, a single LLM call is deemed sufficient. Conversational questions, such as requests for interpretation, explanation, or business context, do not require specific numerical outputs derived from computation. In these cases, the LLM draws upon sheet profiles, summary statistics, and prior computed results present in the chat history, which provide adequate grounding for interpretive responses.

This two-call architecture may be understood as a constrained application of the ReAct framework (Yao et al., 2023), as discussed in Section 2.2, wherein the reasoning step (classification) is separated from the action step (plan execution) and followed by a synthesis step (narration). The principal distinction is that the action space in the present system is deliberately limited to a finite, validated set of operations.

#### 4.2.3 Analysis Engine: Structured Plans as Intermediate Representation

A critical architectural decision underlying the proposed system is that the LLM is never permitted to generate executable code. Instead, it produces a structured JSON analysis plan specifying what to compute, and the Analysis Engine interprets and executes the plan using a validated set of operations. This decision is motivated by the security concerns associated with LLM-generated code identified by Chen et al. (2021), as discussed in Section 2.2.

The `AnalysisPlan` schema comprises five components: (a) source specification, identifying the target file and sheet; (b) analysis intent, drawn from one of six types (`aggregate`, `distribution`, `trend`, `comparison`, `top_n`, or `correlation`); (c) target fields, specifying the columns to be analyzed; (d) query operators, including group-by clauses, filters, sort order, and result limits; and (e) chart specification, defining the chart type, title, and axis mappings.

Prior to execution, the engine performs comprehensive validation encompassing source validation (verifying file and sheet existence), column validation (confirming that all referenced columns exist in the dataset), and operator/type validation (ensuring that operators are compatible with the data types of the target columns). Plans that fail validation result in descriptive error messages returned prior to any computation.

This approach is designed to provide three guarantees. First, with respect to security, no arbitrary code can be executed on the server, thereby eliminating injection attack vectors. Second, with respect to predictability, the finite operation space ensures well-defined behavior for each operation type. Third, with respect to debuggability, plans are human-readable JSON artifacts that can be logged, inspected, and reproduced independently of the LLM.

#### 4.2.4 Chart Visualization

The client layer employs Apache ECharts (via the `echarts-for-react` wrapper library) for chart rendering. ECharts was selected on the basis of several criteria: its comprehensive chart type library, its capacity to render large datasets, its interactive features (including tooltips, zoom, and responsive layout), its thorough documentation, and its widespread adoption within the Chinese market (Apache ECharts, 2024). The MVP supports four chart types: bar, line, pie, and scatter. Chart type selection is performed by the LLM as part of the analysis plan generation, informed by the analytical intent and data characteristics of the query.

#### 4.2.5 Session Memory Module

Session state is managed in-memory using a dictionary that maps session identifiers to `SessionData` objects. Each session encapsulates parsed files (DataFrames), sheet profiles, the complete chat history (comprising all prior questions, responses, and computed results), timestamps, and memory footprint metrics.

With respect to session lifecycle management, sessions expire following 30 minutes of inactivity, and a background cleanup task executes at 5-minute intervals to evict expired sessions. A maximum capacity of 50 concurrent sessions is enforced; requests exceeding this capacity receive an HTTP 503 response. Each session access operation updates the `last_accessed_at` timestamp, thereby refreshing the time-to-live window.

The `SessionStore` is implemented as an abstract base class, enabling the in-memory implementation to be replaced with a persistent store (e.g., Redis) for production deployment without necessitating modifications to any dependent components.

### 4.3 API Design

Three REST endpoints serve the MVP, as specified in Table 4.

_Table 4_

_REST API Endpoint Specification_

| Endpoint | Method | Function |
|---|---|---|
| `/api/upload` | POST | Upload files (multipart); returns session identifier, file metadata, and auto-generated dashboard chart with initial insights |
| `/api/chat` | POST | Submit a question with session identifier; returns response text and optional chart specification |
| `/api/session/{id}` | GET | Retrieve current session state for page refresh recovery |

All error responses conform to a consistent envelope structure (`{ error: { code, message } }`) with messages designed to be comprehensible to non-technical users. The error handling matrix addresses 10 categories, including invalid file format, exceeded file size, empty file, parse errors, session not found, LLM service unavailability, invalid analysis plans, and server capacity limits.

### 4.4 Client Architecture

The frontend is implemented as a React/Vite single-page application organized around three application states: (a) the upload state, presenting a file dropzone interface for data file upload; (b) the session state, displaying file metadata, an auto-generated dashboard chart, and a chat input field following successful upload; and (c) the chat state, providing an active conversational interface with message history, chart results, and an input field.

State management utilizes React's built-in `useState` hook; no external state management library is required given the limited scope of the MVP. The component directory structure is organized into three modules: `upload/` for landing screen components, `session/` for post-upload views, and `shared/` for reusable components including Chart, ChatMessage, and ChatInput.

### 4.5 Integration Strategy with Zhihuiji

ChatBI is designed as an embeddable module within the Zhihuiji platform. During the current MVP phase, it operates as a standalone web application that accepts file uploads. In subsequent development phases, the system would integrate directly with Zhihuiji's data layer, thereby eliminating the file upload requirement; the user's sales, inventory, purchasing, and accounts data would become accessible to ChatBI automatically.

This progressive integration strategy permits the proof of concept to validate the core AI analytics capability independently of modifications to Zhihuiji's production infrastructure, while preserving a clear path toward full platform integration.

---

## 5. Expected Objectives and Forms of Achievements

### 5.1 Objectives by Stage

The project follows a three-stage development roadmap, with defined exit conditions at each stage gate.

**Stage 1: Proof of Concept (PoC), Weeks 1–4.** The objective of this stage is to validate that the core pipeline, from natural language question through structured analysis plan to data computation and chart visualization, functions reliably. Exit conditions include: (a) QSR ≥ 85% on a standardized test set of business questions; (b) core pipeline functionality demonstrated end-to-end; and (c) the Classify–Compute–Narrate pattern producing grounded, non-hallucinated numerical outputs.

**Stage 2: V1 Internal Release, Weeks 5–9.** The objective of this stage is to refine the system for internal testing, incorporating session memory, robust error handling, and cross-sheet query capability. Exit conditions include: (a) session memory supporting multi-turn conversation with context retention; (b) error handling covering all defined error categories; (c) internal team testing with representative merchant datasets completed; and (d) cross-sheet join queries functional for multi-file uploads.

**Stage 3: Closed Beta, Weeks 10–13.** The objective of this stage is to conduct user testing with real merchant users, collect feedback, and produce final benchmarks. Exit conditions include: (a) real merchant users having tested the system and provided feedback; (b) QSR validated on real-world merchant questions; (c) performance benchmarks meeting the specification requirements defined in Section 3.2; and (d) the final feasibility demonstration report completed.

### 5.2 Forms of Achievements

The project is expected to produce the following tangible, verifiable deliverables, as summarized in Table 5.

_Table 5_

_Project Deliverables and Verification Methods_

| # | Deliverable | Format | Verification Method |
|---|---|---|---|
| 1 | Working ChatBI prototype | Deployed web application | Live demonstration: upload, dashboard generation, multi-turn chat with charts |
| 2 | Product Requirements Document (PRD) | Written document | Validated pain points (87 support tickets), user segments, feature specifications |
| 3 | Technical Architecture Specification | Written document | Complete system design with API specifications, data flow diagrams, component architecture |
| 4 | Competitive Analysis Report | Written document | Structured comparison of 6 competitors across 3 feature dimensions |
| 5 | Query Success Rate benchmarks | Test results | QSR measured on standardized business question test set |
| 6 | User testing results | Feedback records | Qualitative and quantitative feedback from merchant users during closed beta |
| 7 | Feasibility Demonstration Report | Written document (this report) | Comprehensive engineering analysis of problem, solution, and results |
| 8 | Source code repository | Git repository | Complete codebase with version history demonstrating iterative development |

### 5.3 Outcome Statement

The completed project is intended to demonstrate that an AI-powered conversational data analytics agent, built upon large language model technology and embedded within an existing micro-enterprise SaaS platform, can reliably interpret natural language business questions, execute data computations with verified accuracy, and present results in visual chart format. In doing so, it addresses the long-tail reporting problem that has persisted in the micro-merchant segment for nearly a decade, as evidenced by the support ticket analysis presented in Section 1.2.

The engineering contribution resides not only in the construction of a functional prototype, but in the design of a system architecture that seeks to ensure answer correctness by construction, through the Classify–Compute–Narrate pattern that separates the LLM's planning role from deterministic computation, rather than relying on the language model to produce accurate numerical outputs directly.

---

## 6. Evaluation Design and Results

This section describes the evaluation methodology employed to assess the proposed system's query handling capability and presents the results obtained during the proof-of-concept phase.

### 6.1 Test Set Construction

A standardized test set of 50 business questions was constructed for evaluation purposes. Questions were derived from two sources: (a) the 55 valid support tickets from the Zhihuiji operations backend, which provided authentic examples of user information needs (see Section 1.2), and (b) synthetic questions designed to cover analytical scenarios not represented in the ticket data but consistent with the user segments and pain points identified in Section 3.1.

The test set was stratified across six analytical categories to ensure comprehensive coverage of the system's intended functionality, as detailed in Table 6.

_Table 6_

_Test Set Composition by Analytical Category_

| Category | Question Count | Example Question |
|---|---|---|
| Sales analytics | 12 | "What are the top 10 best-selling products this month?" |
| Inventory management | 10 | "Which products have had no sales in the past 30 days?" |
| Purchasing analysis | 8 | "What is the total purchasing cost by supplier this quarter?" |
| Accounts receivable | 8 | "Which customers have balances overdue by more than 30 days?" |
| Trend and time-series | 7 | "How has daily sales revenue changed over the past two weeks?" |
| Cross-sheet queries | 5 | "What is the profit margin for each product category, combining sales and cost data?" |

Each question was designed to exercise at least one of the six supported analysis intents (aggregate, distribution, trend, comparison, top_n, correlation) and to test the system's capacity for column identification, filter construction, and chart type selection.

### 6.2 Evaluation Criteria

Each question was assessed against a three-level rubric, defined as follows:

A response was classified as _correct_ if the system returned numerically accurate results, selected an appropriate chart type, and provided a comprehensible narrative interpretation, with all values verifiable against manual computation on the source dataset. A response was classified as _partially correct_ if the system returned a response containing a non-critical deficiency, such as correct numerical values accompanied by a suboptimal chart type, or correct aggregation accompanied by an imprecise narrative description. A response was classified as _failed_ if the system returned incorrect numerical values, produced a system error, generated an irrelevant response, or failed to produce any output.

For the purpose of QSR calculation, both "correct" and "partially correct" outcomes were counted as successes, consistent with the specification that QSR measures the rate at which the system produces usable responses (see Section 3.2.2, Spec P-01).

### 6.3 Results

The proof-of-concept evaluation yielded the results presented in Table 7.

_Table 7_

_Evaluation Results by Analytical Category_

| Category | Total | Correct | Partially Correct | Failed | Success Rate |
|---|---|---|---|---|---|
| Sales analytics | 12 | 11 | 0 | 1 | 91.7% |
| Inventory management | 10 | 9 | 0 | 1 | 90.0% |
| Purchasing analysis | 8 | 7 | 1 | 0 | 100.0% |
| Accounts receivable | 8 | 7 | 0 | 1 | 87.5% |
| Trend and time-series | 7 | 5 | 1 | 1 | 85.7% |
| Cross-sheet queries | 5 | 3 | 0 | 2 | 60.0% |
| **Total** | **50** | **42** | **2** | **6** | **88.0%** |

The overall QSR of 88.0% (44 successful responses out of 50 questions) exceeds the pre-defined PoC exit threshold of 85%, thereby satisfying the primary evaluation criterion established in Section 5.1.

It should be noted that performance varies considerably across categories. Single-sheet analytical categories (sales, inventory, purchasing, accounts receivable) achieved success rates ranging from 87.5% to 100.0%, whereas the cross-sheet query category achieved only 60.0%. This disparity is examined further in the failure analysis below.

### 6.4 Failure Analysis

The six failed questions were subjected to systematic analysis to identify recurring failure modes. The results of this analysis are presented in Table 8.

_Table 8_

_Failure Mode Classification_

| Failure Mode | Count | Description |
|---|---|---|
| Cross-sheet join ambiguity | 2 | The LLM was unable to identify the correct join key when column names across sheets were inconsistent (e.g., "product name" in one sheet versus "item" in another) |
| Complex temporal reasoning | 2 | Questions involving relative date calculations (e.g., "compared to the same period last year") exceeded the analysis engine's current temporal operation vocabulary |
| Ambiguous column mapping | 1 | The question referenced a business concept ("profit") that required computing a derived column not explicitly present in the dataset |
| Filter expression error | 1 | The LLM generated a filter condition with an incorrect operator for the target column's data type |

The cross-sheet join failures, which account for 2 of the 5 cross-sheet questions tested, identify schema alignment across heterogeneous sheets as the highest-priority area for improvement. The temporal reasoning failures suggest that the current six-intent analysis vocabulary may require extension to accommodate time-comparison operations, as discussed further in Section 9.2.

### 6.5 Future Evaluation Plan

To strengthen the validity and generalizability of the evaluation findings, the following expanded testing protocol is planned for the V1 and Closed Beta stages.

During the V1 stage, the test set will be expanded from 50 to 150 questions through three mechanisms: (a) the addition of questions derived from real merchant interactions during internal testing, (b) the introduction of adversarial questions designed to test edge cases such as ambiguous phrasing, out-of-scope requests, and questions for which no answer exists in the data, and (c) an increase in cross-sheet query coverage to at least 20 questions, thereby providing a more statistically meaningful sample for this category.

To address the limitation of single-evaluator assessment (see Section 9.1), a multi-evaluator protocol will be introduced at the V1 stage. A minimum of two independent evaluators will assess each question, and inter-rater reliability will be measured using Cohen's kappa coefficient (Cohen, 1960), with a target agreement threshold of κ ≥ 0.80.

During the Closed Beta stage, merchant users will interact with the system using their own business data. With user consent, questions will be logged to construct a naturalistic test set reflecting authentic usage patterns. This naturalistic test set will be evaluated separately from the standardized test set to assess the ecological validity of the findings.

A regression test suite will be maintained on an ongoing basis throughout development. Each bug fix or feature addition will be followed by a full regression run to verify that previously passing questions remain correct. This suite will be automated using pytest, with each test case specifying the input question, the expected analysis intent, and the expected key numerical outputs.

Finally, during the Closed Beta stage, response latency will be measured under controlled conditions across three load profiles: single user, 10 concurrent sessions, and 50 concurrent sessions (the system's maximum capacity). Latency percentiles (p50, p95, p99) will be reported separately for computational and conversational query paths.

---

## 7. Conditions for Carrying Out Practical Work

This section documents the technical, data, human, and institutional resources available for the execution of the project.

### 7.1 Technical Resources

| Resource | Description | Status |
|---|---|---|
| DeepSeek LLM API | Large language model for natural language understanding, classification, plan generation, and narration | Secured |
| Development environment | Python 3.11+, Node.js, VS Code, Git | Configured |
| Frontend framework | React 19, Vite 8, TypeScript 6, ECharts 6 | Established |
| Backend framework | FastAPI 0.115, pandas 2.2, openpyxl 3.1, xlrd 2.0 | Established |
| Testing framework | pytest 8.3 (backend), TypeScript compiler checks (frontend) | Available |

### 7.2 Data Resources

| Resource | Description | Status |
|---|---|---|
| Representative merchant datasets | Sample sales, inventory, purchasing, and accounts data in Excel and CSV format, reflecting Zhihuiji data structures | Prepared |
| Support ticket database | 87 user support tickets related to reporting functionality, utilized for pain point validation and test set construction | Analyzed and categorized |
| Competitive product data | Feature comparisons, pricing, and capability assessments for six competitor products | Completed |

### 7.3 Human Resources

| Role | Responsibility | Person |
|---|---|---|
| Product Manager (Intern) | Product definition, user research, PRD authorship, competitive analysis, feature specification, feasibility assessment | Duong Phuong Thao (Author) |
| Engineering team | Technical guidance, code review, infrastructure support | Kingdee Zhihuiji engineering team |
| Internship supervisor | Project oversight, strategic direction, institutional support | Kingdee supervisor |

### 7.4 Institutional Support

Kingdee serves as the supporting enterprise for this project, providing: (a) platform environment access, including the Zhihuiji architecture, data schemas, and user behavior patterns; (b) access to real merchant users for closed beta testing and feedback collection; (c) domain expertise concerning micro-merchant business workflows, reporting needs, and operational constraints; and (d) infrastructure guidance regarding production deployment considerations, scalability, and integration strategy.

The combination of these resources ensures that the project can be executed within the planned timeline without reliance upon external resources that have not yet been secured.

---

## 8. Progress Schedule and Key Milestones

### 8.1 Three-Stage Roadmap

The project is organized into three stages spanning 13 weeks, as outlined in Table 9.

_Table 9_

_Project Roadmap and Stage Gate Criteria_

| Stage | Weeks | Duration | Key Milestone | Exit Gate |
|---|---|---|---|---|
| PoC | 1–4 | 4 weeks | Core pipeline functional; QSR ≥ 85% | QSR measured on test set; pipeline demonstration to supervisor |
| V1 | 5–9 | 5 weeks | Session memory, cross-sheet queries, error handling, internal testing | Internal test pass; all error categories handled |
| Closed Beta | 10–13 | 4 weeks | Merchant user testing, feedback collection, final benchmarks | User feedback collected; final QSR validated; report submitted |

### 8.2 Detailed Phase Breakdown

**Phase 1: Proof of Concept (Weeks 1–4).** During Week 1, the file parser module (supporting XLSX, XLS, and CSV formats), data profiler, and session store are to be implemented, enabling file upload with display of structure, column types, and statistical metadata. Week 2 focuses on DeepSeek LLM integration, the analysis engine, and dashboard generation, producing the upload-to-dashboard pipeline. Week 3 addresses the chat module, including question classification, the Classify–Compute–Narrate pattern, and the chat interface. Week 4 is devoted to error handling, session cleanup, QSR evaluation on the standardized test set, and PoC demonstration.

**Phase 2: V1 Internal Release (Weeks 5–9).** Weeks 5 and 6 focus on session memory refinement and multi-turn conversation optimization to improve context retention across conversation turns. Week 7 addresses cross-sheet join support for multi-file queries. Week 8 introduces irrelevant question filtering and edge case handling to ensure graceful responses to out-of-scope or ambiguous questions. Week 9 is dedicated to internal testing with representative datasets and the resolution of identified defects.

**Phase 3: Closed Beta (Weeks 10–13).** Weeks 10 and 11 encompass deployment to the closed beta environment and the recruitment of merchant testers. Week 12 focuses on user feedback collection and resolution of critical issues. Week 13 is devoted to final QSR benchmarking, performance testing, and compilation of the feasibility demonstration report.

### 8.3 Risk Checkpoints

Three risk checkpoints are defined to trigger stage gate reviews, as specified in Table 10.

_Table 10_

_Risk Checkpoint Definitions and Contingency Actions_

| Checkpoint | Trigger Condition | Contingency Action |
|---|---|---|
| PoC Gate (End of Week 4) | QSR < 85% on standardized test set | Investigate failure modes; adjust LLM prompts, analysis engine logic, or test set scope prior to proceeding |
| V1 Gate (End of Week 9) | Internal testing reveals critical usability or accuracy deficiencies | Extend V1 phase by one week; compress beta timeline accordingly |
| Beta Gate (End of Week 12) | User feedback indicates fundamental design misalignment with user needs | Reassess product direction; document findings and lessons learned |

---

## 9. Limitations and Future Work

### 9.1 Limitations

Several limitations of the present work warrant acknowledgment.

First, the current prototype operates on a file-upload-only basis, requiring users to upload data files manually rather than querying live database records. This design introduces friction into the user experience and restricts analyses to static data snapshots rather than real-time records. While integration with Zhihuiji's live data layer is planned, it has not been implemented in the current phase.

Second, the analysis engine supports a constrained vocabulary of six intent types (aggregate, distribution, trend, comparison, top_n, and correlation). Although these types cover the majority of identified user needs, they do not encompass all possible analytical operations. In particular, forecasting, anomaly detection, and cohort analysis are not currently supported. As the failure analysis presented in Section 6.4 demonstrates, complex temporal comparisons (e.g., year-over-year analysis) exceed the current operation vocabulary.

Third, the MVP operates without user authentication or data isolation between sessions. While this is acceptable for proof-of-concept validation, it is insufficient for production deployment in which data confidentiality must be assured.

Fourth, the QSR evaluation reported in Section 6.3 was conducted by a single evaluator (the author). Although the evaluation criteria were defined in advance to minimize subjectivity, the absence of independent verification introduces the possibility of evaluator bias. The multi-evaluator protocol described in Section 6.5 is intended to address this limitation in subsequent evaluation phases.

Fifth, the 50-question test set, while adequate for PoC-level validation, provides limited statistical power for drawing conclusions about specific analytical categories. The cross-sheet query category, in particular, with only five questions, is too small to yield reliable performance estimates. Confidence intervals for category-level success rates remain wide at this sample size.

Sixth, the system's functionality is contingent upon the availability and responsiveness of the external DeepSeek LLM API. Network latency, API rate limits, and service interruptions directly affect system reliability. At present, no offline fallback mechanism has been implemented.

### 9.2 Future Work

Several directions for future development emerge from the findings of the present work.

The highest-priority enhancement for production viability is direct integration with Zhihuiji's data layer, which would eliminate the file upload requirement and enable real-time queries against the user's current business data.

The analysis intent vocabulary should be extended to encompass temporal comparison operations (month-over-month, year-over-year), forecasting capabilities (simple moving average, linear trend projection), and anomaly detection (statistical outlier identification). Each new intent type would require corresponding validation rules and execution logic within the analysis engine.

The failure analysis presented in Section 6.4 identifies cross-sheet join ambiguity as the weakest performance area. Future work should investigate automated schema alignment techniques, including fuzzy column name matching and semantic similarity-based join key inference, to improve the system's robustness when confronted with inconsistent sheet schemas.

A formal user study conducted with a statistically significant sample of merchant users would provide considerably stronger evidence for the system's practical utility. Such a study should measure task completion rates, time-to-insight, user satisfaction (e.g., using the System Usability Scale; Brooke, 1996), and performance relative to the current manual workflow as a baseline.

Finally, transitioning from the monolithic MVP to a production-ready architecture would necessitate persistent session storage (e.g., Redis), user authentication, data isolation between tenants, horizontal scaling capabilities, and comprehensive monitoring infrastructure.

---

## 10. Review Opinions from Supporting Unit (Kingdee)

_This section is to be completed by the supporting enterprise._

---

**Review Opinion from Supporting Unit**

**Enterprise Name:** Shenzhen Kingdee Tianyou Cloud Computing Co., Ltd.
**Platform/Product:** Zhihuiji

**Project Title:** ChatBI — AI-Powered Conversational Data Analytics Agent for Zhihuiji

**Review Content:**

We confirm that the above project was conducted within the Zhihuiji product team at Kingdee during the applicant's internship period. The project addresses a validated business need, specifically the inability of micro-merchant users to access and interpret their own business data without professional analysis skills, which has been documented through user support tickets in our operations system.

The applicant served as the Product Manager responsible for user research, pain point validation, competitive analysis, product requirements definition, and technical feasibility assessment. The applicant demonstrated the ability to independently identify the problem, design the solution, and coordinate with the engineering team for implementation.

The ChatBI prototype demonstrates technical feasibility and practical value for the Zhihuiji platform. The conversational natural language query approach, combined with automatic chart visualization and session memory, represents a meaningful contribution to the micro-enterprise SaaS analytics domain.

We endorse the applicant's contribution and confirm that the work presented in this report accurately reflects the project as conducted.

**Authorized Representative:** ______________________
**Title:** ______________________
**Date:** ______________________
**Official Seal:**

---

_Note: The above is a draft template. The final version should be reviewed, modified as needed, and officially signed and sealed by the authorized representative at Kingdee._

---

## References

Alibaba Cloud. (2024). *Quick BI: Intelligent business analytics platform*. https://www.alibabacloud.com/product/quickbi

Androutsopoulos, I., Ritchie, G. D., & Thanisch, P. (1995). Natural language interfaces to databases: An introduction. *Natural Language Engineering*, *1*(1), 29–81. https://doi.org/10.1017/S135132490000005X

Apache ECharts. (2024). *Apache ECharts: An open source JavaScript visualization library*. https://echarts.apache.org/

Braun, V., & Clarke, V. (2006). Using thematic analysis in psychology. *Qualitative Research in Psychology*, *3*(2), 77–101. https://doi.org/10.1191/1478088706qp063oa

Brooke, J. (1996). SUS: A "quick and dirty" usability scale. In P. W. Jordan, B. Thomas, B. A. Weerdmeester, & I. L. McClelland (Eds.), *Usability evaluation in industry* (pp. 189–194). Taylor & Francis.

Chen, M., Tworek, J., Jun, H., Yuan, Q., Pinto, H. P. de O., Kaplan, J., Edwards, H., Burda, Y., Joseph, N., Brockman, G., Ray, A., Puri, R., Krueger, G., Petrov, M., Khlaaf, H., Sastry, G., Mishkin, P., Chan, B., Gray, S., … Zaremba, W. (2021). Evaluating large language models trained on code. *arXiv preprint arXiv:2107.03374*. https://doi.org/10.48550/arXiv.2107.03374

Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, *20*(1), 37–46. https://doi.org/10.1177/001316446002000104

Fanruan. (2024). *FineBI: Self-service business intelligence platform*. https://www.fanruan.com/finebi

Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design patterns: Elements of reusable object-oriented software*. Addison-Wesley.

Gao, D., Wang, H., Li, Y., Sun, X., Qian, Y., Ding, B., & Zhou, J. (2023). Text-to-SQL empowered by large language models: A benchmark evaluation. *arXiv preprint arXiv:2308.15363*. https://doi.org/10.48550/arXiv.2308.15363

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y. J., Madotto, A., & Fung, P. (2023). Survey of hallucination in natural language generation. *ACM Computing Surveys*, *55*(12), 1–38. https://doi.org/10.1145/3571730

Martin, R. C. (2003). *Agile software development: Principles, patterns, and practices*. Prentice Hall.

Microsoft. (2023). *Copilot in Power BI*. https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction

Ministry of Industry and Information Technology. (2023). *Guiding opinions on promoting digital transformation of small and medium-sized enterprises*. MIIT.

OpenAI. (2023). *ChatGPT plugins and code interpreter*. https://openai.com/index/chatgpt-plugins

Pourreza, M., & Rafiei, D. (2023). DIN-SQL: Decomposed in-context learning of text-to-SQL with self-correction. *Advances in Neural Information Processing Systems*, *36*. https://doi.org/10.48550/arXiv.2304.11015

Salesforce. (2024). *Tableau AI: Generative AI for business intelligence*. https://www.tableau.com/products/tableau-ai

Schick, T., Dwivedi-Yu, J., Dessì, R., Raileanu, R., Lomeli, M., Hambro, E., Zettlemoyer, L., Cancedda, N., & Scialom, T. (2023). Toolformer: Language models can teach themselves to use tools. *Advances in Neural Information Processing Systems*, *36*. https://doi.org/10.48550/arXiv.2302.04761

Shushi Technology. (2024). *SwiftAgent: Intelligent data analytics platform*. https://www.shushitech.com/

Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q. V., & Zhou, D. (2022). Chain-of-thought prompting elicits reasoning in large language models. *Advances in Neural Information Processing Systems*, *35*, 24824–24837.

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. *International Conference on Learning Representations (ICLR)*. https://doi.org/10.48550/arXiv.2210.03629

Yu, T., Zhang, R., Yang, K., Yasunaga, M., Wang, D., Li, Z., Ma, J., Li, I., Yao, Q., Roman, S., Zhang, Z., & Radev, D. (2018). Spider: A large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-SQL task. *Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing*, 3911–3921. https://doi.org/10.18653/v1/D18-1425

Zhong, V., Xiong, C., & Socher, R. (2017). Seq2SQL: Generating structured queries from natural language using reinforcement learning. *arXiv preprint arXiv:1709.00103*. https://doi.org/10.48550/arXiv.1709.00103
