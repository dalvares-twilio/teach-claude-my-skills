# Reference exemplar — WhatsApp sender flow on Temporal

The ground truth to copy when converting a channel. All anchors verified in `~/Projects/messaging-ott-management-api` on 2026-08-28. Re-derive from these files if anything looks stale.

## Anatomy of the WhatsApp CREATE flow (the cleanest exemplar)

| Piece | File / anchor |
|---|---|
| SDK | `go.mod:43-44` — `go.temporal.io/api v1.49.1`, `go.temporal.io/sdk v1.35.0` |
| Handler routes channel → WhatsApp | `internal/management/server/endpoints/create/handler.go:264-267` |
| Endpoint kicks off workflow | `internal/management/server/endpoints/create/whatsapp.go:162` → `workflow.StartRegisterSenderWithWorkflows(...)` |
| Start helper (StartWorkflowOptions, WorkflowID, reuse policy, memo) | `internal/management/workflow/whatsapp_workflows.go:87-100` |
| Workflow definition | `RegisterSenderWorkflow` — `internal/management/workflow/whatsapp_workflows.go:315` |
| Activities | `internal/management/workflow/activities_registration.go`, `activities_verification.go`, `activities_sync.go`, `activities_profile.go`; constructed via `NewActivities` in `activities_base.go` |
| Worker registration | `internal/management/temporalworker/worker.go:163-207` (`registerCreateSenderWorker`: `RegisterWorkflow` :164, `RegisterActivity` :184-206) |
| Task queue | `internal/consts/workflow/consts.go:96` — `CreateSenderTaskQueue = "create_sender"` |
| WorkflowID prefix | `internal/consts/workflow/consts.go:92-94` — `REGISTER_<CHANNEL>_<SENDER_SID>` (`whatsapp_workflows.go:90`) |
| Conflict → 409 | `update/handler.go:312` via `serviceerror.WorkflowExecutionAlreadyStarted` |

## UPDATE flow counterpart

- Workflow `UpdateRegisterSenderWorkflow` — `whatsapp_workflows.go:859`; start helper `:113-125` (WorkflowID `UPDATE_REGISTER_<CHANNEL>_<SENDER_SID>`); kickoff `update/handler.go:309`; task queue `UpdateSenderTaskQueue = "update_sender"` (`consts/workflow/consts.go:97`).
- Other workflows: `ProfileUpdateWorkflow` (`whatsapp_workflows.go:566`, also a child workflow `:229`); `DisplayNameUpdateWorkflow` (`display_name_workflow.go:39`) — registered on the worker (`worker.go:265`) but on `main` has NO endpoint caller yet.

## Worker lifecycle (important — not a separate binary)

- Worker manager `internal/management/temporalworker/worker.go`: `New()` :48-160 builds client + two workers (one per task queue, :137-138); `Start()` :276-309, `Stop()` :312-333.
- Wired in `internal/management/app/app.go`: `temporalworker.New()` :116; **started only on the ILB lease-holder pod** (`ilbListener` :257-265, gated by `ConsumerEnabled` :250; `oolbListener` stops it :280-283). Runs in-process in the `cmd/management` binary. `cmd/kyc` and `cmd/lookup` do NOT use Temporal.

## Client + config

- Client factory `internal/clients/temporal/client.go` — `NewWithStats` :38-60, mTLS to Temporal Cloud (`tls.LoadX509KeyPair` :44); skips TLS for local (`hostPort` contains "local" :40-42). Metrics `internal/clients/temporal/metrics.go`.
- Config struct `internal/management/config/config.go:403-409` — `TemporalConfig{CertFile, KeyFile, HostPort, Namespace}`; schema keys `configuration-schema.yaml:69-80`.
- **Namespaces are WhatsApp-specific today** (`-wa-`): dev `messaging-ott-mgmt-wa-dev-us1.plbec` (`chart/messaging-ott-management-api/values-dev.yaml:176-179`), stage `...-wa-stage-us1.plbec` (`values-stage.yaml:158-161`), prod `messaging-ott-mgmt-wa-us1.plbec` (`values-prod.yaml:140-143`).

## Determinism / correctness conventions present (copy these)

- Deterministic time: `temporalwf.Now(ctx)` not `time.Now()` (`whatsapp_workflows.go:317`).
- Durable sleep: `temporalwf.Sleep(ctx, ...)` (`display_name_workflow.go:76`).
- Deterministic WorkflowIDs as business keys (prefixes above).
- Reuse policy `WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE` + `WorkflowExecutionErrorWhenAlreadyStarted: true` for 409 detection (`whatsapp_workflows.go:92-93, 117-118`).
- Log-field propagation via memo + `LogFieldsContextPropagator` (`context_propagator.go`; injected `worker.go:60`; memo `whatsapp_workflows.go:94-96`; read `WithLogFieldsFromMemo` `:348`).
- Activity retry/timeout from `config.Get().WorkflowConfig` (`whatsapp_workflows.go:366-374`; struct `config.go:439+`).
- Retryable-vs-terminal classification via `temporal.ApplicationError.NonRetryable()` in `isActionableError` (`whatsapp_workflows.go:59-71`).

## Known gap (the skill must IMPROVE on the exemplar)

⚠ No `workflow.GetVersion`, `workflow.Patched`, `SideEffect`, `ContinueAsNew`, signals, or queries anywhere under `internal` (repo-wide grep empty). The exemplar has **no versioning/patching guard** — any change to a running workflow risks non-determinism. A new channel workflow should adopt `GetVersion`/`Patched` from the start.
