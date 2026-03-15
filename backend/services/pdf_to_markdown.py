import sys
from pathlib import Path
import pymupdf4llm

DOCS_DIR     = Path("/app/data/docs")
MARKDOWN_DIR = Path("/app/data/markdown")


def convert_pdf(pdf_path: Path) -> Path:
    print(f"📄 Converting: {pdf_path.relative_to(DOCS_DIR)}")
    md_text  = pymupdf4llm.to_markdown(str(pdf_path))
    # Prefix with subfolder name to avoid name conflicts (e.g. fire__ed6230.md)
    subfolder = pdf_path.parent.name if pdf_path.parent != DOCS_DIR else ""
    stem      = f"{subfolder}__{pdf_path.stem}" if subfolder else pdf_path.stem
    out_path  = MARKDOWN_DIR / (stem + ".md")
    out_path.write_text(md_text, encoding="utf-8")
    print(f"   ✅ {out_path.name}  ({len(md_text)/1024:.1f} KB)")
    return out_path


def main():
    MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(DOCS_DIR.rglob("*.pdf"))  # rglob = recursive, finds PDFs in subfolders

    if not pdfs:
        print(f"⚠️  No PDFs found in {DOCS_DIR}")
        sys.exit(0)

    print(f"\n🔍 Found {len(pdfs)} PDF(s)\n")
    ok, fail = [], []

    for pdf in pdfs:
        try:
            convert_pdf(pdf)
            ok.append(pdf.name)
        except Exception as e:
            print(f"   ❌ {pdf.name} — {e}")
            fail.append(pdf.name)

    print(f"\n✅ Converted: {len(ok)}  ❌ Failed: {len(fail)}")
    print("Next: python services/ingest.py")


if __name__ == "__main__":
    main()