# repos/storehouse — messaging-ott-storehouse

> Derived by reading the repo on 2026-08-28. Paths confirmed in-repo; items marked **(inferred)** / **⚠ UNVERIFIED** were not confirmed by an enforcing gate. `.worktrees/` (PR checkouts) excluded.

## Identity

- **Repo:** `~/Projects/messaging-ott-storehouse`
- **Owner:** Sender Management (CODEOWNERS `* @messaging/ott-channels-sender-management`)
- **Language/framework:** **Java 17**, Maven multi-module (`pom.xml:16-19`: `protocol`, `service`, `client`, `load-test`); **Dropwizard 4 + Jersey (Jakarta)** (`pom.xml:187-188`, bootstrapped via `DW40ApplicationAdapter`, `StoreHouseService.java:226`); parent `com.twilio:twilio-parent-pom:10.10.54`. JDBI (skife) for DB; AWS SDK v2; Lombok; Freemarker.
- **OTK role name:** `messaging-ott-storehouse` (`about.yaml:3`, `chart/values.yaml:63`).
- **Deploy repo:** `messaging-ott-storehouse-deploy`.

## What it does + relationship to ottm

CRUD REST API over the **Channels metadata tables in Aurora/MySQL** (DB `twilio_messaging_channels`, `StoreHouseService.java:121`). Owns **module data + customer installation (module-install) data** (`README.md:7`). See [[reference_moduleinstalldata_scope]] — ModuleInstallData is account-level; per-sender data is ConnectedServiceConfiguration.

**Link to ottm:** ottm calls storehouse as its **primary datastore accessor** via `ottm/internal/clients/storehouse` (confirmed from the ottm side). So sender persistence flows ottm → storehouse → Aurora. (Storehouse's own source contains no ottm reference — the dependency is one-directional, ottm→storehouse.)

Consumers of storehouse (`README.md:7`): portal-crane, monkey, console, messaging-console, messaging-whatsapp-container, messaging-whatsapp-k8s-orch. Downstream deps it calls (`chart/values.yaml:327-345`): accounts-api, stored-credentials-service, feature-service, messaging-service-configuration, whatsapp-k8s-orch, id-lifecycle-events-service, ratequeue-ott.

## Interfaces

- **HTTP REST (primary):** JAX-RS `@Path` resource classes, path constants in `StoreHouseRouter.java`, registered in `StoreHouseService.run()` (`StoreHouseService.java:556-577`). Public base `/v1/Public` (`StoreHouseRouter.java:37`).
  - Example: `ChannelsResource` `@Path(PUBLIC_BASE_PATH)` (`resources/api/ChannelsResource.java:74`); GET/POST `/Accounts/{accountSid}/Channels` (`:133-186`); `@DELETE` (`:481`).
  - Resource set: `resources/` (Account, Developer, DeveloperAdminView, Internal, InternalConnectedServices[V2], Marketing, MessageTemplate, MessageTemplatePublicEndpoint, Service, Vendor, VendorAdminView) + `resources/api/` (Channels, Credentials, Public) + `resources/ui/`.
- **Kafka producer:** module lifecycle events — topics `Marketplace.ModuleInstallEvents`, `Channels.ModuleInstallData` (`marketplace/ModuleService.java:31-32`); publish methods `:211-219`.
- **Kafka consumer:** number inventory — topic `Numbers.InventoryDidUpdates` (`kafka/numberevents/NumberEventConsumer.java:20`, config `conf/messaging-ott-storehouse-local.yml:174`), processor `NumberEventProcessor.java`, wired `StoreHouseService.java:579-592`.
- **SQS producer:** `sqs/SqsEnqueuer.java`, queue `messaging-channels-sender-status-update-events` (`conf/...local.yml:216-219`), event types `sqs/event/`.

## Data stores

- **Aurora/MySQL (primary):** source+replica DBIs via `AuroraDBIFactory` (`StoreHouseService.java:320-337`). Schema reference `init.sql` — tables `module_types`, `integration_points`, `modules`, `module_specifications`, `module_integrations`, `module_installs`, `module_install_configurations`, `configuration_to_integrations`. DDL applied to RDS **outside this repo** (inferred). SQL lives in JDBI DAO annotations, e.g. `db/dao/MarketplaceDAO.java:32-127`.
- **DynamoDB (secondary):** deleted WhatsApp templates, 30-day TTL. Table `channels.messaging-ott-storehouse.deleted-templates` (`conf/dynamodb/*.json`); code `dynamodb/DeletedTemplateDao.java`, wired `StoreHouseService.java:454-457`. Created via AWS CLI/console + Admiral IAM, **not Terraform** (`conf/dynamodb/README.md:49-53`).

## Layering

| Layer | Where |
|---|---|
| Resources (HTTP) | `resources/`, `resources/api/`, `resources/ui/` |
| Controllers (orchestration) | `controllers/` (ConnectedService, ModuleDataDelete, ModuleInstallationConfiguration) |
| Services (business logic) | `db/` (MySqlUserDataService, ConnectedServicesDataService…), `marketplace/` (ModuleService, LifecycleEventService), `modules/` |
| DAOs (JDBI) | `db/dao/` (+ mappers `db/jdbi/mappers`, `db/dao/*Mapper.java`) |
| Downstream clients | `clients/` (WhatsAppK8sOrch, StoredCredentials, RateQueueOtt, FeatureService) |
| DTOs/domain | `protocol/` module |
| Config | `config/` + runtime `conf/messaging-ott-storehouse-local.yml` |
| Composition root | `StoreHouseService.run()` (`StoreHouseService.java:267-593`) |

## PLAYBOOK — common changes and the files to touch

1. **Add/modify a REST endpoint:** add method + `@Path`/`@GET`/etc. in the relevant `resources/` (or `resources/api/`) class; add path constant to `StoreHouseRouter.java`; register the resource in `StoreHouseService.java:556-577`; add controller/service logic; add test under `service/src/test/...`.
2. **Add/change a DB query or table:** edit the JDBI DAO in `db/dao/` (`@SqlQuery`/`@SqlUpdate`), add/adjust row mapper (`db/dao/*Mapper.java`, `db/jdbi/mappers/`), reflect schema in `init.sql`. Actual DDL is applied to RDS outside this repo (inferred).
3. **Module-install lifecycle / Kafka events:** `marketplace/ModuleService.java` (topics/publish) + callers `controllers/ModuleDataDeleteController.java`, `resources/DeveloperResource.java`; tests in `service/src/test/.../marketplace`.
4. **Deleted-template / DynamoDB:** `dynamodb/DeletedTemplateDao.java`, `dynamodb/DeletedTemplateItem.java`, table def `conf/dynamodb/*.json`, `modules/templates/WhatsappTemplateService.java`.
5. **Number-event consumption:** `kafka/numberevents/NumberEventConsumer.java` / `NumberEventProcessor.java`, topic config `conf/...local.yml:174`.
6. **New downstream client:** add client in `clients/`, config class in `config/`, wire in `StoreHouseService.java`, add base-URL env var in `chart/values.yaml:327-345`.
7. **Config / dep bumps:** `pom.xml` (+ module poms), `conf/messaging-ott-storehouse-local.yml`.
8. **Deploy/infra:** `chart/values*.yaml` + `chart/templates/*`, `argocd/app/.../*.yaml`, `.buildkite/` + `cluster-config/*.json` (new cluster = new argocd app + cluster-config entry — inferred).

## Deploy

- Buildkite: `.buildkite/pipeline.yaml` (env-gated fan-out), `.buildkite/build/build-and-validate.yml`, `.buildkite/deploy/otk-deploy.yaml` (`SERVICE_NAME: messaging-ott-storehouse:48`; uploads shared `pipelines/modules/pipeline-deploy.yml`), `.buildkite/deploy/cluster-config/{dev,stage,prod}.json`.
- Helm: `chart/` (`values.yaml` + `values-{dev,stage,prod}[-us-east-1].yaml`; templates Rollout/Keda/VirtualService/Canary/EnvoyFilter/AnalysisTemplate). Admiral secrets `chart/values.yaml:349-354`.
- ArgoCD: `argocd/app/{dev,stage,prod}/us-east-1/*.yaml` → deploy repo `messaging-ott-storehouse-deploy`.
- Docker: `service/Dockerfile`, `Dockerfile.local`. Snapshot/PR-label deploys `README.md:54-63`.

## Tests

- **Unit:** `service/src/test/java/com/twilio/ott/storehouse/` mirroring main packages (+ `protocol/src/test`, `client/src/test`). Run `mvn test` (`CLAUDE.md:57-66`).
- **Cluster/smoke:** `chart/tests/test.sh <team> <aws_account> <env> <region>`; chart workflow templates `chart/templates/Workflow*.yaml`.
- **Load:** `load-test/` module (JMeter `storehouse-base.jmx`).
- No dedicated `integration/`/`e2e/` source dir (inferred — integration checks are the chart smoke test + load module).

## Ops helpers

Backfill/operational scripts in `scripts/` (`updateModuleInstallData`, `lifecycle-events-backfill`, `backfill_message_limit`, `patchMps`, `slowqueryfixes`). ADRs in `docs/adr/`.

## Source anchors (re-derive from these)

`README.md`, `CLAUDE.md`, `pom.xml`, `about.yaml`, `service/src/main/java/com/twilio/ott/storehouse/StoreHouseService.java`, `.../StoreHouseRouter.java`, `resources/**`, `controllers/**`, `db/**`, `marketplace/**`, `kafka/**`, `sqs/**`, `dynamodb/**`, `clients/**`, `protocol/`, `conf/messaging-ott-storehouse-local.yml`, `conf/dynamodb/`, `init.sql`, `chart/`, `argocd/`, `.buildkite/`, `Makefile`.
