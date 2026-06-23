# VasyERP Graph RAG Agent

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph%20DB-00B1A4?logo=neo4j&logoColor=white)](https://neo4j.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-green)](https://www.langchain.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?logo=ollama)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-Not%20Specified-lightgrey)](LICENSE)

A **fully local, privacy-preserving Graph RAG (Retrieval-Augmented Generation) system** for enterprise ERP data. Built on Neo4j, LangChain, and locally-running Ollama models, it translates plain-English business questions into Cypher queries and returns grounded, hallucination-resistant answers — no cloud API keys required.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Graph Schema](#graph-schema)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [Dataset Generation](#dataset-generation)
- [Data Ingestion](#data-ingestion)
- [RAG Pipeline](#rag-pipeline)
- [Benchmark & Evaluation](#benchmark--evaluation)
- [Testing](#testing)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)

---

## Overview

VasyERP is a real-world multi-tenant ERP platform. Its raw data exports contain well-documented data-quality hazards: `NaN`-contaminated numeric fields, deliberate schema typos in column names (`ProductVarientID`, `BillingCompnyName`), walk-in POS orders with null customer references, soft-deleted records flagged via `IsDeleted`, and negative quantities for returns and credit notes.

This project builds a **Graph RAG agent** on top of VasyERP's data that:

1. Ingests messy, multi-tenant CSV exports into a structured Neo4j knowledge graph using defensive Cypher patterns.
2. Routes natural-language business questions through a two-LLM pipeline: a specialist Cypher-generation model and a QA synthesis model.
3. Uses a heavily constrained, few-shot prompt engineering strategy to prevent Cypher hallucinations — a critical failure mode for small local models.
4. Provides a 20-question benchmark suite to measure end-to-end pipeline accuracy across revenue, customer, product, and order-analytics query categories.

**Target users:** ML engineers, data engineers, and enterprise AI practitioners building production RAG systems over structured business data with local LLM deployments.

---

## Features

- **Fully local inference** — zero external API calls; all LLMs run via Ollama
- **Dual-LLM architecture** — specialist Cypher-generation model decoupled from QA synthesis model
- **Defensive data ingestion** — scrubs `NaN` strings before they reach Neo4j, maps known column typos, handles null walk-in POS customer IDs
- **Multi-tenant data isolation** — data scoped by `CompanyID` across four tenant companies (101, 202, 305, 450)
- **Strict Cypher prompt engineering** — absolute rule set, negative examples, and 12 few-shot query mappings to suppress hallucination
- **Soft-delete awareness** — `IsDeleted` flag filtering built into ground-truth test harness
- **Return/credit-note handling** — negative quantities correctly propagated for `posreturn` and `creditnote` order types
- **Interactive CLI chatbot** — real-time schema inspection and conversational query mode
- **20-test benchmark suite** — covers industry distribution, regional filtering, revenue aggregation, product rankings, and cross-company analytics
- **Pandas ground-truth validator** — independent CSV-level verification to establish ground truth for benchmark answers
- **Schema visualization** — included PNG diagram of the knowledge graph schema

---

## Tech Stack

| Category | Technology |
|---|---|
| Graph Database | Neo4j (Bolt protocol, local instance) |
| LLM Runtime | Ollama (fully local inference) |
| Cypher Generation Model | `tomasonjo/llama3-text2cypher-demo` |
| QA Synthesis Model | `qwen2.5:3b` |
| LLM Orchestration | LangChain (`langchain_neo4j`, `langchain_ollama`, `langchain_core`) |
| Data Processing | Python `csv`, `pandas`, `random`, `datetime` |
| Configuration | `python-dotenv` |
| Testing / Validation | `pandas` (ground-truth), custom benchmark harness |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User (CLI)                           │
│              Natural Language Business Question             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  GraphCypherQAChain                         │
│              (LangChain Orchestration Layer)                 │
│                                                             │
│  ┌───────────────────┐         ┌──────────────────────────┐ │
│  │  Cypher LLM       │         │  QA LLM                  │ │
│  │  (llama3-         │         │  (qwen2.5:3b)            │ │
│  │   text2cypher)    │         │                          │ │
│  │                   │         │  Synthesizes plain-      │ │
│  │  Strict prompt:   │         │  English answer from     │ │
│  │  - Graph schema   │         │  raw database context    │ │
│  │  - Absolute rules │         │                          │ │
│  │  - Few-shot maps  │         └──────────────────────────┘ │
│  │  - Neg. examples  │                    ▲                 │
│  └─────────┬─────────┘                   │                 │
│            │ Cypher Query                │ DB Context       │
└────────────┼─────────────────────────────┼─────────────────┘
             │                             │
             ▼                             │
┌────────────────────────────┐             │
│         Neo4j              │─────────────┘
│     Knowledge Graph        │  Query Results
│                            │
│  Nodes: Customer, Order,   │
│  OrderItem, Product,       │
│  Company                   │
│                            │
│  Edges: PLACED,            │
│  BELONGS_TO, PROCESSED_BY, │
│  HAS_LINE_ITEM, IS_PRODUCT │
└────────────────────────────┘
             ▲
             │ Ingestion
┌────────────┴───────────────┐
│    ingest_vasy_erp.py      │
│                            │
│  CSV Sources:              │
│  customers.csv             │
│  products.csv              │
│  orders.csv                │
│  order_items.csv           │
│                            │
│  Defensive pre-processing: │
│  - NaN scrubbing           │
│  - Typo mapping            │
│  - Null-safe MERGE         │
└────────────────────────────┘
             ▲
             │ Generation
┌────────────┴───────────────┐
│    augmented_data.py       │
│                            │
│  Synthetic ERP dataset     │
│  with injected traps:      │
│  NaN, soft deletes,        │
│  walk-in POS, typos,       │
│  returns                   │
└────────────────────────────┘
```

---

## Project Structure

```
VASY-ERP-RAG/
├── augmented_data.py       # Synthetic VasyERP dataset generator (1K customers,
│                           #   500 products, 25K orders with intentional traps)
├── ingest_vasy_erp.py      # Defensive CSV → Neo4j ingestion pipeline
├── rag_pipeline.py         # Core Graph RAG: Cypher generation + QA synthesis
├── db_test.py              # Neo4j connectivity and schema smoke test
├── master_benchmark.py     # 20-question end-to-end evaluation suite
├── Tests/
│   └── tests.py            # Pandas ground-truth validator (CSV-level verification)
├── visualisation-schema.png # Knowledge graph schema diagram
└── .gitignore
```

### Module Responsibilities

| File | Purpose |
|---|---|
| `augmented_data.py` | Generates four CSV files simulating VasyERP exports, deliberately injecting NaN contamination, schema typos, soft-delete flags, walk-in POS null references, and return orders with negative quantities |
| `ingest_vasy_erp.py` | Reads and scrubs CSVs, then loads them into Neo4j using null-safe `MERGE` patterns with conditional relationship creation to handle walk-in POS orders |
| `rag_pipeline.py` | Builds the `GraphCypherQAChain` with a highly constrained Cypher generation prompt (schema rules, negative examples, few-shot query mappings) and a strict QA prompt; exposes an interactive CLI |
| `db_test.py` | Verifies Neo4j connection and counts ingested nodes as a post-ingestion sanity check |
| `master_benchmark.py` | Imports the chain from `rag_pipeline.py` and runs 20 natural-language questions, printing generated Cypher, database context, final answers, and per-query runtime |
| `Tests/tests.py` | Uses `pandas` to compute ground-truth values directly from the source CSV files for independent verification |

---

## Graph Schema

```
(:Customer)-[:PLACED]->(:Order)
(:Customer)-[:BELONGS_TO]->(:Company)
(:Order)-[:PROCESSED_BY]->(:Company)
(:Order)-[:HAS_LINE_ITEM]->(:OrderItem)
(:OrderItem)-[:IS_PRODUCT]->(:Product)
(:Product)-[:BELONGS_TO]->(:Company)
```

### Node Properties

| Label | Key Properties |
|---|---|
| `Customer` | `id`, `name`, `Industry`, `Region`, `company_id`, `gstin` |
| `Order` | `id`, `date`, `status`, `type`, `company_id`, `is_deleted`, `billing_company_name` |
| `OrderItem` | `id`, `Quantity`, `LineTotal`, `ProductVarientID` |
| `Product` | `id`, `name`, `category`, `price`, `stock`, `company_id` |
| `Company` | `companyId` |

### Dataset Scale (Generated)

| Entity | Count |
|---|---|
| Customers | 1,000 |
| Products | 500 |
| Orders | 25,000 |
| Order Items | ~50,000–100,000 |
| Tenant Companies | 4 (IDs: 101, 202, 305, 450) |

---

## Installation

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.10+ | |
| Neo4j Desktop or Server | 5.x | Community Edition works |
| Ollama | Latest | [ollama.com](https://ollama.com/) |
| `tomasonjo/llama3-text2cypher-demo` | — | Pull via Ollama |
| `qwen2.5:3b` | — | Pull via Ollama |

### 1. Clone the Repository

```bash
git clone https://github.com/Shreyansh1812/VASY-ERP-RAG.git
cd VASY-ERP-RAG
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 3. Install Python Dependencies

```bash
pip install neo4j langchain langchain-neo4j langchain-ollama langchain-core python-dotenv pandas
```

### 4. Pull Ollama Models

```bash
ollama pull tomasonjo/llama3-text2cypher-demo
ollama pull qwen2.5:3b
```

### 5. Start Neo4j

Launch Neo4j Desktop or your Neo4j Server instance and ensure it is accessible at `bolt://localhost:7687`. Create or confirm a database is active.

---

## Environment Variables

Create a `.env` file in the project root for the ingestion pipeline:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
```

> **Note:** `rag_pipeline.py` currently uses hardcoded connection values. It is recommended to refactor it to read from `.env` before any production or shared deployment.

| Variable | Description | Required |
|---|---|---|
| `NEO4J_URI` | Bolt URI for the Neo4j instance | Yes (ingestion) |
| `NEO4J_USERNAME` | Neo4j username | Yes (ingestion) |
| `NEO4J_PASSWORD` | Neo4j password | Yes (ingestion) |

---

## Running Locally

### Step 1 — Generate the Synthetic Dataset

```bash
python augmented_data.py
```

This produces four CSV files in the working directory: `customers.csv`, `products.csv`, `orders.csv`, `order_items.csv`. Each file contains intentional data quality traps mirroring real VasyERP exports.

> **Important:** Update the `BASE_PATH` constant in `ingest_vasy_erp.py` to point to the directory where these CSVs were generated, or move the CSVs to the path already configured.

### Step 2 — Verify Neo4j Connectivity

```bash
python db_test.py
```

Expected output:

```
 Successfully connected
Verified: Graph contains 0 products.
```

### Step 3 — Ingest Data into Neo4j

```bash
python ingest_vasy_erp.py
```

Expected output:

```
Connecting to Neo4j...
Wiping existing database to prepare for VasyERP data...
Ingesting Customers...
Ingesting Products...
Ingesting Orders & Connections (This handles Walk-in POS)...
Ingesting Order Items (Mapping Typos and Returns)...
 Full VasyERP Database Ingestion Complete! Defense protocols held.
```

### Step 4 — Launch the Interactive RAG Chatbot

```bash
python rag_pipeline.py
```

```
============================================================
Graph RAG Chatbot Initialized
Type your questions below.
Type 'schema' to inspect the schema.
Type 'exit' or 'quit' to close.
============================================================

Ask your Graph Database a question: What industries are represented in Florida?
```

---

## Dataset Generation

`augmented_data.py` is a standalone dataset factory that deliberately injects the known failure modes of VasyERP exports:

| Trap | Description |
|---|---|
| **NaN Contamination** | ~2% of `UnitPrice` and `LineTotal` fields are set to the string `"NaN"` instead of a float |
| **Soft Delete Flag** | ~5% of orders carry `IsDeleted = 1` and must be excluded from active-record queries |
| **Walk-in POS** | ~30% of POS orders from Company 450 have a null `CustomerID`, breaking naive JOIN-style queries |
| **Schema Typos** | `ProductVarientID` (not `ProductVariantID`) and `BillingCompnyName` (not `BillingCompanyName`) are intentional |
| **Negative Quantities** | `posreturn` and `creditnote` orders carry negative `Quantity` and `LineTotal` values |
| **Multi-tenancy** | Four companies (101, 202, 305, 450) share the same tables; Company 450 is predominantly POS |

---

## Data Ingestion

`ingest_vasy_erp.py` implements a defensive ingestion strategy:

- **Pre-scrub:** All `"NaN"` string values are converted to Python `None` before touching Neo4j, preventing type coercion errors.
- **Null-safe MERGE:** Customers, Products, and Orders use `MERGE` with `WHERE` guards on required ID fields.
- **Conditional relationship creation:** Walk-in POS orders (null `CustomerID`) receive an `Order` node but no `PLACED` edge — preserving the order data without creating orphaned relationships.
- **Typo mapping:** `ProductVarientID` is mapped directly to `Product.id` in the `CONTAINS` relationship query.
- **Full wipe on re-run:** `MATCH (n) DETACH DELETE n` ensures idempotent re-ingestion.

---

## RAG Pipeline

`rag_pipeline.py` constructs a `GraphCypherQAChain` with two independently configured LLMs:

### Cypher Generation LLM

`tomasonjo/llama3-text2cypher-demo` — a domain-specialized model fine-tuned for text-to-Cypher tasks. It receives a structured prompt containing:

- The live graph schema (refreshed at startup)
- Explicit relationship path declarations
- Per-node property reference tables
- 15 absolute rules (no SQL syntax, no Cartesian products, always use `toLower()` for string matching, revenue is always `SUM(toFloat(oi.LineTotal))`, etc.)
- 12 question-to-query canonical mappings (few-shot examples)
- Negative examples with explanations of why they are wrong

### QA Synthesis LLM

`qwen2.5:3b` — a small, efficient general-purpose model that receives only the raw database context and the original question, formats the result into a human-readable answer, and is strictly forbidden from inventing information.

### Chain Configuration

```python
cypher_chain = GraphCypherQAChain.from_llm(
    cypher_llm=cypher_llm,
    qa_llm=qa_llm,
    graph=graph,
    cypher_prompt=cypher_prompt,
    qa_prompt=qa_prompt,
    verbose=True,
    return_direct=False,
    return_intermediate_steps=True,
    allow_dangerous_requests=True
)
```

`return_intermediate_steps=True` enables full observability: the CLI prints the generated Cypher query, the raw database context, and the final synthesized answer for every question.

---

## Benchmark & Evaluation

`master_benchmark.py` runs a structured 20-question evaluation suite covering the full range of business analytics query patterns:

| Test | Category | Sample Question |
|---|---|---|
| T1 | Regional filtering | Industries among Texas customers |
| T2 | Count | Healthcare customer count |
| T3 | Count | Florida customer count |
| T4 | Ranking | All industries by customer count |
| T5 | Aggregate | Total order count |
| T6 | Filtered count | Completed orders |
| T7 | Distribution | Orders by status |
| T8 | Revenue | Total revenue across all orders |
| T9 | Revenue (filtered) | Revenue from Healthcare customers |
| T10 | Revenue (filtered) | Revenue from Texas customers |
| T11 | Revenue (multi-filter) | Completed orders, Healthcare customers |
| T12 | Revenue (multi-filter) | Completed orders, Texas customers |
| T13 | Multi-tenant | Customers per company |
| T14 | Multi-tenant | Company with most orders |
| T15 | Aggregate | Total product count |
| T16 | Product ranking | Most purchased products |
| T17 | Product ranking | Highest revenue products |
| T18 | Revenue (filtered) | Completed orders, Technology customers |
| T19 | Cross-dimension | Company 202 products, Finance customers |
| T20 | Distinct count | Number of distinct industries |

Each test records: generated Cypher, raw database context, final answer, and runtime in seconds.

```bash
python master_benchmark.py
```

---

## Testing

### Ground-Truth Validation

`Tests/tests.py` provides independent pandas-based verification of specific benchmark answers directly against the source CSV files, bypassing the LLM pipeline entirely. This isolates graph correctness from model accuracy.

```bash
python Tests/tests.py
```

Example output:

```
Loading orders.csv...

==================================================
📊 PANDAS GROUND TRUTH CHECK (QUESTION 8)
==================================================
Total 'posreturn' for Company 450 (Including Deleted): 342
Active 'posreturn' for Company 450 (IsDeleted == 0) : 325
==================================================
```

### Neo4j Connectivity Test

```bash
python db_test.py
```

---

## Security Considerations

- **Credentials in source code:** `rag_pipeline.py` contains hardcoded Neo4j credentials. These must be moved to environment variables before any non-local or shared deployment.
- **`allow_dangerous_requests=True`:** This LangChain flag permits the chain to execute arbitrary Cypher generated by the LLM. The strict prompt engineering and schema constraints are the primary mitigation, but this should be evaluated carefully for any production deployment.
- **Local-only LLMs:** All inference runs via Ollama on the local machine. No data leaves the host, making this appropriate for environments with strict data residency requirements.
- **`.env` exclusion:** The `.gitignore` correctly excludes `.env` files from version control.

---

## Performance Notes

- **Cold-start latency:** The first query after launching `rag_pipeline.py` incurs Ollama model load time. Subsequent queries are faster as models stay warm.
- **Small model trade-offs:** `qwen2.5:3b` is optimized for low resource usage. Complex multi-hop aggregation queries may require prompt adjustments or a larger QA model.
- **Cypher specialist advantage:** Separating Cypher generation from QA synthesis allows each model to be independently swapped or scaled without affecting the other.
- **Schema refresh:** `graph.refresh_schema()` is called at startup and available interactively via the `schema` CLI command, ensuring the prompt always reflects the current Neo4j state.

---

## Troubleshooting

| Issue | Cause | Resolution |
|---|---|---|
| `Connection failed` in `db_test.py` | Neo4j not running or wrong credentials | Start Neo4j and verify URI, username, and password |
| `404` or model not found in Ollama | Model not pulled | Run `ollama pull <model-name>` |
| `NaN` errors during ingestion | `read_and_scrub_csv` not catching all NaN patterns | Inspect CSV for variant NaN representations and extend the scrub function |
| Cypher query returns empty result | Schema mismatch or typo in query | Run `schema` in the CLI and compare with the prompt's property reference table |
| `Cartesian product` warning in Neo4j | Unconnected `MATCH` clauses | Review generated Cypher; the prompt's absolute rules should prevent this — upgrade to a larger Cypher LLM if persistent |
| `BASE_PATH` file not found | Hardcoded path in `ingest_vasy_erp.py` | Update `BASE_PATH` to the directory containing your generated CSV files |
| `allow_dangerous_requests` error | LangChain safety gate | The flag is already set to `True` in `rag_pipeline.py`; no action needed |

---

## Roadmap

- [ ] Move all hardcoded credentials to `.env` and load via `python-dotenv` in `rag_pipeline.py`
- [ ] Add a `requirements.txt` or `pyproject.toml` for reproducible dependency installation
- [ ] Extend graph schema with `Invoice`, `Payment`, and `Vendor` nodes for accounts-payable queries
- [ ] Implement a scoring harness in `master_benchmark.py` with numeric ground-truth comparison
- [ ] Add a FastAPI REST endpoint to expose the RAG pipeline as a service
- [ ] Experiment with larger Ollama models (`qwen2.5:7b`, `llama3.1:8b`) for improved multi-hop accuracy
- [ ] Introduce a Streamlit or Gradio front end for non-CLI usage
- [ ] Add QLoRA fine-tuning pipeline to adapt the Cypher generation model to VasyERP's specific schema

---

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository and create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with clear, descriptive commits
3. Test your changes using `db_test.py` and `master_benchmark.py`
4. Open a pull request with a summary of the changes and the motivation

When adding new benchmark tests to `master_benchmark.py`, please also add a corresponding pandas ground-truth check in `Tests/tests.py`.

---

## Acknowledgements

- **[LangChain](https://www.langchain.com/)** — orchestration framework providing `GraphCypherQAChain`, `langchain-neo4j`, and `langchain-ollama`
- **[Neo4j](https://neo4j.com/)** — native graph database and Bolt driver
- **[Ollama](https://ollama.com/)** — local LLM runtime enabling fully private inference
- **[tomasonjo/llama3-text2cypher-demo](https://huggingface.co/tomasonjo/llama3-text2cypher-demo)** — domain-specialized text-to-Cypher model by Tomáš Souček
- **[Qwen2.5](https://qwen.readthedocs.io/)** — Alibaba's small, efficient language model used for QA synthesis
- **VasyERP** — the enterprise ERP platform whose real-world data quality challenges motivated this project's defensive engineering patterns

---

## License

License information was not found in the repository.
