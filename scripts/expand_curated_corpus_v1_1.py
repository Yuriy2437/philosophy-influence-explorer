"""Append a reviewable Kant/Mill corpus slice. Dry run by default; --apply writes CSVs."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
from pathlib import Path

from philosophy_influence_explorer.ingestion.validators import validate_curated_corpus

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "curated"

A = ('Autonomy of the will is that property of it by which it is a law to itself '
     '(independently of any property of the objects of volition). The principle of autonomy then is: '
     '"Always so to choose that the same volition shall comprehend the maxims of our choice as a universal law."')
B = ('Accordingly the practical imperative will be as follows: So act as to treat humanity, '
     'whether in thine own person or in that of any other, in every case as an end withal, never as means only.')
C = ('That the only purpose for which power can be rightfully exercised over any member of a '
     'civilised community, against his will, is to prevent harm to others.')
D = ('Having said that Individuality is the same thing with development, and that it is only the '
     'cultivation of individuality which produces, or can produce, well-developed human beings, '
     'I might here close the argument: for what more or better can be said of any condition of '
     'human affairs, than that it brings human beings themselves nearer to the best thing they '
     'can be? or what worse can be said of any obstruction to good, than that it prevents this?')


def row(*values: str) -> tuple[str, ...]:
    return values


ROWS: dict[str, list[tuple[str, ...]]] = {
    "philosophers.csv": [
        row("philosopher:kant", "Immanuel Kant", "Immanuel Kant", "Иммануил Кант", "Immanuel Kant", "1724", "1804", "German philosopher; author of the Groundwork of the Metaphysics of Morals.", "candidate"),
        row("philosopher:mill", "John Stuart Mill", "John Stuart Mill", "Джон Стюарт Милль", "John Stuart Mill", "1806", "1873", "British philosopher; author of On Liberty.", "candidate"),
    ],
    "works.csv": [
        row("work:kant:groundwork", "philosopher:kant", "Grundlegung zur Metaphysik der Sitten", "Groundwork of the Metaphysics of Morals", "Основоположение к метафизике нравов", "Grundlegung zur Metaphysik der Sitten", "de", "1785", "primary_text", "false", "source:kant:gutenberg-5682", "public_domain_us", "candidate"),
        row("work:mill:on-liberty", "philosopher:mill", "On Liberty", "On Liberty", "О свободе", "Über die Freiheit", "en", "1859", "primary_text", "false", "source:mill:gutenberg-34901", "public_domain_us", "candidate"),
    ],
    "sources.csv": [
        row("source:kant:gutenberg-5682", "kant-gutenberg-5682", "Fundamental Principles of the Metaphysic of Morals", "Immanuel Kant; translated by Thomas Kingsmill Abbott", "1785", "digital_translation", "https://www.gutenberg.org/ebooks/5682", "public_domain_us", "English Abbott translation on Project Gutenberg; check exact wording against ebook 5682 and reuse rights outside the US before publication.", "candidate"),
        row("source:mill:gutenberg-34901", "mill-gutenberg-34901", "On Liberty", "John Stuart Mill", "1859", "digital_edition", "https://www.gutenberg.org/ebooks/34901", "public_domain_us", "Project Gutenberg ebook 34901; verify exact wording and reuse rights outside the US before publication.", "candidate"),
    ],
    "concepts.csv": [
        row("concept:autonomy", "autonomy", "autonomy", "автономия", "Autonomie", "The will considered as giving law to itself in Kant's Groundwork.", "ethics", "candidate"),
        row("concept:moral-law", "moral law", "moral law", "моральный закон", "moralisches Gesetz", "The universal-law aspect of Kant's account of moral willing.", "ethics", "candidate"),
        row("concept:humanity", "humanity", "humanity", "человечество", "Menschheit", "Humanity as named in Kant's practical imperative; not a synonym for biological species alone.", "ethics", "candidate"),
        row("concept:end-in-itself", "end in itself", "end in itself", "цель сама по себе", "Zweck an sich selbst", "The end-status Kant ascribes to humanity in the practical imperative.", "ethics", "candidate"),
        row("concept:liberty", "liberty", "liberty", "свобода", "Freiheit", "Individual liberty as treated in Mill's On Liberty.", "political_philosophy", "candidate"),
        row("concept:harm-principle", "harm principle", "harm principle", "принцип вреда", "Schadensprinzip", "Editorial label for Mill's criterion of preventing harm to others.", "political_philosophy", "candidate"),
        row("concept:individuality", "individuality", "individuality", "индивидуальность", "Individualität", "Cultivation and development of individuality in Mill's On Liberty.", "political_philosophy", "candidate"),
    ],
    "passages.csv": [
        row("passage:kant:groundwork:2:autonomy:en", "work:kant:groundwork", "source:kant:gutenberg-5682", "en", A, "primary_quote", "true", "false", "false", "", "Second Section; autonomy of the will", "2", "Fundamental Principles of the Metaphysic of Morals, Second Section (Abbott translation)", "public_domain_us", "candidate"),
        row("passage:kant:groundwork:2:humanity:en", "work:kant:groundwork", "source:kant:gutenberg-5682", "en", B, "primary_quote", "true", "false", "false", "", "Second Section; practical imperative", "2", "Fundamental Principles of the Metaphysic of Morals, Second Section (Abbott translation)", "public_domain_us", "candidate"),
        row("passage:mill:on-liberty:1:harm:en", "work:mill:on-liberty", "source:mill:gutenberg-34901", "en", C, "primary_quote", "true", "false", "false", "", "Chapter I; Introductory", "1", "On Liberty, Chapter I", "public_domain_us", "candidate"),
        row("passage:mill:on-liberty:3:individuality:en", "work:mill:on-liberty", "source:mill:gutenberg-34901", "en", D, "primary_quote", "true", "false", "false", "", "Chapter III; Of Individuality", "3", "On Liberty, Chapter III", "public_domain_us", "candidate"),
    ],
}


def relation(id: str, kind: str, origin: str, target: str, properties: dict[str, object]) -> tuple[str, ...]:
    return row(id, kind, origin, target, json.dumps(properties, ensure_ascii=False, separators=(",", ":")), "candidate")


RELATIONS = [
    relation("relation:kant:wrote:groundwork", "WROTE", "philosopher:kant", "work:kant:groundwork", {"role": "author", "certainty": 1.0}),
    relation("relation:mill:wrote:on-liberty", "WROTE", "philosopher:mill", "work:mill:on-liberty", {"role": "author", "certainty": 1.0}),
]
for index, (work, passage, concepts) in enumerate([
    ("work:kant:groundwork", "passage:kant:groundwork:2:autonomy:en", ["autonomy", "moral-law"]),
    ("work:kant:groundwork", "passage:kant:groundwork:2:humanity:en", ["humanity", "end-in-itself"]),
    ("work:mill:on-liberty", "passage:mill:on-liberty:1:harm:en", ["liberty", "harm-principle"]),
    ("work:mill:on-liberty", "passage:mill:on-liberty:3:individuality:en", ["individuality", "liberty"]),
], start=1):
    RELATIONS.append(relation(f"relation:v1-1:has-passage:{index}", "HAS_PASSAGE", work, passage, {"order": index}))
    for concept in concepts:
        RELATIONS.append(relation(f"relation:v1-1:discusses:{index}:{concept}", "DISCUSSES", passage, f"concept:{concept}", {"extraction_method": "curated", "confidence": 0.9, "review_status": "candidate"}))
ROWS["relations.csv"] = RELATIONS


def append_rows(path: Path, new_rows: list[tuple[str, ...]]) -> None:
    with path.open(encoding="utf-8", newline="") as source:
        existing = list(csv.reader(source))
    if not existing:
        raise ValueError(f"No header in {path}")
    width = len(existing[0])
    if any(len(record) != width for record in new_rows):
        raise ValueError(f"Column count mismatch: {path.name}")
    current_ids = {record[0] for record in existing[1:]}
    new_ids = {record[0] for record in new_rows}
    if len(new_ids) != len(new_rows) or current_ids & new_ids:
        raise ValueError(f"Duplicate IDs in {path.name}: {current_ids & new_ids}")
    with path.open("a", encoding="utf-8", newline="") as target:
        if path.stat().st_size and path.read_bytes()[-1:] not in (b"\n", b"\r"):
            target.write("\n")
        csv.writer(target, lineterminator="\n").writerows(new_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Append validated additions to actual CSV files")
    args = parser.parse_args()
    before = validate_curated_corpus(CORPUS)
    with tempfile.TemporaryDirectory() as temporary:
        staged = Path(temporary)
        for filename, new_rows in ROWS.items():
            shutil.copy2(CORPUS / filename, staged / filename)
            append_rows(staged / filename, new_rows)
        after = validate_curated_corpus(staged)
        counts = {name: (len(before[name]), len(after[name])) for name in before}
        print("Validated corpus counts (before, after):", counts)
        if not args.apply:
            print("Dry run only; no project files changed.")
            return
        for filename, new_rows in ROWS.items():
            append_rows(CORPUS / filename, new_rows)
        print("Appended CSV rows; Neo4j was not changed. Review git diff before seeding.")


if __name__ == "__main__":
    main()
