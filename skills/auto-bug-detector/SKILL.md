---
name: auto-bug-detector
description: Automated bug detection pipeline that orchestrates error scanning, classification, and reporting. User-friendly interface for complete end-to-end bug discovery from BigQuery logs.
---

# Auto Bug Detector (Pipeline Orchestrator)

## Overview

Complete automated bug detection pipeline that combines error scanning, classification, and reporting into a single user-friendly workflow. **Works with ANY Twilio project** through the centralized project registry.

## When to Use

- "Scan {table/skill} for bugs from last N hours"
- "Find bugs in {table}"
- "Scan OTTM/Senders logs for bugs"
- "Auto-detect bugs and create tickets"
- "Check {monitoring-skill} for new bugs"
- "Scan {project_id} for bugs" (e.g., "Scan ottm for bugs")

## Pipeline Stages

```
0. Load Project Registry
   ↓ Read ~/.claude/project-registry.yaml
0.5. Auto-Detect Project
   ↓ Match table name against registered patterns
1. Error Discovery (bigquery-error-scanner)
   ↓ Finds UNIQUE error patterns using project's column config
2. Bug Classification (bug-analyzer)
   ↓ Categorizes: BUG / EXPECTED / IMPROVEMENT
   ↓ Uses project's custom error_patterns
3. Error Mapping Check (if project.error_mapping.enabled)
   ↓ Identifies unmapped external API error codes
4. User Review
   ↓ User decides on actions
5. Actions (optional)
   ↓ Create tickets using project's Jira config
6. Final Report
```

## Pre-Approved Actions

- Reading ~/.claude/project-registry.yaml
- Invoking bigquery-error-scanner
- Invoking bug-analyzer
- Invoking universal-error-mapping-scanner (if project.error_mapping.enabled)
- Reading codebase error handler files (from project.repository)
- Reading results from invoked skills
- Displaying comprehensive reports
- Asking user for action decisions

## Instructions

### Step 0: Load Project Registry

**Read the project registry file:**
```bash
cat ~/.claude/project-registry.yaml
```

**Parse into memory:**
- Extract all project configurations
- Build lookup table of `table_patterns` → `project_id`
- Store for use in subsequent steps

**If registry not found:**
```
Project registry not found at ~/.claude/project-registry.yaml
Would you like to:
1. Create a new registry with a project (use project-onboarding-wizard)
2. Continue with manual configuration
```

### Step 0.5: Auto-Detect Project

**Option A: Project ID explicitly provided**
```
User: "Scan ottm for bugs" or "Scan OTTM logs"
→ project_id = "ottm"
→ Load config from registry.projects.ottm
```

**Option B: Table name provided - Pattern Match**
```
User: "Scan qtco-messaging-channels.prod.app_messaging_ott_management_api_mgmt_stdout"
→ Extract table name
→ Check against each project's table_patterns
→ "messaging_ott_management" matches ottm.bigquery.table_patterns
→ project_id = "ottm"
→ Load config from registry.projects.ottm
```

**Option C: Generated skill name provided**
```
User: "Scan ottm-logs-monitor for bugs"
→ Check if skill has project_id metadata
→ Or extract from skill name pattern
→ Load config from registry
```

**Option D: No match found**
```
Could not auto-detect project. Which project is this for?

Available projects:
1. ottm - OTT Management API (Sender Management)
2. taskrouter - TaskRouter (Flex TaskRouter)
3. [Other registered projects...]
4. None - Use manual configuration
```

**Store detected project config for use in subsequent steps:**
```yaml
current_project:
  id: "ottm"
  name: "OTT Management API"
  bigquery: { ... }
  jira: { ... }
  error_patterns: { ... }
  error_mapping: { ... }
```

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

**If project detected (from Step 0.5)**:
- Use project's BigQuery config from registry:
  - `table`: `{project.bigquery.project}.{env}.{project.bigquery.tables.app_logs}`
  - `error_column`: `{project.bigquery.columns.error}`
  - `timestamp_column`: `{project.bigquery.columns.timestamp}`
  - `level_column`: `{project.bigquery.columns.level}`
  - `partition_column`: `{project.bigquery.columns.partition}`
  - `identity_column`: `{project.bigquery.columns.request_id}` or `{project.bigquery.columns.resource_id}`

**If using generated skill**:
- Generated skill contains all configuration
- Invoke skill directly: `{skill-name}`

**If using table name directly (no project match)**:
- Need to get column configuration from user
- Invoke `bigquery-error-scanner` with provided details

**Execute scanner**:

Follow the `bigquery-error-scanner` skill instructions with these parameters:
- table: `{project.bigquery.project}.{env}.{project.bigquery.tables.app_logs}`
- error_column: `{project.bigquery.columns.error}` (default: "error")
- timestamp_column: `{project.bigquery.columns.timestamp}` (default: "timestamp")
- level_column: `{project.bigquery.columns.level}` (default: "level")
- partition_column: `{project.bigquery.columns.partition}` (default: "PARTITIONDATE")
- identity_column: `{project.bigquery.columns.request_id}` (optional)
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
1. Yes - use project repository ({project.repository})
2. Yes - provide different repository path
3. No - classify based on error messages only
```

**Execute analyzer**:

Follow the `bug-analyzer` skill instructions with:
- errors: {list of NEW errors}
- repository_path: `{project.repository}` or user-provided path
- **project_context**: Pass project's custom error patterns from registry:
  ```yaml
  project_context:
    project_id: "{project.id}"
    project_name: "{project.name}"
    error_patterns:
      expected: {project.error_patterns.expected}
      bugs: {project.error_patterns.bugs}
  ```

> **Note**: The bug-analyzer skill merges project-specific patterns with universal patterns. Project patterns take precedence for classification.

**Collect classification results**:
- Bugs detected
- Expected behaviors
- Improvement opportunities
- Code review findings (if performed)
- Confidence levels (High/Medium/Low)

**Display analyzer summary**:
```
## Stage 2: Bug Classification

Analyzed: {N} new errors
Results:
- 🐛 BUGS: {bug_count}
- ✅ EXPECTED: {expected_count}
- 💡 IMPROVEMENTS: {improvement_count}
```

### Step 4.5: Error Mapping Check (If Configured)

**Check if project has error mapping enabled:**
```yaml
# From project registry
project.error_mapping.enabled: true/false
```

**When to run this step**:
- Project has `error_mapping.enabled: true` in registry
- Errors contain patterns matching `project.error_mapping.error_patterns`

**Trigger conditions** (any of these):
1. Bug analyzer classified errors as "UNKNOWN" or low confidence
2. Errors contain external API error codes that returned generic responses
3. User explicitly requests mapping check

**If triggered, follow `universal-error-mapping-scanner` instructions** with project config:

1. **Extract error codes** from discovered errors using project's patterns:
   - Use `project.error_mapping.error_patterns` to identify relevant errors
   - Parse error codes/subcodes from error messages
   - Build list of unique code combinations

2. **Read codebase error handlers** from project config:
   ```
   Repository: {project.repository}
   Files: {project.error_mapping.handler_files}
   Variable: {project.error_mapping.mapping_variable}
   ```

3. **Cross-reference** to find unmapped codes:
   - Extract handled codes from `{project.error_mapping.mapping_variable}` in codebase
   - Compare with codes found in errors
   - Identify gaps

4. **Display mapping check results**:
```
## Stage 3: {project.error_mapping.external_api} Error Mapping Check

Project: {project.name}
External API: {project.error_mapping.external_api}
Checked: {N} error codes from discovered errors
Mapped in codebase: {mapped_count}
**Unmapped (Gaps)**: {unmapped_count}

{IF GAPS FOUND}
### Unmapped {project.error_mapping.external_api} Error Codes

| Code | Subcode | Occurrences | Context | Suggested Action |
|------|---------|-------------|---------|------------------|
| {code} | {subcode} | {count} | {endpoint} | Add to error handler |

⚠️  These errors are returning generic responses to customers.
Consider adding mappings in `{project.error_mapping.handler_files[0]}`.
{END IF}

{IF NO GAPS}
✅ All {project.error_mapping.external_api} error codes are properly mapped in codebase.
{END IF}
```

5. **Add to ticket creation options** (Step 6):
   - If gaps found, offer to create tech debt ticket for mapping improvements
   - Group with other improvement opportunities

**Skip this step if**:
- `project.error_mapping.enabled` is false or not configured
- No errors matching `project.error_mapping.error_patterns` found
- User opts out

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

**If project detected (from Step 0.5)**:
- Auto-configure using project's Jira settings:
  ```yaml
  ticket_config:
    project_key: "{project.jira.project_key}"
    team_field: "{project.jira.team_field}"
    issue_type: "{project.jira.issue_type}"
  ```
- Confirm with user:
  ```
  Will create tickets in {project.jira.project_key} ({project.name}).
  Proceed? (Y/n)
  ```

**If no project detected**:
Ask user which system to use:
```
Question: "Which ticket system should be used for bugs?"
Options:
1. Select from registered projects: [list from registry]
2. Jira - Generic (provide project_key, team, type)
3. None (just report, no tickets)
```

**Use universal-jira-ticket-creator** with project config:
```yaml
universal-jira-ticket-creator:
  project_id: "{project.id}"  # Loads config from registry
  # OR explicit config:
  project_key: "{project.jira.project_key}"
  team_field: "{project.jira.team_field}"
  issue_type: "{project.jira.issue_type}"
```

**Store selection** for the session - don't ask again for subsequent bugs.

### Step 7: Execute Actions (If Requested)

**If user wants tickets**:

**Ask for epic** (if creating tickets):
```
What parent epic should tickets be linked to?
(Leave empty for no parent)
Example: {project.jira.project_key}-XXXXX
```

**For each bug/improvement**:
- Follow the `universal-jira-ticket-creator` skill instructions
- Pass project config: `project_id: "{project.id}"` or explicit jira config
- Pass bug details: summary, description, impact, code location, etc.
- Collect ticket keys

**Display ticket results**:
```
✅ Created tickets:
- {project.jira.project_key}-123: {bug summary} (High impact)
- {project.jira.project_key}-124: {bug summary} (Medium impact)

⚠️  Remember to set "Team (migrated)" field to "{project.jira.team_field}"
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

### Session 1: Auto-Detected Project Scan

```
User: "Scan ottm for bugs from last 4 hours"

Bot:
## Step 0: Loading Project Registry
Reading ~/.claude/project-registry.yaml...
Found 3 registered projects.

## Step 0.5: Project Detection
Matched "ottm" → OTT Management API (Sender Management)
Using project config from registry.

## Stage 1: Error Discovery
Scanned: qtco-messaging-channels.prod.app_messaging_ott_management_api_mgmt_stdout
Found 12 errors, 2 NEW unique patterns

## Stage 2: Bug Classification
Perform code review? (Yes/No)
1. Yes - use project repository (~/Projects/messaging-ott-management-api)
2. Yes - provide different path
3. No
User: "1"

Analyzing with project's custom error patterns...
- 🐛 BUGS: 1
- ✅ EXPECTED: 1

### Bug 1: PiedPiper debug event JSON validation failure
**Impact**: Medium
**Code**: internal/management/workflow/activity_error_handler.go:265
**Fix**: Validate AccountSID before publishing

### Expected 1: Meta API phone already registered
**Impact**: N/A (matched project pattern: "External validation - phone already registered on WhatsApp")

What would you like to do?
User: "Create ticket for the bug"

Will create tickets in MSGADVCHNL (OTT Management API). Proceed? (Y/n)
User: "Y"

Epic? (empty for none)
User: "MSGADVCHNL-11802"

✅ Created MSGADVCHNL-12640

⚠️  Remember to set "Team (migrated)" field to "Sender Management"

Report complete!
```

### Session 2: Project with Error Mapping Scanner

```
User: "Scan OTTM prod logs for bugs from last 24 hours"

Bot:
## Step 0: Loading Project Registry
Found: ottm (OTT Management API)

## Step 0.5: Project Detection
Auto-detected project: ottm
Note: Project has error_mapping.enabled = true (Meta Graph API)

## Stage 1: Error Discovery
Scanned: qtco-messaging-channels.prod.app_messaging_ott_management_api_mgmt_stdout
Found 25 errors, 5 NEW unique patterns

## Stage 2: Bug Classification
Analyzing with project error patterns...
- 🐛 BUGS: 1 (PiedPiper JSON validation failure)
- ✅ EXPECTED: 2 (Meta API rejections)
- ❓ UNKNOWN: 2 (Meta errors with generic responses)

## Stage 3: Meta Graph API Error Mapping Check
Project: OTT Management API
External API: Meta Graph API
Checking codebase at ~/Projects/messaging-ott-management-api/...

Reading: internal/management/workflow/activity_error_handler.go
Reading: internal/management/processor/parser.go

Checked: 4 Meta error codes from discovered errors
Mapped in codebase: 2
**Unmapped (Gaps)**: 2

### Unmapped Meta Graph API Error Codes

| Code | Subcode | Occurrences | Context | Suggested Action |
|------|---------|-------------|---------|------------------|
| 138015 | 2593145 | 15 | update/async | Add to error handler |
| 131031 | 0 | 3 | create/async | Add to error handler |

⚠️  These errors are returning generic responses to customers.

What would you like to do?
1. Create ticket for bug (PiedPiper issue)
2. Create ticket for unmapped error codes (tech debt)
3. Create both tickets
4. Just report

User: "3"

Epic for tickets?
User: "MSGADVCHNL-12497"

✅ Created tickets:
- MSGADVCHNL-12641: PiedPiper JSON validation failure (Bug)
- MSGADVCHNL-12642: Add Meta error mappings for unmapped codes (Tech Debt)

⚠️  Remember to set "Team (migrated)" field to "Sender Management"

Report complete!
```

### Session 3: Unrecognized Table (Manual Config)

```
User: "Scan my-company.prod.errors for bugs from last 6 hours"

Bot:
## Step 0: Loading Project Registry
Found 3 registered projects.

## Step 0.5: Project Detection
Table "my-company.prod.errors" did not match any registered patterns.

Could not auto-detect project. Which project is this for?
1. ottm - OTT Management API (Sender Management)
2. taskrouter - TaskRouter (Flex TaskRouter)
3. verify - Verify Service (Verify Team)
4. None - Use manual configuration

User: "4"

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
Analyzing with universal patterns only...
- 🐛 BUGS: 2
- 💡 IMPROVEMENTS: 1

(Stage 3 skipped - no error_mapping configured)

[Results displayed]

Create tickets?
User: "Just report for now"

Report saved!
```

### Session 4: New Project (First-Time Setup)

```
User: "Scan taskrouter logs for bugs"

Bot:
## Step 0: Loading Project Registry
Found: taskrouter (TaskRouter)

## Step 0.5: Project Detection
Auto-detected project: taskrouter
Note: Project has error_mapping.enabled = false

## Stage 1: Error Discovery
Scanned: twilio-taskrouter.prod.taskrouter_app_logs
Found 5 errors, 2 NEW unique patterns

## Stage 2: Bug Classification
Perform code review?
1. Yes - use project repository (~/Projects/taskrouter)
2. Yes - provide different path
3. No
User: "1"

Analyzing with project error patterns + universal patterns...
- 🐛 BUGS: 1
- ✅ EXPECTED: 1

(Stage 3 skipped - error_mapping not enabled for this project)

What would you like to do?
User: "Create ticket"

Will create tickets in TASKROUTER (TaskRouter). Proceed? (Y/n)
User: "Y"

Epic?
User: ""

✅ Created TASKROUTER-5432

⚠️  Remember to set "Team (migrated)" field to "Flex TaskRouter"

Report complete!
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
- `bigquery-error-scanner` - error discovery (Stage 1)
- `bug-analyzer` - classification (Stage 2) with project_context
- `universal-error-mapping-scanner` - codebase gap analysis (Stage 3, if enabled)
- `universal-jira-ticket-creator` - ticketing (optional) with project's jira config
- Generated monitoring skills - table-specific scanning

**Used by**:
- Direct user invocation
- Scheduled tasks (future)
- CI/CD pipelines (future)

**Configuration Sources**:
- `~/.claude/project-registry.yaml` - centralized project configurations

## Privacy & Security

✅ Uses existing skill permissions (scanner + analyzer)
✅ No additional data exposure
✅ Local processing only
✅ User approval for all actions (tickets, etc.)
✅ Project configs stored locally in user's ~/.claude directory

## Related Skills

- **project-onboarding-wizard**: Add new projects to registry (setup)
- **bigquery-skill-builder**: Creates monitoring skills for any project
- **bigquery-error-scanner**: Stage 1 of pipeline (error discovery)
- **bug-analyzer**: Stage 2 of pipeline (classification with project_context)
- **universal-error-mapping-scanner**: Stage 3 of pipeline (if project.error_mapping.enabled)
- **universal-jira-ticket-creator**: Ticketing with project's jira config
- **ottm-bigquery-debugging**: Deep-dive debugging (complementary)
- **request-analyzer**: Analyze specific request IDs (complementary)

## Deprecated Skills (Backward Compatibility)

These skills are deprecated but still work. Use universal versions instead:
- `sender-management-jira-ticket-creator` → use `universal-jira-ticket-creator` with project_id="ottm"
- `meta-error-mapping-scanner` → use `universal-error-mapping-scanner` with project_id="ottm"
