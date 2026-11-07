# Experiments — Grounded Search System

## Experiment tracking rules

Record each experiment with:
- Experiment ID
- Objective
- Hypothesis
- Configuration
- Test questions
- Observed results
- Failure cases
- Decision based on evidence

Do not record an experiment as successful until it has actually been run.

## E1. PDF extraction quality

**Status:** Pending

**Objective:** Verify that text and tables can be extracted reliably from source PDFs.

**Things to investigate:**
- Empty or missing extracted text.
- Incorrect reading order.
- Headers and footers mixed into content.
- Table row and column alignment.
- Financial values split across lines.
- Page number preservation.

**Evaluation:** Inspect representative PDFs from different document types and compare extracted content with the original PDF pages.

## E2. Chunking strategy

**Status:** Pending

**Objective:** Determine how to split extracted documents without losing important context.

**Things to compare:**
- Fixed-size chunks.
- Overlapping chunks.
- Page-aware chunks.
- Structure-aware chunks, where headings and tables are preserved.

**Evaluation:** Check whether retrieved chunks contain enough context to answer questions accurately and preserve page provenance.

## E3. Duplicate document impact

**Status:** Pending

**Objective:** Determine whether potential duplicate documents introduce redundant or conflicting retrieval results.

**Candidate:** AMD 2022 10-K and annual report.

**Evaluation:**
- Compare extracted content.
- Compare retrieved chunks for relevant questions.
- Check whether duplicate content dominates top-k retrieval.
- Determine whether retaining both affects answer quality.

**Rule:** Do not remove documents without evaluation evidence.

## E4. Retrieval quality

**Status:** Pending

**Objective:** Measure whether the correct evidence is retrieved for dev questions.

**Evaluate:**
- Correct document retrieval.
- Correct page retrieval.
- Relevant context in top-k results.
- Multi-page evidence retrieval.
- Retrieval after desk filtering.

**Metrics to consider:**
- Recall@k
- Precision@k
- MRR
- Evidence coverage

## E5. Desk-based access filtering

**Status:** Pending

**Objective:** Verify that retrieval only returns documents authorized for the user's desk.

**Evaluation:**
- Test each desk separately.
- Test queries against documents belonging to other desks.
- Verify that unauthorized documents do not appear in retrieved results.

**Important:** Enforce filtering in the retrieval layer, not just through the LLM prompt.

## E6. Grounded answer quality

**Status:** Pending

**Objective:** Verify that generated answers are supported by retrieved evidence.

**Evaluate:**
- Factual correctness.
- Citation correctness.
- Correct page references.
- Unsupported claims or hallucinations.
- Financial calculations.
- Multi-page reasoning.

**Rule:** A correct answer without supporting evidence is not sufficient for a grounded search system.

---

## Experiment status summary

No experiments above have been marked as completed. Day 1 work currently establishes the dataset baseline and validation results. Experiments will be run during ingestion, retrieval, and answer evaluation.