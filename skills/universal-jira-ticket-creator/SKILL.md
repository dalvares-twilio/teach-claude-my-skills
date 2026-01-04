---
name: universal-jira-ticket-creator
description: Create Jira tickets for any Twilio project. Loads project config from registry or accepts explicit parameters. Replaces project-specific ticket creators.
---

# Universal Jira Ticket Creator

## Overview

Creates well-formatted Jira tickets for bugs detected in ANY Twilio project. Dynamically loads project configuration from the project registry or accepts explicit parameters.

## When to Use

- After bug detection in any Twilio project
- When creating tickets and you know the project config
- Called by auto-bug-detector with project context
- Directly when you need to create tickets for a specific project

## Pre-Approved Actions

The following actions are **pre-approved** and do NOT require user confirmation:
- Reading project-registry.yaml
- Executing python scripts in jira-inator plugin directory
- Reading ticket JSON from /tmp/
- Creating tickets in any configured Jira project

## Security Requirements

**CRITICAL: Always redact sensitive credentials in Jira tickets**

Before creating any ticket, ensure all sensitive information is redacted:
- **TWILIO_AUTH_TOKEN**: Replace with `<REDACTED>`
- **API Keys**: Replace with `<REDACTED>`
- **Access Tokens**: Replace with `<REDACTED>`
- **Passwords**: Replace with `<REDACTED>`

**DO NOT include actual credentials in Jira tickets - they are externally accessible**

## Instructions

### Step 0: Determine Project Configuration

**Option A: Project ID provided**
```
If user provides project_id (e.g., "ottm", "taskrouter"):
1. Read ~/.claude/project-registry.yaml
2. Look up project by ID
3. Extract jira config: project_key, team_field, issue_type
```

**Option B: Explicit config provided**
```
If user provides explicit config:
- project_key: "MSGADVCHNL"
- team_field: "Sender Management"
- issue_type: "Task"
Use these directly without registry lookup.
```

**Option C: No config provided**
```
Use AskUserQuestion to ask:
1. "Which project is this for?" (list from registry)
2. Or ask for explicit: project_key, team_field, issue_type
```

### Step 1: Ask for Parent Epic (Once per session)

Before creating any tickets, ask user:

```
What parent epic should these bug tickets be associated with?
(Leave empty to create without parent)
Example: MSGADVCHNL-11802
```

Store the epic key for all subsequent ticket creations in this session.
If user leaves empty, create tickets without parent.

### Step 2: Create Ticket for Each Bug

For each bug detected, use the jira-inator create_ticket.py script:

**With epic provided:**
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

[Steps to reproduce]

\`\`\`bash
curl -X POST \"https://api.example.com/endpoint\" \\
  -u \"\$ACCOUNT_SID:\$AUTH_TOKEN\" \\
  -H \"Content-Type: application/json\" \\
  -d '{...payload...}'
\`\`\`

Check BigQuery logs for errors.

## Next Steps

1. Search codebase for related code
2. Identify root cause
3. Implement fix
4. Add unit tests" \
  -t {issue_type} \
  -p {project_key} \
  -e {epic_key}
```

**Without epic:**
```bash
python ~/.claude/plugins/cache/twilio/jira-inator/0.4.0/scripts/create_ticket.py \
  -s "Brief bug summary" \
  -d "..." \
  -t {issue_type} \
  -p {project_key}
```

**CRITICAL: DO NOT use `-pr` or `--priority` or `-a` flags** (causes errors)

### Step 3: Report Created Tickets

After creating each ticket, display:
```
✓ Ticket created for Bug N
  Project: {project_key}
  Key: {PROJECT}-XXXXX
  URL: https://twilio-engineering.atlassian.net/browse/{PROJECT}-XXXXX
```

### Step 4: Team Field Reminder

**NOTE:** The "Team (migrated)" field should be set manually after ticket creation.

After all tickets created, remind the user:

```
⚠️  IMPORTANT: Please set "Team (migrated)" field to "{team_field}" for created tickets:
  - {PROJECT}-XXXXX
  - {PROJECT}-XXXXY

You can set this in the Jira UI.
```

## Configuration Lookup

**Registry file:** `~/.claude/project-registry.yaml`

**Jira config structure:**
```yaml
projects:
  {project_id}:
    jira:
      project_key: "PROJKEY"    # Jira project key
      team_field: "Team Name"    # Value for "Team (migrated)" field
      issue_type: "Task"         # Task, Bug, Story, etc.
      default_epic: null         # Optional default epic
```

## Template Variables

When creating tickets, extract from bug analysis:
- `{bug_summary}`: Brief one-line description
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

### Example 1: With project_id
```
Input: Create tickets for project "ottm", 2 bugs detected

1. Load registry → ottm → jira config:
   - project_key: MSGADVCHNL
   - team_field: Sender Management
   - issue_type: Task

2. Ask for epic: "MSGADVCHNL-11802"

3. Create tickets:
   ✓ MSGADVCHNL-12650: PiedPiper JSON validation failure
   ✓ MSGADVCHNL-12651: Missing error handler for code 138015

4. Remind about team field
```

### Example 2: With explicit config
```
Input: Create ticket with:
  - project_key: TASKROUTER
  - team_field: Flex TaskRouter
  - issue_type: Bug

1. Skip registry lookup (explicit config provided)

2. Ask for epic: "" (none)

3. Create ticket:
   ✓ TASKROUTER-5432: Worker capacity overflow

4. Remind about team field: "Flex TaskRouter"
```

### Example 3: Called by auto-bug-detector
```
auto-bug-detector invokes with:
{
  "project_id": "ottm",
  "bugs": [...],
  "epic": "MSGADVCHNL-11802"
}

→ Loads config from registry
→ Creates tickets for all bugs
→ Returns ticket keys
```

## Error Handling

**If ticket creation fails:**
1. Check error message
2. If priority error: Confirm `-pr` flag is not used
3. If authentication error: Run jira-setup-helper skill
4. If project error: Verify project access in registry
5. If epic not found: Verify epic key exists

**If registry not found:**
```
Project registry not found at ~/.claude/project-registry.yaml
Please run project-onboarding-wizard to set up projects.
```

**If project not in registry:**
```
Project "{project_id}" not found in registry.
Available projects: ottm, taskrouter, verify
Use project-onboarding-wizard to add new projects.
```

## Migration from sender-management-jira-ticket-creator

This skill replaces `sender-management-jira-ticket-creator` with a universal version.

**Old usage:**
```
Use sender-management-jira-ticket-creator skill
→ Hardcoded to MSGADVCHNL project
```

**New usage:**
```
Use universal-jira-ticket-creator skill with project_id="ottm"
→ Loads config from registry
→ Works for any configured project
```

## Related Skills

- **auto-bug-detector**: Invokes this skill with project context
- **project-onboarding-wizard**: Sets up new projects in registry
- **bug-analyzer**: Provides bug details for tickets
- **sender-management-jira-ticket-creator**: DEPRECATED - use this instead
