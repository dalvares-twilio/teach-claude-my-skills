# repos/ottm — messaging-ott-management-api (the Senders API)

> Derived by reading the repo on 2026-08-28. Every path below was confirmed in-repo; items marked **(inferred)** or **⚠ UNVERIFIED** were not confirmed by an enforcing gate. Re-derive from the Source anchors when in doubt.

## Identity

- **Repo:** `~/Projects/messaging-ott-management-api`
- **Owner:** Sender Management (CODEOWNERS `* @messaging/ott-channels-sender-management`)
- **Language/framework:** **Go 1.24** (`go.mod:3`), HTTP via **gorilla/mux** + gorilla/handlers (`go.mod:22-24`); validation `go-playground/validator/v10`; OpenAPI parsing `getkin/kin-openapi` (contract tests).
- **Multi-role monorepo:** one Go codebase → three OTK roles (`.buildkite/deploy/otk-deploy.yml:5`):
  - `messaging-ott-management-api` — **the Senders API (this playbook)**
  - `messaging-ott-kyc` — KYC role (lives HERE, not a separate repo)
  - `messaging-ott-senders-lookup-api` — senders lookup
- **OTK role name (management):** `messaging-ott-management-api` (`about.yaml:3-4`).

## API surface

- Public path fronted by the gateway: `/v2/Channels/Senders` (in `open-api` repo `spec/messaging/v2/openapi.yaml:156`, `downstreamServiceName: messaging-ott-management-api`, backend `/v2/Accounts/{AccountSid}/Senders`, lines 224-227).
- In-service routes are `/v2/Accounts/{accountSid}/Senders/...` and internal `/Internal/...` tooling routes.
- **Routes are all defined in one file:** `internal/management/server/router/router.go` (`mux.NewRouter()` at `:141`; bindings `:143-187`). Paths are constants in `internal/consts/server/consts.go`; metric endpoint-names are constants in the same file.
- Example: `router.go:148` → `r.HandleFunc(srvconst.SendersByIDRoute, deleteSender.Handler).Methods(http.MethodDelete)`, path `consts.go:19` `SendersByIDRoute = "/v2/Accounts/{accountSid:AC[a-z0-9]{32}}/Senders/{senderSid:XE[a-z0-9]{32}}"`, handler `internal/management/server/endpoints/delete/delete.go:96`.

## Layering (no separate service object — handlers orchestrate validator + typed clients)

| Layer | Where | Note |
|---|---|---|
| Route binding | `internal/management/server/router/router.go` | mux |
| Path & metric constants | `internal/consts/server/consts.go` | every route/handler references these |
| Handler (controller) | `internal/management/server/endpoints/<name>/<name>.go` | struct + `New()` + `Handler(w,r)` |
| Request/response DTOs | `internal/management/server/types/` (`whatsapp.go`, `rcs.go`, `generics.go`) | never in the endpoint package (CLAUDE.md:19-27) |
| Validator | `internal/management/server/validator/` (`validator.go`, `rcs.go`, `rcsui.go`) | optional per endpoint |
| Persistence / downstream | `internal/clients/*` (e.g. `storehouse`, `meta`) | typed HTTP clients = the "repository"; **Storehouse is the primary datastore accessor** |
| Handler helpers | `internal/management/server/endpoints/util/util.go` | `GetRequestID`, `SetHeaders`, `GetErrorResponse`, `WriteCodeAndResponse` |
| Metrics | `internal/metrics`, `internal/consts/metrics` | 4 metrics per handler (CLAUDE.md:29-42) |
| App wiring | `cmd/management/main.go:40` → `internal/management/app/app.go:111` (`router.New()`), serves `:124/:154` | |

Persistence is remote (Storehouse service, Meta API, DynamoDB) — no local DB DAO.

## PLAYBOOK — add one new REST endpoint (ordered, file-level)

1. **Constants:** add `<Name>Route` (path) and `<Name>Endpoint` (metric name) in `internal/consts/server/consts.go`.
2. **DTOs:** add request/response types in `internal/management/server/types/` (`whatsapp.go`/`rcs.go`/`generics.go`) — never in the endpoint package (CLAUDE.md:19-27).
3. **Endpoint package:** create `internal/management/server/endpoints/<name>/<name>.go` with inline client/validator interfaces, an `Endpoint` struct, `New() (*Endpoint, error)` building needed `internal/clients/*` from `config.Get()`, and `Handler(w,r)`. Model on `deregister/deregister.go` (one client) or `delete/delete.go` (validator + multiple clients).
4. **Metrics:** emit the full set — `RequestReceived`, deferred `RequestSyncTime` (flip `reason` to failure on error), `PublishIncrFailureMetric` on every error return, `RequestSuccess`/`RequestAccepted` on success (copy from `delete/delete.go`, CLAUDE.md:29-42).
5. **Validation (if needed):** add a method on the validator in `internal/management/server/validator/` and reference it via the handler's inline `validator` interface. Optional — `deregister.go` does inline checks with no validator. ⚠ UNVERIFIED: exact new-validator-method signature convention.
6. **Wire the route:** in `internal/management/server/router/router.go` add import alias (`:12-30`), construct in `New()` with error wrapping (`:45-138`), register `r.HandleFunc(srvconst.<Name>Route, <name>.Handler).Methods(...)` (`:143-187`).
7. **Unit test:** `internal/management/server/endpoints/<name>/<name>_test.go`, mocking client interfaces (see `deregister/deregister_test.go`; per-client mocks exist as `client_mock.go`, e.g. `internal/clients/meta`).
8. **In-repo OpenAPI:** update `openapi/public/messaging-ott-management-api.yaml` (public) or `openapi/internal/**` (internal/tooling). Required — `make test-contract` validates responses against these (`openapi/public/...yaml:1-3`).
9. **Contract test:** add coverage in `tests/api/management/` (or `tests/api/tooling/`). (inferred — parity with existing.)
10. **Public endpoints only — gateway spec:** update `open-api` repo `spec/messaging/v2/openapi.yaml`, mapping the public path to `downstreamServiceName: messaging-ott-management-api` (pattern `:224-227`). (inferred requirement for gateway exposure; `/Internal/...` routes are not in that spec.)
11. **Deploy:** normally **no manifest change** for a new route — the chart deploys the whole binary. `chart/`/`argocd/` change only for infra (new secrets/config keys via `chart/templates/ConfigMap.yaml`/`Secrets.yaml`). (inferred.)

## Deploy

- Buildkite: entry `.buildkite/pipeline.yaml`; build `.buildkite/build/build-and-validate.yml` (lint, unit, contract, sonar, docker, release); deploy `.buildkite/deploy/otk-deploy.yml` (management role `:33-71`, `DEPLOYMENT_REPO_NAME: messaging-ott-management-api-deploy`, `HELM_SOURCE_PATH: chart`).
- Helm: `chart/` (shared `chart/templates/*`: Rollout/Deployment/VirtualService/Service/ConfigMap/Secrets/KedaScaledObject); per-role values `chart/messaging-ott-management-api/values*.yaml` (base + dev/stage/prod + region). `rolloutManagesDeployment: true`, image in `Rollout.yaml`.
- Cluster targets: `.buildkite/deploy/cluster-config/messaging-ott-management-api.json` (dev use1-002/003; stage 002-004; prod 002-008).
- ArgoCD: `argocd/app/{dev,stage,prod}/us-east-1/messaging-ott-management-api-*.yaml`. OTK validator: `.otk-validator/config.yaml`.
- Container: `Dockerfile`, `Dockerfile.tests`, `docker-compose.yml` (local).

## Tests (Makefile targets)

- **Unit:** co-located `*_test.go` — `make test` (`Makefile:11`).
- **Contract:** `tests/api/**` vs in-repo `openapi/` — `make test-contract` (`Makefile:25`).
- **Cluster/e2e:** `tests/cluster/**` — `make whatsapp-cluster` / `make rcs-cluster` (`Makefile:31,35`).
- **Integration:** `tests/integration/**` (meta/google/clients).
- **Load:** `tests/load/k6/`.

## Source anchors (re-derive from these)

`go.mod`, `about.yaml`, `.buildkite/deploy/otk-deploy.yml`, `.buildkite/pipeline.yaml`, `.buildkite/build/build-and-validate.yml`, `internal/management/server/router/router.go`, `internal/consts/server/consts.go`, `internal/management/server/endpoints/{delete,deregister}/`, `internal/management/server/types/`, `internal/management/server/validator/`, `internal/clients/`, `internal/management/app/app.go`, `cmd/management/main.go`, `openapi/`, `tests/`, `chart/`, `Makefile`, `CLAUDE.md`, and `~/Projects/open-api/spec/messaging/v2/openapi.yaml`.

## Temporal (WhatsApp runs on it; RCS does not)

WhatsApp create/update sender flows run as Temporal workflows (`internal/management/workflow/`, worker `internal/management/temporalworker/worker.go`, Temporal Cloud namespaces `-wa-*`). RCS is SQS-async (`create/rcs.go` → `processor/rcs.go`); tooling endpoints are synchronous. To move a channel onto Temporal, use the **`sm-convert-channel-to-temporal`** skill (exemplar-based).

## Corrections this file made to prior assumptions

- ottm is **Go**, not Java (open-api is the Java/Maven repo).
- **kyc is a role in this repo**, not a separate repo.
