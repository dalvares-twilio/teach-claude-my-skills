# Worked example — convert RCS to Temporal

The skill's procedure instantiated for RCS. RCS today is SQS-async; this is the delta to make it a workflow like WhatsApp. Anchors verified 2026-08-28.

## RCS today (what we're replacing)

- Create: `create/handler.go:268-270` → `handleRCSCreate` (`create/rcs.go:26`) → `e.SQSProducer.Produce(prepareSQSMessageForCreateRCSSender(...))` (`create/rcs.go:95`) → consumed by `internal/management/processor/processor.go` → `createRCSSender` (`processor/rcs.go:30`).
- Update: `update/handler.go:228-230` → `handleRCSUpdate` → `processor/rcs.go:updateRCSSender:124`.

**The processor functions are the future activities.**

## Target (mirrors WhatsApp)

| Step | RCS file to create/change | Modeled on |
|---|---|---|
| WorkflowID prefix (`REGISTER_RCS_<SENDER_SID>`) + task queue choice | `internal/consts/workflow/consts.go` | `:92-97` |
| Activities (lift `createRCSSender`/`updateRCSSender` logic) | `internal/management/workflow/activities_rcs.go` + wire in `activities_base.go` | `activities_registration.go` |
| Workflow `RegisterRCSSenderWorkflow` (+ update) | `internal/management/workflow/rcs_workflows.go` | `RegisterSenderWorkflow` `whatsapp_workflows.go:315`, start helper `:87-100` |
| Worker registration | `internal/management/temporalworker/worker.go` | `registerCreateSenderWorker:163-207` |
| Handler starts workflow instead of SQS | `create/rcs.go` (replace `:95` Produce), `update` RCS branch | `create/whatsapp.go:162` |
| Retire SQS RCS path (decision) | remove/guard `create/rcs.go` SQS + `processor/rcs.go` | — |
| Config/chart if new namespace/queue | `config.go:403-409`, `configuration-schema.yaml:69-80`, `chart/.../values-*.yaml` | `values-*.yaml` (`-wa-` namespaces) |
| Tests | `internal/management/workflow/rcs_workflows_test.go` | existing `*_test.go` |

## RCS-specific cautions

- RCS steps differ from WhatsApp (no WABA registration/verification; RCS has its own provisioning). **Copy the workflow *structure*, not WhatsApp's activity bodies** — the RCS activity bodies come from `processor/rcs.go`.
- Namespaces are `-wa-` today → RCS almost certainly needs the namespace/task-queue decision resolved before step 8. Flag it.
- Add `workflow.GetVersion`/`Patched` from the first commit (exemplar has none).

## Verify

`make test` + `make test-contract`; RCS cluster test; confirm run in Temporal Cloud dev namespace `messaging-ott-mgmt-wa-dev-us1.plbec` (or the new RCS namespace if provisioned) via `workflow_id`+`run_id` from logs — see [[reference_temporal_cloud_dev]].
