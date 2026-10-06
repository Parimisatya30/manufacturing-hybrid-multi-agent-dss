# Manufacturing Hybrid Multi-Agent Decision Support System

## 1. Purpose

The Manufacturing Decision Support System (DSS) provides evidence-based
analysis of manufacturing operational data and engineering knowledge.

The system combines:

- Structured MES data from SQLite
- Unstructured engineering documents
- Deterministic business rules
- Retrieval-Augmented Generation (RAG)
- Predefined manufacturing workflows
- Bounded agentic investigation

The objective is to provide grounded manufacturing insights,
diagnosis and recommendations rather than relying only on an LLM.

---

## 2. High-Level Architecture

```text
                         User
                           |
                           v
                 Intent / Task Router
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
    Simple Query     Known Workflow    Complex Investigation
          |                |                |
          v                v                v
     Direct Tool      Workflow / DAG    Bounded ReAct
          |                |                |
          +----------------+----------------+
                           |
                           v
                     Tool Layer
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
         SQL          Text-to-SQL          RAG
          |                |                |
          +----------------+----------------+
                           |
                           v
                   Deterministic Rules
                           |
              +------------+------------+
              |                         |
              v                         v
           MES.db             Engineering Documents
              |                         |
              +------------+------------+
                           |
                           v
                       Evidence
                           |
                           v
                 Decision / Recommendation
                           |
                           v
                       Response