---
name: bug-analyzer
description: Universal bug analyzer that classifies ANY error as BUG, EXPECTED BEHAVIOR, or IMPROVEMENT OPPORTUNITY using service-agnostic principles. Optional code review for root cause analysis.
---

# Bug Analyzer (Universal)

## Overview

Service-agnostic error analyzer that classifies errors using universal software engineering principles. Works with errors from ANY service without requiring domain-specific knowledge.

## When to Use

- After discovering errors (from bigquery-error-scanner or other sources)
- "Analyze this error for bugs"
- "Classify these errors"
- "Is this error a bug or expected behavior?"
- Used by auto-bug-detector for automated classification

## Project Context Support

This analyzer accepts an optional `project_context` parameter from the auto-bug-detector.
When provided, project-specific error patterns are merged with universal patterns.

**How it works:**
1. Auto-bug-detector loads project from registry
2. Passes `project_context` with custom error patterns
3. Bug-analyzer merges patterns (project patterns take precedence)
4. Classification uses combined pattern set

**Example project_context:**
```yaml
project_context:
  project_id: "ottm"
  project_name: "OTT Management API"
  error_patterns:
    expected:
      - pattern: "Meta API.*phone already registered"
        reason: "External validation - phone registered on WhatsApp"
    bugs:
      - pattern: "PiedPiper.*Unable to process JSON"
        reason: "Malformed payload sent to PiedPiper"
```

**Pattern Merge Rules:**
- Project patterns checked FIRST (higher priority)
- Universal patterns checked if no project match
- If both match, project pattern takes precedence

## Classification Categories

### 🐛 BUG
Genuine software defects that should be fixed.

### ✅ EXPECTED BEHAVIOR
Legitimate validation or external failures (not bugs).

### 💡 IMPROVEMENT OPPORTUNITY
Not broken, but could be better (performance, observability, UX).

## Pre-Approved Actions

- Reading error details from any source
- Using Grep to search repository (if provided)
- Reading source files for code review
- Displaying analysis results with code snippets
- NO ticket creation (use jira-ticket-creator separately)

## Instructions

### Step 1: Parse Error Input

Accept errors in various formats:
- **Structured**: JSON with error message, level, timestamp, context
- **Unstructured**: Plain text error messages
- **BigQuery results**: Output from bigquery-error-scanner
- **Log lines**: Raw log entries

**Extract key information**:
- Error message
- Severity/level (if available)
- Timestamp (if available)
- Context (request ID, service name, etc.)
- Stack trace (if available)

### Step 2: Ask for Repository (Optional)

If user wants code review, ask for repository path:

**Use AskUserQuestion**:
```
Question: "Perform code review to find root cause?"
Options:
1. Yes - provide repository path (e.g., ~/Projects/my-service)
2. No - classify based on error message only
```

If yes, store repository path for later code search.

### Step 3: Classify Error

Apply universal classification logic using pattern matching.

#### BUG Indicators

Check error message for these patterns:

**System Failures**:
- HTTP 500, 502, 503, 504 errors
- "Internal server error", "Service unavailable"
- "Crash", "Exception", "Fatal", "Panic"
- "NullPointerException", "undefined is not a function"
- "Segmentation fault", "Core dumped"

**Data Integrity Issues**:
- "Malformed JSON", "Invalid JSON", "Unable to parse"
- "Missing required field", "Field cannot be null"
- "Data corruption", "Inconsistent state"
- "Foreign key constraint", "Integrity violation"

**Logic Errors**:
- "Divide by zero", "Arithmetic overflow"
- "Index out of bounds", "Array out of range"
- "Deadlock detected", "Race condition"
- "Infinite loop", "Stack overflow"

**Resource Issues**:
- "Out of memory", "Memory exhausted"
- "Connection pool exhausted", "Too many connections"
- "Disk full", "No space left on device"
- "File handle limit exceeded"

**Unhandled Edge Cases**:
- "Unexpected null", "Cannot read property of undefined"
- "Illegal state", "Invalid state transition"
- "Should never happen", "Unreachable code reached"

#### EXPECTED BEHAVIOR Indicators

Check for these patterns:

**External API Failures**:
- "Meta API rejected", "Google API error"
- "Upstream service unavailable"
- "Third-party timeout", "External dependency failed"
- Contains API provider name + error code

**User Input Validation**:
- HTTP 400, 422 errors
- "Invalid input", "Validation failed"
- "Missing required parameter", "Invalid format"
- "Email address invalid", "Phone number invalid"

**Access Control**:
- HTTP 401, 403 errors
- "Unauthorized", "Access denied", "Permission denied"
- "Authentication required", "Invalid credentials"
- "Token expired", "Insufficient permissions"

**Resource Not Found** (legitimate):
- HTTP 404 errors with valid user request
- "Resource not found", "User not found"
- "Record does not exist"

**Rate Limiting**:
- HTTP 429 errors
- "Rate limit exceeded", "Too many requests"
- "Quota exceeded", "Throttled"

**Business Rules**:
- HTTP 409 errors
- "Already exists", "Duplicate entry"
- "Conflict detected", "Resource locked"

#### IMPROVEMENT OPPORTUNITY Indicators

Check for these patterns:

**Performance Issues**:
- "Query took X seconds" (where X > threshold)
- "Slow query", "High latency", "Timeout"
- "Response time exceeded"
- Contains duration measurements

**Missing Observability**:
- Generic error messages without context
- "An error occurred" (no details)
- Errors without request IDs or correlation
- Missing stack traces where expected

**Retry-able Errors**:
- Transient failures that could be handled
- "Connection reset", "Temporary failure"
- "Service temporarily unavailable"
- Could benefit from retry logic

**Poor Error Messages**:
- Unclear to developers or users
- Contains internal implementation details
- No actionable guidance
- Technical jargon without explanation

**Security/Deprecation**:
- "Deprecated", "Legacy code path"
- "Using insecure", "Vulnerable dependency"
- Security warnings

### Step 3.5: Apply Classification Precedence

When multiple patterns match, apply this precedence to avoid misclassification:

**Precedence Order**:

1. **Check External Service First**
   - If error mentions Meta, Google, AWS, Twilio API, PiedPiper response, etc.
   - External API errors are almost always EXPECTED (not our bug)
   - Exception: If we're sending malformed data TO the external service

2. **Check HTTP Status Origin**
   - 4xx from external API → EXPECTED (their validation)
   - 5xx from external API → EXPECTED (their outage, not our bug)
   - 5xx from OUR service → BUG (we crashed)
   - 4xx from OUR service → Usually EXPECTED (validation working)

3. **Check Error Level Context**
   - `info` level errors → Usually EXPECTED (informational logging)
   - `warning` level → Could be either (investigate further)
   - `error` level → More likely BUG (but check source)

4. **Check for Known Non-Bug Patterns**
   - "already exists", "duplicate", "conflict" → EXPECTED (idempotency)
   - "rate limit", "throttle", "429" → EXPECTED (external limits)
   - "not found" with user-provided ID → EXPECTED (bad input)

5. **Default Rule**
   - If patterns conflict or unclear → Classify as IMPROVEMENT
   - Add note: "Recommend human review - ambiguous classification"

**Example Precedence Application**:
```
Error: "400 response from Meta Graph API: phone already registered"

Patterns matched:
- BUG indicator: "400 response" (HTTP error)
- EXPECTED indicator: "Meta Graph API" (external service)
- EXPECTED indicator: "already registered" (duplicate resource)

Apply precedence:
1. External service (Meta) mentioned → lean EXPECTED
2. 400 is from external API → EXPECTED
3. "already registered" is known non-bug → EXPECTED

Final: EXPECTED BEHAVIOR (external validation)
```

### Step 4: Determine Impact Level

**HIGH Impact**:
- Service unavailability (all users affected)
- Data loss or corruption
- Security vulnerability
- Revenue impact (payments, orders failing)
- Affects >10% of requests

**MEDIUM Impact**:
- Observability gaps (harder to debug)
- Performance degradation (slow but working)
- Non-critical features broken
- Affects 1-10% of requests
- Workaround exists

**LOW Impact**:
- Cosmetic issues (logging, formatting)
- Development/debug tools
- Affects <1% of requests
- No user-facing impact

### Step 4.5: Calculate Confidence Score

Assign a confidence score to each classification based on evidence strength.

**Confidence Factors**:

| Factor | Weight | When Applied |
|--------|--------|--------------|
| Exact pattern match | +0.30 | Known pattern from indicators list matched |
| HTTP status clear | +0.20 | 500=BUG or 400-from-external=EXPECTED clearly indicated |
| External API mentioned | -0.25 | Meta/Google/AWS/etc. in error (leans toward EXPECTED) |
| Error level = "error" | +0.15 | Log level is error (not info/warning) |
| Code review confirms | +0.30 | Found root cause in code that confirms classification |
| Multiple patterns match | -0.20 | Ambiguous - patterns conflict with each other |
| Stack trace present | +0.10 | More context available for analysis |
| Request context available | +0.10 | Have request ID, endpoint, timing info |

**Confidence Calculation**:
```python
confidence = 0.5  # Base confidence

# Add/subtract based on factors present
if exact_pattern_match: confidence += 0.30
if http_status_clear: confidence += 0.20
if external_api_mentioned: confidence -= 0.25
if error_level_is_error: confidence += 0.15
if code_review_confirms: confidence += 0.30
if multiple_patterns_conflict: confidence -= 0.20
if stack_trace_present: confidence += 0.10
if request_context_available: confidence += 0.10

# Clamp to [0, 1]
confidence = max(0.0, min(1.0, confidence))
```

**Confidence Levels**:
- **High** (≥0.70): Strong evidence, proceed with classification
- **Medium** (0.40-0.69): Reasonable confidence, note uncertainty in report
- **Low** (<0.40): Unclear classification, recommend human review

**Report Format with Confidence**:
```
**Classification**: BUG 🐛 (Confidence: High - 0.85)
**Classification**: EXPECTED ✅ (Confidence: Medium - 0.55)
**Classification**: IMPROVEMENT 💡 (Confidence: Low - 0.35) ⚠️ Recommend human review
```

### Step 5: Code Review (If Repository Provided)

If user provided repository path, search for error origin:

**1. Search for exact error message**:
```bash
grep -r "{error_message}" {repository_path} --include="*.go" --include="*.js" --include="*.py" --include="*.java" --include="*.ts" --include="*.rb"
```

**2. Search for error logging**:
```bash
grep -r "log.Error\|logger.error\|console.error\|fmt.Errorf" {repository_path} -A 2 -B 2
```

**3. Read relevant files**:
- Use Read tool to examine files where error originates
- Focus on error handling code
- Identify root cause

**4. Provide code analysis**:
- **Location**: file:line
- **Root Cause**: What triggers the error
- **Code Snippet**: Relevant code section
- **Issue**: Why this is problematic
- **Suggested Fix**: Specific recommendation

### Step 6: Generate Analysis Report

**Output format**:

```
## Error Analysis

### Error: "{error_message}"

**🔍 Classification**: {BUG 🐛 | EXPECTED ✅ | IMPROVEMENT 💡} (Confidence: {High|Medium|Low} - {0.XX})

**Reasoning**:
{Detailed explanation of why this classification}

**Confidence Factors**:
- {factor 1}: {+/-weight}
- {factor 2}: {+/-weight}
- Final score: {0.XX}

**Impact**: {High | Medium | Low}
{Impact description}

**Evidence**:
- Error Level: {level}
- Pattern Matched: {which indicator pattern}
- Timestamp: {if available}
- Context: {any available context}

{IF CODE REVIEW PERFORMED}
**Code Review**:
- **Location**: {file:line}
- **Root Cause**: {what in code causes this}
- **Code Analysis**:
  ```{language}
  {relevant code snippet}
  ```
- **Issue**: {explanation of problem}
- **Suggested Fix**: {specific recommendation}
{END IF}

**Recommended Action**:
{What should be done about this error}
```

### Step 7: Provide Summary

After analyzing all errors:

```
## Analysis Summary

**Total Errors Analyzed**: {N}
**Bugs Detected**: {bug_count} 🐛
**Expected Behavior**: {expected_count} ✅
**Improvement Opportunities**: {improvement_count} 💡

{IF CODE REVIEW PERFORMED}
**Code Review Performed**: Yes ({repository_path})
{END IF}

### Bugs Requiring Action
{List all bugs with impact level}

### Improvement Opportunities
{List all improvements with priority}

### Expected Errors (No Action Needed)
{List expected errors for reference}
```

## Classification Examples

### Example 1: BUG

**Error**: "Connection pool exhausted: maximum 5 connections reached"

**Classification**: 🐛 BUG

**Reasoning**: This is a system failure indicating incorrect resource configuration. A connection pool size of 5 is too small for production workloads, causing service degradation under normal load.

**Impact**: High (service unavailability under load)

**Action**: Increase connection pool size to appropriate value (e.g., 50-100)

### Example 2: EXPECTED BEHAVIOR

**Error**: "Meta API rejected request: Phone number already registered (code: 136024)"

**Classification**: ✅ EXPECTED BEHAVIOR

**Reasoning**: This is an external API validation error. Meta API is correctly rejecting the request because the phone number is already claimed by another WhatsApp account. This is legitimate business logic enforcement by the provider.

**Impact**: N/A (expected validation)

**Action**: None - this is proper error handling of invalid user input

### Example 3: IMPROVEMENT OPPORTUNITY

**Error**: "Query execution took 5.2 seconds"

**Classification**: 💡 IMPROVEMENT OPPORTUNITY

**Reasoning**: The system is functioning but performance is poor. Query latency of 5+ seconds degrades user experience significantly. This indicates missing database optimization.

**Impact**: Medium (poor UX, but functional)

**Action**: Add database index on frequently queried columns, consider query optimization or caching

## Service-Specific Patterns

### Senders API / OTTM Patterns

> **Note:** These patterns are stored in `~/.claude/project-registry.yaml` under `projects.ottm.error_patterns`.
> When auto-bug-detector runs with project=ottm, these patterns are automatically loaded via `project_context`.

These patterns are specific to the Twilio Senders API (messaging-ott-management-api).

**Expected Errors (NOT bugs)**:
- Meta API "Request code error" (phone already registered on WhatsApp)
- Meta API OAuthException code 136024 (phone number validation)
- Meta API "This phone number is already registered"
- "Resource already exists" (duplicate sender registration)
- WABA validation failures from Meta
- "Sender not found" when querying non-existent sender
- Rate limiting from Meta Graph API

**Bug Indicators (likely bugs)**:
- PiedPiper payload malformation: "Unable to process JSON", "is invalid"
- Storehouse lookup failures when data SHOULD exist
- "Failed to publish debug event" with malformed payload
- Internal service errors (500) from OTTM endpoints
- Temporal workflow failures due to code errors
- Missing AccountSID or invalid SID format in internal calls
- JSON serialization errors in event publishing

**Context Clues**:
- `endpoint: create` + Meta error → Usually EXPECTED (Meta validation)
- `endpoint: create` + PiedPiper error → Usually BUG (our payload issue)
- `level: info` + "Non-retryable" → EXPECTED (informational logging)
- `level: error` + internal service name → Investigate as potential BUG

**Example Classifications**:

| Error | Classification | Reason |
|-------|---------------|--------|
| "400 from Meta: phone already registered" | EXPECTED | External validation |
| "400 from PiedPiper: Unable to process JSON" | BUG | We sent bad data |
| "Storehouse lookup failed for existing sender" | BUG | Data should exist |
| "Meta API rate limited" | EXPECTED | External rate limit |
| "Failed to serialize event: undefined field" | BUG | Code error |

## Advanced Features

### Pattern Learning

Track classification patterns over time:
```json
{
  "error_pattern": "Connection pool exhausted",
  "classification": "BUG",
  "confidence": 0.95,
  "seen_count": 10,
  "always_classified_as": "BUG"
}
```

### Confidence Scoring

Assign confidence to classifications:
- **High confidence**: Clear patterns match
- **Medium confidence**: Some indicators but ambiguous
- **Low confidence**: Unclear, needs human review

Report confidence with verdict:
```
**Classification**: BUG 🐛 (Confidence: High)
```

### Cross-Service Learning

Build knowledge base of error patterns across services:
- "PiedPiper JSON validation" → always BUG
- "Meta API rate limit" → always EXPECTED
- "Slow query" → always IMPROVEMENT

## Error Handling

**If error message is unclear**:
- Request more context from user
- Classify with LOW confidence
- Suggest gathering more information

**If multiple classifications possible**:
- Report primary classification
- Note alternative interpretations
- Recommend human review

**If code search finds nothing**:
- Note in report: "Error origin not found in repository"
- Suggest error may be from external dependency
- Provide classification based on message alone

## Integration with Other Skills

**Used by**:
- `auto-bug-detector` - for automated pipeline
- `senders-e2e-testing` - for E2E test error analysis
- Generated monitoring skills - for error classification

**Uses**:
- Grep tool - for code search
- Read tool - for file analysis

**Outputs to**:
- `sender-management-jira-ticket-creator` - bugs become tickets
- `auto-bug-detector` - summary report

## Privacy & Security

✅ Analyzes error messages only (no sensitive data exposed)
✅ Code review respects repository permissions
✅ No external API calls (runs locally)
✅ No data transmission (analysis done in-process)

## Related Skills

- **bigquery-error-scanner**: Discovers errors for this analyzer
- **auto-bug-detector**: Orchestrates scanner + analyzer pipeline
- **sender-management-jira-ticket-creator**: Creates tickets for detected bugs
- **senders-bug-analyzer**: Senders API-specific version (being replaced by this universal version)
