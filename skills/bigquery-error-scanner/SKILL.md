---
name: bigquery-error-scanner
description: "Scan BigQuery tables for error logs. ONLY use when user explicitly mentions 'BigQuery', 'BQ', 'logs table', or a specific BigQuery table name like 'project.dataset.table'. NOT for general bug finding or code scanning."
---

# BigQuery Error Scanner

## Overview

Universal error discovery engine that scans ANY BigQuery table for errors and reports only UNIQUE/NEW error patterns. Filters out repeated occurrences using error signature tracking.

## When to Use

**ONLY invoke this skill when the user explicitly:**
- Mentions "BigQuery" or "BQ" (e.g., "scan BigQuery for errors")
- Provides a fully-qualified table name like `project.dataset.table`
- Says "scan logs table" or "query error logs"
- References a specific monitoring skill (e.g., "ottm-logs-monitor")

**DO NOT invoke for:**
- General "find bugs" or "scan for issues" requests
- Code review or codebase scanning
- API testing (use senders-e2e-testing instead)
- Jira ticket creation
- Any task not explicitly about BigQuery log tables

**Example triggers (YES):**
- "Scan BigQuery for errors from last 4 hours"
- "Query qtco-messaging-channels.prod.app_logs for unique errors"
- "Check BQ logs for new error patterns"
- "Scan the OTTM logs table"

**Example non-triggers (NO):**
- "Find bugs in my code"
- "Scan for issues"
- "Check for errors" (too vague - must mention BigQuery)
- "Test the API"

## Key Features

✅ **Scans any BigQuery table** - flexible configuration
✅ **Reports UNIQUE errors only** - tracks signatures to avoid noise
✅ **Normalizes error messages** - groups similar errors together
✅ **Privacy-preserving** - only queries specified columns
✅ **Fast signature lookup** - /tmp/ storage for quick access

## Pre-Approved Actions

- BigQuery DESCRIBE queries (column names only)
- BigQuery SELECT on user-specified columns
- Reading/writing to /tmp/ for signature tracking
- Displaying discovered unique errors

## Instructions

### Step 1: Parse User Request

Extract configuration from request:
- **Table**: project.dataset.table
- **Error column**: which column contains error messages
- **Level column**: which column contains severity (optional)
- **Timestamp column**: which column has timestamps
- **Partition column**: for query performance (optional)
- **Identity column**: for correlation (optional)
- **Time window**: hours to look back (default: 4)
- **Custom conditions**: additional WHERE clauses (optional)

**If configuration not provided**, ask using AskUserQuestion.

### Step 2: Discover Schema (If Needed)

If user doesn't specify columns, discover schema:

```bash
CLOUDSDK_PYTHON_SITEPACKAGES=1 bq query --format=json --use_legacy_sql=false '
SELECT column_name, data_type
FROM `{project}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = "{table}"
ORDER BY ordinal_position
'
```

**Display columns to user** (names only, no data):
```
Table has {N} columns:
- timestamp (TIMESTAMP)
- error (STRING)
- level (STRING)
- request_id (STRING)
...
```

**Ask user to specify** which columns to use via AskUserQuestion.

### Step 3: Build Query

**Construct BigQuery query** using provided configuration:

```sql
SELECT
  {timestamp_column} as timestamp,
  {error_column} as error_message,
  {level_column} as error_level,
  {identity_column} as identity,
  {additional_columns}
FROM `{project}.{dataset}.{table}`
WHERE {error_column} IS NOT NULL
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL CAST(CEILING({hours}/24.0) AS INT64) DAY)
  AND {timestamp_column} >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
  {AND custom_conditions IF PRESENT}
ORDER BY {timestamp_column} DESC
LIMIT 100
```

> **Multi-Day Support**: The partition filter uses `CEILING(hours/24)` to include enough partition days. For example:
> - 4 hours → 1 day partition
> - 30 hours → 2 day partitions
> - 72 hours → 3 day partitions

**Example queries**:

For standard error table:
```sql
SELECT
  timestamp,
  error as error_message,
  level as error_level,
  request_id as identity
FROM `qtco-messaging-channels.prod.app_logs`
WHERE error IS NOT NULL
  AND PARTITIONDATE >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 HOUR)
ORDER BY timestamp DESC
LIMIT 100
```

With custom conditions:
```sql
SELECT
  created_at as timestamp,
  error_message,
  severity as error_level,
  transaction_id as identity
FROM `my-project.prod.transactions`
WHERE error_message IS NOT NULL
  AND severity IN ('ERROR', 'CRITICAL')
  AND created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 6 HOUR)
ORDER BY created_at DESC
LIMIT 100
```

### Step 4: Execute Query

**Print query before executing**:
```
=== BIGQUERY QUERY ===
<full SQL query>
```

**Execute and extract clean JSON**:
```bash
# Execute query and extract only the JSON array (skip warnings)
CLOUDSDK_PYTHON_SITEPACKAGES=1 bq query --format=json --use_legacy_sql=false '<QUERY>' | grep '^\[' > /tmp/bq_results_clean.json

# Verify JSON is valid
cat /tmp/bq_results_clean.json | python3 -m json.tool > /dev/null 2>&1 && echo "✓ Valid JSON" || echo "✗ Invalid JSON"
```

**IMPORTANT**: BigQuery output includes warnings/deprecation messages before the JSON. Always use `grep '^\['` to extract only the JSON array starting with `[`.

**Parse results** into error list from `/tmp/bq_results_clean.json`.

### Step 5: Load Error Signature Database

**Signature file path**:
```
/tmp/bigquery_error_signatures_{project}_{dataset}_{table}.json
```

**Load existing signatures**:
```bash
cat /tmp/bigquery_error_signatures_{project}_{dataset}_{table}.json 2>/dev/null || echo '{}'
```

**Format**:
```json
{
  "signature_hash_abc123": {
    "first_seen": "2026-01-03T10:00:00Z",
    "last_seen": "2026-01-03T14:30:00Z",
    "expires_at": "2026-01-10T14:30:00Z",
    "count": 5,
    "normalized_message": "Connection timeout to service-NUMBER",
    "sample_error": "Connection timeout to service-123",
    "level": "error"
  }
}
```

**Expiry Rules**:
- `expires_at` = `last_seen` + 7 days (default)
- On each signature update, refresh `expires_at`
- Signatures that haven't been seen for 7 days will expire
- This allows old errors to resurface if they return after a long absence

**Cleanup expired signatures on load**:
```python
from datetime import datetime

def load_and_cleanup_signatures(filepath):
    signatures = json.load(open(filepath)) if os.path.exists(filepath) else {}
    now = datetime.utcnow().isoformat() + 'Z'

    # Remove expired signatures
    active_signatures = {
        k: v for k, v in signatures.items()
        if v.get('expires_at', '9999-12-31') > now
    }

    return active_signatures
```

### Step 6: Process Each Error

**Load clean JSON results**:
```python
import json

# Load errors from clean JSON file
with open('/tmp/bq_results_clean.json', 'r') as f:
    errors = json.load(f)
```

For each error from BigQuery:

**1. Extract error message**:
```python
error_msg = row['error_message'] or row.get('error') or str(row)
```

**2. Normalize message** (strip variable parts):
```python
# Strip request IDs
normalized = re.sub(r'RQ[a-f0-9]{32}', 'REQUEST_ID', error_msg)
normalized = re.sub(r'[A-Z]{2}[a-f0-9]{32}', 'RESOURCE_ID', normalized)

# Strip account/resource SIDs
normalized = re.sub(r'[A-Z]{2}[a-f0-9]+', 'SID', normalized)

# Strip numbers
normalized = re.sub(r'\b\d+\b', 'NUMBER', normalized)

# Strip dates
normalized = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', normalized)
normalized = re.sub(r'\d{2}/\d{2}/\d{4}', 'DATE', normalized)

# Strip timestamps
normalized = re.sub(r'\d{2}:\d{2}:\d{2}', 'TIME', normalized)

# Strip IP addresses
normalized = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP_ADDRESS', normalized)

# Strip UUIDs
normalized = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 'UUID', normalized)

# Strip email addresses
normalized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL', normalized)

# Strip URLs
normalized = re.sub(r'https?://[^\s]+', 'URL', normalized)

# Strip phone numbers (E.164 format)
normalized = re.sub(r'\+\d{10,15}', 'PHONE', normalized)

# Strip Twilio SIDs (AC, SK, XE, SA, SM, etc. - 2 uppercase + 32 hex)
normalized = re.sub(r'\b[A-Z]{2}[a-f0-9]{32}\b', 'TWILIO_SID', normalized)

# Strip JWT tokens (three base64 sections separated by dots)
normalized = re.sub(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', 'JWT_TOKEN', normalized)

# Strip Bearer tokens
normalized = re.sub(r'Bearer\s+[A-Za-z0-9_-]+', 'BEARER_TOKEN', normalized)

# Strip hex strings (32+ chars, likely hashes or tokens)
normalized = re.sub(r'\b[a-f0-9]{32,}\b', 'HEX_STRING', normalized)

# Strip file paths
normalized = re.sub(r'/[\w/.-]+', 'PATH', normalized)
```

**3. Generate signature** (using stable hash):
```python
import hashlib
signature = hashlib.sha256(f"{normalized_message}|{error_level}".encode()).hexdigest()[:16]
```

> **Note**: Use SHA256 instead of Python's built-in `hash()` because `hash()` is not stable across Python sessions (randomized by default). SHA256 ensures the same error always produces the same signature.

**4. Check if NEW**:
```python
from datetime import datetime, timedelta

now = datetime.utcnow()
expires_at = (now + timedelta(days=7)).isoformat() + 'Z'

if signature not in signature_database:
    # NEW error - add to results and database
    signature_database[signature] = {
        "first_seen": now.isoformat() + 'Z',
        "last_seen": now.isoformat() + 'Z',
        "expires_at": expires_at,
        "count": 1,
        "normalized_message": normalized_message,
        "sample_error": error_msg,
        "level": error_level
    }
    # Add to results for reporting
else:
    # SEEN before - update and skip
    signature_database[signature]["last_seen"] = now.isoformat() + 'Z'
    signature_database[signature]["expires_at"] = expires_at  # Refresh expiry
    signature_database[signature]["count"] += 1
    # Skip (don't report)
```

### Step 7: Update Signature Database

**Save updated signatures**:
```bash
echo '<JSON>' > /tmp/bigquery_error_signatures_{project}_{dataset}_{table}.json
```

### Step 8: Display Results

**Summary**:
```
## BigQuery Error Scan Results

**Table**: {project}.{dataset}.{table}
**Time Window**: Last {N} hours
**Scan Time**: {current_timestamp}

**Total errors found**: {total}
**UNIQUE errors** (new patterns): {new_count}
**Seen before**: {seen_count}
```

**For each NEW error**:
```
### Error {N}: {error_message} ✨ NEW

- **Timestamp**: {timestamp}
- **Level**: {error_level}
- **Identity**: {identity_value}
- **Normalized Pattern**: {normalized_message}
- **Signature**: {signature_hash}

**Full Details**:
{complete error row in JSON}
```

**For seen errors** (optional summary):
```
### Seen Before (not new)
- "{sample_error_1}" - seen {count} times since {first_seen}
- "{sample_error_2}" - seen {count} times since {first_seen}
...
```

### Step 9: Offer Next Actions

Ask user:
```
Found {N} new unique errors. What would you like to do?

1. Analyze for bugs (classify each as BUG/EXPECTED/IMPROVEMENT)
2. Show full error details
3. Reset signature database (see all errors as new)
4. Nothing (just reporting)
```

If user chooses analysis, prepare error list for `bug-analyzer` skill.

## Signature Database Management

**View signatures**:
```bash
cat /tmp/bigquery_error_signatures_{project}_{dataset}_{table}.json | jq '.'
```

**Count signatures**:
```bash
cat /tmp/bigquery_error_signatures_{project}_{dataset}_{table}.json | jq 'length'
```

**Reset (see all errors as new)**:
```bash
rm /tmp/bigquery_error_signatures_{project}_{dataset}_{table}.json
```

**Find specific signature**:
```bash
cat /tmp/bigquery_error_signatures_*.json | jq '.[] | select(.normalized_message | contains("timeout"))'
```

## Configuration Modes

### Mode 1: Explicit Configuration
User provides all metadata:
```
"Scan qtco-messaging-channels.prod.app_logs
 error column: error
 level column: level
 timestamp column: timestamp
 from last 4 hours"
```

### Mode 2: Auto-Discovery
Scanner discovers schema and asks for columns:
```
"Scan my-project.prod.customer_logs for errors"
→ Discovers schema
→ Asks which columns to use
→ Executes scan
```

### Mode 3: Using Generated Skills
Generated monitoring skills provide all configuration:
```
User: "Scan app-logs-monitor for bugs"
→ Skill has configuration baked in
→ Invokes scanner with config
→ No questions needed
```

## Privacy & Security

✅ **Schema discovery**: Queries column names only (no data)
✅ **Selective querying**: Only queries user-specified columns
✅ **Normalized signatures**: Strips sensitive data (IDs, emails, etc.)
✅ **Local storage**: Signatures stored in /tmp/ (not transmitted)
❌ **Never auto-queries**: Requires explicit column specification

## Example Sessions

### Session 1: Standalone Scan

```
User: "Scan qtco-messaging-channels.prod.app_logs for errors from last 6 hours"

Scanner:
Q: "Which column contains errors?"
A: "error"

Q: "Which column is timestamp?"
A: "timestamp"

Q: "Severity column? (optional)"
A: "level"

Executing scan...
Found 15 total errors
→ 3 NEW unique error patterns
→ 12 seen before

### New Error 1: "Connection timeout to meta-graph-api" ✨
- Timestamp: 2026-01-03 15:30:45
- Level: error
- Request ID: RQabc123...

### New Error 2: "PiedPiper ingest service unavailable" ✨
- Timestamp: 2026-01-03 15:25:12
- Level: error
- Request ID: RQdef456...

### New Error 3: "Database connection pool exhausted" ✨
- Timestamp: 2026-01-03 14:50:00
- Level: critical
- Request ID: RQghi789...

What would you like to do?
1. Analyze for bugs
2. Show full details
3. Reset signatures
4. Nothing
```

### Session 2: With Generated Skill

```
User: "Scan ottm-logs-monitor for bugs"

Generated Skill:
→ Uses pre-configured settings
→ Invokes scanner with config
→ No questions asked

Scanner:
Scanning qtco-messaging-channels.prod.app_messaging_ott_management_api_mgmt_stdout...
Found 20 errors, 2 NEW patterns

[Results displayed]
```

## Performance Considerations

- **Partition filtering**: Always use partition column if available (10-100x faster)
- **Time window**: Limit to reasonable range (default: 4 hours, max: 7 days)
- **Result limit**: Cap at 100 rows to avoid overwhelming output
- **Signature lookup**: O(1) hash lookup in memory (fast)
- **Query cost**: ~1-5 cents per scan (depends on table size and partition usage)

## Error Handling

**If BigQuery output has warnings** (Python deprecation, etc.):
- ALWAYS use `grep '^\['` to extract only JSON array
- BigQuery outputs warnings to stderr/stdout before JSON
- Clean extraction prevents JSON parsing errors
- Example: `bq query ... | grep '^\[' > /tmp/clean.json`

**If BigQuery query fails**:
- Check table exists: `bq show {project}:{dataset}.{table}`
- Verify column names match schema
- Check BigQuery permissions

**If JSON parsing fails**:
- Verify clean JSON extraction was used
- Check file contains valid JSON: `cat /tmp/bq_results_clean.json | python3 -m json.tool`
- If warnings mixed with JSON, re-run with `grep '^\['`

**If signature file corrupt**:
- Delete file: `rm /tmp/bigquery_error_signatures_*.json`
- Will recreate on next scan

**If no errors found**:
- Report: "✅ No errors found in time window"
- Ask if user wants to expand time window

## Related Skills

- **bigquery-skill-builder**: Creates table-specific skills that use this scanner
- **bug-analyzer**: Classifies errors discovered by this scanner
- **auto-bug-detector**: Orchestrates scanner + analyzer pipeline
- **ottm-bigquery-debugging**: Original inspiration for generated skills
