# Design: sender-management-kb

**Date:** 2026-08-28 · **Owner:** dalvares (Sender Management)

## Goal

A single knowledge base that lets Claude work Sender Management tasks autonomously: given a requirement, produce an actionable tech design; given a design, produce actionable tickets that name the specific code to modify; given a ticket, implement it — always knowing the exact repo and files. The KB must also **grow itself**: recognize skill-worthy procedures during work, propose them, and fold learnings back in.

## Two layers

- **Layer 1 — Knowledge (the memory):** `fleet-map.md` + `repos/*.md` per-repo playbooks with **file-level anchors**. This is what makes "which code do I change?" answerable.
- **Layer 2 — Flywheel (the workflow + growth):**
  - **2A Pipeline:** requirement → tech design → tickets → implementation, each stage pulling from Layer 1 and from existing skills.
  - **2B Propose-a-skill reflex:** during any task, detect repeatable procedures → ask the user → build with `writing-skills` → register.
  - **2C Reuse:** `skill-registry.md` routes to existing skills (e.g. `senders-e2e-testing`) instead of rebuilding.

## Key decisions

1. **Home = a Claude skill**, not the Obsidian vault or the YAML registry — because the goal is autonomous auto-loading. The vault/registry are referenced as substrate, not duplicated.
2. **Breadth-first router, depth-on-demand playbooks.** The router knows the whole fleet (for correct + negative routing); deep playbooks exist only for repos we actually change (ottm, storehouse first). Others are stubs promoted on first touch.
3. **Derived, not hand-written.** Playbooks are built by reading the real repos and list their **source anchors** so they can be regenerated. Anti-hallucination is a stated operating rule; unverifiable facts are marked `⚠ UNVERIFIED`.
4. **Ownership is authoritative via CODEOWNERS.** Verified owned: `messaging-ott-management-api`, `messaging-ott-storehouse`. Full org list to be reconciled against Backstage (owner `ott-channels-sender-management`).

## Structure

```
sender-management-kb/
  skill.md            # hub: repo-router + skill-router + pipeline protocol + propose-a-skill reflex
  fleet-map.md        # every repo → owner, role, route-here/not-ours
  repos/ottm.md       # deep, file-level playbook (Senders API)
  repos/storehouse.md # deep, file-level playbook
  conventions.md      # OpenAPI→code flow, error codes, deploy, testing
  skill-registry.md   # existing skills to route to
  playbooks/*.md      # task-type procedures (embryonic skills)
  routing-examples.md # worked few-shot cases
  DESIGN.md           # this file
```

## Build order

1. Hub skeleton (`skill.md`) + `fleet-map.md` + `skill-registry.md` — done, grounded in verified ownership.
2. `repos/ottm.md` — derived from reading the repo (file-level anchors).
3. `repos/storehouse.md` — derived from reading the repo.
4. `conventions.md`, `playbooks/add-api.md` + `test-a-sender.md`, `routing-examples.md`.
5. Reconcile full owned-repo list against Backstage; promote stubs as we touch repos.

## Non-goals (YAGNI)

- No deep playbooks for sibling-team repos (edge/gateway/send/template-orch) — negative routing only.
- No duplication of `project-registry.yaml`, `open-api` specs, or vault docs — point to them.
