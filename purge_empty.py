import pathlib

for p in pathlib.Path(".").iterdir():
    if p.is_file() and p.stat().st_size <= 34:
        if p.name == "Template.md" or not p.name.endswith(".md"):
            continue
        print(f"Deleting {p} ({p.stat().st_size} bytes)")
        p.unlink()
