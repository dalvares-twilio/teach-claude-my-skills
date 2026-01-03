---
name: sender-management-jira-ticket-creator
description: Create Jira Task tickets for Sender Management API bugs detected in E2E tests. Automatically formats bug details, sets "Team (migrated)" to "Sender Management", and avoids common ticket creation errors.
---

# Sender Management Jira Ticket Creator

## Overview

This skill creates well-formatted Jira Task tickets for bugs detected during Senders API E2E testing.

## When to Use

- After E2E test detects bugs in Senders API
- When creating Task tickets in MSGADVCHNL project
- To avoid common ticket creation errors (priority field)

## Pre-Approved Actions

The following actions are **pre-approved** and do NOT require user confirmation:
- Executing python scripts in jira-inator plugin directory
- Reading ticket JSON from /tmp/
- Creating Task tickets in MSGADVCHNL project

**IMPORTANT: Always ask user for parent epic once at the start**

## Security Requirements

**CRITICAL: Always redact sensitive credentials in Jira tickets**

Before creating any ticket, ensure all sensitive information is redacted:
- **TWILIO_AUTH_TOKEN**: Replace with `<REDACTED>`
- **API Keys**: Replace with `<REDACTED>`
- **Access Tokens**: Replace with `<REDACTED>`
- **Passwords**: Replace with `<REDACTED>`

Example of properly redacted reproduction steps:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=<REDACTED>

curl -X POST "https://messaging.dev.twilio.com/v2/Channels/Senders" \
  -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**DO NOT include actual credentials in Jira tickets - they are externally accessible**

## Instructions

### Step 1: Ask for Parent Epic (Once)

Before creating any tickets, ask user:

```
What parent epic should these bug tickets be associated with?
(Leave empty to create without parent)
Example: MSGADVCHNL-11802
```

Store the epic key for all subsequent ticket creations.
If user leaves empty, create tickets without parent.

### Step 2: Create Ticket for Each Bug

For each bug detected, use the jira-inator create_ticket.py script:

**IMPORTANT: Always create Task tickets (not Bug tickets)**

**If epic provided:**
```bash
python ~/.claude/plugins/cache/twilio/jira-inator/0.4.0/scripts/create_ticket.py \
  -s "Brief bug summary" \
  -d "## Problem

[Error description]

## Evidence

**Request ID:** [RQ_ID]
**Error:** \`[error details]\`
**Log Level:** [level]
**Flow:** [Sync/Async (Temporal/SQS)]
**Timestamp:** [timestamp]

## Root Cause Analysis

[Analysis from bug detection]

## Impact

- **Severity:** [severity]
- **Customer Impact:** [impact]
- **Affected Flow:** [sync/async flow]

## Reproduction

[Steps to reproduce from E2E test]

\`\`\`bash
curl -X POST \"https://messaging.dev.twilio.com/v2/Channels/Senders\" \\
  -u \"\$TWILIO_ACCOUNT_SID:\$TWILIO_AUTH_TOKEN\" \\
  -H \"Content-Type: application/json\" \\
  -d '{...payload...}'
\`\`\`

Check BigQuery logs for errors.

## Next Steps

1. Search codebase for related code
2. Identify root cause
3. Implement fix
4. Add unit tests" \
  -t Task \
  -p MSGADVCHNL \
  -e PARENT_EPIC_KEY
```

**If no epic provided:**
```bash
python ~/.claude/plugins/cache/twilio/jira-inator/0.4.0/scripts/create_ticket.py \
  -s "Brief bug summary" \
  -d "..." \
  -t Task \
  -p MSGADVCHNL
```

**CRITICAL: DO NOT use `-pr` or `--priority` or `-a` flags**

### Step 3: Report Created Tickets

After creating each ticket, display:
```
✓ Ticket created for Bug N
  Key: MSGADVCHNL-XXXXX
  URL: https://twilio-engineering.atlassian.net/browse/MSGADVCHNL-XXXXX
```

### Step 4: Team Field (Important)

**NOTE:** The "Team (migrated)" field should be set to "Sender Management" for all tickets.

Currently, the jira-inator script doesn't support the Team custom field.
After ticket creation, remind the user:

```
⚠️  IMPORTANT: Please set "Team (migrated)" field to "Sender Management" for created tickets:
  - MSGADVCHNL-XXXXX
  - MSGADVCHNL-XXXXY

You can set this in the Jira UI or ask to investigate adding Team field support to jira-inator.
```

## Error Handling

**If ticket creation fails:**
1. Check error message
2. If priority error: Confirm `-pr` flag is not used
3. If authentication error: Run jira-setup-helper skill
4. If project error: Verify MSGADVCHNL project access
5. If epic not found: Verify epic key exists

## Template Variables

When creating tickets, extract from bug analysis:
- `{bug_summary}`: Brief one-line description (e.g., "PiedPiper debug event publishing fails with malformed JSON")
- `{request_id}`: RQ ID from BigQuery
- `{error}`: Full error message
- `{level}`: error/warning/info
- `{flow}`: Sync/Async (Temporal/SQS)
- `{timestamp}`: Error timestamp
- `{analysis}`: Root cause analysis
- `{severity}`: Impact severity (High/Medium/Low)
- `{customer_impact}`: Customer-facing impact description
- `{reproduction}`: Steps from E2E test

## Example Usage

**Input:** 3 bugs detected in E2E test, epic MSGADVCHNL-11802

**Output:**
```
What parent epic should these bug tickets be associated with?
(Leave empty to create without parent)
Example: MSGADVCHNL-11802
> MSGADVCHNL-11802

Creating Jira ticket for Bug 1...
✓ Task ticket created for Bug 1
  Key: MSGADVCHNL-12633
  URL: https://twilio-engineering.atlassian.net/browse/MSGADVCHNL-12633

Creating Jira ticket for Bug 2...
✓ Task ticket created for Bug 2
  Key: MSGADVCHNL-12634
  URL: https://twilio-engineering.atlassian.net/browse/MSGADVCHNL-12634

Creating Jira ticket for Bug 3...
✓ Task ticket created for Bug 3
  Key: MSGADVCHNL-12635
  URL: https://twilio-engineering.atlassian.net/browse/MSGADVCHNL-12635

⚠️  IMPORTANT: Please set "Team (migrated)" field to "Sender Management" for created tickets:
  - MSGADVCHNL-12633
  - MSGADVCHNL-12634
  - MSGADVCHNL-12635
```

Tickets will be Task type, unassigned, and have default P2 priority.

## Future Improvement

To avoid manual "Team (migrated)" field setting, investigate adding custom field support to jira-inator:
1. Find "Team (migrated)" field ID (customfield_XXXXX) for MSGADVCHNL project
2. Add TEAM_FIELD_TWILIO_ENGINEERING configuration to jira-inator .env
3. Update create_ticket.py to support --team flag
