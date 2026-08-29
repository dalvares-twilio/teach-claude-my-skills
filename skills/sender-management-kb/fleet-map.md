# Fleet Map

Ownership verified via each repo's CODEOWNERS on 2026-08-28. Purpose lines are grounded where a `repos/*.md` playbook exists; otherwise marked `⚠ UNVERIFIED`. **Reconcile the full owned set against Backstage** (owner `ott-channels-sender-management`) via `backstage-tools:query-entities` — CODEOWNERS only covers locally-cloned repos.

## Owned by Sender Management ✅

| Repo | Lang | Role / OTK role | What it owns | Playbook |
|---|---|---|---|---|
| `messaging-ott-management-api` (ottm) | Go | 3 OTK roles: `messaging-ott-management-api` (Senders API), `messaging-ott-kyc`, `messaging-ott-senders-lookup-api` | Public **Senders API** `/v2/Channels/Senders`; sender CRUD/registration; KYC; lookup | `repos/ottm.md` |
| `messaging-ott-storehouse` | Java 17 (Dropwizard 4) | `messaging-ott-storehouse` | CRUD API over Channels **Aurora/MySQL** metadata (module + module-install data); Kafka/SQS events; DynamoDB deleted-templates | `repos/storehouse.md` |

**Key correction from prior assumptions:** `kyc` and `senders-lookup-api` are **roles inside the ottm repo**, not separate repos. ottm is **Go**, not Java.

### Deploy repos (paired, do not confuse with source)
- `messaging-ott-management-api-deploy`, `messaging-ott-storehouse-deploy` — Helm/ArgoCD targets.

## NOT ours — negative routing (hand to the owning team)

| Repo | Owner (CODEOWNERS) | Route to |
|---|---|---|
| `messaging-ott-edge` | `@messaging/channels-x` | channels-x. Purpose ⚠ UNVERIFIED |
| `messaging-ott-gateway` | `@messaging/channels-delivery` (+channels-x) | channels-delivery. Purpose ⚠ UNVERIFIED |
| `messaging-ott-send` | `@messaging/channels-delivery` | channels-delivery (send path). ⚠ confirm |
| `messaging-template-orch` | `@messaging/channels-x` | channels-x (template orchestration). ⚠ confirm |
| `messaging-ott-rbm` | ⚠ no CODEOWNERS found locally | Verify owner before touching |
| `messaging-ott-whatsapp` | ⚠ no CODEOWNERS found locally | Verify owner before touching |

## Shared / referenced (not owned, but we change specs here)

| Repo | Use |
|---|---|
| `open-api` (Java/Maven) | Gateway/public OpenAPI specs. Senders: `spec/messaging/v2/openapi.yaml:156` → `downstreamServiceName: messaging-ott-management-api`. Update here for **externally-exposed** ottm endpoints. |
| `rest-proxy` | Public API gateway that fronts the services. |

## Routing quick rules

- Public REST endpoint / sender resource / registration / KYC / lookup → **ottm** (`repos/ottm.md`).
- Stored sender/module/module-install data, Channels metadata, DB query, template deletion, number-inventory or sender-status events → **storehouse** (`repos/storehouse.md`).
- Send path, gateway, edge, templates → **not ours** — name the owning team and stop.
- Externally-exposed new ottm endpoint → also update `open-api` gateway spec.
