---
name: senders-bug-analyzer
description: "[DEPRECATED] Use bug-analyzer instead - it now includes Senders API patterns. Analyze Senders API errors to determine if they are bugs or expected behavior."
---

# Senders Bug Analyzer

> ⚠️ **DEPRECATED**: This skill is deprecated. Use `bug-analyzer` instead, which now includes:
> - All Senders API / OTTM-specific patterns
> - Confidence scoring for classifications
> - Pattern precedence rules to avoid misclassification
> - Enhanced code review capabilities
>
> The `bug-analyzer` skill is service-agnostic but includes a "Senders API / OTTM Patterns" section with all the domain knowledge from this skill.

## Overview
Expert bug analysis for Senders API errors. Distinguishes genuine bugs from expected behavior (Meta API rejections, validation errors, etc.).

## When to Use
- After detecting errors in Senders API operations
- When E2E tests find errors and need bug classification
- For standalone error analysis without running full E2E tests
- When debugging specific Request IDs from BigQuery

## Pre-Approved Actions

The following actions are **pre-approved** and do NOT require user confirmation:
- Reading error details from /tmp/
- Displaying analysis results
- Using Grep to search repository for error strings
- Reading source files in repository
- Displaying code snippets in analysis
- NO ticket creation (use sender-management-jira-ticket-creator for that)

## Instructions

### Input Format

Expect error details with:
- Request ID
- Error message
- Log level (error/warning/info)
- Flow type (Sync/Async - Temporal/SQS)
- Timestamp
- Endpoint
- Full error JSON

### Step 1: Ask for Repository Location

At the start of bug analysis, ask user for repository location:

**Use AskUserQuestion tool:**

Question: "To perform code review and identify root causes in the codebase, what is the repository location?"

Options:
1. Default OTTM location: ~/Projects/messaging-ott-management-api/ (Recommended)
2. Custom path (user will specify)

**Store the repository path for subsequent code review searches.**

### Step 2: Analyze Errors (Pattern-Based)

**Bug Indicators:**
- Malformed data (invalid JSON, missing fields)
- System failures (service unavailable, internal errors)
- Data loss (events not reaching destination)
- Incorrect error handling
- Unexpected exceptions
- Code defects causing incorrect behavior

**Not-a-Bug Indicators:**
- External API rejections (Meta API validation failures)
- Business rule violations (duplicate resource, already exists)
- Expected validation errors (invalid input format)
- Rate limiting responses
- Resource already exists errors
- User input validation failures

### Step 3: Code Review (For Detected Bugs)

For each bug detected in Step 2, perform code review:

**3.1: Search for Error Origin**

Use Grep to search in repository:
1. Search for exact error message strings
2. Search for error logging statements
3. Search for related function/class names

**3.2: Read Relevant Files**

Read files where error is generated/logged:
- Focus on error handling code
- Look for validation logic (or lack thereof)
- Trace data flow to error point

**3.3: Identify Root Cause**

Analyze code to determine:
- What triggers the error?
- Is validation missing?
- Is there incorrect logic?
- Are there edge cases not handled?

**3.4: Report Code Findings**

Add to bug analysis output:

```
**Code Review:**
- **Location:** [file:line]
- **Root Cause:** [Specific code issue]
- **Code Analysis:**
  ```[language]
  [Relevant code snippet]
  ```
- **Issue:** [Explanation of the problem]
- **Suggested Fix:** [Code suggestion or approach]
```

If error originates from external service (Meta API, etc.), note that code review shows proper error handling.

### Output Format

For each error, provide:

```
## Bug Analysis

### Error 1: [Error message]
- **Request ID:** [RQ_ID]
- **Verdict:** ✅ BUG / ❌ NOT A BUG
- **Reason:** [Detailed explanation of why this is/isn't a bug]
- **Impact:** High/Medium/Low
  - High: Data loss, system unavailability, security issue
  - Medium: Observability gaps, non-critical failures
  - Low: Cosmetic issues, logging problems

**Code Review:** (if bug detected)
- **Location:** [file:line]
- **Root Cause:** [What in the code causes this]
- **Code Analysis:** [Code snippet and explanation]
- **Suggested Fix:** [Recommendation]

### Error 2: [Error message]
- **Request ID:** [RQ_ID]
- **Verdict:** ✅ BUG / ❌ NOT A BUG
- **Reason:** [Detailed explanation]
- **Impact:** High/Medium/Low

**Code Review:** (if bug detected)
- **Location:** [file:line]
- **Root Cause:** [What in the code causes this]
- **Code Analysis:** [Code snippet and explanation]
- **Suggested Fix:** [Recommendation]
```

### Summary Section

After analyzing all errors, provide:

```
## Summary

**Total Errors Analyzed:** N
**Bugs Detected:** X
**Expected Behavior:** Y
**Code Review Performed:** Yes ([repository path])

### Bugs List (for ticket creation)
1. Bug 1 - [Request ID] - [Brief description] ([file:line])
2. Bug 2 - [Request ID] - [Brief description] ([file:line])
```

## Context-Specific Knowledge

### Senders API Error Patterns

**Common Expected Errors (NOT bugs):**
- Meta API "Request code error" (phone already registered)
- Meta API OAuthException 136024 (phone number issues)
- "Resource already exists" errors
- WABA validation failures

**Common Bugs:**
- PiedPiper payload malformation ("Unable to process JSON")
- Storehouse lookup failures (when data should exist)
- Missing error handling causing unclear failures
- JSON serialization issues in events

## Example Session

Input: 3 errors from E2E test
- Error 1: Meta API 400 "Request code error"
- Error 2: PiedPiper 400 "Unable to process JSON"
- Error 3: Meta API non-retryable error (same as Error 1)

Repository: ~/Projects/messaging-ott-management-api/

Output:
```
## Bug Analysis

### Error 1: Failed to request verification code with Meta API
- **Request ID:** RQ001
- **Verdict:** ❌ NOT A BUG
- **Reason:** Meta API rejected the request because the phone number is already registered on WhatsApp. This is expected behavior when attempting to register an already-claimed number.
- **Impact:** N/A (expected validation)

**Code Review:**
- **Location:** src/workflows/whatsapp/requestVerificationCode.ts:87
- **Analysis:** Code properly handles Meta API rejection and logs error
- **Conclusion:** Error handling is correct; this is expected behavior

### Error 2: Failed to publish debug event to piedpiper
- **Request ID:** RQ001
- **Verdict:** ✅ BUG
- **Reason:** PiedPiper ingest service rejected the payload with "Unable to process JSON" and details " is invalid". This indicates malformed JSON being generated by our debug event publisher, likely due to missing field validation or improper escaping.
- **Impact:** Medium (observability data loss, no customer impact)

**Code Review:**
- **Location:** src/events/debugEventPublisher.ts:142
- **Root Cause:** Missing validation for undefined fields in payload
- **Code Analysis:**
  ```typescript
  const payload = {
    event: errorContext.message,
    details: errorContext.details // <- Can be undefined
  };
  await piedPiper.publish(payload);
  ```
- **Issue:** `details` field can be undefined, creating invalid JSON
- **Suggested Fix:**
  ```typescript
  const payload = {
    event: errorContext.message || 'Unknown error',
    details: errorContext.details || ''
  };
  ```

### Error 3: [RequestCode] Non-retryable Meta API error
- **Request ID:** RQ001
- **Verdict:** ❌ NOT A BUG
- **Reason:** This is an info-level log about the same Meta API rejection from Error 1. It's documenting that the error is non-retryable, which is expected behavior for phone number validation failures.
- **Impact:** N/A (expected validation)

## Summary

**Total Errors Analyzed:** 3
**Bugs Detected:** 1
**Expected Behavior:** 2
**Code Review Performed:** Yes (~/Projects/messaging-ott-management-api/)

### Bugs List (for ticket creation)
1. Bug 1 - RQ001 - PiedPiper payload validation missing (src/events/debugEventPublisher.ts:142)
```
