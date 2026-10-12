# Manufacturing Hybrid Multi-Agent Decision Support System

A Python-based manufacturing Decision Support System (DSS) for investigating equipment health, manufacturing root causes, and quality defects using structured MES data, engineering knowledge, deterministic rules, and LLM-assisted explanations.

## 1. Project Overview

The system combines:

- SQLite-based Manufacturing Execution System (MES) data access.
- Engineering document ingestion and Retrieval-Augmented Generation (RAG).
- Semantic retrieval and evidence collection.
- Deterministic manufacturing rules and decision logic.
- Intent/task routing, predefined workflows, and bounded agentic investigation.
- LLM-assisted response explanations using a configurable local Ollama model.
- Request logging, tracing, duration metrics, and error handling.
- Human approval gating for decisions that require review.

## 2. Manufacturing Use Cases

### Predictive Maintenance

Investigates a specified machine using available manufacturing data and returns a structured decision with findings, supporting evidence, data gaps, and approval information.

### Root Cause Analysis (RCA)

Combines structured manufacturing records and engineering knowledge to investigate potential causes. Candidate causes must not be treated as confirmed without sufficient corroborating evidence.

### Defect Monitoring

Evaluates available quality-control records and configured rules to identify quality concerns and report supporting evidence.

## 3. Architecture

The intended architecture follows this flow:

```text
User / API Client
       |
       v
Intent / Task Router
       |
       +--> Direct Tool Execution
       |
       +--> Predefined Manufacturing Workflow
       |
       +--> Bounded Agentic Investigation
                    |
                    v
              Tool Layer
          /       |       \
        SQL      Rules     RAG
          \       |       /
           v      v      v
         MES Data + Engineering Documents
                    |
                    v
             Evidence Collection
                    |
                    v
          Decision and Response Synthesis
                    |
                    v
            Structured API Response
```

See [docs/architecture.md](docs/architecture.md) for the architecture description and [docs/development-history.md](docs/development-history.md) for implementation milestones.

## 4. Technology Stack

- Python 3.11
- FastAPI and Pydantic
- SQLite
- Sentence Transformers and semantic retrieval
- Ollama with Gemma 3 4B by default
- Pytest
- OpenTelemetry instrumentation

## 5. Prerequisites

Install or prepare:

1. Python 3.11.
2. Git.
3. The project MES database at `data/raw/MES.db`.
4. The engineering PDF documents used by the knowledge-base ingestion process.
5. Ollama, with the configured LLM model downloaded, if LLM explanations are required.

Install Ollama from its official website: https://ollama.com/

Download the default model:

```powershell
ollama pull gemma3:4b
```

Ensure Ollama is running before testing LLM-assisted explanations. Deterministic processing and LLM explanation generation have different responsibilities; an LLM failure may leave the deterministic response available.

## 6. Setup

Clone the repository:

```powershell
git clone https://github.com/Parimisatya30/manufacturing-hybrid-multi-agent-dss.git
cd manufacturing-hybrid-multi-agent-dss
```

Create and activate a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create the local environment configuration:

```powershell
Copy-Item .env.example .env
```

Review `.env` and ensure the database path and LLM settings match your environment. Do not commit secrets or machine-specific configuration.

Example settings:

```dotenv
APP_NAME=manufacturing-dss
ENVIRONMENT=development
MES_DATABASE_PATH=data/raw/MES.db
LLM_PROVIDER=ollama
LLM_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT_SECONDS=120
```

The application resolves the database path relative to the project root.

## 7. Run the API

From the repository root, with the virtual environment activated:

```powershell
uvicorn app.main:app --reload
```

The API should be available at:

- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

Health-check example:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## 8. API Examples

### Predictive Maintenance

```powershell
$body = @{
    machine_id = 8
    user_query = "Assess predictive maintenance risk for machine 8"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/api/v1/maintenance/investigate `
    -ContentType "application/json" `
    -Body $body
```

### Root Cause Analysis

```powershell
$body = @{
    user_query = "Investigate critical manufacturing defects and identify possible root causes"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/api/v1/rca/investigate `
    -ContentType "application/json" `
    -Body $body
```

### Defect Monitoring

```powershell
$body = @{
    user_query = "Monitor manufacturing defects and evaluate quality thresholds"
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri http://127.0.0.1:8000/api/v1/defects/monitor `
    -ContentType "application/json" `
    -Body $body
```

The API returns structured findings and evidence according to the selected workflow. Inspect the response and the interactive API documentation for the exact response schema.

## 9. Document Ingestion and Retrieval Evaluation

The repository includes scripts for inspecting source documents, ingesting PDFs, and running retrieval evaluation.

Run retrieval evaluation from the repository root:

```powershell
python -m scripts.run_retrieval_evaluation
```

The evaluation uses manually labelled relevant chunk IDs and reports:

- Recall@3
- Precision@3
- Mean Reciprocal Rank (MRR)

See [docs/retrieval-evaluation.md](docs/retrieval-evaluation.md) for the baseline, interpretation, validation examples, and known limitations.

## 10. Testing

Run all tests:

```powershell
python -m pytest -q
```

Run the response-generator tests:

```powershell
python -m pytest tests/unit/test_response_generator.py -q
```

Run focused retrieval and evaluation tests:

```powershell
python -m pytest tests/evaluation tests/rag -q
```

The last recorded full-suite baseline was 254 passing tests. Re-run the suite in your environment to verify the current checkout and dependencies.

## 11. Observability and Failure Handling

The API middleware records request IDs, request duration, HTTP status, and unexpected failures. The response-generation path preserves deterministic results if LLM explanation generation fails.

Responses may identify missing or unavailable sensor data. Evidence-reference traceability indicates that referenced evidence records exist; it does not independently guarantee semantic entailment for every generated claim.

## 12. Evaluation Summary

The initial retrieval baseline recorded:

| Metric | Baseline |
|---|---:|
| Mean Recall@3 | 1.000 |
| Mean Precision@3 | 0.533 |
| Mean Reciprocal Rank | 0.900 |

Three live API workflows were also exercised: predictive maintenance, root cause analysis, and defect monitoring. These checks establish functional execution examples, not a comprehensive accuracy benchmark.

Controlled latency benchmarking and automated semantic grounding verification remain future evaluation work.

## 13. Known Limitations

- Retrieval metrics are based on a small, manually labelled evaluation dataset.
- Retrieval scores do not measure final-answer correctness or faithfulness.
- Evidence ID traceability does not prove that a claim is semantically supported by its evidence.
- Missing sensor data can limit the strength of a maintenance diagnosis.
- Aggregate quality-control metrics should not be interpreted as time-based trends unless the workflow explicitly performs temporal analysis.
- Controlled latency measurements and broader failure-mode benchmarks remain future work.
- No chatbot UI is currently documented as part of the implemented application.

## 14. Repository Structure

```text
app/
  agents/
  api/
  config/
  context/
  database/
  decision/
  evaluation/
  evidence/
  llm/
  memory/
  models/
  observability/
  rag/
  router/
  semantic/
  synthesis/
  tools/
  workflows/
data/
  processed/
  raw/
docs/
scripts/
tests/
```

## 15. Development Approach

The project is developed incrementally using focused implementation changes, automated tests, and separate Git commits. See `docs/development-history.md` for the recorded milestones.
