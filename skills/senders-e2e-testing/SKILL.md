---
name: senders-e2e-testing
description: Automated end-to-end testing of Senders API with BigQuery log verification, error detection, and code review trigger. Use when running multiple API tests and want automated log polling, error detection, and bug analysis.
---

# Senders E2E Testing

This skill automates end-to-end testing of the Senders API with integrated BigQuery log verification.

## Overview

Use this skill when you need to:
- Run multiple Senders API tests (10+ per session)
- Automatically verify requests appear in BigQuery logs
- Detect errors and trigger code review if bugs found
- Avoid rate limiting through efficient batch queries

## When to Use

- "Run E2E tests for Senders API"
- "Test the create/update/delete flow and check for errors"
- "Verify my Senders API changes in dev/stage/prod"
- "Run regression tests and analyze any failures"

## Credential Detection

When user provides a curl command with credentials:
1. Extract `TWILIO_ACCOUNT_SID` from `-u` parameter or environment variable
2. Extract `TWILIO_AUTH_TOKEN` from `-u` parameter or environment variable
3. Detect environment from URL hostname:
   - `messaging.dev.twilio.com` → dev
   - `messaging.stage.twilio.com` → stage
   - `messaging.twilio.com` → prod
4. Use payload from user's curl if provided

Only use AskUserQuestion if credentials or environment cannot be detected.

## Pre-Approved Permissions

The following actions are **pre-approved** and do NOT require user confirmation:

- **BigQuery queries**: Execute `bq query` commands without asking for permission
- **BigQuery polling**: Run multiple queries during log polling without prompts
- **Sleep/wait commands**: Use `sleep` for polling intervals
- **Reading from /tmp/**: ALL read operations from /tmp directory (cat, grep, awk, etc.)
- **Writing to /tmp/**: ALL write operations to /tmp directory
- **Executing curl requests**: No approval needed for API calls
- **Displaying headers and responses**: No approval needed to show output
- **Creating Jira tickets**: Using sender-management-jira-ticket-creator skill for bugs (ask for parent epic once)

**NEVER ask for approval when:**
- Reading files from `/tmp/` directory
- Writing files to `/tmp/` directory
- Executing BigQuery queries
- Using sleep/wait commands
- Displaying curl responses
- **Displaying error details from BigQuery (even if verbose or multiple errors)**
- Auto-creating Jira tickets for detected bugs (but ask for parent epic once at start)

Only prompt for:
- Twilio API credentials IF they cannot be auto-detected from curl command
- Environment confirmation IF it cannot be detected from URL
- Test case selection IF user's intent is unclear
- **Parent epic ONCE before creating bug tickets** (allow empty response)

## Instructions

Follow this workflow step-by-step:

### Step 1: Setup

**Auto-detect from user's curl command:**
1. Extract `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` from `-u` parameter or environment variables
2. Detect environment from URL (dev/stage/prod)
3. Extract payload from curl's `-d` parameter if provided
4. Determine test operations based on user's request

**Only use AskUserQuestion if:**
- Credentials cannot be extracted from curl
- Environment is ambiguous
- User's intent for test operations is unclear

### Step 2: Execute Tests and Collect RQ IDs

Execute each test sequentially using **separate Bash tool calls**:

**CRITICAL: Use 5 separate Bash calls for each test. Do NOT combine steps.**

```bash
# Bash Call 1: Write payload to file (for POST/PATCH)
cat > /tmp/payload.json << 'EOF'
{
  "sender_id": "whatsapp:+18565589907",
  "configuration": { "waba_id": "101347185975530" },
  "profile": { "name": "Test Sender" }
}
EOF

# Bash Call 2: Execute curl (double quotes for variable substitution)
curl -s -D /tmp/headers.txt -X POST "https://messaging.dev.twilio.com/v2/Channels/Senders" \
  -u "ACCOUNT_SID:AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/payload.json -o /tmp/response.json

# Bash Call 3: Display response headers
cat /tmp/headers.txt

# Bash Call 4: Display response body
cat /tmp/response.json | python3 -m json.tool

# Bash Call 5: Extract RQ ID
grep -i "twilio-request-id" /tmp/headers.txt | awk '{print $2}' | tr -d '\r'
```

**Why separate calls?**
- Prevents bash parsing errors with complex command chaining
- Makes debugging easier (each step succeeds/fails independently)
- Clearer output for user visibility

**For each test, ALWAYS print:**
```
=== TEST N: CREATE ===
Request: POST https://messaging.dev.twilio.com/v2/Channels/Senders
Payload: {"sender_id": "whatsapp:+1234567890", ...}

=== RESPONSE HEADERS ===
HTTP/2 201
X-Twilio-Request-Id: RQ123abc...
Content-Type: application/json

=== RESPONSE BODY ===
{...formatted JSON...}

RQ ID Collected: RQ123abc...
```

**For each test:**
1. **Bash Call 1**: Write payload file (if POST/PATCH)
2. **Bash Call 2**: Execute curl with `-D /tmp/headers.txt -o /tmp/response.json`
3. **Bash Call 3**: Display headers with `cat /tmp/headers.txt`
4. **Bash Call 4**: Display response body with `cat /tmp/response.json | python3 -m json.tool`
5. **Bash Call 5**: Extract RQ ID with `grep -i "twilio-request-id"`
6. Store RQ ID in collection for batch query
7. Brief 100ms pause between tests (use `sleep 0.1`)

**Track collected RQ IDs** for later batch query.

### Step 3: Wait for Log Propagation

After all tests complete:

```
"All tests executed. Collected {N} RQ IDs."
"Waiting 30 seconds for logs to propagate to BigQuery..."
```

Use `sleep 30` for initial wait.

### Step 4: Poll BigQuery for Logs (Batch Query)

**Polling parameters:**
- Initial wait: 30 seconds (already done)
- Poll interval: 30 seconds
- Max attempts: 10 (covers ~5 minutes total)

**ALWAYS print the query before executing:**
```
=== BIGQUERY QUERY (Poll Attempt 1) ===
SELECT DISTINCT request_id
FROM `qtco-messaging-channels.dev.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id IN ("RQ123...", "RQ456...", "RQ789...")
  AND PARTITIONDATE = CURRENT_DATE()
```

**Batch query to check for logs:**
```bash
CLOUDSDK_PYTHON_SITEPACKAGES=1 bq query --format=json --use_legacy_sql=false '
SELECT DISTINCT request_id
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id IN ("RQ123...", "RQ456...", "RQ789...")
  AND PARTITIONDATE = CURRENT_DATE()
'
```

**Polling logic:**
```
Loop (max 10 attempts):
  1. Print the query being executed
  2. Execute batch query with all RQ IDs
  3. Print results summary
  4. Report: "Found logs for X/Y requests..."
  5. If all found: proceed to error detection
  6. If missing: wait 30s and retry
  7. If max attempts reached: report missing RQ IDs and proceed anyway
```

### Step 5: Error Detection

Once logs are found, query for errors.

**ALWAYS print the error detection query:**
```
=== BIGQUERY QUERY (Error Detection) ===
SELECT request_id, timestamp, level, msg, error, endpoint, sender_sid, sender_id
FROM `qtco-messaging-channels.dev.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id IN ("RQ123...", "RQ456...", "RQ789...")
  AND (error IS NOT NULL OR level = "error")
  AND PARTITIONDATE = CURRENT_DATE()
ORDER BY request_id, timestamp ASC
```

**Execute the query:**
```bash
CLOUDSDK_PYTHON_SITEPACKAGES=1 bq query --format=json --use_legacy_sql=false '
SELECT
  request_id,
  timestamp,
  level,
  msg,
  error,
  endpoint,
  sender_sid,
  sender_id
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id IN ("RQ123...", "RQ456...", "RQ789...")
  AND (error IS NOT NULL OR level = "error")
  AND PARTITIONDATE = CURRENT_DATE()
ORDER BY request_id, timestamp ASC
'
```

**Error classification:**
- `error IS NOT NULL` - Application-level errors with error field populated
- `level = "error"` - Log entries at error level
- Check access logs for HTTP 4xx/5xx status codes

**CRITICAL: Display ALL errors found**

When errors are detected, display EVERY error row returned by the query in full detail.

**Report format:**
```
## Error Summary

Found {N} errors/warnings across request(s):

### Error 1: {msg}
- **Request ID:** {request_id}
- **Level:** {level}
- **Flow:** Sync (during HTTP request) or Async (Temporal/SQS) - determine from context
- **Timestamp:** {timestamp}
- **Endpoint:** {endpoint}
- **Sender ID:** {sender_id}
- **Sender SID:** {sender_sid}
- **Error Details:**
```json
{error field - full JSON}
```

### Error 2: {msg}
- **Request ID:** {request_id}
- **Level:** {level}
- **Flow:** Sync (during HTTP request) or Async (Temporal/SQS) - determine from context
- **Timestamp:** {timestamp}
- **Endpoint:** {endpoint}
- **Sender ID:** {sender_id}
- **Sender SID:** {sender_sid}
- **Error Details:**
```json
{error field - full JSON}
```

(Repeat for ALL errors found - do not skip any)
```

**How to determine Flow type:**
- **Sync**: Error occurred during HTTP request processing (HTTP response code was 4xx/5xx)
- **Async - Temporal**: Error occurred after 202 Accepted, in background Temporal workflow
- **Async - SQS**: Error occurred in SQS message processing
- Check HTTP response code and timing to determine flow type

**Important:**
- Include errors at ALL levels: error, warning, info
- Display the full error JSON for each
- Number each error sequentially (Error 1, Error 2, Error 3...)
- DO NOT summarize or skip any errors
- If 10 errors found, display all 10 with complete details

### Step 5.5: Bug Analysis

After displaying all errors, use the `senders-bug-analyzer` skill to analyze them.

**Invoke the bug analyzer skill:**
Provide all error details from Step 5 to the bug analyzer.

The bug analyzer will ask for repository location to perform code review.
Provide the OTTM repository path: ~/Projects/messaging-ott-management-api/

The bug analyzer will:
- Analyze each error to determine if it's a bug or expected behavior
- Perform code review for detected bugs
- Search codebase for error origins
- Identify root causes in code
- Provide file:line references
- Suggest potential fixes

**If bugs detected:** Proceed to Step 5.6 (Create Jira Tickets)
**If no bugs:** Skip to Step 6

### Step 5.6: Create Jira Tickets for Detected Bugs

When bugs are detected by the bug analyzer in Step 5.5, automatically create Jira tickets.

**IMPORTANT: Use the `sender-management-jira-ticket-creator` skill**

Use the bugs list from the bug analyzer output to create tickets.

For each bug:
1. Ask user once for parent epic: "What parent epic should these tickets be associated with? (Leave empty to create without parent)"
2. Create ticket with:
   - Summary: Brief error description
   - Description: Complete bug details from error analysis
   - Issue Type: Bug
   - Project: MSGADVCHNL
   - Parent: User-provided epic key (if provided)
   - Team: "Sender Management" (remind user to set manually)

**DO NOT:**
- Use `-pr` or `--priority` flag (causes errors)
- Use `-a` or `--assignee` flag (leave unassigned)
- Ask for parent multiple times (ask once, reuse for all bugs)
- Ask for confirmation before each ticket (auto-create)

**Example output:**
```
What parent epic should these tickets be associated with?
(Leave empty to create without parent)
Example: MSGADVCHNL-11802
> MSGADVCHNL-11802

Creating Jira ticket for Bug 1...
✓ Ticket created: MSGADVCHNL-12633
  URL: https://twilio-engineering.atlassian.net/browse/MSGADVCHNL-12633

Creating Jira ticket for Bug 2...
✓ Ticket created: MSGADVCHNL-12634
  URL: https://twilio-engineering.atlassian.net/browse/MSGADVCHNL-12634

⚠️  IMPORTANT: Please set Team field to "Sender Management" for:
  - MSGADVCHNL-12633
  - MSGADVCHNL-12634
```

### Step 6: Code Review (If Errors Found)

**When errors are detected:**

1. **Extract error context:**
   - Error message
   - Endpoint/operation that failed
   - Request lifecycle from logs

2. **Search codebase for related code:**
   ```
   Use Grep to search for:
   - Error message strings
   - Endpoint handler functions
   - Related business logic
   ```

3. **Analyze potential root cause:**
   - Review the code path
   - Identify where the error originates
   - Check for missing validation, incorrect logic, or external dependencies

4. **Report findings:**
   ```
   ## Code Review

   ### Error: "Provider phone number not found in Storehouse"

   **Location**: src/services/whatsapp/getSender.ts:142

   **Analysis**:
   The error occurs when querying Storehouse for phone number metadata.
   This could indicate:
   1. Phone number not provisioned in Storehouse
   2. Storehouse API connectivity issue
   3. Incorrect phone number format

   **Suggested Investigation**:
   - Verify phone number exists in Storehouse
   - Check Storehouse API logs
   - Validate phone number format matches expected pattern
   ```

### Step 7: Final Report

Generate a summary report:

```
## E2E Test Results

**Environment**: dev
**Tests Executed**: 12
**RQ IDs Collected**: 12
**Logs Found**: 12/12

### Results by Operation
- CREATE: 3 tests, 1 error
- GET: 4 tests, 0 errors
- UPDATE: 3 tests, 1 error
- DELETE: 2 tests, 0 errors

### Errors Detected

**IMPORTANT: List ALL errors with complete details from Step 5**

DO NOT just list error messages. Include for each error:
- Error number (Error 1, Error 2, etc.)
- Request ID
- Severity level (error/warning/info)
- Flow type: Sync (during HTTP request) or Async (Temporal/SQS)
- Full error message
- Timestamp
- Complete error context

Example:
1. **Error 1** (RQ005 - CREATE): "Provider phone number not found in Storehouse"
   - Level: error
   - Flow: Sync (returned in HTTP response)
   - Timestamp: 2024-01-15T10:30:45Z
   - Full details in Step 5 error summary

2. **Error 2** (RQ009 - UPDATE): "Invalid WABA ID format"
   - Level: warning
   - Flow: Async (Temporal workflow)
   - Timestamp: 2024-01-15T10:31:15Z
   - Full details in Step 5 error summary

### Bugs Detected

**IMPORTANT: List all bugs identified by the bug analyzer in Step 5.5**

For each bug:
1. **Bug N** (Request ID): Error message
   - Verdict: BUG
   - Reason: [Why it's a bug]
   - Impact: [severity]
   - Jira Ticket: [TICKET-KEY with URL]

Example:
1. **Bug 1** (RQc7c1515209a7c51eff5783f4202aee6b): PiedPiper debug event publishing failure
   - Verdict: BUG - Malformed JSON payload
   - Reason: PiedPiper ingest service rejected payload with "Unable to process JSON"
   - Impact: Medium (observability data loss, no customer impact)
   - Jira Ticket: [MSGADVCHNL-12632](https://twilio-engineering.atlassian.net/browse/MSGADVCHNL-12632)

**If no bugs detected:** State "No bugs detected. All errors are expected behavior."

### Code Review Status
- 2 potential bugs identified
- See detailed analysis above
```

## Query Templates

### Template 1: Check Logs Exist (Batch)
```sql
SELECT DISTINCT request_id
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id IN ({rq_ids})
  AND PARTITIONDATE = CURRENT_DATE()
```

### Template 2: Error Detection (Batch)
```sql
SELECT
  request_id, timestamp, level, msg, error, endpoint, sender_sid, sender_id
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id IN ({rq_ids})
  AND (error IS NOT NULL OR level = 'error')
  AND PARTITIONDATE = CURRENT_DATE()
ORDER BY request_id, timestamp ASC
```

### Template 3: Full Request Trace (Batch)
```sql
SELECT
  request_id, timestamp, level, msg, endpoint, workflow, channel, error
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id IN ({rq_ids})
  AND PARTITIONDATE = CURRENT_DATE()
ORDER BY request_id, timestamp ASC
```

### Template 4: Access Logs (HTTP Metadata)
```sql
SELECT
  request_id, http_method, request, response_code, duration
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_access`
WHERE request_id IN ({rq_ids})
  AND PARTITIONDATE = CURRENT_DATE()
```

## Rate Limiting Considerations

### BigQuery
- Batch all RQ IDs in single query using `IN` clause
- Max ~11 queries for entire workflow (vs 100+ without batching)
- Early termination when all logs found

### Senders API
- 100ms pause between requests
- Sequential execution (not parallel)

### Efficiency
- 10 tests + 10 polling attempts = max 11 BigQuery queries
- Single batch query checks all RQ IDs at once

## Example Session

```
User: "test senders api e2e here is a curl
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

curl -v -X POST https://messaging.dev.twilio.com/v2/Channels/Senders ..."

Claude: "Extracted credentials from curl command.
Environment detected: dev
Executing CREATE test...

=== TEST 1: CREATE SENDER ===
Request: POST https://messaging.dev.twilio.com/v2/Channels/Senders

=== RESPONSE HEADERS ===
HTTP/1.1 202 Accepted
Twilio-Request-Id: RQ001abc...

=== RESPONSE BODY ===
{
  "sid": "XE123...",
  "status": "CREATING",
  ...
}

RQ ID Collected: RQ001abc...

All tests executed. Collected 1 RQ ID.
Waiting 30 seconds for logs to propagate...

Polling BigQuery... Found 1/1 logs

Checking for errors...

## Error Summary

Found 3 errors/warnings across request(s):

### Error 1: Failed to request verification code with Meta API
- **Request ID:** RQ001abc...
- **Level:** error
- **Flow:** Async (Temporal workflow - after 202 response)
- **Timestamp:** 2026-01-03 07:33:45
- **Endpoint:** create
- **Sender ID:** whatsapp:+14197242589
- **Sender SID:** null
- **Error Details:**
```json
400 response from Meta Graph API: {
  "error": {
    "message": "Request code error",
    "type": "OAuthException",
    "code": 136024,
    "error_subcode": 2388091,
    "error_user_msg": "Request code failed: Please try again in some time."
  }
}
```

### Error 2: Failed to publish debug event to piedpiper
- **Request ID:** RQ001abc...
- **Level:** warning
- **Flow:** Async (Background processing)
- **Timestamp:** 2026-01-03 07:33:45
- **Endpoint:** create
- **Sender ID:** whatsapp:+14197242589
- **Sender SID:** null
- **Error Details:**
```json
400 response from pied-piper-ingest service: {
  "code": 400,
  "message": "Unable to process JSON",
  "details": " is invalid"
}
```

### Error 3: [RequestCode] Non-retryable Meta API error
- **Request ID:** RQ001abc...
- **Level:** info
- **Flow:** Async (Temporal workflow)
- **Timestamp:** 2026-01-03 07:33:45
- **Endpoint:** create
- **Sender ID:** whatsapp:+14197242589
- **Sender SID:** null
- **Error Details:**
```json
400 response from Meta Graph API: {
  "error": {
    "message": "Request code error",
    "type": "OAuthException",
    "code": 136024
  }
}
```

## E2E Test Results
- Environment: dev
- Tests Executed: 1
- RQ IDs Collected: 1
- Logs Found: 1/1
- Errors: 3 (1 error, 1 warning, 1 info)

### Errors Detected

1. **Error 1** (RQ001abc - CREATE): "Failed to request verification code with Meta API"
   - Level: error
   - Flow: Async (Temporal)
   - Root Cause: Phone number already registered on WhatsApp

2. **Error 2** (RQ001abc - CREATE): "Failed to publish debug event to piedpiper"
   - Level: warning
   - Flow: Async
   - Root Cause: Malformed JSON in event payload

3. **Error 3** (RQ001abc - CREATE): "Non-retryable Meta API error"
   - Level: info
   - Flow: Async (Temporal)
   - Same root cause as Error 1

Status: ⚠️ TESTS COMPLETED WITH ERRORS (background async errors after 202)"
```

## Related Skills

- `senders-api-testing` - Generate curl commands for individual API tests
- `ottm-bigquery-debugging` - Deep-dive into specific request logs
