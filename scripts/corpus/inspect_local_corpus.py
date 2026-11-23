"""Validate an offline staging corpus without database or network access."""
import argparse
import hashlib
import json
from pathlib import Path

def load_rows(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)

def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def validate(root):
    root = Path(root)
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    source_pages = {}
    total_pages = 0
    for source in catalog["sources"]:
        records = list(load_rows(root / source["pages_path"]))
        assert len(records) == source["pdf_leaves"], source["id"]
        assert [r["pdf_leaf"] for r in records] == list(range(1, len(records) + 1))
        for record in records:
            assert record["source_id"] == source["id"]
            assert digest(record["text"]) == record["text_sha256"]
            assert record["verification_status"] == "not_checked"
        source_pages[source["id"]] = {r["pdf_leaf"]: r["text"] for r in records}
        total_pages += len(records)
    ids = set()
    used_spans = {}
    fragments = 0
    for work in catalog["works"]:
        assert work["local_work_id"] not in ids
        ids.add(work["local_work_id"])
        assert not work["runtime_import"] and not work["primary_quote_ready"]
        records = list(load_rows(root / work["pages_path"]))
        assert len(records) == work["fragment_count"]
        assert sum(len(r["text"]) for r in records) == work["characters"]
        for record in records:
            assert record["source_id"] == work["source_id"]
            assert record["local_work_id"] == work["local_work_id"]
            full = source_pages[record["source_id"]][record["pdf_leaf"]]
            a, b = record["start_char"], record["end_char"]
            assert 0 <= a < b <= len(full)
            assert full[a:b] == record["text"]
            assert digest(record["text"]) == record["text_sha256"]
            key = (record["source_id"], record["pdf_leaf"])
            for previous_a, previous_b in used_spans.setdefault(key, []):
                assert b <= previous_a or a >= previous_b, (key, "overlapping works")
            used_spans[key].append((a, b))
        fragments += len(records)
    return {"status": "ok", "sources": len(source_pages), "pdf_leaves": total_pages,
            "works": len(ids), "work_page_fragments": fragments,
            "database_access": False, "network_access": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.root), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
