---
name: sender-management-kb
description: Knowledge base and work-router for the Sender Management fleet (messaging-ott-management-api "ottm" = the Senders API, and messaging-ott-storehouse). Use for ANY sender-management task — adding or changing an API, testing a sender, turning a requirement into a tech design, breaking a design into actionable tickets, or implementing a change — to identify the exact repo and files to modify, route to the right existing skill, and run the requirement→design→tickets→implementation pipeline. Also fires the "should this become a skill?" reflex whenever a repeatable procedure emerges.
---

# Sender Management Knowledge Base (hub)

This is the entry point for all Sender Management work. It does three jobs:

1. **Routes** a task to the correct repo + the exact code to change (Layer 1: knowledge).
2. **Runs the pipeline** requirement → tech design → actionable tickets → implementation (Layer 2A).
3. **Grows itself** — spots skill-worthy procedures, proposes them, and folds learnings back in (Layer 2B).

## OPERATING RULE — ground everything in actuals (non-negotiable)

> Every file path, route, deploy target, and convention you state MUST be confirmed by reading the real repo. **Never fabricate.** If a reference file here is marked `⚠ UNVERIFIED`, verify it (run the cited command / read the cited file) before you rely on it, then update the file. When you learn something new, update the reference file in the same session. Stale knowledge is a bug — fix it in place.

## The fleet at a glance (ownership = verified via CODEOWNERS)

| Repo | Owned by | Role | Route work here? |
|---|---|---|---|
| `messaging-ott-management-api` (ottm, **Go**) | **Sender Management** ✅ | The Senders API (`/v2/Channels/Senders`). **Multi-role monorepo** — also builds the `messaging-ott-kyc` and `messaging-ott-senders-lookup-api` roles | **Yes** — see `repos/ottm.md` |
| `messaging-ott-storehouse` (**Java 17 / Dropwizard**) | **Sender Management** ✅ | CRUD API over Channels **Aurora/MySQL** metadata (module + module-install data); Kafka/SQS events; DynamoDB deleted-templates | **Yes** — see `repos/storehouse.md` |
| `messaging-ott-edge` | channels-x | ⚠ UNVERIFIED purpose | No — **not ours**, hand to channels-x |
| `messaging-ott-gateway` | channels-delivery | ⚠ UNVERIFIED purpose | No — **not ours**, hand to channels-delivery |
| `messaging-ott-send` | channels-delivery | Send path (`⚠ confirm`) | No — **not ours**, hand to channels-delivery |
| `messaging-template-orch` | channels-x | Template orchestration (`⚠ confirm`) | No — **not ours** |
| `messaging-ott-rbm` / `-whatsapp` | ⚠ no CODEOWNERS found locally | ⚠ UNVERIFIED | Verify ownership before touching |
| `messaging-ott-kyc` | **role inside ottm**, not a separate repo | KYC role built from the ottm monorepo | Work in `messaging-ott-management-api` |
| `open-api` (shared) | shared / twilio | OpenAPI specs for Twilio APIs | Referenced, not owned |
| `rest-proxy` (shared) | shared / twilio | Public API gateway | Referenced, not owned |

**Reconcile the full owned list against Backstage** (authoritative for the org, not just what's cloned locally): use `backstage-tools:query-entities` filtered by owner `ott-channels-sender-management`. Update this table + `fleet-map.md` when you do.

## Routing procedure — "which repo / which code?"

1. **Is it ours?** If the change is on the send path, gateway, edge, or templates, it's likely a sibling team (see table) — say so and stop; that's a correct answer, not a dead end.
2. **Classify the surface.** Public REST endpoint / sender resource → **ottm**. Module-install / stored sender config / data → **storehouse**. (Confirm surface details in the repo playbooks.)
3. **Open the repo playbook** (`repos/<repo>.md`) for the file-level anchors and the ordered steps.
4. If the repo has no playbook yet, it's a **stub** — derive it from the repo now (see "Freshness" below), write `repos/<repo>.md`, then proceed.

## The pipeline (Layer 2A) — each stage is actionable and cites specific code

| Stage | Output | Use |
|---|---|---|
| Requirement → **Tech design** | Design naming affected repos/APIs/**files** + tradeoffs | `superpowers:brainstorming`, then `superpowers:writing-plans`; pull facts from `fleet-map.md` + `repos/*` |
| Tech design → **Tickets** | Tickets with **Deliverable + Steps + Done-when**, each naming the specific code to modify (see [[feedback_actionable_tickets]]) | `jira-inator:jira-ticket-creator` (project `MSGADVCHNL`, Team=Sender Management); never use KB shorthand in Jira (see [[feedback_no_kb_placeholders_in_jira]]) |
| Tickets → **Implementation** | The change | The ordered steps in the repo playbook |

## The "propose-a-skill" reflex (Layer 2B — the growth engine)

Run this at the **end of every SM task** (and whenever you catch yourself figuring something out). Don't leave it to memory — apply the rubric.

### Step 1 — Where does this learning belong? (route before you propose)

| The learning is… | Home | Not a skill |
|---|---|---|
| A **fact** (a path, a table name, an ID, "prod DB = X") | → a `repos/*.md` / `conventions.md` reference file, or a memory | ✅ never a skill |
| Covered by an **existing** skill (check `skill-registry.md`) | → **update that skill**, don't create one | ✅ |
| A **repeatable procedure**, proven & general | → **new skill** via `writing-skills` | candidate ↓ |
| A repeatable procedure, **not yet proven** | → a `playbooks/*.md` entry; promote later | candidate ↓ |

### Step 2 — Skill-worthiness rubric (score the candidate)

Propose a skill only when **most** of these are true:
- **Recurs** — it'll happen again across senders/channels/repos (not a one-off).
- **Multi-step + error-prone** — an ordered procedure with gotchas easy to get wrong.
- **Discovery had a cost** — you had to dig to figure it out (that cost is what the skill saves).
- **Not obvious from code** — encodes conventions/tribal knowledge/external-API quirks.
- **Stable** — won't churn every few weeks.
- **Generalizable** — bigger than this single instance.

**Anti-triggers (do NOT make a skill):** one-off; trivial/single obvious step; volatile; it's just data; already a skill (→ update instead).

### Step 3 — Propose

If it clears the rubric, STOP and propose to the user:
- **Proposed skill name** · **Why** (which rubric points it hits) · **What it helps with** (concretely) · **Trigger** (when it auto-loads) · **Reuses/updates** (existing skill or data it builds on).

On the user's yes → build with `superpowers:writing-skills`, register in `skill-registry.md`, and cross-link from the relevant `repos/*.md`.

### Worked examples (SM-specific)

| Learning while working | Verdict |
|---|---|
| "Add a new WhatsApp sender sub-resource" — recurs, spans ottm+storehouse+2 specs, ordered gotchas | ✅ **new skill** (or playbook first) |
| "Onboard a new channel type to the Senders API" | ✅ **new skill** |
| "Which Meta API error codes are unhandled?" | 🔄 query `otel_logs` via `grafana-clickhouse-access` for Meta error codes, diff against ottm handlers. (The `*-error-mapping-scanner` / `*-bigquery-*` skills are **BigQuery-based → RETIRED**.) *Handling* a code = edit ottm error handlers |
| "Run senders E2E for a sender" | 🔄 already `senders-e2e-testing` — route to it |
| "prod DB is `twilio_messaging_channels`" | 📄 **fact** → `repos/storehouse.md`, not a skill |
| "Fix a typo in one error string" | ❌ one-off — nothing to capture |

## Reuse before you build (Layer 2C)

Check `skill-registry.md` FIRST — many tasks are already covered. E.g. **"test a sender" already has `senders-e2e-testing`** — route to it, don't rebuild. Also reuse: `project-registry.yaml` (ottm structured data), `service-dependency-mapper` (downstream deps), `open-api` (specs).

## Freshness / how to regenerate a playbook

Each `repos/*.md` ends with a **Source anchors** list (the real files it was derived from). To refresh: re-read those files, diff against the playbook, update. When in doubt, re-derive from the repo — the repo is the source of truth, this KB is a cache.

## Reference files

- `fleet-map.md` — full per-repo detail + negative-routing notes
- `repos/ottm.md`, `repos/storehouse.md` — deep, file-level playbooks
- `skill-registry.md` — existing skills to route to
- `conventions.md` — cross-repo OpenAPI→code flow, error codes, deploy, testing
- `playbooks/*.md` — task-type procedures (embryonic skills)
- `routing-examples.md` — worked "add X → repo + steps" cases
- `DESIGN.md` — why this KB is shaped the way it is
