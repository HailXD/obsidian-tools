from datetime import date, timedelta
from pathlib import Path

START_DATE = date(2026, 3, 31)
END_DATE = date(2026, 5, 1)
OUTPUT_FILE = Path("2026-03-29_to_2026-05-01.txt")
SEPARATOR = "\n===\n"


def iter_dates():
    current = START_DATE
    while current <= END_DATE:
        yield current
        current += timedelta(days=1)


def read_entry(current):
    path = Path(f"{current:%Y-%m-%d}.md")
    if not path.is_file():
        return "", path.name
    content = path.read_text(encoding="utf-8").rstrip()
    return f"{current:%Y-%m-%d}\n{content}", ""


def main():
    entries = []
    missing = []

    for current in iter_dates():
        entry, absent = read_entry(current)
        if absent:
            missing.append(absent)
            continue
        entries.append(entry)

    OUTPUT_FILE.write_text(SEPARATOR.join(entries), encoding="utf-8")

    print(f"Wrote {len(entries)} entries to {OUTPUT_FILE}")
    if missing:
        print(f"Skipped {len(missing)} missing files:")
        for name in missing:
            print(name)


if __name__ == "__main__":
    main()
