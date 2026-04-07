---
name: llm-wiki
description: "Build and maintain LLM-powered personal knowledge bases using the LLM Wiki pattern. Use when user wants to (1) create a new knowledge base/wiki from raw sources, (2) ingest new documents into an existing wiki, (3) query a wiki for synthesized answers, (4) lint/health-check a wiki. Triggers on phrases like 'build a wiki', 'create knowledge base', 'ingest this document', 'add to wiki', 'query the wiki', 'lint the wiki', 'build me an LLM wiki'."
---

# LLM Wiki

Pattern for building persistent, compounding knowledge bases where the LLM maintains all wiki content.

## Core Concept

Unlike RAG (re-derive knowledge each query), LLM Wiki **compiles knowledge once** into interlinked markdown. The wiki compounds with each source and query.

```
raw/ (immutable sources) → wiki/ (LLM-maintained) → user queries
```

## Directory Structure

```
<knowledge-base>/
├── CLAUDE.md          # Schema file (conventions, formats, workflows)
├── raw/               # Immutable source documents
│   └── assets/        # Downloaded images
└── wiki/
    ├── index.md       # Master catalog (~100 entries per section max)
    ├── log.md         # Chronological activity log
    ├── overview.md    # High-level synthesis
    ├── health.md      # Lint report (LLM-maintained)
    ├── sources/       # One summary per ingested source
    ├── concepts/      # Topic/concept pages
    ├── entities/      # Entity pages (APIs, people, products, etc.)
    ├── queries/       # Filed Q&A outputs
    └── outputs/       # Generated artifacts
        ├── slides/    # Marp presentations
        └── charts/    # Visualizations
```

## Operations

### Initialize Wiki
```bash
python3 scripts/init_wiki.py <path> --name "<Wiki Name>"
```

Or manually:
1. Create directory structure
2. Copy schema template from `assets/schema-template.md` → `CLAUDE.md`
3. Customize schema for domain
4. Create empty index.md, log.md, overview.md

### Ingest Source

1. Read source completely
2. Create `wiki/sources/<slug>.md` with frontmatter and summary
3. Identify concepts → create/update `wiki/concepts/<concept>.md`
4. Identify entities → create/update `wiki/entities/<entity>.md`
5. Add cross-references (`[[wiki/path/page]]`) between related pages
6. Update `wiki/index.md` (add new page entries)
7. Update `wiki/overview.md` if synthesis changes
8. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <Source Title>`

### Query

1. Read `wiki/index.md` to find relevant pages
2. Read relevant wiki pages
3. Synthesize answer with citations (`[[wiki/sources/...]]`)
4. If answer is valuable → file to `wiki/queries/<slug>.md`
5. Update `wiki/index.md` with query entry
6. Append to `wiki/log.md`: `## [YYYY-MM-DD] query | <Question Summary>`

### Lint

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

## Page Formats

### Source (`wiki/sources/`)
```markdown
---
type: source
title: "<Title>"
source_file: "[[raw/<filename>]]"
source_url: "<URL>"
ingested: YYYY-MM-DD
tags: [tag1, tag2]
---

## Summary
<2-3 paragraphs>

## Key Points
- Point 1
- Point 2

## Related Concepts
- [[wiki/concepts/<concept>]]

## Related Entities
- [[wiki/entities/<entity>]]
```

### Concept (`wiki/concepts/`)
```markdown
---
type: concept
title: "<Name>"
aliases: [alt1, alt2]
sources: <count>
---

## Overview
<explanation>

## Details
<deeper info>

## Related
- [[wiki/concepts/<related>]]
- [[wiki/entities/<related>]]

## Sources
- [[wiki/sources/<source>]]
```

### Entity (`wiki/entities/`)
```markdown
---
type: entity
title: "<Name>"
entity_type: "<api|person|product|place|etc>"
---

## Description
<what it is>

## Usage
<how used>

## Related
- [[wiki/concepts/<concept>]]

## Sources
- [[wiki/sources/<source>]]
```

### Query (`wiki/queries/`)
```markdown
---
type: query
title: "<Question Summary>"
query: "<Original question asked>"
answered: YYYY-MM-DD
tags: [tag1, tag2]
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
- [ ] Item 2
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
- More content
```

### Charts (`wiki/outputs/charts/`)

Generate via matplotlib/Python, save PNG to `wiki/outputs/charts/<name>.png`.
Reference in wiki pages: `![[wiki/outputs/charts/<name>.png]]`

## Image References

Use Obsidian-style links:
```markdown
![[raw/assets/filename.png]]
```

## Best Practices

- **Never modify raw/** — sources are immutable
- **Cross-reference extensively** — links are the wiki's value
- **Cite sources** — every claim traces to a source
- **Keep index.md lean** — one line per page, ~150 chars
- **Update overview.md** — reflects current synthesis
- **Log everything** — chronological record of operations

## Pattern Reference

For the full LLM Wiki pattern philosophy, see `references/llm-wiki-pattern.md`.
