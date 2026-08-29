# Playbook: test a sender

**This is already covered by skills — route to them, do not hand-roll.**

## Decide which

- **Full E2E** (create a sender end-to-end against a live env, exercise registration, etc.): `senders-e2e-testing`. Per [[feedback]] on that skill: use a **new phone number per session** and **show all errors in full detail**.
- **API-level** checks of the Senders API: `senders-api-testing`.
- **Phone number provisioning** for a test: `twilio-phone-number-manager`.

## Environments (from project-registry.yaml)

- dev `https://messaging.dev.twilio.com/v2/Channels/Senders`
- stage `https://messaging.stage.twilio.com/v2/Channels/Senders`
- prod `https://messaging.twilio.com/v2/Channels/Senders`
- Auth: basic (`TWILIO_ACCOUNT_SID:TWILIO_AUTH_TOKEN`); request-id header `X-Twilio-Request-Id`.

## If something fails

- Trace logs: `grafana-clickhouse-access` (otel_logs) or `oncall:investigate-issues`.
- Reach the running role: `otk-service-connect` (role `messaging-ott-management-api`).
- Find where a request originated: `request-origin-tracer`.
- Expected-vs-bug errors: ottm expected-error patterns are in `~/.claude/project-registry.yaml` (e.g. "phone already registered" = external validation, not a bug).

## Repo-side tests (when changing code, not live testing)

See `conventions.md` → Tests (ottm `make whatsapp-cluster`/`rcs-cluster`; storehouse `chart/tests/test.sh`).
