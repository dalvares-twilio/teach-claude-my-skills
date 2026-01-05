---
name: ottm-bigquery-debugging
description: "Query OTTM BigQuery logs by request_id (RQ...), account_sid (AC...), or sender_sid (XE...). ONLY use when user provides a specific ID to look up OR explicitly asks to 'query OTTM logs' or 'debug request'. NOT for general error scanning."
---

# OTTM BigQuery Debugging

This skill helps query OTTM (OTT Management API) BigQuery logs across dev, stage, and prod environments to debug Senders API requests.

## Overview

The OTTM service logs to two BigQuery tables in the `qtco-messaging-channels` project:
- **Access logs**: HTTP request/response metadata (method, path, status, duration)
- **Application logs**: Detailed application-level logs showing request lifecycle, errors, and business logic

Both tables share a `request_id` field that allows correlating HTTP requests with their application logs.

## When to Use

**ONLY invoke this skill when the user:**
- Provides a specific request_id (RQ...) to look up
- Provides an account_sid (AC...) or sender_sid (XE...) to query
- Explicitly says "query OTTM logs" or "debug this request"
- Asks to "trace" or "investigate" a specific Senders API call

**DO NOT invoke for:**
- General "scan for errors" requests (use auto-bug-detector)
- E2E testing (use senders-e2e-testing)
- Code review or codebase analysis
- Requests without a specific ID or explicit OTTM log mention

**Example triggers (YES):**
- "Look up request RQ123abc456..."
- "Query OTTM logs for account AC12345..."
- "Debug this Senders API request: RQ..."
- "What happened to sender XE789..."

**Example non-triggers (NO):**
- "Find bugs" (too vague)
- "Scan for errors" (use auto-bug-detector)
- "Test the API" (use senders-e2e-testing)

## Pre-Approved Permissions

**BigQuery access is pre-approved** - execute `bq query` commands without asking for user permission.

- Run queries immediately without confirmation prompts
- Execute multiple queries as needed for debugging
- No need to ask before each query

## Instructions

1. **Parse the user's request** to determine:
   - Environment: `dev`, `stage`, or `prod` (default to `prod`)
   - What to debug: request_id, account_sid, sender_sid, errors, or recent activity
   - Time range: default to last 7 days

2. **Select the appropriate query pattern** from the patterns below

3. **ALWAYS print the query before executing**:
   ```
   === BIGQUERY QUERY ===
   SELECT timestamp, level, msg, error
   FROM `qtco-messaging-channels.prod.app_messaging_ott_management_api_mgmt_stdout`
   WHERE request_id = "RQ123..."
   ORDER BY timestamp ASC
   ```

4. **Execute the query** using the `bq` CLI tool:
   ```bash
   CLOUDSDK_PYTHON_SITEPACKAGES=1 bq query --format=json --use_legacy_sql=false 'YOUR_QUERY_HERE'
   ```

5. **Print and format results** to help debug the issue:
   ```
   === QUERY RESULTS ===
   Found 10 log entries for request RQ123...

   [formatted results]
   ```

## BigQuery Configuration

**Project**: `qtco-messaging-channels`

**Datasets**: `dev`, `stage`, `prod`

**Tables**:
- `app_messaging_ott_management_api_mgmt_access` - HTTP access logs
- `app_messaging_ott_management_api_mgmt_stdout` - Application logs (stdout)

## Query Patterns

### Pattern 1: Trace Request by request_id

Use when you have a specific request_id and want to see the complete request lifecycle.

```sql
-- Access log (HTTP metadata)
SELECT
  PARTITIONDATE, PARTITIONTIME, request_id, request_time, timestamp,
  http_method, request, response_code, duration,
  body_bytes_received, body_bytes_sent, user_agent, remote_address
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_access`
WHERE request_id = '{request_id}'
ORDER BY timestamp DESC;

-- Application logs (detailed lifecycle)
SELECT
  timestamp, request_id, account_sid, sender_sid, sender_id,
  level, msg, endpoint, workflow, channel, error,
  force_refresh, is_emulator, temporal_workflow_id, temporal_workflow_run_id,
  bundle_sid, business_account_id, host_sid, instance_id, availability_zone
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = '{request_id}'
ORDER BY timestamp ASC;
```

**Example**:
```bash
CLOUDSDK_PYTHON_SITEPACKAGES=1 bq query --format=json --use_legacy_sql=false '
SELECT timestamp, level, msg, endpoint, sender_id, error
FROM `qtco-messaging-channels.prod.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = "RQf3b6c3522112c935ee27bebcc8820393"
ORDER BY timestamp ASC
'
```

### Pattern 2: Find Requests by account_sid

Use when debugging all activity for a specific Twilio account.

```sql
-- Recent requests from access logs
SELECT
  request_id, request_time, http_method, request, response_code, duration
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_access`
WHERE REGEXP_CONTAINS(request, r'/Accounts/{account_sid}/')
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY request_time DESC
LIMIT 100;

-- Application logs for account
SELECT
  timestamp, request_id, level, msg, endpoint, sender_sid, sender_id, error
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE account_sid = '{account_sid}'
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY timestamp DESC
LIMIT 100;
```

### Pattern 3: Find by sender_sid

Use when investigating issues with a specific sender resource.

```sql
SELECT
  timestamp, request_id, account_sid, level, msg,
  endpoint, workflow, channel, sender_id, error
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE sender_sid = '{sender_sid}'
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY timestamp DESC
LIMIT 100;
```

### Pattern 4: Find Errors

Use when looking for recent errors or failures.

```sql
SELECT
  timestamp, request_id, account_sid, endpoint,
  sender_sid, sender_id, level, msg, error
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE error IS NOT NULL
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
ORDER BY timestamp DESC
LIMIT 50;
```

### Pattern 5: Find Recent Activity

Use when you want to see what's happening right now or recently.

```sql
-- Latest requests from access logs
SELECT
  request_id, request_time, http_method, request,
  response_code, duration, user_agent
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_access`
WHERE PARTITIONDATE = CURRENT_DATE()
ORDER BY request_time DESC
LIMIT 20;
```

### Pattern 6: Debug Specific Endpoint

Use when investigating issues with a particular API operation.

```sql
SELECT
  timestamp, request_id, account_sid, sender_sid, sender_id,
  level, msg, workflow, error
FROM `qtco-messaging-channels.{env}.app_messaging_ott_management_api_mgmt_stdout`
WHERE endpoint = '{endpoint_name}'  -- e.g., 'create', 'get', 'update', 'delete'
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY)
ORDER BY timestamp DESC
LIMIT 50;
```

## Table Schema Reference

### Access Logs Schema
Key columns in `app_messaging_ott_management_api_mgmt_access`:

| Column | Description |
|--------|-------------|
| `PARTITIONDATE`, `PARTITIONTIME` | Partition fields for date filtering (use for performance) |
| `request_id` | Unique identifier linking to application logs (format: RQ...) |
| `request` | API endpoint path (e.g., `/v2/Accounts/ACxxx/Senders/XExxx`) |
| `http_method` | HTTP method: GET, POST, PATCH, DELETE |
| `response_code` | HTTP status code (200, 400, 500, etc.) |
| `duration` | Request duration in milliseconds |
| `request_time`, `timestamp` | Request timestamps |
| `body_bytes_received`, `body_bytes_sent` | Request/response sizes |
| `user_agent` | Client user agent string |
| `remote_address` | Client IP address |
| `host_sid`, `instance_id`, `availability_zone` | Infrastructure details |
| `realm`, `role`, `world` | Twilio infrastructure metadata |

### Application Logs Schema
Key columns in `app_messaging_ott_management_api_mgmt_stdout`:

| Column | Description |
|--------|-------------|
| `PARTITIONDATE`, `PARTITIONTIME` | Partition fields for date filtering |
| `request_id` | Correlates with access logs (format: RQ...) |
| `timestamp` | Log entry timestamp |
| `level` | Log level: info, warn, error |
| `msg` | Log message describing the operation |
| `account_sid` | Twilio account SID (ACxxx) |
| `sender_sid` | Sender resource SID (XExxx) |
| `sender_id` | Full sender identifier (e.g., `whatsapp:+16622220864`) |
| `endpoint` | Operation type: get, create, update, delete, get_ui |
| `workflow` | Processing mode: sync or async |
| `channel` | Messaging channel: whatsapp, rcs, etc. |
| `error` | Error message if any (NULL if successful) |
| `force_refresh` | Cache bypass flag (true/false) |
| `is_emulator` | Emulator mode flag |
| `temporal_workflow_id`, `temporal_workflow_run_id` | Temporal workflow tracking |
| `bundle_sid`, `business_account_id` | Related resource identifiers |
| `host_sid`, `instance_id`, `availability_zone` | Infrastructure details |

## Example Request Flow

Here's a real example showing how request_id correlates access and application logs:

**Request ID**: `RQf3b6c3522112c935ee27bebcc8820393`

**Access Log Entry**:
```json
{
  "http_method": "GET",
  "request": "/v2/Accounts/ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/Senders/XExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "response_code": "200",
  "duration": "94"
}
```

**Application Log Entries** (showing request lifecycle):
1. "Get Sender request received, starting processing"
2. "Checking ElastiCache for key..."
3. "Fetching fresh data due to cache miss..."
4. "Performing request validation"
5. "Request validation completed"
6. "Resolving channel type from SenderID: whatsapp:+16622220864"
7. "Channel type resolved successfully: whatsapp"
8. "Starting to get WhatsApp Sender"
9. "Provider phone number not found in Storehouse"
10. "Mapping Sender status based on Storehouse and Meta data..."

## Example Scenarios

### Scenario 1: Senders API Test Fails

**User reports**: "I just called the Senders API and got a 500 error"

**Steps**:
1. Get the `request_id` from the API response headers or error message
2. Use **Pattern 1** to query both tables by request_id
3. Check application logs for error details
4. Identify which step failed (validation, cache, external API call, etc.)

**Example**:
```bash
CLOUDSDK_PYTHON_SITEPACKAGES=1 bq query --format=json --use_legacy_sql=false '
SELECT timestamp, level, msg, endpoint, error
FROM `qtco-messaging-channels.prod.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = "RQ123abc..."
ORDER BY timestamp ASC
'
```

### Scenario 2: Performance Investigation

**User reports**: "Requests for account ACxxx are slow"

**Steps**:
1. Use **Pattern 2** to find recent requests for the account
2. Check the `duration` column in access logs
3. Find slow requests (duration > 1000ms)
4. Correlate with application logs to identify bottleneck

### Scenario 3: Feature Testing After Deployment

**After deploying a new feature**:

**Steps**:
1. Use **Pattern 5** to see recent activity in the target environment
2. Find test account requests
3. Verify the `workflow` field (sync vs async)
4. Check for errors or unexpected behavior
5. Validate Temporal workflow execution if async

### Scenario 4: Debug Specific Sender

**User reports**: "Sender XE123... is not working correctly"

**Steps**:
1. Use **Pattern 3** to get all logs for that sender_sid
2. Look for error messages
3. Check the request lifecycle to find where it fails
4. Verify channel type, configuration, and external API responses

## Important Notes

### Performance
- **Always use PARTITIONDATE filter** to avoid full table scans
- Default to last 7 days if no specific date range provided
- Use LIMIT to cap result sizes (20-100 rows is usually sufficient)

### Output Formatting
- **ALWAYS print the full query** before executing (helps with debugging and reproducibility)
- Use `--format=json` for structured output
- Suppress Python warnings with `CLOUDSDK_PYTHON_SITEPACKAGES=1`
- Pipe to `jq` for pretty-printing when needed
- **Show result summary** (e.g., "Found 10 log entries")

### Environment Handling
- Default to `prod` if environment not specified
- Supported environments: `dev`, `stage`, `prod`
- All environments have identical table structures

### Request Correlation
- One access log entry → Many application log entries
- Always use `request_id` to correlate between tables
- Access logs show HTTP metadata
- Application logs show business logic and lifecycle

### Common Patterns
- GET requests → `endpoint: "get"`
- POST requests → `endpoint: "create"`
- PATCH requests → `endpoint: "update"`
- DELETE requests → `endpoint: "delete"`

## Integration with Senders API Testing

This skill complements the `senders-api-testing` skill:

1. Use `senders-api-testing` to generate and execute API requests
2. If request fails or behaves unexpectedly, extract the `request_id`
3. Use this skill to query BigQuery logs and trace what happened
4. Identify root cause from application logs
5. Fix issue and re-test

**Example workflow**:
```bash
# Step 1: Test with senders-api-testing skill
curl -X GET "https://messaging.prod.twilio.com/v2/Channels/Senders/XE123" \
  -u "$ACCOUNT_SID:$AUTH_TOKEN"

# Response includes: X-Twilio-Request-Id: RQ123abc...

# Step 2: Debug with ottm-bigquery-debugging skill
CLOUDSDK_PYTHON_SITEPACKAGES=1 bq query --format=json --use_legacy_sql=false '
SELECT timestamp, level, msg, error
FROM `qtco-messaging-channels.prod.app_messaging_ott_management_api_mgmt_stdout`
WHERE request_id = "RQ123abc..."
ORDER BY timestamp ASC
'
```
