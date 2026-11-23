"""Literal offline search over extracted works, not semantic search or AI generation."""
import argparse
import json
from pathlib import Path

def search(root, query, author=None, work=None, limit=5):
    if not query.strip() or limit < 1:
        raise ValueError("A nonempty query and positive limit are required")
    root = Path(root)
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    found = []
    for item in catalog["works"]:
        if author and item["author"] != author:
            continue
        if work and item["local_work_id"] != work:
            continue
        with (root / item["pages_path"]).open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                position = row["text"].lower().find(query.lower())
                if position < 0:
                    continue
                snippet = row["text"][max(0, position - 140):position + len(query) + 230]
                found.append({"title": item["title"], "local_work_id": item["local_work_id"],
                    "source_id": row["source_id"], "pdf_leaf": row["pdf_leaf"],
                    "char_in_extracted_page": row["start_char"] + position,
                    "snippet": snippet, "verification_status": item["verification_status"]})
                if len(found) >= limit:
                    return found
    return found

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--author", choices=["cusanus", "frank"])
    parser.add_argument("--work", help="Local staging work ID, not an application passage ID")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(search(args.root, args.query, args.author, args.work, args.limit),
                     ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
