# Twilio Sender Management — Claude Skills

A collection of Claude Code skills for Sender Management work.

> **History:** this repo began as a "Universal Bug Detection System" built on BigQuery. **BigQuery has been retired**, so those skills were removed. Log querying, error analysis, and analytics now go through **Grafana / ClickHouse `otel_logs`** (use the `grafana-clickhouse-access` skill or `oncall:investigate-issues`).

## Skills

| Skill | Purpose |
|-------|---------|
| `sender-management-kb` | Knowledge-base **hub**: routes any Sender Management task to the exact repo + files, runs the requirement→design→tickets→implementation pipeline, and self-extends (propose-a-skill rubric). Start here. |
| `sm-convert-channel-to-temporal` | Convert a channel's Senders flow (e.g. RCS, currently SQS-async) to a Temporal workflow, modeled on the WhatsApp exemplar in ottm. |
| `senders-e2e-testing` | End-to-end testing of the Senders API. ⚠ Its log-verification steps still reference BigQuery and must be ported to `otel_logs`. |
| `universal-jira-ticket-creator` | Create Jira tickets for any project; loads config from `project-registry.yaml`. |
| `twilio-phone-number-manager` | Provision / manage phone numbers for tests. |
| `llm-wiki` | Build & maintain LLM-powered knowledge bases. |

## Prerequisites

| Requirement | Purpose | Setup |
|-------------|---------|-------|
| **jira-inator plugin** | Create Jira tickets | `claude plugin install jira-inator@twilio` |
| **Grafana `otel_logs` access** | Query logs/traces | via the `grafana-clickhouse-access` skill |

## File locations

| File | Purpose |
|------|---------|
| `project-registry.yaml` | Per-project config (Jira, repo paths) for the Jira creator. |
| `skills/` | Skill definitions. |
| `/tmp/claude_created_tickets.json` | Log of created Jira tickets. |
