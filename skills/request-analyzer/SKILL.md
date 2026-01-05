---
name: request-analyzer
description: "Analyze a specific OTTM Request ID (RQ...). ONLY use when user provides an RQ ID like 'analyze RQ123...' or 'what happened in RQ...'. Requires a specific request ID."
---

# Request Analyzer

## Overview

Analyzes any OTTM (Senders API) Request ID to detect bugs and provide a detailed summary of what happened during request processing. Combines BigQuery log analysis with bug classification to give a clear verdict.

## When to Use

**ONLY invoke when user provides a specific Request ID (RQ...):**
- "Analyze request RQ123abc..."
- "What happened in request RQ..."
- "Check RQ... for bugs"

**DO NOT invoke for:**
- General "analyze requests" without a specific ID
- "Find bugs" or "scan for errors" (use auto-bug-detector)
- E2E testing (use senders-e2e-testing)

**This skill REQUIRES a specific RQ ID to function.**

## Pre-Approved Permissions

The following actions are **pre-approved** and do NOT require user confirmation:

- **BigQuery queries**: Execute `bq query` commands without asking
- **Reading from /tmp/**: ALL read operations
- **Writing to /tmp/**: ALL write operations for temporary data
- **Sleep commands**: For any polling needs

## Instructions

### Step 1: Parse Input

Extract from user's request:
- **Request ID**: The RQ... identifier (required)
- **Environment**: dev/stage/prod (optional, will ask if not provided)

**Request ID format**: `RQ[a-f0-9]{32}` (e.g., RQ27ee6ab09ac8b03ad07a4fff868c1fbc)

If environment not specified, use AskUserQuestion:
```
Question: "Which environment should I query?"
Options:
1. dev
2. stage
3. prod
```

### Step 2: Query BigQuery for All Logs

**Print query before executing:**
```
=== BIGQUERY QUERY (Full Request Trace) ===
SELECT timestamp, level, msg, error, workflow, endpoint, sender_sid, sender_id
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = "{request_id}"
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY timestamp ASC
```

**Execute query:**
```bash
CLOUDSDK_PYTHON_SITEPACKAGES=1 bq query --format=json --use_legacy_sql=false '
SELECT timestamp, level, msg, error, workflow, endpoint, sender_sid, sender_id
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = "{request_id}"
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY timestamp ASC
'
```

**Save results** to /tmp/request_trace.json for analysis.

If no logs found, report and exit:
```
No logs found for request {request_id} in {env} environment.
Check:
1. Request ID is correct
2. Environment is correct
3. Request was made within last 7 days
```

### Step 3: Analyze for Errors

**Query for errors/warnings:**
```sql
SELECT timestamp, level, msg, error, workflow, endpoint
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = "{request_id}"
  AND (error IS NOT NULL OR level IN ("error", "warning"))
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY timestamp ASC
```

**Classify each error** using these patterns:

#### BUG Indicators

**System Failures:**
- HTTP 500, 502, 503, 504 errors
- "Internal server error", "Service unavailable"
- "Crash", "Exception", "Fatal", "Panic"
- "NullPointerException", "undefined is not"

**Data Integrity Issues:**
- "Malformed JSON", "Invalid JSON", "Unable to parse"
- "Unable to process JSON" (PiedPiper errors)
- "Missing required field", "Field cannot be null"
- "Data corruption", "Inconsistent state"

**Logic Errors:**
- "Index out of bounds", "Array out of range"
- "Deadlock detected", "Race condition"
- "Unexpected null", "Cannot read property of undefined"
- "Should never happen", "Unreachable code"

**Resource Issues:**
- "Out of memory", "Connection pool exhausted"
- "Too many connections", "Timeout" (internal)

#### EXPECTED BEHAVIOR Indicators

**External API Failures (Meta, etc.):**
- "Meta API" + error code
- "400 response from Meta Graph API"
- Phone number already registered
- Rate limiting from external service
- "Request code error" (Meta OTP issues)

**User Input Validation:**
- HTTP 400, 422 errors with validation message
- "Invalid input", "Validation failed"
- "Missing required parameter"

**Business Rules:**
- HTTP 409 errors
- "Already exists", "Duplicate entry"
- "Resource locked", "Conflict detected"

**Access Control:**
- HTTP 401, 403 errors
- "Unauthorized", "Access denied"

### Step 4: Generate Flow Summary

Parse logs to identify key milestones:

**Sync Phase Milestones:**
- Request received
- Request parsed/validated
- Channel type resolved
- Sender lookup in Storehouse
- Temporal workflow triggered
- HTTP response sent

**Async Phase Milestones:**
- Workflow started
- WABA sync/subscription
- Phone number operations
- OTP operations
- Profile updates
- Workflow completion

**Extract metadata:**
- Operation type (CREATE, GET, UPDATE, DELETE)
- Account SID
- Sender ID
- Sender SID
- Total duration (first to last log timestamp)

### Step 5: Output Report

Generate formatted report:

```markdown
## Request Analysis: {request_id}

### Bug Analysis
| Category | Count |
|----------|-------|
| Errors   | {error_count} |
| Warnings | {warning_count} |
| Total Logs | {total_logs} |

### Verdict: {BUG DETECTED / NO BUGS DETECTED}

---

### Request Summary
| Field | Value |
|-------|-------|
| Request ID | {request_id} |
| Environment | {env} |
| Operation | {operation_type} |
| Account | {account_sid} |
| Sender ID | {sender_id} |
| Sender SID | {sender_sid} |
| Duration | {duration} |
| Status | {final_status} |

---

### Flow Breakdown

#### Sync Phase ({sync_log_count} logs)
| Timestamp | Status | Step |
|-----------|--------|------|
| {ts} | {status} | {description} |
...

#### Async Phase ({async_log_count} logs)
| Timestamp | Status | Step |
|-----------|--------|------|
| {ts} | {status} | {description} |
...

---

### Errors Found

{IF ERRORS}
#### Error 1: {error_msg}
- **Timestamp:** {timestamp}
- **Level:** {level}
- **Workflow:** {sync/async}
- **Classification:** {BUG / EXPECTED BEHAVIOR}
- **Reasoning:** {why this classification}
- **Error Details:**
```json
{error_field}
```

(Repeat for each error)
{ENDIF}

{IF NO ERRORS}
No errors or warnings detected in request processing.
{ENDIF}

---

### Final Status
{Summary of request outcome}
```

### Step 6: Create Jira Tickets (If Bugs Found)

**If bugs were detected:**

1. **Ask for parent epic ONCE:**
```
Question: "What parent epic should bug tickets be associated with?"
Options: (allow empty response for no parent)
Example: MSGADVCHNL-11802
```

2. **For each bug, invoke sender-management-jira-ticket-creator skill:**

Provide bug details:
- Summary: Brief error description
- Description: Full context including:
  - Request ID
  - Timestamp
  - Error message
  - Classification reasoning
  - Flow context (what step failed)
  - Impact assessment
- Project: MSGADVCHNL
- Issue Type: Bug
- Parent: User-provided epic (if any)

3. **Display results:**
```
Created Jira tickets for detected bugs:
- MSGADVCHNL-12345: {bug summary} - {URL}
- MSGADVCHNL-12346: {bug summary} - {URL}

Remember to set "Team (migrated)" field to "Sender Management" for:
- MSGADVCHNL-12345
- MSGADVCHNL-12346
```

**If no bugs detected:**
```
No bugs detected. No Jira tickets created.
```

## Query Templates

### Template 1: Full Request Trace
```sql
SELECT timestamp, level, msg, error, workflow, endpoint, sender_sid, sender_id
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = "{request_id}"
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY timestamp ASC
```

### Template 2: Error Detection
```sql
SELECT timestamp, level, msg, error, workflow, endpoint
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = "{request_id}"
  AND (error IS NOT NULL OR level IN ("error", "warning"))
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY timestamp ASC
```

### Template 3: Access Logs (HTTP Metadata)
```sql
SELECT request_id, http_method, request, response_code, duration
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_access`
WHERE request_id = "{request_id}"
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

### Template 4: Log Count Summary
```sql
SELECT
  COUNT(*) as total_logs,
  COUNTIF(level = 'error') as errors,
  COUNTIF(level = 'warning') as warnings,
  COUNTIF(workflow = 'sync') as sync_logs,
  COUNTIF(workflow = 'async') as async_logs
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = "{request_id}"
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

## Example Session

```
User: "Analyze request RQ27ee6ab09ac8b03ad07a4fff868c1fbc in dev"

Claude:
=== BIGQUERY QUERY (Full Request Trace) ===
[query displayed]

Querying BigQuery...

## Request Analysis: RQ27ee6ab09ac8b03ad07a4fff868c1fbc

### Bug Analysis
| Category | Count |
|----------|-------|
| Errors   | 0 |
| Warnings | 0 |
| Total Logs | 59 |

### Verdict: NO BUGS DETECTED

---

### Request Summary
| Field | Value |
|-------|-------|
| Request ID | RQxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |
| Environment | dev |
| Operation | CREATE |
| Account | ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |
| Sender ID | whatsapp:+1XXXXXXXXXX |
| Sender SID | XExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |
| Duration | 12 seconds |
| Status | CREATING (pending OTP) |

---

### Flow Breakdown

#### Sync Phase (30 logs)
| Timestamp | Status | Step |
|-----------|--------|------|
| 03:47:50 | OK | Request received |
| 03:47:50 | OK | Channel resolved: whatsapp |
| 03:47:53 | OK | Payload validated |
| 03:47:53 | OK | Temporal workflow triggered |
| 03:47:53 | OK | HTTP 202 returned |

#### Async Phase (29 logs)
| Timestamp | Status | Step |
|-----------|--------|------|
| 03:47:53 | OK | RegisterSenderWorkflow started |
| 03:47:54 | OK | WABA subscribed (messaging) |
| 03:47:57 | OK | WABA subscribed (voice) |
| 03:47:58 | OK | Phone ID saved |
| 03:48:01 | OK | OTP requested |
| 03:48:02 | OK | Non-customer-owned, OTP skipped |

---

### Errors Found
No errors or warnings detected in request processing.

---

### Final Status
Request completed successfully. Sender is in CREATING status pending OTP verification (skipped for non-customer-owned number).

No bugs detected. No Jira tickets created.
```

## Related Skills

- **ottm-bigquery-debugging**: Deep-dive debugging with custom queries
- **senders-e2e-testing**: Automated E2E testing (calls this skill)
- **bug-analyzer**: Universal bug classification patterns
- **sender-management-jira-ticket-creator**: Jira ticket creation
