# Manufacturing Hybrid Multi-Agent Decision Support System

A Python-based Manufacturing Decision Support System (DSS) for investigating equipment health, manufacturing root causes, and quality defects using structured MES data, engineering knowledge, deterministic rules, and LLM-assisted explanations.

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
- A Streamlit interface for interactive demonstration.

The objective is to demonstrate how manufacturing data and engineering knowledge can be combined to produce evidence-backed decision support while keeping important decisions subject to human review.

## 2. Manufacturing Use Cases

### 2.1 Predictive Maintenance

Investigates a specified machine using available manufacturing data and returns a structured decision with findings, supporting evidence, data gaps, and approval information.

The system supports maintenance risk investigation using available sensor and manufacturing records. Missing data must be considered when interpreting findings.

### 2.2 Root Cause Analysis (RCA)

Combines structured manufacturing records and engineering knowledge to investigate potential causes of manufacturing problems.

Candidate causes must not be treated as confirmed without sufficient corroborating evidence.

### 2.3 Defect Monitoring

Evaluates available quality-control records and configured rules to identify quality concerns and report supporting evidence.

The interpretation of defect findings depends on the data available and the analysis implemented by the workflow.

## 3. Architecture

The intended architecture follows this flow:

```text
User / Streamlit UI / API Client
              |
              v
       FastAPI Application
              |
              v
       Intent / Task Router
              |
       +------+------------------+
       |                         |
       v                         v
Direct Tool Execution     Predefined Workflow
       |                         |
       +------------+------------+
                    |
                    v
        Bounded Agentic Investigation
                    |
                    v
                 Tool Layer
             /       |       \
           SQL      Rules      RAG
             \       |       /
              \      |      /
                    v
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
                    |
                    v
        Human Approval, When Required
```

The architecture separates structured data access, document retrieval, deterministic decision logic, and LLM-assisted explanation.

See the following documents for more details:

- `docs/architecture.md` — architecture description.
- `docs/development-history.md` — implementation milestones.
- `docs/retrieval-evaluation.md` — retrieval evaluation and limitations.

## 4. Technology Stack

- **Language:** Python 3.11
- **API:** FastAPI
- **Data validation:** Pydantic
- **Structured data:** SQLite
- **Semantic embedding model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional embeddings)
- **Embedding library:** Sentence Transformers (`SentenceTransformer`)
- **LLM inference runtime:** Ollama
- **Generation model:** Gemma 3 4B (`gemma3:4b`, configured as the default model)
- **UI:** Streamlit
- **Testing:** Pytest
- **Observability:** OpenTelemetry instrumentation and application request logging

The exact Python dependencies are listed in `requirements.txt`. External components such as Python, Ollama, and the downloaded LLM model must be installed or prepared separately.

## 5. Prerequisites

Prepare the following before running the application on a new Windows PC.

| Component | Requirement |
|---|---|
| Python | Python 3.11 |
| Git | Required to clone the repository |
| Python packages | Installed from `requirements.txt` |
| Ollama | Installed for local LLM inference |
| Generation model | `gemma3:4b`, or the model configured in the environment |
| MES database | `data/raw/MES.db` |
| Engineering documents | Source PDFs required by the knowledge-base ingestion process |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Retrieval index | Generated or prepared according to the repository's ingestion procedure |

### Install Python

Install Python 3.11 and ensure the Python launcher is available in PowerShell.

Verify the installation:

```powershell
py -3.11 --version
```

### Install Ollama and the generation model

Install Ollama from its official website:

https://ollama.com/

Verify the installation:

```powershell
ollama --version
```

Download the default model:

```powershell
ollama pull gemma3:4b
```

Verify that the model is available:

```powershell
ollama list
```

Test local inference:

```powershell
ollama run gemma3:4b
```

Enter a test prompt and confirm that the model responds. Exit the interactive session when finished.

Ollama must be running when the application requires LLM-assisted explanations. The model is downloaded separately from the Python dependencies.

## 6. Fresh-PC Setup

Perform these steps from the project root.

### 6.1 Clone the repository

```powershell
git clone https://github.com/Parimisatya30/manufacturing-hybrid-multi-agent-dss.git
cd manufacturing-hybrid-multi-agent-dss
```

### 6.2 Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, enable the policy for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verify the Python version:

```powershell
python --version
```

### 6.3 Install Python dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

If installation fails, inspect the error and verify the Python version and package compatibility before changing dependency versions.

### 6.4 Configure the environment

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Review `.env` and confirm that the configuration matches your environment.

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

These are example settings; use the names and defaults supported by the current application configuration. If the approval workflow requires a supervisor ID setting, configure it according to `app/config/settings.py` and `.env.example`.

Do not commit `.env`, credentials, or machine-specific configuration to Git.

The application resolves the database path relative to the project root.

### 6.5 Verify the MES database

Ensure the required database exists:

```text
data/raw/MES.db
```

The application expects the configured database path to be accessible. If the database is missing, obtain the assignment-provided database and place it at the expected location, or update `MES_DATABASE_PATH`.

SQLite is a file-based database. A separate SQLite database server is not required; Python's SQLite support is generally included with standard Python installations.

### 6.6 Prepare the engineering knowledge base

Ensure that the engineering PDF documents required by the retrieval workflow are available.

#### Models used by this project

| Purpose | Model / component | What it does |
|---|---|---|
| Text generation and LLM-assisted explanations | **Gemma 3 4B** (`gemma3:4b`) through Ollama | Generates language-based explanations for the application's workflows. |
| Text embeddings for semantic retrieval | **`sentence-transformers/all-MiniLM-L6-v2`** | Converts document chunks and user queries into 384-dimensional vectors. |
| Python embedding runtime | Sentence Transformers (`SentenceTransformer`) | Loads the embedding model and creates normalized embeddings. |
| Vector retrieval | Project's in-memory `VectorStore` | Stores chunk vectors and retrieves semantically similar chunks during the process. |

The embedding model is explicitly set as the default in `app/rag/embeddings.py`:

```python
model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
```

Both document chunks and queries are embedded using `normalize_embeddings=True`. The embedding model and generation model serve different purposes: **Gemma generates text; MiniLM creates vectors for retrieval.** Pulling `gemma3:4b` with Ollama does not install the embedding model.

On first initialization, Sentence Transformers may download `sentence-transformers/all-MiniLM-L6-v2` from Hugging Face and cache it locally. Internet access and disk space may be needed for this initial download. For offline use, prepare the model cache in advance and ensure the runtime can access it.

The current vector store is in memory. Unless the application separately persists or reloads the index, its vectors must be recreated when the process starts. Follow the repository's ingestion scripts and configuration to load the engineering PDFs and initialize retrieval.

## 7. Run the Application

Start the API and UI in separate PowerShell terminals. Activate `.venv` in each terminal and run the commands from the repository root.

### 7.1 Start FastAPI

**Terminal 1:**

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API should be available at:

- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

Verify the health endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 7.2 Start Streamlit

**Terminal 2:**

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run ui/streamlit_app.py --server.port 8502
```

Open the interface:

http://localhost:8502

Keep the API and UI running while testing the workflows.

## 8. API Examples

The following PowerShell examples demonstrate the API endpoints.

### 8.1 Predictive Maintenance

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

### 8.2 Root Cause Analysis

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

### 8.3 Defect Monitoring

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

The API returns structured findings and evidence according to the selected workflow. Refer to the interactive API documentation for the exact request and response schemas.

## 9. Human Approval Workflow

The maintenance workflow supports a human approval gate for decisions that require supervisor review.

The approval workflow provides:

- Creation and persistence of approval requests.
- Retrieval of an approval request by its request ID.
- Approval or rejection through the approval API.
- Supervisor authorization checks.
- Persistence of the final decision in a local SQLite database.
- Integration with the Streamlit review interface.

### Approval API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/approvals/{request_id}` | Retrieve an approval request |
| POST | `/api/v1/approvals/{request_id}/decision` | Submit an approval or rejection decision |

The current implementation stores approval decisions in:

```text
data/processed/approvals.db
```

The approval repository manages decision records independently of the MES database.

### Security limitation

The current supervisor-ID mechanism is intended for local assignment demonstration. A supervisor ID alone is not production-grade authentication.

A production implementation should use an identity provider, authenticated user identities, role-based authorization, appropriate audit controls, and secure configuration management.

**Approval is not physical execution.** Recording an approval or rejection does not itself execute a machine repair, change manufacturing equipment settings, or perform a physical control action.

## 10. Document Ingestion and Retrieval Evaluation

The repository includes scripts for inspecting source documents, ingesting PDFs, and running retrieval evaluation.

Run retrieval evaluation from the repository root:

```powershell
python -m scripts.run_retrieval_evaluation
```

The evaluation uses manually labelled relevant chunk IDs and reports:

- Recall@3
- Precision@3
- Mean Reciprocal Rank (MRR)

See `docs/retrieval-evaluation.md` for the baseline, interpretation, validation examples, and known limitations.

Ensure the source documents and any required retrieval index are available before running evaluation. Consult the repository's ingestion scripts and documentation for the exact indexing procedure.

## 11. Testing

Run the full test suite:

```powershell
python -m pytest -q
```

Run response-generator tests:

```powershell
python -m pytest tests/unit/test_response_generator.py -q
```

Run focused retrieval and evaluation tests:

```powershell
python -m pytest tests/evaluation tests/rag -q
```

The latest recorded full-suite run completed with **278 passed, 1 warning** in approximately 51 seconds.

The warning was a Starlette/httpx test-client deprecation warning. It did not cause the test suite to fail.

Re-run the test suite in your environment to verify the current checkout and installed dependencies. Use the result from the actual final run when reporting test status.

## 12. Observability and Failure Handling

The API middleware records request IDs, request duration, HTTP status, and unexpected failures. The response-generation path is designed to preserve deterministic results if LLM explanation generation fails.

Responses may identify missing or unavailable sensor data. Evidence-reference traceability indicates that referenced evidence records exist; it does not independently guarantee semantic entailment for every generated claim.

OpenTelemetry instrumentation provides a foundation for observability. Production deployment would require validating the complete telemetry configuration and integrating the appropriate collection and monitoring infrastructure.

## 13. Evaluation Summary

The initial retrieval baseline recorded the following results:

| Metric | Baseline |
|---|---:|
| Mean Recall@3 | 1.000 |
| Mean Precision@3 | 0.533 |
| Mean Reciprocal Rank | 0.900 |

Three live API workflows were exercised:

- Predictive maintenance.
- Root cause analysis.
- Defect monitoring.

These checks establish functional execution examples, not a comprehensive accuracy benchmark.

Controlled latency benchmarking and automated semantic grounding verification remain future evaluation work.

## 14. Known Limitations

- Retrieval metrics are based on a small, manually labelled evaluation dataset.
- Retrieval scores do not measure final-answer correctness or faithfulness.
- Evidence ID traceability does not prove that a claim is semantically supported by its evidence.
- Missing sensor data can limit the strength of a maintenance diagnosis.
- Aggregate quality-control metrics should not be interpreted as time-based trends unless the workflow explicitly performs temporal analysis.
- Controlled latency measurements and broader failure-mode benchmarks remain future work.
- The Streamlit interface is intended for demonstration and evaluation; production deployment would require additional hardening, access controls, and operational monitoring.
- The demo supervisor-ID mechanism is not suitable as a production authentication mechanism.
- Human approval records a decision but does not execute a physical machine action.
- The application depends on the availability of the configured local LLM and the required retrieval assets for LLM-assisted and document-grounded functionality.

## 15. Troubleshooting

### Ollama connection error

Confirm Ollama is installed and running. Check the configured base URL, usually:

```text
http://localhost:11434
```

Verify that the model is available:

```powershell
ollama list
```

### Model not found

Download the configured generation model:

```powershell
ollama pull gemma3:4b
```

If `LLM_MODEL` is configured to another model, pull that model instead.

### MES database not found

Verify that the database exists at:

```text
data/raw/MES.db
```

Check the `MES_DATABASE_PATH` setting in `.env`.

### No document retrieval results

Verify that the engineering PDFs are available, `sentence-transformers/all-MiniLM-L6-v2` can be loaded, and the ingestion/indexing procedure has been completed. The embedding model may need to download and cache on first use. Check the retrieval configuration and index initialization.

### Python import errors

Activate the project's virtual environment and reinstall dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
```

### Port already in use

Stop the process using the required port or configure a different port. Update the URL used by the UI or API client accordingly.

### Tests fail

Run:

```powershell
python -m pytest -q
```

Inspect the first failing test and its traceback. Verify the environment and dependencies before changing application code or package versions.

## 16. Repository Structure

The following is a logical overview. Some directories may be empty or contain additional files depending on the current checkout.

```text
manufacturing-hybrid-multi-agent-dss/
├── app/
│   ├── agents/
│   ├── api/
│   ├── config/
│   ├── context/
│   ├── database/
│   ├── decision/
│   ├── evaluation/
│   ├── evidence/
│   ├── llm/
│   ├── memory/
│   ├── models/
│   ├── observability/
│   ├── rag/
│   ├── router/
│   ├── semantic/
│   ├── synthesis/
│   ├── tools/
│   └── workflows/
├── data/
│   ├── processed/
│   └── raw/
│       └── MES.db
├── docs/
│   ├── architecture.md
│   ├── development-history.md
│   └── retrieval-evaluation.md
├── scripts/
├── tests/
├── ui/
│   └── streamlit_app.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## 17. Development Approach

The project is developed incrementally using focused implementation changes, automated tests, and separate Git commits.

See `docs/development-history.md` for the recorded milestones and implementation history.

The implementation emphasizes separation of concerns, evidence-backed responses, deterministic decision logic, testability, and human review for decisions that require approval.

## 18. Future Improvements

Potential next steps include:

- Expand the labelled retrieval evaluation dataset.
- Add automated semantic grounding and faithfulness evaluation.
- Introduce controlled latency and failure-mode benchmarks.
- Improve telemetry collection and operational dashboards.
- Replace demo supervisor identification with production-grade authentication and authorization.
- Integrate approved recommendations with a separately controlled execution system, with appropriate safety interlocks and auditability.

These are future improvements, not claims that the functionality is already implemented.

## 19. License and Assignment Context

This repository was developed as a manufacturing decision-support assignment. Review the applicable assignment terms and repository licensing requirements before redistributing the source code or associated datasets.
