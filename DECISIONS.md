# Day 1 — Data Investigation Decisions

## D1. Preserve all source documents

**Decision:** Keep all 119 PDFs in the dataset. Do not automatically remove documents based on matching company names or reporting years.

**Evidence:**
- Manifest contains 119 records.
- PDF directory contains 119 files.
- No missing files, duplicate filenames, or duplicate `doc_id` values were found.
- Some companies have multiple document types or reporting periods within the same year.
- Different 8-K filing dates may represent separate disclosures.
- AMD 2022 contains a potential duplicate pair (`AMD_2022_10K.pdf` and `AMD_2022_annualreport.pdf`). Their extracted text similarity was 87.16%, but exact duplication was not established.

**Reason:** Company and year alone are insufficient to establish document duplication. Removing a filing could remove information needed to answer questions.

**Implementation:** Ingest all documents and use `doc_id` as the document identity. Keep potential duplicates for evaluation rather than deleting them.

## D2. Preserve document-level metadata

**Decision:** Preserve the available manifest metadata during ingestion.

**Required metadata:**
- `doc_id`
- `company`
- `sector`
- `desk`
- `doc_type`
- `period`

**Reason:** This metadata supports document identification, filtering, traceability, and role-based retrieval.

## D3. Preserve page-level provenance

**Decision:** Every extracted chunk must retain its source `doc_id` and original PDF page number.

**Reason:** Answers need to be traceable to their source pages. Multi-page questions also require combining evidence from multiple pages.

**Implementation:** Store page numbers in chunk metadata and use them when generating citations.

## D4. Apply desk-based retrieval filtering

**Decision:** Use the user's authorized desk to filter documents before retrieval.

**Evidence from dev questions:**
- Consumer: 8 questions, all mapped to consumer desk.
- Health & Industrials: 6 questions, all mapped to health_industrials desk.
- Tech & Telecom: 6 questions, all mapped to tech_telecom desk.
- All 20 question-document pairs matched the manifest desk.

**Reason:** Retrieval must respect document access boundaries. Prompt instructions alone are not an access-control mechanism.

**Implementation:** Apply desk filtering in the retrieval layer, based on trusted authorization context.

## D5. Treat the dev question dataset as an evaluation set

**Decision:** Use `dev_questions.jsonl` to evaluate retrieval and answer quality, not as a source of answers during normal question answering.

**Evidence:**
- 20 questions reference 20 unique documents.
- All 20 document IDs match the manifest.
- All 20 referenced PDFs exist.
- All referenced page numbers are within the corresponding PDF page counts.
- Four questions require multiple pages.

**Reason:** This allows us to evaluate whether the system can independently retrieve the correct evidence and produce grounded answers.

## D6. Handle encrypted PDFs without assuming corruption

**Decision:** Do not classify encrypted PDFs as corrupt solely because they are encrypted.

**Evidence:**
- 119/119 PDFs were successfully opened during the readability investigation.
- 50 PDFs were detected as encrypted.
- No DependencyError or unreadable PDF errors occurred.
- Encryption algorithm was not independently verified.

**Reason:** Encryption status and document readability are separate properties.

**Implementation:** Retain the files and monitor extraction success during ingestion.

---

## Day 1 conclusion

Initial dataset, metadata, document availability, encryption, and dev-question reference checks are complete.

No source documents will be removed at this stage. The next phase is PDF extraction and ingestion design, followed by retrieval evaluation.