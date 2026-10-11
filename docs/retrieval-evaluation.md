\# RAG Retrieval Evaluation Report



\## 1. Objective



Evaluate the manufacturing knowledge base retrieval pipeline using questions derived from the four source PDFs. The evaluation measures whether relevant document chunks appear in the top-ranked search results.



\## 2. Evaluation Scope



\- \*\*Source documents:\*\* Defect Catalog, KPI Handbook, Predictive Maintenance and Condition Monitoring, Root Cause Analysis Guide.

\- \*\*Evaluation queries:\*\* 5 manufacturing questions.

\- \*\*Retrieval depth:\*\* Top 3 chunks per query.

\- \*\*Evaluation method:\*\* Compare retrieved chunk IDs against manually assigned relevant chunk IDs.

\- \*\*Retrieval implementation:\*\* Existing in-memory vector store and embedding-based retrieval pipeline.



\## 3. Metrics



\- \*\*Recall@3:\*\* Fraction of labelled relevant chunks retrieved in the top 3 results.

\- \*\*Precision@3:\*\* Fraction of the top 3 result positions containing relevant chunks. Missing positions count as non-relevant.

\- \*\*Mean Reciprocal Rank (MRR):\*\* Average reciprocal rank of the first relevant result for each query.



\## 4. Initial Baseline Results



| Metric | Baseline |

|---|---:|

| Mean Recall@3 | 1.000 |

| Mean Precision@3 | 0.533 |

| Mean Reciprocal Rank | 0.900 |



\### Interpretation



\- Recall@3 of 1.000 indicates that all labelled relevant chunks were retrieved within the top 3 for the five evaluation queries.

\- Precision@3 of 0.533 indicates that approximately 53.3% of retrieved result positions were labelled relevant.

\- MRR of 0.900 indicates that relevant evidence generally appeared near the top of the result ranking.



\## 5. Evaluation Queries



The initial dataset covers:



1\. Warning and critical vibration thresholds.

2\. Predictive maintenance alert triage.

3\. Plant-wide OEE and lowest-OEE machines.

4\. Material defect investigation and containment.

5\. First-pass yield targets and escalation thresholds.



The relevance labels are stored in `data/processed/retrieval\_evaluation.json`.



\## 6. Reproducing the Evaluation



From the repository root, activate the project virtual environment and run:



```powershell

python scripts/run\_retrieval\_evaluation.py

```



Run the focused tests:



```powershell

python -m pytest tests/evaluation tests/rag -q

```



Run the complete test suite:



```powershell

python -m pytest -q

```



\## 7. Limitations



\- The evaluation contains only five queries and is an initial baseline, not a comprehensive benchmark.

\- Relevance labels were manually assigned after inspecting retrieval output. This creates a risk of evaluation bias; labels should be reviewed independently against the source documents.

\- A chunk not labelled relevant is not necessarily useless or incorrect. It may provide supporting context that has not yet been labelled.

\- Recall, precision, and MRR evaluate retrieval ranking, not the factual correctness, faithfulness, or completeness of a generated answer.

\- The current results do not establish that the system performs equally well on unseen queries or all manufacturing scenarios.



\## 8. Next Improvements



1\. Independently review the relevance labels against the source documents.

2\. Expand the evaluation dataset with additional representative manufacturing questions.

3\. Track retrieval metrics across changes to chunking, embeddings, or ranking.

4\. Evaluate answer faithfulness and evidence grounding separately from retrieval ranking.



\## 9. Status



The initial retrieval evaluation framework is implemented, tested, committed, and pushed. The reported scores are the first baseline; broader quality validation remains future work.



