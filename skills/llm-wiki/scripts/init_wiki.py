#!/usr/bin/env python3
"""Initialize an LLM Wiki knowledge base structure."""

import argparse
import os
from pathlib import Path
from datetime import date

def create_wiki(base_path: str, name: str) -> None:
    """Create the LLM Wiki directory structure."""
    base = Path(base_path)

    # Create directories
    dirs = [
        base / "raw" / "assets",
        base / "wiki" / "sources",
        base / "wiki" / "concepts",
        base / "wiki" / "entities",
        base / "wiki" / "queries",
        base / "wiki" / "outputs" / "slides",
        base / "wiki" / "outputs" / "charts",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created: {d}")

    # Create CLAUDE.md schema
    schema = base / "CLAUDE.md"
    if not schema.exists():
        schema.write_text(get_schema_template(name))
        print(f"Created: {schema}")

    # Create wiki/index.md
    index = base / "wiki" / "index.md"
    if not index.exists():
        index.write_text(f"""# Wiki Index

Master catalog of all pages in this knowledge base.

---

## Overview

- [[wiki/overview]] — High-level synthesis

## Sources

| Page | Summary |
|------|---------|

## Concepts

| Page | Summary |
|------|---------|

## Entities

| Page | Type | Summary |
|------|------|---------|

---

## Statistics

- **Sources**: 0
- **Concepts**: 0
- **Entities**: 0
- **Last updated**: {date.today().isoformat()}
""")
        print(f"Created: {index}")

    # Create wiki/log.md
    log = base / "wiki" / "log.md"
    if not log.exists():
        log.write_text(f"""# Activity Log

Chronological record of wiki operations.

---

## [{date.today().isoformat()}] init | Wiki Created
- Created directory structure
- Initialized index.md, log.md, overview.md
""")
        print(f"Created: {log}")

    # Create wiki/overview.md
    overview = base / "wiki" / "overview.md"
    if not overview.exists():
        overview.write_text(f"""# {name} — Knowledge Base Overview

This knowledge base covers [describe topic].

## Core Topics

[To be filled as sources are ingested]

## Key Concepts

| Concept | Description |
|---------|-------------|

## Key Entities

| Entity | Type | Description |
|--------|------|-------------|

## Current State

- **Sources ingested**: 0
- **Last updated**: {date.today().isoformat()}
- **Coverage**: [describe coverage]
- **Gaps**: [identify gaps]
""")
        print(f"Created: {overview}")

    # Create wiki/health.md
    health = base / "wiki" / "health.md"
    if not health.exists():
        health.write_text("""# Wiki Health Report
Last checked: Never

Run `lint wiki` to populate this report.

## Orphaned Pages
- (none yet)

## Missing Pages
- (none yet)

## Stale Sources
- (none yet)

## Suggested Articles
- (none yet)

## Inconsistencies
- (none yet)

## Action Items
- [ ] Run initial lint after first ingest
""")
        print(f"Created: {health}")

    print(f"\n✅ LLM Wiki initialized at: {base}")
    print("\nNext steps:")
    print("1. Add source documents to raw/")
    print("2. Ask Claude to ingest the sources")


def get_schema_template(name: str) -> str:
    """Return the CLAUDE.md schema template."""
    return f"""# LLM Wiki Schema — {name}

This schema governs how the LLM maintains this knowledge base.

## Directory Structure

```
{name}/
├── CLAUDE.md          # This schema file
├── raw/               # Immutable source documents (never modify)
│   └── assets/        # Downloaded images from sources
└── wiki/              # LLM-generated knowledge base
    ├── index.md       # Master catalog of all wiki pages
    ├── log.md         # Chronological activity log
    ├── overview.md    # High-level synthesis of the knowledge base
    ├── health.md      # Lint report (LLM-maintained)
    ├── sources/       # Summary pages for each ingested source
    ├── concepts/      # Topic and concept pages
    ├── entities/      # Entity pages (APIs, people, products, etc.)
    ├── queries/       # Filed Q&A outputs
    └── outputs/       # Generated artifacts
        ├── slides/    # Marp presentations
        └── charts/    # Visualizations
```

## Core Principles

1. **Raw sources are immutable** — Never modify files in `raw/`. They are the source of truth.
2. **Wiki is LLM-owned** — The LLM writes and maintains all wiki content. User reads, LLM writes.
3. **Knowledge compounds** — Every ingest and query should strengthen the wiki.
4. **Cross-reference extensively** — Use `[[wiki links]]` to connect related concepts.
5. **Cite sources** — Reference raw sources with `[[raw/filename]]` links.

## Page Formats

### Source Summary (`wiki/sources/`)
```markdown
---
type: source
title: "<Document Title>"
source_file: "[[raw/<filename>.md]]"
source_url: "<original URL>"
ingested: YYYY-MM-DD
tags: [<relevant-tags>]
---

## Summary
<2-3 paragraph summary of key content>

## Key Points
- <bullet points of important information>

## Related Concepts
- [[wiki/concepts/<concept>]]

## Related Entities
- [[wiki/entities/<entity>]]
```

### Concept Page (`wiki/concepts/`)
```markdown
---
type: concept
title: "<Concept Name>"
aliases: [<alternate names>]
sources: [<count of sources mentioning this>]
---

## Overview
<explanation of the concept>

## Details
<deeper information>

## Related
- [[wiki/concepts/<related-concept>]]
- [[wiki/entities/<related-entity>]]

## Sources
- [[wiki/sources/<source>]]
```

### Entity Page (`wiki/entities/`)
```markdown
---
type: entity
title: "<Entity Name>"
entity_type: "<api|person|product|place|etc>"
---

## Description
<what this entity is>

## Usage
<how it's used>

## Related
- [[wiki/concepts/<concept>]]
- [[wiki/entities/<entity>]]

## Sources
- [[wiki/sources/<source>]]
```

### Query Page (`wiki/queries/`)
```markdown
---
type: query
title: "<Question Summary>"
query: "<Original question asked>"
answered: YYYY-MM-DD
tags: [<relevant-tags>]
---

## Answer
<synthesized answer>

## Sources Consulted
- [[wiki/sources/<source>]]
- [[wiki/concepts/<concept>]]

## New Insights
<anything discovered not already in wiki — candidates for new pages>
```

### Health Report (`wiki/health.md`)
```markdown
# Wiki Health Report
Last checked: YYYY-MM-DD

## Orphaned Pages
- (pages with no inbound links)

## Missing Pages
- (pages referenced but don't exist)

## Stale Sources
- (raw files without wiki summaries)

## Suggested Articles
- (concepts mentioned 3+ times without dedicated page)

## Inconsistencies
- (conflicting claims across pages)

## Action Items
- [ ] Item 1
```

### Marp Slides (`wiki/outputs/slides/`)
```markdown
---
marp: true
theme: default
title: "<Title>"
generated: YYYY-MM-DD
sources: [<wiki pages used>]
---

# Slide Title
- Content from wiki

---

# Next Slide
```

### Charts (`wiki/outputs/charts/`)

Generate via matplotlib/Python, save PNG to `wiki/outputs/charts/<name>.png`.
Reference in wiki pages: `![[wiki/outputs/charts/<name>.png]]`

## Workflows

### Ingest Source
1. Read the source document completely
2. Create a summary page in `wiki/sources/`
3. Identify concepts — create or update pages in `wiki/concepts/`
4. Identify entities — create or update pages in `wiki/entities/`
5. Update `wiki/index.md` with new pages
6. Update `wiki/overview.md` if the synthesis changes
7. Append entry to `wiki/log.md`

### Answer Query
1. Read `wiki/index.md` to find relevant pages
2. Read relevant wiki pages
3. **Use a subagent to verify** the answer against source material before responding
4. Synthesize answer with citations
5. If answer is valuable → file to `wiki/queries/<slug>.md`
6. Update `wiki/index.md` with query entry
7. Append to `wiki/log.md`: `## [YYYY-MM-DD] query | <Question Summary>`

## Query Response Requirements

**All query responses MUST be citation-verified before delivery:**

1. **Dispatch a verification subagent** to:
   - Find exact source text supporting the answer
   - Extract citation (file path, line number if possible)
   - Provide the source URL (from `source_url` frontmatter)

2. **Only include claims that can be directly cited** from source material

3. **Clearly separate** direct quotes from synthesis/recommendations:
   - Direct quotes: use blockquotes with citation
   - Synthesis: explicitly state "Based on [source1] and [source2], I recommend..."

4. **Always include source URL** for traceability

5. **If synthesizing across multiple sources**, cite each source explicitly

### Lint/Health Check
1. Check for:
   - Orphan pages (no inbound links)
   - Missing pages (referenced but don't exist)
   - Contradictions between pages
   - Stale sources (raw files without wiki summaries)
   - Suggested articles (concepts mentioned 3+ times without page)
2. Write results to `wiki/health.md`
3. Append to `wiki/log.md`: `## [YYYY-MM-DD] lint | Health Check`

### Generate Output
1. Identify wiki content for output (slides, chart, report)
2. Generate artifact in appropriate format
3. Save to `wiki/outputs/<type>/<name>.<ext>`
4. Optionally link from relevant wiki pages
5. Append to `wiki/log.md`: `## [YYYY-MM-DD] output | <Output Name>`

## Image References

When referencing images from raw sources, use Obsidian-style links:
```
![[raw/assets/filename.png]]
```

## Conventions

- **Dates**: Use ISO format (YYYY-MM-DD)
- **Links**: Use relative wiki links `[[wiki/path/page]]`
- **Tags**: Use lowercase, hyphenated tags
- **Filenames**: Use kebab-case for all wiki files
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize an LLM Wiki knowledge base")
    parser.add_argument("path", help="Path where the wiki should be created")
    parser.add_argument("--name", "-n", default="Knowledge Base", help="Name for the wiki")
    args = parser.parse_args()

    create_wiki(args.path, args.name)
