from pathlib import Path
from collections import Counter, defaultdict
import csv
import re

from pypdf import PdfReader
from pypdf.errors import DependencyError, PdfReadError

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
MANIFEST = ROOT / "data" / "manifest.csv"

YEAR_RE = re.compile(r"(?:19|20)\d{2}")


def load_manifest(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    if not PDF_DIR.exists():
        print(f"Folder not found: {PDF_DIR}")
        return
    if not MANIFEST.exists():
        print(f"Manifest not found: {MANIFEST}")
        return

    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    rows = load_manifest(MANIFEST)

    print("=" * 60)
    print("1) TOTAL PDFs")
    print("=" * 60)
    print(f"PDFs in data/pdfs: {len(pdfs)}")
    print(f"Rows in manifest.csv: {len(rows)}")
    print()

    print("=" * 60)
    print("2) ALL FILENAMES")
    print("=" * 60)
    for i, pdf in enumerate(pdfs, start=1):
        print(f"{i:3}. {pdf.name}")
    print()

    print("=" * 60)
    print("3) YEARS")
    print("=" * 60)

    filename_years = []
    no_year = []
    for pdf in pdfs:
        found = YEAR_RE.findall(pdf.name)
        if found:
            filename_years.append(found[0])
        else:
            no_year.append(pdf.name)

    year_counts = Counter(filename_years)
    print("Years from PDF filenames:")
    print(f"  Unique years: {sorted(year_counts)}")
    for year in sorted(year_counts):
        print(f"  {year}: {year_counts[year]} PDFs")
    if no_year:
        print("  No year in filename:")
        for name in no_year:
            print(f"    - {name}")

    period_counts = Counter(row["period"].strip() for row in rows if row.get("period"))
    print("\nYears from manifest period column:")
    print(f"  Unique years: {sorted(period_counts)}")
    for year in sorted(period_counts):
        print(f"  {year}: {period_counts[year]} docs")
    print()

    print("=" * 60)
    print("4) MISSING / DUPLICATE CHECK")
    print("=" * 60)

    name_counts = Counter(p.name for p in pdfs)
    duplicate_names = {name: n for name, n in name_counts.items() if n > 1}
    if duplicate_names:
        print("Duplicate filenames on disk:")
        for name, n in duplicate_names.items():
            print(f"  {name} x {n}")
    else:
        print("Duplicate filenames on disk: none")

    doc_ids = [row["doc_id"].strip() for row in rows]
    id_counts = Counter(doc_ids)
    duplicate_ids = {doc_id: n for doc_id, n in id_counts.items() if n > 1}
    if duplicate_ids:
        print("Duplicate doc_id in manifest:")
        for doc_id, n in duplicate_ids.items():
            print(f"  {doc_id} x {n}")
    else:
        print("Duplicate doc_id in manifest: none")

    pdf_stems = {p.stem for p in pdfs}
    manifest_ids = set(doc_ids)
    missing_pdfs = sorted(manifest_ids - pdf_stems)
    extra_pdfs = sorted(pdf_stems - manifest_ids)

    print(f"Manifest rows with no matching PDF: {len(missing_pdfs)}")
    for doc_id in missing_pdfs:
        print(f"  - {doc_id}")
    print(f"PDFs with no matching manifest row: {len(extra_pdfs)}")
    for stem in extra_pdfs:
        print(f"  - {stem}")

    if year_counts:
        min_year = min(int(y) for y in year_counts)
        max_year = max(int(y) for y in year_counts)
        present = {int(y) for y in year_counts}
        missing_years = [y for y in range(min_year, max_year + 1) if y not in present]
        print(f"Year range in filenames: {min_year} to {max_year}")
        if missing_years:
            print(f"Missing years in that range: {missing_years}")
        else:
            print("No missing years in that range")

    TYPE_LABELS = {
        "10k": "10-K (annual report)",
        "10k_annualreport": "10-K / annual report",
        "10q": "10-Q (quarterly report)",
        "8k": "8-K (current report)",
        "Earnings": "Earnings release",
    }

    print("\nDocument types (10-K, 10-Q, 8-K, Earnings):")
    type_counts = Counter(row["doc_type"] for row in rows)
    for doc_type, n in sorted(type_counts.items()):
        label = TYPE_LABELS.get(doc_type, doc_type)
        print(f"  {label}: {n}")

    print("\nPer-company duplicate years (same company + year, more than 1 doc):")
    by_company_year = defaultdict(list)
    for row in rows:
        by_company_year[(row["company"], row["period"])].append(row)

    dup_company_years = sorted(
        ((key, docs) for key, docs in by_company_year.items() if len(docs) > 1),
        key=lambda item: (item[0][0], item[0][1]),
    )
    if dup_company_years:
        for (company, year), docs in dup_company_years:
            print(f"  {company} {year}: {len(docs)} docs")
            for row in docs:
                label = TYPE_LABELS.get(row["doc_type"], row["doc_type"])
                print(f"      {row['doc_id']}  [{label}]")
    else:
        print("  none")
    print()

    print("\n" + "=" * 60)
    print("5) PDF READABILITY & ENCRYPTION CHECK")
    print("=" * 60)

    ok = 0
    encrypted = []
    needs_crypto = []
    bad = []

    for pdf in pdfs:
        try:
            reader = PdfReader(str(pdf))

            if reader.is_encrypted:
                encrypted.append(pdf.name)

            _ = len(reader.pages)
            ok += 1

        except DependencyError as e:
            needs_crypto.append((pdf.name, str(e)))

        except (PdfReadError, OSError, ValueError) as e:
            bad.append((pdf.name, str(e)))

    print(f"Readable PDFs: {ok}/{len(pdfs)}")

    print(f"\nEncrypted PDFs: {len(encrypted)}")
    for name in encrypted:
        print(f"  - {name}")

    print(f"\nPDFs requiring cryptography dependency: {len(needs_crypto)}")
    for name, err in needs_crypto:
        print(f"  - {name}: {err}")

    print(f"\nPossibly corrupt / unreadable PDFs: {len(bad)}")
    for name, err in bad:
        print(f"  - {name}: {err}")


if __name__ == "__main__":
    main()
