---
name: sm-convert-channel-to-temporal
description: Convert (migrate) a Sender Management channel's Senders API flow from synchronous/SQS-async execution to a Temporal workflow in messaging-ott-management-api (ottm), modeled on the existing WhatsApp workflow. Use when asked to "move <channel> to Temporal", "convert RCS senders to a workflow", "make <channel> registration durable", or add a new channel that should run on Temporal. Produces a grounded design, actionable tickets, and file-level implementation steps.
---

# Convert a channel's Senders flow to Temporal

Turns a channel that is synchronous or SQS-async (e.g. **RCS** today) into a durable Temporal workflow, following the pattern WhatsApp already uses in ottm. This skill is derived from the real WhatsApp implementation — **not invented**.

## Operating rule

Ground every step in the actual repo. **Step 0 is mandatory: read `reference-whatsapp.md`** (the exemplar's real file anchors) and open the current channel's synchronous path before writing anything. Load `temporal:temporal-developer` for Temporal correctness. Mark anything you cannot confirm `⚠ UNVERIFIED`; never fabricate a file path.

## Prerequisites to load

1. `reference-whatsapp.md` (this dir) — the WhatsApp exemplar anatomy.
2. `sender-management-kb` → `repos/ottm.md` — ottm layering + how endpoints are structured.
3. `temporal:temporal-developer` — workflow/activity correctness (determinism, timeouts, retries, versioning).

## Decisions to raise with the user FIRST (don't assume)

These are real forks the grounding exposed — confirm before implementing:
- **Namespace/task-queue:** every Temporal namespace today is WhatsApp-specific (`-wa-`, see `reference-whatsapp.md`). Reuse it, or provision a channel-agnostic / per-channel namespace + task queue? (Affects `chart/values-*.yaml` + `configuration-schema.yaml`.)
- **Fate of the old path:** remove the channel's SQS producer+processor, or keep it for backward-compat/dual-write during migration?
- **Cutover:** big-bang vs feature-flagged per-account rollout?

## Conversion procedure (ordered; `<channel>` = the target, e.g. rcs)

Anchors below are the WhatsApp exemplar; create the `<channel>` equivalents beside them.

1. **Map the current sync/async path.** For the target channel, find the handler branch + its current execution. (RCS: `create/handler.go:268-270` → `create/rcs.go:26` → SQS `create/rcs.go:95` → `processor/rcs.go:createRCSSender:30`; update via `processor/rcs.go:updateRCSSender:124`.) The logic in the processor is what becomes **activities**.
2. **Consts:** add WorkflowID prefix(es) for the channel in `internal/consts/workflow/consts.go` (pattern `REGISTER_<CHANNEL>_` :92-94) and a task queue if not reusing `create_sender`/`update_sender` (:96-97).
3. **Activities:** create `internal/management/workflow/activities_<channel>.go` — lift the processor's steps (`processor/<channel>.go`) into idempotent activities; construct them in `NewActivities` (`activities_base.go`). Reuse shared activities (`activities_sync.go`, etc.) where the step is channel-agnostic.
4. **Workflow:** create `internal/management/workflow/<channel>_workflows.go` with `Register<Channel>SenderWorkflow` (+ update/profile as needed), modeled structurally on `RegisterSenderWorkflow` (`whatsapp_workflows.go:315`) and its start helper (`:87-100`). Use the determinism conventions from `reference-whatsapp.md` (temporalwf.Now/Sleep, memo/context propagator, `isActionableError`, retry config from `WorkflowConfig`). **Add `workflow.GetVersion`/`Patched` from the start** (the exemplar lacks it — improve on it).
5. **Register with the worker:** in `internal/management/temporalworker/worker.go`, register the new workflow + activities (mirror `registerCreateSenderWorker` :163-207 / `registerUpdateSenderWorker` :210-273). If a new task queue was added, create its worker in `New()` (:137-138).
6. **Switch the handler:** change the channel's handler branch to start the workflow instead of enqueuing SQS — mirror `create/whatsapp.go:162` (`StartRegisterSenderWithWorkflows`). Handle the already-started 409 via `serviceerror.WorkflowExecutionAlreadyStarted` (`update/handler.go:312`). Do the same for the update branch.
7. **Retire/guard the old path** per the decision above (remove `<channel>` SQS producer + `processor/<channel>.go`, or gate behind a flag).
8. **Config/deploy:** if namespace/task-queue changed, update `config.go` `TemporalConfig`/`WorkflowConfig`, `configuration-schema.yaml:69-80`, and `chart/messaging-ott-management-api/values-{dev,stage,prod}.yaml`. New task queue also needs its worker started only on the ILB pod (see `app.go:257-265`).
9. **Tests:** add workflow/activity unit tests using the Temporal Go test suite (mirror existing `internal/management/workflow/*_test.go`); the public API surface is unchanged so contract tests (`tests/api/`) should still pass; add/adjust cluster tests (`tests/cluster/`).
10. **Verify:** `make test` + `make test-contract`; cluster test the channel; confirm workflow execution in Temporal Cloud (build a timeline URL from logs' `workflow_id`+`run_id`, dev namespace per `values-dev.yaml`).

## Pipeline output

Feed this into the `sender-management-kb` pipeline: the steps above → a tech design → `MSGADVCHNL` tickets (Deliverable + Steps naming these files + Done-when) → implementation with `test-driven-development`.

## Reference files

- `reference-whatsapp.md` — the exemplar anatomy (keep current; re-derive from ottm).
- `example-rcs.md` — worked RCS instantiation.
