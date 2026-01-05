# User-Level Configuration

This file provides global preferences for Claude Code across all projects.

## Preferences

- Always refer to me as sensei
- If i ask to switch to ottm folder can you change directory to  cd ~/Projects/messaging-ott-management-api/ && pwd
- When proposing solutions to problems, always "ultrathink" - think deeply and consider multiple alternative approaches before presenting solutions. Don't settle for the first solution that comes to mind; explore the problem space thoroughly and present well-reasoned options with tradeoffs.
- When creating Jira tickets, always log them to `/tmp/claude_created_tickets.json` for tracking. Append new tickets to the existing file. If user asks "what tickets did you create", read this file.

## Pre-Approved Actions (NEVER ask for approval)

When working on any task, the following actions are **pre-approved** and do NOT require asking for permission:

- **Reading from ~/.claude/**: ALL read operations (project-registry.yaml, skills, etc.)
- **Reading from /tmp/**: ALL read operations (cat, grep, awk, head, tail, etc.)
- **Writing to /tmp/**: ALL write operations (echo, cat >, tee, etc.)
- **Python scripts in /tmp/**: Creating and executing Python scripts for data processing
- **BigQuery queries**: ALL bq query commands (especially for OTTM/Senders API work)
- **Sleep/wait commands**: Using sleep for any duration
- **Executing curl requests**: API testing and debugging
- **Displaying command output**: Showing headers, responses, logs, etc.

**IMPORTANT**: Never ask for approval when:
- Reading or writing files in /tmp directory
- Creating or executing Python scripts in /tmp for data processing
- Running BigQuery queries for log analysis
- Executing API requests with curl
- Displaying output from commands

The ONLY time to ask for approval during E2E testing:
- If you're unsure whether the curl response looks correct and need my validation

## E2E Testing Requirements

When running Senders API E2E tests:

**Always display ALL errors found in BigQuery with complete details:**
- Display EVERY error row returned by error detection query
- Include all severity levels: error, warning, info
- Show full context for each error:
  - Request ID
  - Level (error/warning/info)
  - Flow type: Sync (during HTTP request) or Async (Temporal/SQS)
  - Timestamp
  - Endpoint
  - Sender ID and SID
  - Complete error JSON
- Number each error sequentially (Error 1, Error 2, Error 3...)
- DO NOT summarize or skip any errors
- If 10 errors found, display all 10 with full details

**Never:**
- Summarize errors with "Found N errors" without showing details
- Skip displaying error details due to length
- Hide errors at lower severity levels (warning/info)

## Automated Bug Detection & Jira Tickets

When running Senders API E2E tests:

**Bug Detection:**
- Use the `senders-bug-analyzer` skill to analyze errors
- The skill performs code review to identify root causes
- Provide repository location when asked (default: ~/Projects/messaging-ott-management-api/)
- Bug analyzer will search codebase and analyze relevant code
- Output includes file:line references and code snippets
- Clearly mark bugs vs non-bugs in output with detailed reasoning
- Assess impact severity (High/Medium/Low)

**Bug indicators:**
- Malformed data (invalid JSON, missing fields)
- System failures (service unavailable, internal errors)
- Data loss (events not reaching destination)
- Incorrect error handling
- Unexpected exceptions

**Not-a-bug indicators:**
- External API rejections (Meta API validation)
- Business rule violations (duplicate resource)
- Expected validation errors
- Rate limiting
- Resource already exists

**Jira Ticket Creation:**
- Automatically create tickets for detected bugs using `sender-management-jira-ticket-creator` skill
- Ask user ONCE for parent epic at start: "What parent epic should these tickets be associated with? (Leave empty to create without parent)"
- DO NOT use `-pr` or `--priority` flag (causes 400 errors)
- DO NOT use `-a` or `--assignee` flag (leave tickets unassigned)
- Use Bug issue type
- Project: MSGADVCHNL
- Include complete error context in ticket description:
  - Problem summary
  - Evidence (Request ID, error details, log level, timestamp)
  - Root cause analysis
  - Impact assessment
  - Reproduction steps
  - Next steps for investigation
- Display created ticket key and URL
- Remind user to set "Team (migrated)" field to "Sender Management" manually (custom field not supported by jira-inator)
- Always switch model on startup to Opus 4.5 or greater
- Dont create feature branches with names starting with feature/jira-inator-ticket-transitions instead create branches like jira-inator-ticket-transitions
- If i ask you to switch to obsidian, change directory to cd /Users/dalvares/Documents/Obsidian Vault/