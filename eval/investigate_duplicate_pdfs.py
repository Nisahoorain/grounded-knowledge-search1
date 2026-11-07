
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import re

from pypdf import PdfReader
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
MANIFEST = ROOT / "data" / "manifest.csv"
OUTPUT = ROOT / "data" / "duplicate_investigation.csv"


def load_manifest():
    with MANIFEST.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def extract_period_info(doc_id):
    name = doc_id.upper()

    quarter_match = re.search(r"Q([1-4])", name)
    date_match = re.search(
        r"DATED[-_]?(\d{4}-\d{2}-\d{2})", name
    )

    return {
        "quarter": quarter_match.group(1) if quarter_match else None,
        "filing_date": date_match.group(1) if date_match else None
    }


def normalize_doc_type(doc_type):
    doc_type = doc_type.strip().lower()

    aliases = {
        "10k": "annual_filing",
        "10k_annualreport": "annual_filing",
        "10q": "quarterly_filing",
        "8k": "current_filing",
        "earnings": "earnings_release"
    }

    return aliases.get(doc_type, doc_type)


def extract_pdf_info(path):
    reader = PdfReader(str(path))

    pages_text = [
        page.extract_text() or ""
        for page in reader.pages
    ]

    full_text = "\n".join(pages_text)
    normalized = re.sub(
        r"\s+", " ", full_text
    ).strip().lower()

    return {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "page_count": len(reader.pages),
        "metadata": reader.metadata,
        "pages_text": pages_text,
        "normalized_text": normalized,
        "text_hash": hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()
    }


def compare_documents(a, b):
    similarity = SequenceMatcher(
        None,
        a["normalized_text"],
        b["normalized_text"]
    ).ratio() * 100

    if a["text_hash"] == b["text_hash"]:
        classification = "EXACT TEXT DUPLICATE"
    elif similarity >= 95:
        classification = "NEAR DUPLICATE - REVIEW"
    elif similarity >= 70:
        classification = "PARTIAL SIMILARITY - REVIEW"
    else:
        classification = "DIFFERENT DOCUMENTS"

    return similarity, classification


def inspect_differences(a, b):
    print("\n--- DOCUMENT DETAILS ---")

    print("File A:", a["file"])
    print("File B:", b["file"])

    print("Pages A:", a["page_count"])
    print("Pages B:", b["page_count"])

    print("Size A:", a["size_bytes"])
    print("Size B:", b["size_bytes"])

    print("\n--- FIRST PAGE A ---")
    print(a["pages_text"][0][:1500])

    print("\n--- FIRST PAGE B ---")
    print(b["pages_text"][0][:1500])

    print("\n--- PAGE COUNT DIFFERENCE ---")
    print(abs(a["page_count"] - b["page_count"]))

    print("\n--- DIFFERENT PAGES ---")

    max_pages = max(
        len(a["pages_text"]),
        len(b["pages_text"])
    )

    for i in range(max_pages):
        page_a = (
            a["pages_text"][i]
            if i < len(a["pages_text"]) else ""
        )

        page_b = (
            b["pages_text"][i]
            if i < len(b["pages_text"]) else ""
        )

        if page_a.strip() != page_b.strip():
            print(f"Page {i + 1}: Different")

    print("\n--- SELECTED PAGE CONTENT COMPARISON ---")

    for page_num in [10, 50, 100]:
        print(f"\n========== PAGE {page_num} ==========")

        print("\n--- FILE A ---")
        print(a["pages_text"][page_num - 1][:1000])

        print("\n--- FILE B ---")
        print(b["pages_text"][page_num - 1][:1000])


def main():
    rows = load_manifest()

    groups = defaultdict(list)

    for row in rows:
        key = (
            row["company"].strip(),
            row["period"].strip()
        )
        groups[key].append(row)

    results = []

    print("=" * 65)
    print("DUPLICATE CANDIDATE INVESTIGATION")
    print("=" * 65)

    for (company, year), docs in sorted(groups.items()):

        if len(docs) < 2:
            continue

        print(f"\n{company} - {year}")

        # First group by document type
        by_type = defaultdict(list)

        for doc in docs:
            doc_type = normalize_doc_type(doc["doc_type"])
            by_type[doc_type].append(doc)

        for doc_type, same_type_docs in by_type.items():

            if len(same_type_docs) < 2:
                continue

            print(f"\n  Document type: {doc_type}")

            # Extract quarter and filing date
            candidates = []

            for doc in same_type_docs:
                info = extract_period_info(doc["doc_id"])
                candidates.append((doc, info))

            for i in range(len(candidates)):
                for j in range(i + 1, len(candidates)):

                    row_a, info_a = candidates[i]
                    row_b, info_b = candidates[j]

                    # Different known quarters: skip
                    if (
                        info_a["quarter"]
                        and info_b["quarter"]
                        and info_a["quarter"] != info_b["quarter"]
                    ):
                        print(
                            f"  SKIP: Different quarters - "
                            f"{row_a['doc_id']} / {row_b['doc_id']}"
                        )
                        continue

                    # Different known filing dates: flag for review
                    if (
                        info_a["filing_date"]
                        and info_b["filing_date"]
                        and info_a["filing_date"] != info_b["filing_date"]
                    ):
                        print(
                            f"  DATE REVIEW: Different filing dates - "
                            f"{row_a['doc_id']} / {row_b['doc_id']}"
                        )

                        results.append({
                            "company": company,
                            "year": year,
                            "document_a": row_a["doc_id"],
                            "document_b": row_b["doc_id"],
                            "document_type": doc_type,
                            "status": "DIFFERENT FILING DATES - REVIEW",
                            "similarity_percent": "",
                            "classification": "NOT COMPARED"
                        })
                        continue

                    # Compare only remaining candidates
                    path_a = PDF_DIR / f"{row_a['doc_id']}.pdf"
                    path_b = PDF_DIR / f"{row_b['doc_id']}.pdf"

                    if not path_a.exists() or not path_b.exists():
                        print("  MISSING PDF - skipped")
                        continue

                    try:
                        a = extract_pdf_info(path_a)
                        b = extract_pdf_info(path_b)


                        similarity, classification = compare_documents(a, b)
                        inspect_differences(a, b)

                        print(
                            f"  COMPARED: {a['file']} / {b['file']}"
                        )
                        print(f"  Similarity: {similarity:.2f}%")
                        print(f"  Result: {classification}")

                        results.append({
                            "company": company,
                            "year": year,
                            "document_a": a["file"],
                            "document_b": b["file"],
                            "document_type": doc_type,
                            "status": "COMPARED",
                            "similarity_percent": round(similarity, 2),
                            "classification": classification
                        })

                    except Exception as e:
                        print(f"  ERROR: {e}")

    if results:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)

        with OUTPUT.open(
            "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=results[0].keys()
            )
            writer.writeheader()
            writer.writerows(results)

    print("\n" + "=" * 65)
    print("INVESTIGATION FINISHED")
    print(f"Compared / reviewed pairs: {len(results)}")
    print(f"Report: {OUTPUT}")
    print("=" * 65)


if __name__ == "__main__":
    main()
