# Manufacturing Hybrid Multi-Agent Decision Support System

A Python-based Manufacturing Decision Support System (DSS) combining structured MES data, engineering knowledge retrieval, deterministic rules, and agentic investigation.

## Project Goals

- Query manufacturing execution system (MES) data.
- Retrieve engineering knowledge from documents using RAG.
- Apply deterministic rules for manufacturing decisions.
- Support bounded agentic investigation.
- Provide traceable, context-aware decision support.

## Implementation Status

### Completed

- **Document models:** Represent documents, structural blocks, and semantic chunks with source metadata.
- **PDF ingestion:** Extract document structure and preserve relevant provenance.
- **Text cleaning:** Clean extracted content and filter common document noise.
- **Semantic chunking:** Split content into meaningful retrieval units.
- **Embedding generation:** Generate normalized semantic embeddings using `sentence-transformers/all-MiniLM-L6-v2`.
- **Vector storage:** Store chunk embeddings in an in-memory index.
- **Semantic search:** Rank chunks using cosine similarity.
- **Retrieval service:** Provide a tested interface for retrieving relevant document chunks.

### Current Limitations

- The vector store is in memory; indexed data is not persisted across application restarts.
- The retrieval service has not yet been integrated into the main application flow.
- End-to-end RAG responses and source-grounded answer generation remain to be implemented.

## Technology Stack

- Python 3.11
- SQLite / MES data access
- Sentence Transformers
- Pytest
- OpenTelemetry

## Testing

Run the test suite from the project root:

```bash
python -m pytest -q
```

Latest verified baseline: **93 tests passed**.

## Development Approach

The project is being developed incrementally, with focused implementation steps, automated tests, and separate Git commits for completed milestones.

## Next Steps

1. Integrate the retrieval service into the application workflow.
2. Add source-grounded answer generation.
3. Connect structured MES queries and deterministic rules through the hybrid decision-support flow.
4. Add end-to-end tests for representative manufacturing questions.
