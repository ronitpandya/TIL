#!/usr/bin/env python3
"""Regenerate README.md from all dated entries under YYYY/MM-Month/*.md.

Reads simple YAML front matter (date, tags) from each entry and builds:
  - a reverse-chronological log
  - an index grouped by tag

Run via ./til.sh index, or automatically from the pre-commit hook.
"""
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YEAR_DIR_RE = re.compile(r"^\d{4}$")
ENTRY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


def parse_front_matter(text):
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 4:]

    meta = {"date": "", "tags": []}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("date:"):
            meta["date"] = line.split(":", 1)[1].strip()
        elif line.startswith("tags:"):
            rest = line.split(":", 1)[1].strip()
            if rest.startswith("["):
                inner = rest.strip("[]").strip()
                if inner:
                    meta["tags"] = [t.strip().strip('"\'') for t in inner.split(",") if t.strip()]
            else:
                tags = []
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith("-"):
                    tags.append(lines[j].strip().lstrip("-").strip().strip('"\''))
                    j += 1
                meta["tags"] = tags
                i = j - 1
        i += 1
    return meta, body


def first_heading_or_snippet(body):
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("## "):
            heading = line[3:].strip()
        if line and not line.startswith("#") and not line.startswith("-") and line != "":
            return line[:120]
    return ""


def collect_entries():
    entries = []
    for year in sorted(os.listdir(ROOT)):
        year_path = os.path.join(ROOT, year)
        if not YEAR_DIR_RE.match(year) or not os.path.isdir(year_path):
            continue
        for month in sorted(os.listdir(year_path)):
            month_path = os.path.join(year_path, month)
            if not os.path.isdir(month_path):
                continue
            for fname in sorted(os.listdir(month_path)):
                if not ENTRY_RE.match(fname):
                    continue
                fpath = os.path.join(month_path, fname)
                with open(fpath, encoding="utf-8") as f:
                    text = f.read()
                meta, body = parse_front_matter(text)
                date = meta.get("date") or fname[:-3]
                rel = os.path.relpath(fpath, ROOT)
                entries.append({
                    "date": date,
                    "tags": meta.get("tags", []),
                    "path": rel,
                    "snippet": first_heading_or_snippet(body),
                })
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def build_readme(entries):
    total = len(entries)
    lines = []
    lines.append("# TIL — Today I Learned")
    lines.append("")
    lines.append("A daily log of things I learn. One entry per day, organized by date, tagged by topic.")
    lines.append("")
    lines.append(f"**{total} entries** so far.")
    lines.append("")
    lines.append("## How this works")
    lines.append("")
    lines.append("```")
    lines.append("./til.sh new              # scaffold today's entry from the template")
    lines.append("./til.sh index            # regenerate this README (also runs automatically on commit)")
    lines.append("```")
    lines.append("")

    lines.append("## Log")
    lines.append("")
    if not entries:
        lines.append("_No entries yet — run `./til.sh new` to add the first one._")
    else:
        for e in entries:
            tag_str = " ".join(f"`{t}`" for t in e["tags"])
            snippet = f" — {e['snippet']}" if e["snippet"] else ""
            lines.append(f"- **[{e['date']}]({e['path']})** {tag_str}{snippet}")
    lines.append("")

    by_tag = defaultdict(list)
    for e in entries:
        for t in e["tags"]:
            by_tag[t].append(e)
    if by_tag:
        lines.append("## By topic")
        lines.append("")
        for tag in sorted(by_tag):
            lines.append(f"### {tag}")
            lines.append("")
            for e in by_tag[tag]:
                lines.append(f"- [{e['date']}]({e['path']})")
            lines.append("")

    lines.append("## Projects")
    lines.append("")
    lines.append("Bigger hands-on learning projects live in [`projects/`](projects/).")
    lines.append("")

    return "\n".join(lines) + "\n"


def main():
    entries = collect_entries()
    readme = build_readme(entries)
    out_path = os.path.join(ROOT, "README.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"README.md regenerated ({len(entries)} entries).")


if __name__ == "__main__":
    sys.exit(main())
