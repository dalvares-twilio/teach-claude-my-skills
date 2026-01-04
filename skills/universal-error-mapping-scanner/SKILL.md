---
name: universal-error-mapping-scanner
description: Scan BigQuery logs for external API error codes and identify which ones are NOT handled in a project's codebase. Works with any Twilio project configured in the registry.
---

# Universal Error Mapping Scanner

## Overview

Proactively identifies gaps in external API error handling by:
1. Loading project configuration from the registry
2. Querying BigQuery for external API errors matching project patterns
3. Cross-referencing with the project's codebase error handlers
4. Reporting unhandled codes with occurrence counts and context

**Works with ANY project** that has `error_mapping.enabled: true` in the registry.

## When to Use

- "Scan {project_id} for missing error mappings"
- "Find unhandled {external_api} error codes in {project}"
- "Check for error mapping gaps"
- "What errors are we not handling?"
- Called by auto-bug-detector when `project.error_mapping.enabled: true`

## Pre-Approved Permissions

- **BigQuery queries**: Execute `bq query` commands
- **Reading codebase files**: Read handler files from project repository
- **Reading registry**: Read ~/.claude/project-registry.yaml
- **Writing to /tmp/**: Store intermediate results

## Configuration (From Registry)

When using `project_id`, loads config from `~/.claude/project-registry.yaml`:

```yaml
projects:
  {project_id}:
    repository: "~/Projects/my-service"
    error_mapping:
      enabled: true
      external_api: "Meta Graph API"        # Name of external API
      error_patterns:                        # Patterns to match in logs
        - "OAuthException"
        - "GraphMethodException"
      handler_files:                         # Files containing error mappings
        - "internal/workflow/error_handler.go"
        - "internal/processor/parser.go"
      mapping_variable: "metaErrorMapping"   # Variable name in code
```

**Can also accept explicit parameters** if project_id not provided.

## Instructions

### Step 1: Load Configuration

**Option A: Project ID provided**
```
User: "Scan ottm for missing error mappings"
→ Load config from registry.projects.ottm.error_mapping
```

**Option B: Explicit config provided**
```
User provides:
- repository, external_api, error_patterns, handler_files, mapping_variable
→ Use provided values directly
```

**Option C: No config**
```
Check registry for projects with error_mapping.enabled: true
Offer selection to user
```

**If error_mapping.enabled is false:**
```
Error mapping is not configured for project "{project_id}".
To enable, add error_mapping section to ~/.claude/project-registry.yaml
```

### Step 2: Parse Parameters

Extract from user input or use defaults:
- **Time window**: Default 30 days
- **Environment**: Default prod
- **Min occurrences**: Default 10

From registry:
- `project.repository`
- `project.error_mapping.external_api`
- `project.error_mapping.error_patterns`
- `project.error_mapping.handler_files`
- `project.error_mapping.mapping_variable`
- `project.bigquery.project`
- `project.bigquery.datasets.{env}`
- `project.bigquery.tables.app_logs`

### Step 3: Query BigQuery for External API Errors

**Build query dynamically from project config:**

```sql
=== BIGQUERY QUERY ({external_api} Errors) ===
WITH api_errors AS (
  SELECT
    error,
    REGEXP_EXTRACT(error, r'"code":(\d+)') as error_code,
    REGEXP_EXTRACT(error, r'"error_subcode":(\d+)') as error_subcode,
    REGEXP_EXTRACT(error, r'"type":"([^"]+)"') as error_type,
    REGEXP_EXTRACT(error, r'"message":"([^"]{1,150})') as error_message,
    endpoint,
    workflow
  FROM `{bigquery_project}.{env}.{app_logs_table}`
  WHERE ({error_pattern_conditions})
    AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
)
SELECT
  error_code,
  COALESCE(error_subcode, "0") as error_subcode,
  error_type,
  ANY_VALUE(error_message) as sample_message,
  ANY_VALUE(endpoint) as sample_endpoint,
  ANY_VALUE(workflow) as sample_workflow,
  COUNT(*) as occurrence_count
FROM api_errors
WHERE error_code IS NOT NULL
GROUP BY error_code, error_subcode, error_type
HAVING COUNT(*) >= {min_occurrences}
ORDER BY occurrence_count DESC
```

**Where `{error_pattern_conditions}` is built from `error_patterns`:**
```sql
(error LIKE "%OAuthException%" OR error LIKE "%GraphMethodException%" OR ...)
```

### Step 4: Read Codebase Error Handlers

Read each file in `project.error_mapping.handler_files`:

```bash
Read {repository}/{handler_files[0]}
Read {repository}/{handler_files[1]}
...
```

### Step 5: Extract Handled Codes

Parse files to find the mapping variable and extract handled codes:

**Pattern to match:**
```go
var {mapping_variable} = map[int]map[int]types.ResponseType{
    100: {
        2388028: types.SomeResponse,
        2388112: types.SomeResponse,
    },
    ...
}
```

**Extract into set:**
```
handled_codes = {
    (100, 2388028),
    (100, 2388112),
    ...
}
```

### Step 6: Cross-Reference to Find Gaps

```python
unhandled = []
for error in bigquery_results:
    code = (error['error_code'], error['error_subcode'])
    if code not in handled_codes:
        unhandled.append(error)
```

### Step 7: Generate Report

```markdown
## {external_api} Error Mapping Gap Analysis

**Project:** {project.name} ({project_id})
**Scan Date:** {current_date}
**Environment:** {env}
**Time Window:** Last {days} days
**Minimum Occurrences:** {min_occurrences}

### Summary

| Metric | Count |
|--------|-------|
| Total Unique Error Codes | {total} |
| Handled in Codebase | {handled_count} |
| **Unhandled (Gaps)** | **{unhandled_count}** |

---

### Handled Error Codes (Reference)

Found in: {handler_files}
Variable: {mapping_variable}

| Code | Subcode | Mapped Response |
|------|---------|-----------------|
| {code} | {subcode} | {response_type} |

---

### Unhandled Error Codes (ACTION REQUIRED)

{IF unhandled_count > 0}
| Code | Subcode | Occurrences | Context | Message | Suggested Action |
|------|---------|-------------|---------|---------|------------------|
| {code} | {subcode} | {count} | {endpoint}/{workflow} | {message} | Add mapping |

### Files to Modify

- {handler_files[0]}
- {handler_files[1]}
{ENDIF}

{IF unhandled_count == 0}
All {external_api} error codes are properly mapped in codebase.
{ENDIF}
```

### Step 8: Offer Ticket Creation (Optional)

If gaps found:

```
Found {N} unhandled {external_api} error codes.

Create Jira tickets?
1. Yes - Create tech debt ticket for all gaps
2. No - Just report
```

**If creating tickets:**
Use `universal-jira-ticket-creator` with `project_id`:
- Summary: "Add {external_api} error mappings for unhandled codes"
- Description: Include all gaps with occurrences and recommendations

## Example Sessions

### Session 1: Project ID from Registry

```
User: "Scan ottm for missing Meta error mappings"

Claude:
## Loading Configuration
Project: ottm (OTT Management API)
External API: Meta Graph API
Repository: ~/Projects/messaging-ott-management-api
Handler Files: internal/management/workflow/activity_error_handler.go

## Querying BigQuery
Environment: prod
Time Window: Last 30 days
[query executed]

Found 13 unique Meta error code combinations.

## Reading Codebase
Reading activity_error_handler.go...
Reading parser.go...
Extracted 15 handled code/subcode combinations.

## Meta Graph API Error Mapping Gap Analysis

**Project:** OTT Management API (ottm)
**Scan Date:** 2026-01-04

### Summary
| Metric | Count |
|--------|-------|
| Total Unique Error Codes | 13 |
| Handled in Codebase | 10 |
| **Unhandled (Gaps)** | **3** |

### Unhandled Error Codes

| Code | Subcode | Occurrences | Context | Message |
|------|---------|-------------|---------|---------|
| 138015 | 2593145 | 85 | update/async | Calling APIs cannot be enabled |
| 131031 | 0 | 3 | create/async | Business Account locked |
| 100 | 1752278 | 296 | getall/sync | Failed to get verification state |

Create Jira ticket for these gaps? (y/n)
```

### Session 2: Multiple Projects Available

```
User: "Check for error mapping gaps"

Claude:
Projects with error_mapping enabled:
1. ottm - OTT Management API (Meta Graph API)
2. verify - Verify Service (Twilio REST API)

Which project? > 1

[continues with ottm config]
```

## Integration Points

**Called by:**
- `auto-bug-detector` - when project has `error_mapping.enabled: true`

**Uses:**
- `universal-jira-ticket-creator` - for gap tickets

**Replaces:**
- `meta-error-mapping-scanner` (OTTM-specific version)

## Related Skills

- **auto-bug-detector**: Orchestrates this as Stage 3 (if enabled)
- **project-onboarding-wizard**: Configures error_mapping settings
- **universal-jira-ticket-creator**: Creates tickets for gaps
- **bug-analyzer**: Classifies errors as bugs or expected behavior
