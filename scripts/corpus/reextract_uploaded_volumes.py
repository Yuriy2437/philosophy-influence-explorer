"""Re-extract the three uploaded PDFs with Poppler; never overwrites a destination."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Destination already exists; choose a new directory")
    executable = shutil.which("pdftotext")
    if not executable:
        raise SystemExit("Poppler pdftotext must be installed and available on PATH")
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    checked = []
    for source in catalog["sources"]:
        path = args.source_dir / source["original_filename"]
        if not path.is_file():
            raise SystemExit(f"Missing source: {path.name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["original_sha256"]:
            raise SystemExit(f"Source checksum mismatch: {path.name}")
        checked.append((source, path))
    for source, path in checked:
        data = subprocess.run([executable, "-enc", "UTF-8", "-layout", str(path), "-"],
                              capture_output=True, check=True).stdout.decode("utf-8")
        pages = data.split("\f")
        if pages[-1] == "":
            pages.pop()
        if len(pages) != source["pdf_leaves"]:
            raise SystemExit("Unexpected page count; stop and inspect extraction")
        destination = args.output / source["id"]
        destination.mkdir(parents=True)
        rows = [{"pdf_leaf": i, "text": text,
                 "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
                for i, text in enumerate(pages, 1)]
        (destination / "pages.jsonl").write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8")
    print("Extracted into a new directory. Different Poppler versions may change offsets.")
    print("Do not reuse old character spans until page text hashes have been compared.")

if __name__ == "__main__":
    main()
