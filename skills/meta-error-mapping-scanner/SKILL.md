---
name: meta-error-mapping-scanner
description: "DEPRECATED - use universal-error-mapping-scanner instead. Only use if user explicitly says 'Meta error mapping' or 'Meta API error codes not handled'."
---

# Meta Error Mapping Scanner

> **DEPRECATED**: This skill is deprecated. Use `universal-error-mapping-scanner` with `project_id="ottm"` instead.
>
> The universal version loads configuration from `~/.claude/project-registry.yaml` and works with any Twilio project that has `error_mapping.enabled: true`.
>
> **Migration:**
> - Old: `Scan for missing Meta error mappings`
> - New: `Scan ottm for missing error mappings` (auto-detects from registry)

## Overview

Proactively identifies gaps in Meta API error handling by:
1. Querying BigQuery for all Meta error codes/subcodes in production
2. Cross-referencing with the OTTM codebase error handlers
3. Reporting unhandled codes with occurrence counts and context
4. Optionally creating Jira tickets for significant gaps

## When to Use

**ONLY invoke if user explicitly says:**
- "Meta error mapping" or "Meta error mappings"
- "Unhandled Meta error codes"
- "Meta API error mapping gaps"

**Otherwise use `universal-error-mapping-scanner` with project_id="ottm"**

**DO NOT invoke for general bug scanning or error detection.**

## Pre-Approved Permissions

The following actions are **pre-approved**:

- **BigQuery queries**: Execute `bq query` commands without asking
- **Reading codebase files**: Read error handler files from OTTM repo
- **Writing to /tmp/**: Store intermediate results
- **Grep/search operations**: Search codebase for error codes

## Configurable Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Time window | 30 days | How far back to scan logs |
| Environment | prod | dev/stage/prod |
| Min occurrences | 10 | Minimum count to report |
| Repository path | ~/Projects/messaging-ott-management-api | OTTM codebase location |
| Create tickets | ask | Auto-create Jira tickets for gaps |

## Instructions

### Step 1: Parse User Request

Extract parameters from user input:
- Time window (e.g., "last 7 days", "last month")
- Environment (dev/stage/prod)
- Minimum occurrence threshold
- Whether to create tickets

**Defaults:**
```
Time window: 30 days
Environment: prod
Min occurrences: 10
Create tickets: ask user
```

### Step 2: Query BigQuery for Meta Errors

**Print query before executing:**

```sql
=== BIGQUERY QUERY (Meta Errors) ===
WITH meta_errors AS (
  SELECT
    error,
    REGEXP_EXTRACT(error, r'"code":(\d+)') as meta_code,
    REGEXP_EXTRACT(error, r'"error_subcode":(\d+)') as meta_subcode,
    REGEXP_EXTRACT(error, r'"type":"([^"]+)"') as error_type,
    REGEXP_EXTRACT(error, r'"message":"([^"]{1,150})') as meta_message,
    REGEXP_EXTRACT(error, r'"error_user_msg":"([^"]{1,150})') as error_user_msg,
    endpoint,
    workflow
  FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
  WHERE (error LIKE "%OAuthException%"
     OR error LIKE "%GraphMethodException%"
     OR error LIKE "%Meta Graph API%"
     OR error LIKE "%FacebookGraphApi%")
    AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
)
SELECT
  meta_code,
  COALESCE(meta_subcode, "0") as meta_subcode,
  error_type,
  ANY_VALUE(meta_message) as sample_message,
  ANY_VALUE(error_user_msg) as sample_user_msg,
  ANY_VALUE(endpoint) as sample_endpoint,
  ANY_VALUE(workflow) as sample_workflow,
  COUNT(*) as occurrence_count
FROM meta_errors
WHERE meta_code IS NOT NULL
GROUP BY meta_code, meta_subcode, error_type
HAVING COUNT(*) >= {min_occurrences}
ORDER BY occurrence_count DESC
```

**Execute and save results** to `/tmp/meta_errors_scan.json`

### Step 3: Read Codebase Error Handlers

Read the following files from the OTTM repository:

**File 1:** `internal/management/workflow/activity_error_handler.go`
- Contains `metaErrorMapping` map
- Format: `code: { subcode: TwilioErrorResponse }`

**File 2:** `internal/management/processor/parser.go`
- Contains `metaJSONErrorMapping` map
- Same format as above

**File 3:** `internal/consts/workflow/consts.go`
- Contains named constants for known error codes

### Step 4: Extract Handled Codes from Codebase

Parse the error handler files to extract all handled code/subcode combinations.

**Pattern to match in activity_error_handler.go:**
```go
var metaErrorMapping = map[int]map[int]types.TwilioErrorResponse{
    100: {
        2388028: types.TwilioMaxNumberOfWABAPhoneNumbersErrorResponse,
        2388112: types.TwilioMaxNumberOfWABAPhoneNumbersErrorResponse,
        ...
    },
    ...
}
```

**Extract into a set of handled codes:**
```
handled_codes = {
    (100, 2388028),
    (100, 2388112),
    (100, 2388009),
    (33, 0),
    (80008, 0),
    ...
}
```

### Step 5: Cross-Reference to Find Gaps

Compare BigQuery results with handled codes:

```python
unhandled = []
for error in bigquery_results:
    code = (error['meta_code'], error['meta_subcode'])
    if code not in handled_codes:
        unhandled.append(error)
```

**Filter out known exceptions:**
- Code 12400 alone (k8s wrapper, inner error matters)
- Code 503 (service unavailable - transient)

### Step 6: Categorize Unhandled Errors

For each unhandled error, determine:

**Category based on endpoint:**
- `get`, `get_ui`, `getall` → GET operations
- `create` → CREATE operations
- `update` → UPDATE operations
- `delete` → DELETE operations

**Severity based on occurrences:**
- High: > 100 occurrences/month
- Medium: 10-100 occurrences/month
- Low: < 10 occurrences/month

**Suggested response based on error type:**
- Rate limiting (80008, 133016) → `TwilioTooManyRequestsErrorResponse`
- Validation errors → `TwilioValidateRequestErrorResponse`
- Phone number issues → `TwilioPhoneNumberAlreadyRegisteredErrorResponse`
- Calling issues → `TwilioChangeCallingStatusErrorResponse`
- Transient errors → Retryable response (503)

### Step 7: Generate Report

```markdown
## Meta Error Mapping Gap Analysis

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

| Code | Subcode | Mapped Response |
|------|---------|-----------------|
| 100 | 2388028 | TwilioMaxNumberOfWABAPhoneNumbersErrorResponse |
| 33 | 0 | TwilioValidateRequestErrorResponse |
| ... | ... | ... |

---

### Unhandled Error Codes (ACTION REQUIRED)

#### High Severity (>100 occurrences)

| Code | Subcode | Occurrences | Context | Message | Suggested Response |
|------|---------|-------------|---------|---------|-------------------|
| {code} | {subcode} | {count} | {endpoint}/{workflow} | {message} | {suggestion} |

#### Medium Severity (10-100 occurrences)

| Code | Subcode | Occurrences | Context | Message | Suggested Response |
|------|---------|-------------|---------|---------|-------------------|
| {code} | {subcode} | {count} | {endpoint}/{workflow} | {message} | {suggestion} |

---

### Recommendations

1. **{code}/{subcode}**: Add mapping to `{suggested_response}` - {reason}
2. ...

### Files to Modify

- `internal/management/workflow/activity_error_handler.go`
- `internal/management/processor/parser.go`
- `internal/consts/workflow/consts.go` (for new constants)
```

### Step 8: Offer Ticket Creation (Optional)

If unhandled errors found:

```
Found {N} unhandled Meta error codes.

Create Jira tickets?
1. Yes - Create tickets for all gaps
2. Yes - Create tickets for high severity only
3. No - Just report
```

**If creating tickets:**

Group errors by operation type:
- GET/GetAll errors → One ticket
- CREATE/UPDATE errors → One ticket

Use `jira-inator:jira-ticket-creator` skill with:
- Project: MSGADVCHNL
- Type: Task
- Parent: Ask user for epic
- Summary: "Add Meta error code mappings for {operation} operations"
- Description: Include all unhandled codes, occurrences, and recommendations

## Query Templates

### Template 1: All Meta Errors (Grouped)
```sql
WITH meta_errors AS (
  SELECT
    REGEXP_EXTRACT(error, r'"code":(\d+)') as meta_code,
    REGEXP_EXTRACT(error, r'"error_subcode":(\d+)') as meta_subcode,
    REGEXP_EXTRACT(error, r'"type":"([^"]+)"') as error_type,
    REGEXP_EXTRACT(error, r'"message":"([^"]{1,150})') as meta_message,
    endpoint,
    workflow
  FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
  WHERE (error LIKE "%OAuthException%" OR error LIKE "%GraphMethodException%")
    AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
)
SELECT
  meta_code,
  COALESCE(meta_subcode, "0") as meta_subcode,
  error_type,
  ANY_VALUE(meta_message) as sample_message,
  ANY_VALUE(endpoint) as sample_endpoint,
  ANY_VALUE(workflow) as sample_workflow,
  COUNT(*) as occurrence_count
FROM meta_errors
WHERE meta_code IS NOT NULL
GROUP BY 1, 2, 3
HAVING COUNT(*) >= {min_occurrences}
ORDER BY occurrence_count DESC
```

### Template 2: Context for Specific Error
```sql
SELECT
  endpoint,
  workflow,
  COUNT(*) as cnt,
  ANY_VALUE(msg) as sample_msg
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE error LIKE '%"code":{code}%'
  AND error LIKE '%"error_subcode":{subcode}%'
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
GROUP BY endpoint, workflow
ORDER BY cnt DESC
```

## Codebase Parsing Patterns

### Pattern: Extract metaErrorMapping
```bash
grep -E "^\s+[0-9]+:" {repo}/internal/management/workflow/activity_error_handler.go |
  grep -oE "[0-9]+"
```

### Pattern: Extract subcodes
```bash
grep -E "^\s+[0-9]+:" {repo}/internal/management/workflow/activity_error_handler.go -A 10 |
  grep -oE "[0-9]+:"
```

## Example Session

```
User: "Scan for missing Meta error mappings in prod, last 30 days"

Claude:
=== BIGQUERY QUERY (Meta Errors) ===
[query displayed]

Querying BigQuery...
Found 13 unique Meta error code combinations.

=== READING CODEBASE ===
Reading activity_error_handler.go...
Reading parser.go...
Extracted 15 handled code/subcode combinations.

## Meta Error Mapping Gap Analysis

**Scan Date:** 2026-01-04
**Environment:** prod
**Time Window:** Last 30 days

### Summary
| Metric | Count |
|--------|-------|
| Total Unique Error Codes | 13 |
| Handled in Codebase | 8 |
| **Unhandled (Gaps)** | **5** |

### Unhandled Error Codes

| Code | Subcode | Occurrences | Context | Message |
|------|---------|-------------|---------|---------|
| 100 | 1752278 | 296 | getall/sync | Failed to get verification state |
| 2 | 0 | 205 | get/sync | Unexpected error, retry later |
| 138015 | 0 | 110 | update/async | Calling cannot be enabled |
| 138015 | 2593145 | 85 | update/async | Calling APIs cannot be enabled |
| 131031 | 0 | 3 | create/async | Business Account locked |

Create Jira tickets?
1. Yes - Create tickets for all gaps
2. Yes - Create tickets for high severity only
3. No - Just report

User: "1"

Claude:
What parent epic should tickets be associated with?

User: "MSGADVCHNL-12497"

Creating tickets...
✓ MSGADVCHNL-12639: Add Meta error mappings for GET/GetAll operations
✓ MSGADVCHNL-12640: Add Meta error mappings for CREATE/UPDATE operations

Scan complete!
```

## Related Skills

- **request-analyzer**: Analyze specific request IDs for bugs
- **ottm-bigquery-debugging**: Deep-dive debugging with custom queries
- **bug-analyzer**: Classify errors as bugs or expected behavior
- **jira-inator:jira-ticket-creator**: Create Jira tickets for gaps
