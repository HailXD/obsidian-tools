from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(?:-[a-z0-9]+)?\.md$")
TASK_PATTERN = re.compile(r"^\s*-\s*\[[ xX]\]", re.MULTILINE)
TASKS_HEADER = "## Tasks"
NOTES_HEADER = "## Notes"
ROOT = Path(".")


@dataclass
class Entry:
    day: date
    name: str
    path: Path
    task_count: int
    notes_length: int
    tasks_text: str
    notes_text: str
    content: str


def find_section(text, header, fallback):
    parts = re.split(r"(^##\s+.+$)", text, flags=re.MULTILINE)
    for index in range(1, len(parts), 2):
        if parts[index].strip() != header:
            continue
        lines = parts[index + 1].strip().splitlines()
        if lines and lines[0].strip("- ").strip() == "":
            lines = lines[1:]
        return "\n".join(lines).strip()
    return fallback


def parse_day(name):
    stem = name.split(".md")[0]
    year, month, day = stem.split("-")[:3]
    return date.fromisoformat(f"{year}-{month}-{day}")


def parse_entry(path):
    text = path.read_text(encoding="utf-8").strip()
    tasks_text = find_section(text, TASKS_HEADER, text)
    notes_text = find_section(text, NOTES_HEADER, "")
    return Entry(
        day=parse_day(path.name),
        name=path.name,
        path=path,
        task_count=len(TASK_PATTERN.findall(tasks_text)),
        notes_length=len(notes_text),
        tasks_text=tasks_text,
        notes_text=notes_text,
        content=text,
    )


def load_entries():
    entries = []
    for path in sorted(ROOT.iterdir()):
        if not path.is_file() or not DATE_PATTERN.match(path.name):
            continue
        try:
            entries.append(parse_entry(path))
        except ValueError:
            continue
    return entries
