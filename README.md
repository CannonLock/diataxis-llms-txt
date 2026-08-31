# diataxis-llms-txt

An automatically maintained [llms.txt](https://llmstxt.org) rendering of the
[Diátaxis](https://diataxis.fr) documentation framework by Daniele Procida.

- **[`llms.txt`](./llms.txt)** — index of every Diátaxis page with a
  one-line summary and canonical link, per the llms.txt spec.
- **[`llms-full.txt`](./llms-full.txt)** — the complete content of every
  page, converted to Markdown and concatenated into a single file.

Both files are rebuilt automatically whenever the upstream source changes,
so a git commit hash of this repository pins an exact snapshot of the
content. To reference a stable version, link to the file at a specific
commit, e.g.:

```
https://raw.githubusercontent.com/<owner>/diataxis-llms-txt/<commit-sha>/llms-full.txt
```

## How it works

- The Diátaxis reStructuredText source lives in the `diataxis/` git
  submodule, tracking
  [evildmp/diataxis-documentation-framework](https://github.com/evildmp/diataxis-documentation-framework).
- A GitHub Actions workflow ([`.github/workflows/update.yml`](.github/workflows/update.yml))
  runs daily. It fast-forwards the submodule to the latest upstream commit,
  runs [`scripts/build.py`](scripts/build.py), and commits the result if
  anything changed. Each commit message records the upstream commit it was
  built from.
- The build script resolves page order from the Sphinx toctrees, converts
  each page with pandoc, and embeds the attribution notice and exact
  upstream commit SHA in both output files.

## Building locally

Requires Python 3.10+, pandoc, and git.

```sh
git submodule update --init
python scripts/build.py
```

## License and attribution

The Diátaxis content is copyright © Daniele Procida and is licensed under
the [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/)
(CC BY-SA 4.0). See [LICENSE](./LICENSE) for the full text.

The files in this repository — including `llms.txt` and `llms-full.txt`,
which are Adapted Material derived from the Diátaxis source (converted
from reStructuredText to Markdown, concatenated, and reformatted for
consumption by language models) — are likewise made available under
**CC BY-SA 4.0**, as required by the ShareAlike condition. The build
tooling in this repository is available under the same license.

This project is not affiliated with, sponsored, or endorsed by Daniele
Procida or the Diátaxis project.

Original work: <https://diataxis.fr> ·
Source: <https://github.com/evildmp/diataxis-documentation-framework>
