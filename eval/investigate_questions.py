
from pathlib import Path
from collections import Counter
import csv
import json

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent.parent

QUESTIONS_FILE = ROOT / "data" / "dev_questions.jsonl"
MANIFEST_FILE = ROOT / "data" / "manifest.csv"
PDF_DIR = ROOT / "data" / "pdfs"


def load_questions():
    with QUESTIONS_FILE.open(encoding="utf-8") as f:
        return [
            json.loads(line)
            for line in f
            if line.strip()
        ]


def load_manifest():
    with MANIFEST_FILE.open(
        newline="", encoding="utf-8-sig"
    ) as f:
        return list(csv.DictReader(f))


def main():
    questions = load_questions()
    manifest = load_manifest()

    print("=" * 60)
    print("1) QUESTION DATASET OVERVIEW")
    print("=" * 60)

    print(f"Total questions: {len(questions)}")
    print(
        "Unique documents:",
        len({q["doc_id"] for q in questions})
    )

    print("\nQuestions per role:")
    for role, count in Counter(
        q["role"] for q in questions
    ).items():
        print(f"  {role}: {count}")

    print("\nMulti-page questions:")
    multi_page = [
        q for q in questions
        if len(q.get("pages", [])) > 1
    ]
    print(len(multi_page))

    print("\n" + "=" * 60)
    print("2) MANIFEST VALIDATION")
    print("=" * 60)

    manifest_by_id = {
        row["doc_id"].strip(): row
        for row in manifest
    }

    question_ids = {q["doc_id"] for q in questions}

    missing = sorted(
        question_ids - set(manifest_by_id)
    )

    print(f"Matched documents: {len(question_ids) - len(missing)}")
    print(f"Missing documents: {len(missing)}")

    for doc_id in missing:
        print(" ", doc_id)

    print("\n" + "=" * 60)
    print("3) ROLE-TO-DESK VALIDATION")
    print("=" * 60)

    for role in sorted({q["role"] for q in questions}):
        desks = Counter(
            manifest_by_id[q["doc_id"]]["desk"].strip()
            for q in questions
            if q["role"] == role
            and q["doc_id"] in manifest_by_id
        )

        print(f"\n{role}:")
        for desk, count in desks.items():
            print(f"  {desk}: {count}")

    print("\n" + "=" * 60)
    print("4) ACTUAL PDF PAGE VALIDATION")
    print("=" * 60)

    # Case-insensitive PDF filename lookup
    pdf_files = {
        path.stem.casefold(): path
        for path in PDF_DIR.glob("*.pdf")
    }

    # Cache page counts to avoid reopening the same PDF
    page_counts = {}

    invalid_pages = []
    missing_pdfs = []

    for q in questions:
        doc_id = q["doc_id"]

        # Check that the document exists in the manifest
        if doc_id not in manifest_by_id:
            continue

        pdf_path = pdf_files.get(doc_id.casefold())

        if pdf_path is None:
            missing_pdfs.append((q["id"], doc_id))
            continue

        # Read each PDF only once
        if pdf_path not in page_counts:
            reader = PdfReader(str(pdf_path))
            page_counts[pdf_path] = len(reader.pages)

        total_pages = page_counts[pdf_path]
        pages = q.get("pages", [])

        if not pages:
            invalid_pages.append({
                "question_id": q["id"],
                "doc_id": doc_id,
                "problem": "No page references"
            })
            continue

        for page in pages:
            if (
                not isinstance(page, int)
                or isinstance(page, bool)
                or page < 1
                or page > total_pages
            ):
                invalid_pages.append({
                    "question_id": q["id"],
                    "doc_id": doc_id,
                    "requested_page": page,
                    "total_pdf_pages": total_pages
                })

    print(f"PDFs checked: {len(page_counts)}")
    print(f"Missing PDFs: {len(missing_pdfs)}")
    print(f"Invalid page references: {len(invalid_pages)}")

    for item in missing_pdfs:
        print("Missing PDF:", item)

    for item in invalid_pages:
        print("Invalid page:", item)

    print("\nQuestion investigation completed.")


if __name__ == "__main__":
    main()
