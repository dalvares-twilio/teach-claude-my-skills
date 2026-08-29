# Skill Registry — reuse before building

Catalog of skills that already exist and are relevant to Sender Management work. **Check here first** — the goal is to route to an existing skill, not reinvent it. All entries below are real skills present in this environment's skill list; verify a skill still exists before recommending it.

## Pipeline: Requirement → Design → Tickets → Implement

| Stage | Skill | Use when |
|---|---|---|
| Design | `superpowers:brainstorming` | Turning a requirement/idea into a validated design |
| Design | `superpowers:writing-plans` | Turning a design/spec into a step-by-step implementation plan |
| Design | `superpowers:writing-skills` | Creating/editing a skill (used by the propose-a-skill reflex) |
| Tickets | `jira-inator:jira-ticket-creator` | Create actionable `MSGADVCHNL` tickets (Team=Sender Management) |
| Tickets | `jira-inator:jira-search` / `jira-query` / `jira-ticket-updater` | Find/read/update tickets |
| Implement | `superpowers:test-driven-development` | Any feature/bugfix — tests first |
| Implement | `superpowers:executing-plans` / `subagent-driven-development` | Executing a written plan |
| Implement | `superpowers:systematic-debugging` | Any bug/test failure/unexpected behavior |
| Review | `code-review` / `code-review-personae:*` | Reviewing a diff/PR before merge |

## Testing a sender  ← already covered, do NOT rebuild

| Skill | Use when |
|---|---|
| `senders-e2e-testing` | Full E2E test of a sender (new phone number per session, show all errors in full) |
| `senders-api-testing` | API-level testing of the Senders API |
| `twilio-phone-number-manager` | Provisioning/managing phone numbers for tests |

## API design & specs

| Skill | Use when |
|---|---|
| `twilio-openapi:search-twilio-openapi` | Look up an existing Twilio API's spec/params |
| `twilio-openapi:extract-openapi` | Generate an OpenAPI spec from Java REST code |
| `twilio-openapi:review-openapi-spec` / `semantic-review` | Validate a spec against Twilio standards |
| `twilio-openapi:standards-reference` | Answer "what's the standard for naming/pagination/errors" |
| `endpoint-analysis:endpoint-analysis` | Find where an API endpoint is referenced across repos / gateways |
| `twilio-error-code-creator` | Create/document a new Twilio error code page |

## Debugging / operations / observability

| Skill | Use when |
|---|---|
| `otk-service-connect` | Reach/investigate an OTK role (ottm etc.) in dev/stage/prod |
| `grafana-clickhouse-access` | Query otel_logs (access/app logs, traces) via Grafana |
| `grafana-otel-dashboard-builder` | Build a troubleshooting/impact dashboard for a role |
| `request-origin-tracer` | Trace where an RQ… request originated + call chain |
| `service-dependency-mapper` | Map a service's downstream dependencies |
| `auto-bug-detector` / `bug-analyzer` / `ottm-bigquery-debugging` | Scan ottm logs for bugs (registry-driven) |
| `oncall:investigate-issues` / `investigate-page` | On-call investigation |
| `pagerduty-incident-resolver:incident-resolver` | Analyze a PagerDuty incident → code fix (MCP currently down — see session notes) |

## Docs

| Skill | Use when |
|---|---|
| `confluence-inator:confluence-page-creator` / `confluence-sync` | Publish/sync docs to Confluence |

## Substrate (not skills, but reuse as data)

- `~/.claude/project-registry.yaml` — ottm structured config (repo path, BigQuery, Jira, API URLs, error patterns)
- `open-api` repo — OpenAPI specs
- Obsidian vault `ottm-wiki/` + `01-Projects/` — existing human docs and prior designs

## Sender Management channel work

| Skill | Use when |
|---|---|
| `sm-convert-channel-to-temporal` | Convert a channel's Senders flow (e.g. RCS, currently SQS-async) to a Temporal workflow modeled on WhatsApp. Grounded in the real ottm WhatsApp exemplar. **Validation status:** authored from exemplar; not yet proven on a real RCS conversion — treat as embryonic until then. |

## Candidate skills (embryonic — in `playbooks/`, not yet promoted)

_Promote a playbook to a standalone skill once it's proven repeatable. Track candidates here._

- `sm-convert-channel-to-temporal` — promote from embryonic to proven after the first real RCS conversion validates its steps.
