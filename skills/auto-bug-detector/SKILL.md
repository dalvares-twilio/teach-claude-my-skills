---
name: auto-bug-detector
description: Automated bug detection pipeline that orchestrates error scanning, classification, and reporting. User-friendly interface for complete end-to-end bug discovery from BigQuery logs.
---

# Auto Bug Detector (Pipeline Orchestrator)

## Overview

Complete automated bug detection pipeline that combines error scanning, classification, and reporting into a single user-friendly workflow. Works with any BigQuery table or generated monitoring skill.

## When to Use

- "Scan {table/skill} for bugs from last N hours"
- "Find bugs in {table}"
- "Auto-detect bugs and create tickets"
- "Check {monitoring-skill} for new bugs"

## Pipeline Stages

```
1. Error Discovery (bigquery-error-scanner)
   ↓ Finds UNIQUE error patterns
2. Bug Classification (bug-analyzer)
   ↓ Categorizes: BUG / EXPECTED / IMPROVEMENT
3. User Review
   ↓ User decides on actions
4. Actions (optional)
   ↓ Create tickets, log improvements, etc.
5. Final Report
```

## Pre-Approved Actions

- Invoking bigquery-error-scanner
- Invoking bug-analyzer
- Reading results from invoked skills
- Displaying comprehensive reports
- Asking user for action decisions

## Instructions

### Step 1: Parse User Request

Extract configuration from request:

**Option A: Using Generated Skill**:
```
"Scan app-logs-monitor for bugs from last 6 hours"
→ Skill name: app-logs-monitor
→ Time window: 6 hours
```

**Option B: Direct Table Reference**:
```
"Scan qtco-messaging-channels.prod.app_logs for bugs"
→ Table: qtco-messaging-channels.prod.app_logs
→ Will need column configuration
```

**Option C: With Additional Parameters**:
```
"Scan order-logs for bugs from last 4 hours with code review at ~/code/orders"
→ Time window: 4 hours
→ Repository: ~/code/orders
```

### Step 2: Invoke Error Scanner

**Determine scanner configuration**:

**If using generated skill**:
- Generated skill contains all configuration
- Invoke skill directly: `{skill-name}`

**If using table name directly**:
- Need to get column configuration
- Invoke `bigquery-error-scanner` with table details

**Execute scanner**:

Follow the `bigquery-error-scanner` skill instructions with these parameters:
- table: {project.dataset.table}
- error_column: {column}
- timestamp_column: {column}
- level_column: {column} (optional)
- partition_column: {column} (optional)
- identity_column: {column} (optional)
- hours_back: {N}

> **Note**: Skills cannot directly invoke other skills. Instead, follow the skill's documented instructions to perform the scan.

**Collect results**:
- List of UNIQUE/NEW errors found
- Total error count
- Seen before count

**Display scanner summary**:
```
## Stage 1: Error Discovery

Scanned: {table}
Time Window: Last {N} hours
Total Errors: {total}
NEW Unique Patterns: {new_count}
Seen Before: {seen_count}
```

### Step 3: Check Results

**If no NEW errors found**:
```
✅ No new error patterns detected!

All {total} errors in time window are previously seen patterns.

Options:
1. Reset signatures (see all as new)
2. Expand time window
3. Done
```

Return early if user chooses "Done".

**If NEW errors found**, proceed to classification.

### Step 4: Invoke Bug Analyzer

**Prepare error list** for analyzer:
- Extract NEW errors from scanner results
- Format as structured data (JSON or text)

**Ask about code review**:
```
Found {N} new errors. Perform code review to find root causes?

Options:
1. Yes - provide repository path
2. No - classify based on error messages only
```

**Execute analyzer**:

Follow the `bug-analyzer` skill instructions with:
- errors: {list of NEW errors}
- repository_path: {path if provided}

> **Note**: The bug-analyzer skill includes confidence scoring and precedence rules. Results will include confidence levels (High/Medium/Low) for each classification.

**Collect classification results**:
- Bugs detected
- Expected behaviors
- Improvement opportunities
- Code review findings (if performed)

**Display analyzer summary**:
```
## Stage 2: Bug Classification

Analyzed: {N} new errors
Results:
- 🐛 BUGS: {bug_count}
- ✅ EXPECTED: {expected_count}
- 💡 IMPROVEMENTS: {improvement_count}
```

### Step 5: Present Detailed Results

**For each classified error**, display:

```
### Error {N}: {error_message}

**Classification**: {BUG 🐛 | EXPECTED ✅ | IMPROVEMENT 💡} (Confidence: {High|Medium|Low} - {0.XX})
**Impact**: {High | Medium | Low}
**Reasoning**: {explanation}

{IF BUG OR IMPROVEMENT}
**Recommended Action**: {action}
{END IF}

{IF CODE REVIEW}
**Code Location**: {file:line}
**Root Cause**: {cause}
**Suggested Fix**: {fix}
{END IF}
```

### Step 6: Ask for Actions

**Present action options based on results**:

**If bugs detected**:
```
Found {N} bugs. What would you like to do?

1. Create Jira tickets for all bugs
2. Create tickets for high-impact bugs only
3. Show bug details and let me decide
4. Do nothing (just report)
```

**If improvements found**:
```
Found {N} improvement opportunities. How should we track these?

1. Add to backlog (create tickets)
2. Log to file for future review
3. Just note in this report
```

**If expected errors**:
```
{N} errors are expected behavior (no action needed).
Show details anyway?
```

### Step 6.5: Configure Ticket Creator (If Creating Tickets)

Before creating tickets, ask user which system to use:

**Use AskUserQuestion**:
```
Question: "Which ticket system should be used for bugs?"
Options:
1. Jira - Sender Management (sender-management-jira-ticket-creator) - For OTTM/Senders API bugs
2. Jira - Generic (jira-inator:jira-ticket-creator) - For other projects
3. None (just report, no tickets)
```

**Store selection** for the session - don't ask again for subsequent bugs.

### Step 7: Execute Actions (If Requested)

**If user wants tickets**:

**Ask for epic** (if creating tickets):
```
What parent epic should tickets be linked to?
(Leave empty for no parent)
Example: MSGADVCHNL-11802
```

**For each bug/improvement**:
- Follow the selected ticket creator skill instructions
- Pass bug details: summary, description, impact, code location, etc.
- Collect ticket keys

**Display ticket results**:
```
✅ Created tickets:
- BUG-123: {bug summary} (High impact)
- BUG-124: {bug summary} (Medium impact)

⚠️  Remember to set "Team (migrated)" field to appropriate team
```

### Step 8: Generate Final Report

**Comprehensive summary**:

```
# Automated Bug Detection Report

**Date**: {current_timestamp}
**Table/Skill**: {table or skill name}
**Time Window**: Last {N} hours

## Executive Summary

- **Total Errors Found**: {total}
- **New Unique Patterns**: {new_count}
- **Bugs Detected**: {bug_count} 🐛
- **Improvement Opportunities**: {improvement_count} 💡
- **Expected Behaviors**: {expected_count} ✅

## Critical Findings

### High-Impact Bugs ({count})
{List of high-impact bugs with brief descriptions}

### Medium-Impact Bugs ({count})
{List of medium-impact bugs}

### Improvement Opportunities ({count})
{List of improvements}

## Detailed Analysis

{For each error, include:}
- Error message
- Classification and reasoning
- Impact assessment
- Code review findings (if performed)
- Action taken (ticket created, etc.)

## Actions Taken

{IF TICKETS CREATED}
**Jira Tickets Created**:
- [TICKET-123] {summary} - {URL}
- [TICKET-124] {summary} - {URL}
{END IF}

{IF IMPROVEMENTS LOGGED}
**Improvements Logged**: See {file/location}
{END IF}

## Recommendations

{Smart recommendations based on findings, e.g.:}
- Consider adding monitoring for {pattern}
- Review {service} connection pool settings
- Investigate recent deployment from {date}

## Next Steps

1. {Action item 1}
2. {Action item 2}
3. Schedule next scan in {N} hours

---

Generated by auto-bug-detector skill
Error signatures tracked in: /tmp/bigquery_error_signatures_*
```

### Step 9: Offer Follow-Up Actions

```
Report complete! What's next?

1. Run another scan (different time window)
2. Reset error signatures (start fresh)
3. Export report to file
4. Done
```

## Configuration Modes

### Mode 1: Simple

User provides minimal info:
```
"Scan my-logs for bugs"
→ Auto-configure everything
→ Ask only necessary questions
```

### Mode 2: Detailed

User provides full configuration:
```
"Scan project.dataset.table for bugs from last 8 hours
 error column: error_msg
 repository: ~/code/service
 create tickets in JIRA-123 epic"
→ Skip unnecessary questions
→ Execute with provided config
```

### Mode 3: Using Generated Skills

Easiest mode:
```
"Scan app-logs-monitor for bugs"
→ All config in generated skill
→ Minimal questions
→ Fast execution
```

## Example Sessions

### Session 1: Quick Scan with Generated Skill

```
User: "Scan ottm-logs-monitor for bugs from last 4 hours"

Bot:
## Stage 1: Error Discovery
Scanned: qtco-messaging-channels.prod.app_messaging_ott_management_api_mgmt_stdout
Found 12 errors, 2 NEW unique patterns

## Stage 2: Bug Classification
Perform code review? (Yes/No)
User: "Yes, ~/Projects/messaging-ott-management-api"

Analyzing...
- 🐛 BUGS: 1
- ✅ EXPECTED: 1

### Bug 1: PiedPiper debug event JSON validation failure
**Impact**: Medium
**Code**: internal/management/workflow/activity_error_handler.go:265
**Fix**: Validate AccountSID before publishing

### Expected 1: Meta API phone already registered
**Impact**: N/A

What would you like to do?
User: "Create ticket for the bug"

Epic? (empty for none)
User: "MSGADVCHNL-11802"

✅ Created MSGADVCHNL-12640

Report complete!
```

### Session 2: Direct Table Scan

```
User: "Scan my-company.prod.errors for bugs from last 6 hours"

Bot:
Discovering schema...
Found columns: timestamp, error_message, severity, user_id...

Which column has errors?
User: "error_message"

Which is timestamp?
User: "timestamp"

Severity column?
User: "severity"

## Stage 1: Error Discovery
Found 8 errors, 3 NEW patterns

Perform code review?
User: "No"

## Stage 2: Bug Classification
Analyzing...
- 🐛 BUGS: 2
- 💡 IMPROVEMENTS: 1

[Results displayed]

Create tickets?
User: "Just report for now"

Report saved!
```

## Advanced Features

### Scheduled Scanning

Store configuration for repeat scans:
```json
{
  "scan_name": "ottm-prod-hourly",
  "table": "qtco-messaging-channels.prod.app_logs",
  "frequency": "1 hour",
  "auto_ticket": false,
  "epic": "MSGADVCHNL-11802"
}
```

### Trend Analysis

Track bugs over time:
```
Last 7 Days:
- Mon: 3 bugs
- Tue: 1 bug
- Wed: 5 bugs ⚠️  Spike
- Thu: 2 bugs
- Fri: 1 bug
```

### Smart Recommendations

Based on patterns:
- "Error spike detected after deployment X"
- "Consider scaling service Y (connection pool errors)"
- "Performance degradation trend (query times increasing)"

## Performance

- **Scanner**: ~2-5 seconds (depends on table size)
- **Analyzer**: ~1-2 seconds per error
- **Total Pipeline**: ~10-30 seconds for typical scan (10 errors)

## Error Handling

**If scanner fails**:
- Display error message
- Offer to retry
- Suggest checking table access

**If analyzer fails**:
- Continue with partial results
- Note which errors couldn't be analyzed
- Offer to retry those errors

**If ticket creation fails**:
- Continue with report
- Save bug details to file
- Offer manual retry

## Integration Points

**Invokes**:
- `bigquery-error-scanner` - error discovery
- `bug-analyzer` - classification
- `sender-management-jira-ticket-creator` - ticketing (optional)
- Generated monitoring skills - table-specific scanning

**Used by**:
- Direct user invocation
- Scheduled tasks (future)
- CI/CD pipelines (future)

## Privacy & Security

✅ Uses existing skill permissions (scanner + analyzer)
✅ No additional data exposure
✅ Local processing only
✅ User approval for all actions (tickets, etc.)

## Related Skills

- **bigquery-skill-builder**: Creates skills for this orchestrator
- **bigquery-error-scanner**: Stage 1 of pipeline
- **bug-analyzer**: Stage 2 of pipeline
- **sender-management-jira-ticket-creator**: Optional stage 4
- **ottm-bigquery-debugging**: Deep-dive debugging (complementary)
