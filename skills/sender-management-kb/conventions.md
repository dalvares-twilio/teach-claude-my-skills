# Cross-repo conventions

Grounded from the repos on 2026-08-28. Confirm against a repo's own `CLAUDE.md` before relying on a convention for a change.

## OpenAPI → code flow

- **ottm (Go):** two spec locations, different jobs.
  - In-repo `openapi/` (public + internal) is the **contract-validation source of truth** — `make test-contract` (`tests/api/**`) validates responses against it. Update it for every endpoint change.
  - `open-api` repo `spec/messaging/v2/openapi.yaml` is the **gateway/public contract** (RestProxy). Update it only for externally-exposed endpoints, mapping the path to `downstreamServiceName: messaging-ott-management-api`.
- **storehouse (Java):** routes are JAX-RS `@Path` on resource classes; no in-repo OpenAPI contract-test harness observed. ⚠ UNVERIFIED whether a spec is published elsewhere.
- For spec authoring/validation use the `twilio-openapi:*` skills (`review-openapi-spec`, `standards-reference`, `extract-openapi`).

## Metrics (ottm)

Every handler emits the full set: `RequestReceived`, deferred `RequestSyncTime` (flip `reason` to failure on error), `PublishIncrFailureMetric` on each error return, `RequestSuccess`/`RequestAccepted` on success. Constants in `internal/consts/metrics`; pattern in `internal/management/server/endpoints/delete/delete.go` (ottm `CLAUDE.md:29-42`).

## DTO placement

- ottm: request/response types go in `internal/management/server/types/`, never the endpoint package (ottm `CLAUDE.md:19-27`).
- storehouse: DTOs/domain in the `protocol/` Maven module.

## Deploy (both repos)

OTK on AWS EKS via Buildkite → Helm chart (`chart/`) → ArgoCD apps (`argocd/app/{env}/us-east-1/*.yaml`) → paired `*-deploy` repo. Cluster targets in `.buildkite/deploy/cluster-config/`. A new *route* needs no manifest change; new secrets/config keys do (`chart/templates/ConfigMap.yaml`/`Secrets.yaml`). Use the `otk-service-connect` skill to reach a running role.

## Tests

- ottm: `make test` (unit), `make test-contract` (contract vs `openapi/`), `make whatsapp-cluster`/`make rcs-cluster` (e2e), `tests/integration/**`, `tests/load/k6`.
- storehouse: `mvn test` (unit), `chart/tests/test.sh` (smoke), `load-test/` (JMeter).
- Sender E2E against a live env → use `senders-e2e-testing` / `senders-api-testing` skills (see `skill-registry.md`), not a hand-rolled script.

## Jira / tickets

Project `MSGADVCHNL`, Team=Sender Management (customfield_10139 → "Sender Management", id 10475). Close needs Assignee + Work Categorization (customfield_12770="Feature Development"). Lead with Deliverable + Steps + Done-when (see [[feedback_actionable_tickets]]); never put KB shorthand in a ticket (see [[feedback_no_kb_placeholders_in_jira]]).

## Error codes

New Twilio error code / `/docs/errors/<code>` page → `twilio-error-code-creator` skill.
