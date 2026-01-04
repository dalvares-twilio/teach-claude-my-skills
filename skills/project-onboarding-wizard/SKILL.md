---
name: project-onboarding-wizard
description: Interactive wizard to onboard new Twilio projects to the universal bug detection system. Configures BigQuery, Jira, and error patterns in the project registry.
---

# Project Onboarding Wizard

## Overview

Interactive wizard that guides users through adding new Twilio projects to the centralized project registry. Enables the universal auto-bug-detector to work with any Twilio project.

## When to Use

- "Add a new project to bug detection"
- "Onboard {project-name} to auto-bug-detector"
- "Set up bug scanning for {service}"
- "Configure a new Twilio project"
- First time setting up a project for bug detection

## Pre-Approved Actions

- Reading ~/.claude/project-registry.yaml
- Writing to ~/.claude/project-registry.yaml
- Executing BigQuery schema discovery queries
- Reading existing skill files for reference

## Instructions

### Step 1: Welcome and Project Basics

**Display welcome message:**
```
# Project Onboarding Wizard

This wizard will guide you through adding a new Twilio project to the
universal bug detection system.

Once configured, you can scan this project for bugs using:
  "Scan {project_id} for bugs from last N hours"

Let's get started!
```

**Collect basic information:**

```
1. What is the project ID? (lowercase, no spaces, used in commands)
   Example: "ottm", "taskrouter", "verify"
   >

2. What is the human-readable project name?
   Example: "OTT Management API", "TaskRouter", "Verify Service"
   >

3. What is the acronym? (optional, for display)
   Example: "OTTM", "TR", "VS"
   >

4. What team owns this project?
   Example: "Sender Management", "Flex TaskRouter", "Verify Team"
   >

5. Where is the repository located? (optional, for code review)
   Example: "~/Projects/messaging-ott-management-api"
   >
```

### Step 2: BigQuery Configuration

**Ask for BigQuery details:**

```
## BigQuery Configuration

6. What is the GCP project ID?
   Example: "qtco-messaging-channels", "twilio-taskrouter"
   >

7. What are the dataset names for each environment?
   dev:   [default: "dev"] >
   stage: [default: "stage"] >
   prod:  [default: "prod"] >

8. What is the main application logs table name?
   Example: "app_messaging_ott_management_api_mgmt_stdout"
   >

9. Do you have a separate access logs table? (y/n)
   If yes, what is the table name?
   >
```

**Offer schema discovery:**

```
Would you like me to discover the table schema automatically? (y/n)
This will query BigQuery to find available columns.
```

**If yes, execute schema discovery:**
```sql
SELECT column_name, data_type
FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = '{table}'
ORDER BY ordinal_position
```

### Step 3: Column Mapping

**Display discovered columns (if available) or ask manually:**

```
## Column Mapping

Map your table columns to the standard fields used by bug detection.

Available columns: timestamp, level, msg, error, request_id, account_sid, ...

10. Which column contains the timestamp?
    [default: "timestamp"] >

11. Which column contains error messages/details?
    [default: "error"] >

12. Which column contains log level (error/warning/info)?
    [default: "level"] >

13. Which column contains the request ID? (optional)
    [default: "request_id"] >

14. Which column is used for partitioning?
    [default: "PARTITIONDATE"] >

15. Any additional columns to include in bug reports? (comma-separated)
    Example: "endpoint,workflow,sender_sid"
    >
```

### Step 4: Auto-Detection Patterns

**Configure table name patterns for auto-detection:**

```
## Auto-Detection Patterns

These patterns help auto-bug-detector identify your project from table names.

16. Enter patterns that uniquely identify this project (one per line, empty line to finish):
    Example patterns for OTTM: "messaging_ott_management", "ottm", "senders"

    Pattern 1 > {project_id}
    Pattern 2 >
    Pattern 3 >
```

### Step 5: Jira Configuration

**Ask for Jira settings:**

```
## Jira Configuration

17. What is the Jira project key?
    Example: "MSGADVCHNL", "TASKROUTER", "VERIFY"
    >

18. What value should be used for "Team (migrated)" field?
    Example: "Sender Management", "Flex TaskRouter"
    >

19. What issue type should be used for bug tickets?
    Options: Task, Bug, Story
    [default: "Task"] >

20. Default epic for tickets? (optional, press Enter to ask each time)
    Example: "MSGADVCHNL-11802"
    >
```

### Step 6: Custom Error Patterns (Optional)

**Ask about custom error patterns:**

```
## Custom Error Patterns (Optional)

Would you like to define custom error patterns for this project? (y/n)

Custom patterns help classify errors specific to your service:
- Expected behaviors: External API errors, validation failures
- Bug indicators: Internal errors, data corruption patterns
```

**If yes, collect patterns:**

```
### Expected Behavior Patterns (not bugs)

Enter patterns for errors that are expected behavior (empty line to finish):

Pattern > Meta API.*phone already registered
Reason  > External validation - phone already registered on WhatsApp

Pattern > Resource already exists
Reason  > Duplicate resource (idempotency working correctly)

Pattern >

### Bug Indicator Patterns

Enter patterns that indicate bugs in your code (empty line to finish):

Pattern > Unable to process JSON
Reason  > Malformed payload in internal service

Pattern > internal server error
Reason  > Unhandled exception

Pattern >
```

### Step 7: Error Mapping Scanner (Optional)

**Ask about external API error mapping:**

```
## Error Mapping Scanner (Optional)

Does this project map errors from an external API (like Meta Graph API)? (y/n)

If yes, we can scan for unmapped error codes in your codebase.
```

**If yes, collect error mapping config:**

```
21. What is the name of the external API?
    Example: "Meta Graph API", "Twilio REST API", "SendGrid API"
    >

22. What patterns identify these external errors in logs? (comma-separated)
    Example: "OAuthException,GraphMethodException"
    >

23. Which files contain your error mapping code? (relative to repository root)
    File 1 > internal/management/workflow/activity_error_handler.go
    File 2 > internal/management/processor/parser.go
    File 3 >

24. What is the variable name that holds the error mapping?
    Example: "metaErrorMapping", "errorCodeMap"
    >
```

### Step 8: Review and Confirm

**Display configuration summary:**

```
## Configuration Summary

Project ID: {project_id}
Name: {name}
Team: {team}
Repository: {repository}

BigQuery:
  Project: {gcp_project}
  Table: {gcp_project}.{env}.{table}
  Columns: timestamp={ts_col}, error={err_col}, level={lvl_col}

Auto-Detection Patterns:
  - {pattern1}
  - {pattern2}

Jira:
  Project: {jira_project}
  Team Field: {team_field}
  Issue Type: {issue_type}

Custom Error Patterns:
  Expected: {expected_count} patterns
  Bugs: {bug_count} patterns

Error Mapping Scanner: {enabled/disabled}
{If enabled: External API: {api_name}}

---

Does this look correct? (y/n)
```

### Step 9: Save Configuration

**If confirmed, append to registry:**

```yaml
# Append to ~/.claude/project-registry.yaml

  {project_id}:
    name: "{name}"
    acronym: "{acronym}"
    team: "{team}"
    repository: "{repository}"

    bigquery:
      project: "{gcp_project}"
      datasets:
        dev: "{dev_dataset}"
        stage: "{stage_dataset}"
        prod: "{prod_dataset}"
      tables:
        app_logs: "{app_logs_table}"
        {access_logs: "{access_logs_table}"}
      table_patterns:
        - "{pattern1}"
        - "{pattern2}"
      columns:
        timestamp: "{ts_col}"
        error: "{err_col}"
        level: "{lvl_col}"
        request_id: "{req_id_col}"
        partition: "{partition_col}"
        {additional_columns}

    jira:
      project_key: "{jira_project}"
      team_field: "{team_field}"
      issue_type: "{issue_type}"
      default_epic: {epic or null}

    {error_patterns section if defined}

    error_mapping:
      enabled: {true/false}
      {if enabled: external_api, error_patterns, handler_files, mapping_variable}
```

**Display success message:**

```
## Setup Complete!

Project "{name}" has been added to the registry.

You can now scan for bugs using:
  "Scan {project_id} for bugs from last 4 hours"
  "Scan {project_id} prod logs for bugs"

The auto-bug-detector will:
  1. Query {gcp_project}.{env}.{app_logs_table}
  2. Apply your custom error patterns
  3. Create tickets in {jira_project}
  {If error_mapping enabled: 4. Check for unmapped {api_name} error codes}

Happy bug hunting!
```

### Step 10: Offer Additional Actions

```
Would you like to:

1. Scan {project_id} for bugs now (last 4 hours)
2. Generate a monitoring skill for {project_id}
3. Add another project
4. Done
```

## Validation Rules

**Project ID:**
- Lowercase letters, numbers, hyphens only
- No spaces
- Must be unique in registry

**BigQuery table:**
- Must be accessible with current credentials
- Validate by running: `bq show {project}:{dataset}.{table}`

**Jira project:**
- Must be a valid project key
- User must have access

## Error Handling

**If registry doesn't exist:**
```
Creating new project registry at ~/.claude/project-registry.yaml...
```

**If project ID already exists:**
```
Project "{project_id}" already exists in registry.
Would you like to:
1. Update existing configuration
2. Choose a different project ID
3. Cancel
```

**If BigQuery table not found:**
```
Could not find table {project}.{dataset}.{table}
Please verify:
1. Table name is correct
2. You have access to this table
3. Dataset name is correct for the environment

Try again? (y/n)
```

## Example Session

```
User: "Add taskrouter to bug detection"

Bot:
# Project Onboarding Wizard

Let's add TaskRouter to the universal bug detection system.

1. Project ID? > taskrouter
2. Human-readable name? > TaskRouter
3. Acronym? > TR
4. Team? > Flex TaskRouter
5. Repository? > ~/Projects/taskrouter

## BigQuery Configuration

6. GCP project? > twilio-taskrouter
7. Datasets - using defaults (dev/stage/prod)
8. App logs table? > taskrouter_app_logs
9. Access logs table? > (none)

Discovering schema...
Found columns: timestamp, error_message, severity, request_id, workspace_sid...

## Column Mapping

10. Timestamp column? > timestamp
11. Error column? > error_message
12. Level column? > severity
13. Request ID column? > request_id
14. Partition column? > _PARTITIONDATE

## Auto-Detection Patterns

15. Pattern 1 > taskrouter
    Pattern 2 > workspace
    Pattern 3 >

## Jira Configuration

16. Jira project key? > TASKROUTER
17. Team field? > Flex TaskRouter
18. Issue type? > Bug

## Custom Error Patterns

Define custom patterns? > n

## Error Mapping Scanner

Map external API errors? > n

## Configuration Summary
[summary displayed]

Correct? > y

Setup Complete!

Project "TaskRouter" added. Scan with:
  "Scan taskrouter for bugs from last 4 hours"
```

## Registry File Format

**Location:** `~/.claude/project-registry.yaml`

**Template entry:**
```yaml
  {project_id}:
    name: "{name}"
    acronym: "{acronym}"
    team: "{team}"
    repository: "{repository}"

    bigquery:
      project: "{gcp_project}"
      datasets:
        dev: "dev"
        stage: "stage"
        prod: "prod"
      tables:
        app_logs: "{table_name}"
      table_patterns:
        - "{pattern}"
      columns:
        timestamp: "timestamp"
        error: "error"
        level: "level"
        request_id: "request_id"
        partition: "PARTITIONDATE"

    jira:
      project_key: "{key}"
      team_field: "{team}"
      issue_type: "Task"
      default_epic: null

    error_patterns:
      expected: []
      bugs: []

    error_mapping:
      enabled: false
```

## Related Skills

- **auto-bug-detector**: Uses projects configured by this wizard
- **universal-jira-ticket-creator**: Creates tickets using project's jira config
- **universal-error-mapping-scanner**: Scans for unmapped errors using project config
- **bigquery-skill-builder**: Can generate monitoring skills after onboarding
