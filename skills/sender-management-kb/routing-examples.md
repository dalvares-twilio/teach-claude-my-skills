# Routing examples (few-shot)

Worked "task → routing decision → specific code" cases. Add a new row whenever a task teaches a non-obvious routing. Keep each grounded in real files.

---

**Task:** "Add a new field to the sender registration response."
**Routing:** ottm (public API). Response DTO in `internal/management/server/types/whatsapp.go` (or `rcs.go`); populate in the handler under `internal/management/server/endpoints/<name>/`; update in-repo spec `openapi/public/messaging-ott-management-api.yaml`; if the field comes from stored data, also read it via `internal/clients/storehouse` → add/extend a storehouse resource/DAO (`repos/storehouse.md`).
**Tests:** `make test` + `make test-contract`.

---

**Task:** "Change what happens when a module is uninstalled."
**Routing:** storehouse. `marketplace/ModuleService.java` (Kafka publish `Marketplace.ModuleInstallEvents` / `Channels.ModuleInstallData`) + `controllers/ModuleDataDeleteController.java`; tests in `service/src/test/.../marketplace`.

---

**Task:** "A sender's status update isn't reaching downstream."
**Routing:** storehouse SQS producer — `sqs/SqsEnqueuer.java`, queue `messaging-channels-sender-status-update-events` (`conf/messaging-ott-storehouse-local.yml:216-219`). To debug live, use `grafana-clickhouse-access` / `otk-service-connect`.

---

**Task:** "Add a new endpoint to the send path."
**Routing:** **NOT ours.** `messaging-ott-send` / `messaging-ott-gateway` are channels-delivery. Say so, point to that team, stop.

---

**Task:** "Expose a new public Senders endpoint to customers."
**Routing:** ottm (implement, `repos/ottm.md` §PLAYBOOK) **and** `open-api` repo `spec/messaging/v2/openapi.yaml` (gateway contract, `downstreamServiceName: messaging-ott-management-api`).
