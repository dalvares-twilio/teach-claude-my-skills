# Universal Bug Detection System

A Claude Code skill-based system for automated bug detection across Twilio projects. Scans BigQuery logs, classifies errors, and creates Jira tickets automatically.

---

## Prerequisites

### Required

| Requirement | Purpose | Setup |
|-------------|---------|-------|
| **Claude Code CLI** | Run the skills | [Install Claude Code](https://docs.anthropic.com/claude-code) |
| **Twilio Marketplace** | Access Twilio internal plugins | `claude plugin marketplace add twilio-internal/claude-marketplace` |
| **jira-inator plugin** | Create Jira tickets | `claude plugin install jira-inator@twilio` |
| **Google Cloud SDK** | Query BigQuery logs | `brew install google-cloud-sdk` |
| **BigQuery Access** | Read project logs | `gcloud auth login` |

### Optional

| Requirement | Purpose | Setup |
|-------------|---------|-------|
| **Local Repository** | Code review for root cause | Clone the project repo locally |
| **superpowers plugin** | Enhanced agent capabilities | `claude plugin install superpowers@superpowers-marketplace` |

### Installation Order

1. First, add the Twilio internal marketplace:
   ```bash
   claude plugin marketplace add twilio-internal/claude-marketplace
   ```

2. Then install required plugins:
   ```bash
   claude plugin install jira-inator@twilio
   claude plugin install git-tools@twilio
   ```

### Verify Setup

```bash
# Check BigQuery access
bq query --use_legacy_sql=false "SELECT 1"

# Check jira-inator plugin
claude "/plugins"  # Should show jira-inator@twilio
```

### Plugin Configuration

The **jira-inator** plugin requires configuration in `~/.claude/plugins/cache/twilio/jira-inator/<version>/.env`:

```env
JIRA_EMAIL=your.email@twilio.com
JIRA_API_TOKEN=your_jira_api_token
DEFAULT_PROJECT=MSGADVCHNL
TWILIO_JIRA_URL=https://twilio-engineering.atlassian.net
```

To get a Jira API token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Copy it to the `.env` file

---

## Quick Start

### Scan a Project for Bugs

```
"Scan ottm for bugs from last 4 hours"
"Scan k8s-orch prod logs for bugs"
"Scan ottm for bugs from last 24 hours with code review"
```

### Onboard a New Project

```
"Add a new project to bug detection"
"Onboard taskrouter to auto-bug-detector"
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Auto Bug Detection Pipeline                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Load Project    Read ~/.claude/project-registry.yaml        │
│         ↓                                                        │
│  2. Query BigQuery  Scan logs for errors using project config   │
│         ↓                                                        │
│  3. Classify Bugs   Analyze errors: BUG / EXPECTED / IMPROVE    │
│         ↓                                                        │
│  4. Code Review     (Optional) Find root cause in codebase      │
│         ↓                                                        │
│  5. Create Tickets  Auto-create Jira tickets for bugs           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Onboarding a New Project

### Step 1: Start the Wizard

Tell Claude:
```
"Add a new project to bug detection"
```

### Step 2: Provide Project Details

The wizard will ask for:

| Field | Example (OTTM) | Description |
|-------|----------------|-------------|
| Project ID | `ottm` | Lowercase identifier for commands |
| Name | `OTT Management API` | Human-readable name |
| Acronym | `OTTM` | Short abbreviation |
| Team | `Sender Management` | Owning team |
| Repository | `~/Projects/messaging-ott-management-api` | Local repo path (for code review) |

### Step 3: Configure BigQuery

| Field | Example (OTTM) | Description |
|-------|----------------|-------------|
| GCP Project | `qtco-messaging-channels` | BigQuery project ID |
| Datasets | `dev`, `stage`, `prod` | Environment datasets |
| App Logs Table | `app_messaging_ott_management_api_mgmt_stdout` | Main application logs table |
| Access Logs Table | `app_messaging_ott_management_api_mgmt_access` | HTTP access logs table (optional) |

The wizard can **auto-discover** the table schema to help with column mapping.

### Step 4: Map Columns

| Standard Field | Example (OTTM) | Description |
|----------------|----------------|-------------|
| `timestamp` | `timestamp` | When the error occurred |
| `error` | `error` | Error details |
| `level` | `level` | Log level (ERROR, WARN) |
| `request_id` | `request_id` | Request correlation ID |
| `account_id` | `account_sid` | Account identifier |
| `resource_id` | `sender_sid` | Resource identifier |
| `partition` | `PARTITIONDATE` | Table partition column |

### Step 5: Configure Jira

| Field | Example (OTTM) | Description |
|-------|----------------|-------------|
| Project Key | `MSGADVCHNL` | Jira project for tickets |
| Team Field | `Sender Management` | Value for "Team (migrated)" |
| Issue Type | `Task` | Default issue type |
| Default Epic | (optional) | Parent epic for tickets |

### Step 6: Done!

Your project is now in the registry. Scan it with:
```
"Scan ottm for bugs from last 4 hours"
```

---

## Using Auto Bug Detection

### Basic Scan

```
"Scan {project_id} for bugs"
"Scan {project_id} for bugs from last {N} hours"
```

**Examples:**
```
"Scan ottm for bugs"
"Scan k8s-orch for bugs from last 8 hours"
"Scan ottm prod logs for bugs from last 24 hours"
```

### Scan with Code Review

Add "with code review" to find root causes in the codebase:

```
"Scan ottm for bugs from last 4 hours with code review"
```

This will:
1. Find errors in BigQuery
2. Search the codebase for related code
3. Identify root causes with file:line references
4. Suggest fixes

### Scan with Automatic Ticket Creation

```
"Scan ottm for bugs and create tickets"
```

You'll be asked for a parent epic, then tickets are created automatically.

---

## Available Commands

| Command | Description |
|---------|-------------|
| `Scan {project} for bugs` | Run bug detection pipeline |
| `Scan {project} for bugs from last N hours` | Specify time window |
| `Add a new project to bug detection` | Onboard new project |
| `Show project registry for {project}` | View project config |
| `What tickets did you create?` | List created tickets |

---

## Project Registry

All project configurations are stored in:
```
~/.claude/project-registry.yaml
```

### Registry Structure

```yaml
projects:
  ottm:
    name: "OTT Management API"
    team: "Sender Management"
    repository: "~/Projects/messaging-ott-management-api"

    bigquery:
      project: "qtco-messaging-channels"
      datasets:
        dev: "dev"
        stage: "stage"
        prod: "prod"
      tables:
        app_logs: "app_messaging_ott_management_api_mgmt_stdout"
      columns:
        timestamp: "timestamp"
        error: "error"
        level: "level"
        request_id: "request_id"

    jira:
      project_key: "MSGADVCHNL"
      team_field: "Sender Management"
      issue_type: "Task"
```

---

## Currently Registered Projects

| Project ID | Name | Team |
|------------|------|------|
| `ottm` | OTT Management API | Sender Management |
| `k8s-orch` | whatsapp-k8s-orch | Sender Management |

---

## Skills Reference

| Skill | Purpose |
|-------|---------|
| `auto-bug-detector` | Main pipeline orchestrator |
| `project-onboarding-wizard` | Add new projects to registry |
| `bigquery-error-scanner` | Discover unique error patterns |
| `bug-analyzer` | Classify errors as bugs/expected |
| `universal-jira-ticket-creator` | Create tickets for any project |
| `universal-error-mapping-scanner` | Find unmapped external API errors |

---

## Troubleshooting

### "Project not found in registry"

Run the onboarding wizard:
```
"Add {project_name} to bug detection"
```

### "Cannot access BigQuery table"

1. Verify you have access: `bq show {project}:{dataset}.{table}`
2. Check the table name in the registry

### "No errors found"

- Try expanding the time window: `from last 24 hours`
- Check if the correct environment is being scanned (dev/stage/prod)

### Jira ticket creation fails

- Verify the project key exists
- Check you have permission to create tickets
- Remember to set "Team (migrated)" field manually after creation

---

## File Locations

| File | Purpose |
|------|---------|
| `~/.claude/project-registry.yaml` | Project configurations |
| `~/.claude/skills/` | Skill definitions |
| `/tmp/claude_created_tickets.json` | Log of created tickets |
| `/tmp/bigquery_error_signatures_*` | Cached error signatures |
