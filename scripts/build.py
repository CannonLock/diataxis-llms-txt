#!/usr/bin/env python3
"""Build llms.txt and llms-full.txt from the Diátaxis documentation source.

Reads the reStructuredText source in the `diataxis/` submodule
(https://github.com/evildmp/diataxis-documentation-framework), resolves the
page order from the Sphinx toctrees, converts each page to Markdown with
pandoc, and writes:

  llms.txt       — an index per the llms.txt spec (https://llmstxt.org):
                   title, summary, and a link list into diataxis.fr
  llms-full.txt  — the full concatenated content of every page

Both files embed the CC BY-SA 4.0 attribution notice and the exact source
commit they were built from, so output is deterministic for a given
submodule state and can be referenced by git hash.

Requires: python3, pandoc, git.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBMODULE = ROOT / "diataxis"
# The upstream repo keeps its Sphinx source under source/; fall back to the
# repo root in case that layout ever changes back.
SRC = SUBMODULE / "source" if (SUBMODULE / "source" / "index.rst").exists() else SUBMODULE
SITE = "https://diataxis.fr"
UPSTREAM = "https://github.com/evildmp/diataxis-documentation-framework"

TOCTREE_RE = re.compile(r"^(\s*)\.\.\s+toctree::\s*$")
ENTRY_TARGET_RE = re.compile(r"^.*<([^<>]+)>\s*$")


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"error: {' '.join(cmd)}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def submodule_sha() -> str:
    return run(["git", "-C", str(SUBMODULE), "rev-parse", "HEAD"]).strip()


def toctree_targets(rst_path: Path) -> list[str]:
    """Return document targets from every toctree directive in a file, in order."""
    targets: list[str] = []
    lines = rst_path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        match = TOCTREE_RE.match(lines[i])
        if not match:
            i += 1
            continue
        base_indent = len(match.group(1))
        i += 1
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent:
                break
            entry = line.strip()
            i += 1
            if entry.startswith(":"):  # toctree option, e.g. :maxdepth: 1
                continue
            entry_match = ENTRY_TARGET_RE.match(entry)
            target = entry_match.group(1) if entry_match else entry
            if target.startswith(("http://", "https://")):
                continue  # external toctree link
            targets.append(target)
    return targets


def collect_pages() -> list[str]:
    """Depth-first page order starting from index.rst, following toctrees."""
    ordered: list[str] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        path = SRC / f"{name}.rst"
        if not path.exists():
            print(f"warning: toctree entry '{name}' has no .rst file, skipping", file=sys.stderr)
            return
        ordered.append(name)
        for target in toctree_targets(path):
            visit(target)

    visit("index")
    if len(ordered) <= 1:
        print("error: no pages found via toctree; is the submodule checked out?", file=sys.stderr)
        sys.exit(1)
    return ordered


def rst_to_markdown(path: Path) -> str:
    md = run(["pandoc", "--from=rst", "--to=gfm", "--wrap=none", str(path)])
    # Collapse runs of blank lines left behind by skipped Sphinx directives.
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def page_url(name: str) -> str:
    return f"{SITE}/" if name == "index" else f"{SITE}/{name}/"


def extract_title(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("-", " ").title()


def extract_description(md: str) -> str:
    """First body paragraph, flattened to one line, links stripped."""
    in_body = False
    paragraph: list[str] = []
    for line in md.splitlines():
        if line.startswith("# ") and not in_body:
            in_body = True
            continue
        if not in_body:
            continue
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if stripped.startswith(("#", ">", "-", "*", "|", "!", "<")):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    text = " ".join(paragraph)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # [text](url) -> text
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > 200:
        text = text[:197].rsplit(" ", 1)[0] + "..."
    return text


def attribution(sha: str) -> str:
    return f"""<!--
Diátaxis — a systematic approach to technical documentation authoring.
Copyright © Daniele Procida. {SITE}

This file is an adaptation of the Diátaxis documentation, converted from
its reStructuredText source to Markdown and reformatted for consumption
by language models (llms.txt).

Licensed under the Creative Commons Attribution-ShareAlike 4.0
International License (CC BY-SA 4.0):
https://creativecommons.org/licenses/by-sa/4.0/

This adaptation is likewise licensed under CC BY-SA 4.0.

Modifications: converted from reStructuredText to Markdown, concatenated,
and reformatted; Sphinx-specific markup removed. Content otherwise
unaltered.

Built from source commit {sha} of
{UPSTREAM}
-->"""


def main() -> None:
    if not (SRC / "index.rst").exists():
        print(
            "error: diataxis submodule source not found (looked for "
            f"{SRC / 'index.rst'}). Run:\n"
            "  git submodule update --init",
            file=sys.stderr,
        )
        sys.exit(1)

    sha = submodule_sha()
    pages = collect_pages()

    index_entries: list[str] = []
    full_sections: list[str] = []

    for name in pages:
        md = rst_to_markdown(SRC / f"{name}.rst")
        title = extract_title(md, name)
        url = page_url(name)
        description = extract_description(md)
        suffix = f": {description}" if description else ""
        index_entries.append(f"- [{title}]({url}){suffix}")
        full_sections.append(f"{md}\n\nSource: {url}")

    header = attribution(sha)

    llms_txt = (
        f"{header}\n\n"
        f"# Diátaxis\n\n"
        f"> A systematic approach to technical documentation authoring. "
        f"Diátaxis identifies four kinds of documentation — tutorials, "
        f"how-to guides, reference and explanation — and places them in a "
        f"systematic relationship based on user needs.\n\n"
        f"The complete content of every page is available in a single file "
        f"at llms-full.txt alongside this one.\n\n"
        f"## Docs\n\n" + "\n".join(index_entries) + "\n"
    )

    llms_full_txt = (
        f"{header}\n\n" + "\n\n---\n\n".join(full_sections) + "\n"
    )

    (ROOT / "llms.txt").write_text(llms_txt, encoding="utf-8")
    (ROOT / "llms-full.txt").write_text(llms_full_txt, encoding="utf-8")
    print(f"Built llms.txt ({len(pages)} pages) and llms-full.txt from diataxis@{sha[:12]}")


if __name__ == "__main__":
    main()
