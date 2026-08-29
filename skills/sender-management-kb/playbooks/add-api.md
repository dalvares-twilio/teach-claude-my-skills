# Playbook: add a new API (requirement → design → tickets → implementation)

The pipeline instantiated for "add/change a REST endpoint" on the Sender Management fleet. Every stage cites specific code; nothing is invented.

## 1. Route (which repo?)

Use `fleet-map.md`:
- Public sender resource / registration / KYC / lookup → **ottm** (`repos/ottm.md`).
- Stored sender/module/module-install data or Channels metadata query → **storehouse** (`repos/storehouse.md`).
- Send/gateway/edge/templates → **not ours**; name the team and stop.

If the endpoint reads/writes sender data, it's usually **ottm exposing it, storehouse persisting it** — expect a change in both (ottm handler + `internal/clients/storehouse`, and a storehouse resource/DAO).

## 2. Tech design

- Run `superpowers:brainstorming` for anything non-trivial.
- Produce a design that names: affected repos, the exact files per `repos/*.md`, the OpenAPI specs to touch, downstream deps, and tests. Then `superpowers:writing-plans` for the step list.

## 3. Tickets (actionable, code-specific)

Create in `MSGADVCHNL` (Team=Sender Management) with `jira-inator:jira-ticket-creator`. Each ticket = **Deliverable + Steps + Done-when**, and the Steps must name the real files from the repo playbook, e.g.:

> Deliverable: `POST /v2/Accounts/{accountSid}/Senders/{senderSid}/Foo` on ottm.
> Steps: add `FooRoute`/`FooEndpoint` in `internal/consts/server/consts.go`; DTOs in `internal/management/server/types/`; endpoint pkg `internal/management/server/endpoints/foo/foo.go` (model on `deregister/`); wire in `router.go`; spec in `openapi/public/messaging-ott-management-api.yaml`; contract test in `tests/api/management/`.
> Done-when: `make test` + `make test-contract` green; gateway spec updated if public.

Split spikes/decisions into their own tickets (see [[feedback_actionable_tickets]]). No KB shorthand in Jira (see [[feedback_no_kb_placeholders_in_jira]]).

## 4. Implementation

Follow the ordered steps in `repos/ottm.md` (§ PLAYBOOK) and/or `repos/storehouse.md` (§ PLAYBOOK). Use `superpowers:test-driven-development`. Verify with the repo's test targets in `conventions.md` before claiming done.

## 5. Learn (propose-a-skill reflex)

If this task revealed a repeatable procedure not captured here (e.g. "add a WhatsApp sender sub-resource"), propose it as a skill per the hub's reflex, or add a `routing-examples.md` entry.
