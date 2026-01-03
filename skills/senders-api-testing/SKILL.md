---
name: senders-api-testing
description: Use when testing Senders API endpoints, generating curl commands for WhatsApp or RCS senders, creating/updating/deleting sender profiles, or debugging Senders API v2 in dev/stage/prod environments. Includes authentication patterns, payload examples, and credential security best practices.
---

# Senders API Curl Testing

This skill helps generate and execute curl requests to test the Senders API (v2).

## Usage

User will request to test the Senders API with specific parameters. Generate the appropriate curl command based on the environment and payload.

## Instructions

1. **Parse the user's request** to determine:
   - Environment: `dev`, `stage`, or `prod`
   - Operation: `CREATE`, `GET`, `UPDATE`, `DELETE`
   - Payload details (sender_id, waba_id, profile info, etc.)

2. **Determine the base URL** based on environment:
   - Dev: `https://messaging.dev.twilio.com/v2/Channels/Senders`
   - Stage: `https://messaging.stage.twilio.com/v2/Channels/Senders`
   - Prod: `https://messaging.twilio.com/v2/Channels/Senders`

3. **Generate the curl command** based on operation type

4. **If executing the command**:
   - Prompt user for `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` using AskUserQuestion
   - **Print the request** being made (method, URL, headers, payload)
   - Execute the curl command with the provided credentials
   - **Print important response headers** (especially `X-Twilio-Request-Id`)
   - **Print the response body** formatted with jq

5. **Output format** (always show these):
   ```
   === REQUEST ===
   POST https://messaging.dev.twilio.com/v2/Channels/Senders
   Headers: Content-Type: application/json
   Payload: {... formatted JSON ...}

   === RESPONSE ===
   Status: 200 OK
   X-Twilio-Request-Id: RQ123abc...
   Content-Type: application/json

   Body:
   {... formatted JSON response ...}
   ```

## Safe Curl Execution Pattern

**IMPORTANT**: Always use this pattern to avoid bash parsing errors:

1. **Use single quotes** for URLs and credentials (prevents special character issues)
2. **Write payload to file first** for POST/PATCH requests
3. **Use `-d @/tmp/payload.json`** to read payload from file

```bash
# 1. Write payload to file (for POST/PATCH)
cat > /tmp/payload.json << 'EOF'
{
  "sender_id": "whatsapp:+18565589907",
  "configuration": { "waba_id": "101347185975530" },
  "profile": { "name": "Test Sender" }
}
EOF

# 2. Execute curl with single quotes
curl -s -D /tmp/headers.txt -X POST 'https://messaging.stage.twilio.com/v2/Channels/Senders' \
  -u 'ACCOUNT_SID:AUTH_TOKEN' \
  -H 'Content-Type: application/json' \
  -d @/tmp/payload.json -o /tmp/response.json

# 3. Display results
echo "=== RESPONSE HEADERS ==="
grep -iE "^(HTTP|twilio-request-id|content-type|x-twilio)" /tmp/headers.txt
echo ""
echo "=== RESPONSE BODY ==="
cat /tmp/response.json | jq .
```

## API Operations

### CREATE Sender (POST)

```bash
# Step 1: Write payload to file
cat > /tmp/payload.json << 'EOF'
{
  "sender_id": "whatsapp:+18166435132",
  "configuration": {
    "waba_id": "1394386238892041"
  },
  "profile": {
    "name": "Twilio Test1",
    "description": "Senders API UAT",
    "logo_url": "https://www.logomaker.com/wp-content/uploads/2018/10/twitter.png",
    "emails": [{ "email": "twilio@twilio.com" }],
    "websites": [{ "website": "https://twilio.com" }]
  }
}
EOF

# Step 2: Execute curl with single quotes
curl -s -D /tmp/headers.txt -X POST 'https://messaging.dev.twilio.com/v2/Channels/Senders' \
  -u 'ACCOUNT_SID:AUTH_TOKEN' \
  -H 'Content-Type: application/json' \
  -d @/tmp/payload.json -o /tmp/response.json

# Step 3: Display results
echo "=== RESPONSE HEADERS ==="
grep -iE "^(HTTP|twilio-request-id|content-type|x-twilio)" /tmp/headers.txt
echo ""
echo "=== RESPONSE BODY ==="
cat /tmp/response.json | jq .
```

### GET Sender (GET)

```bash
curl -s -D /tmp/headers.txt -X GET 'https://messaging.dev.twilio.com/v2/Channels/Senders/{sender_sid}' \
  -u 'ACCOUNT_SID:AUTH_TOKEN' -o /tmp/response.json

echo "=== RESPONSE HEADERS ==="
grep -iE "^(HTTP|twilio-request-id|content-type|x-twilio)" /tmp/headers.txt
echo ""
echo "=== RESPONSE BODY ==="
cat /tmp/response.json | jq .
```

### GET All Senders (GET with pagination)

```bash
curl -s -D /tmp/headers.txt -X GET 'https://messaging.dev.twilio.com/v2/Channels/Senders?Channel=whatsapp&PageSize=20' \
  -u 'ACCOUNT_SID:AUTH_TOKEN' -o /tmp/response.json

echo "=== RESPONSE HEADERS ==="
grep -iE "^(HTTP|twilio-request-id|content-type|x-twilio)" /tmp/headers.txt
echo ""
echo "=== RESPONSE BODY ==="
cat /tmp/response.json | jq .
```

### UPDATE Sender (PATCH)

```bash
# Step 1: Write payload to file
cat > /tmp/payload.json << 'EOF'
{
  "profile": {
    "name": "Updated Name",
    "description": "Updated Description"
  }
}
EOF

# Step 2: Execute curl with single quotes
curl -s -D /tmp/headers.txt -X PATCH 'https://messaging.dev.twilio.com/v2/Channels/Senders/{sender_sid}' \
  -u 'ACCOUNT_SID:AUTH_TOKEN' \
  -H 'Content-Type: application/json' \
  -d @/tmp/payload.json -o /tmp/response.json

# Step 3: Display results
echo "=== RESPONSE HEADERS ==="
grep -iE "^(HTTP|twilio-request-id|content-type|x-twilio)" /tmp/headers.txt
echo ""
echo "=== RESPONSE BODY ==="
cat /tmp/response.json | jq .
```

### DELETE Sender (DELETE)

```bash
curl -s -D /tmp/headers.txt -X DELETE 'https://messaging.dev.twilio.com/v2/Channels/Senders/{sender_sid}' \
  -u 'ACCOUNT_SID:AUTH_TOKEN' -o /tmp/response.json

echo "=== RESPONSE HEADERS ==="
grep -iE "^(HTTP|twilio-request-id|content-type|x-twilio)" /tmp/headers.txt
echo ""
echo "=== RESPONSE BODY ==="
cat /tmp/response.json | jq .
```

## Important Notes

- **Credentials**: When executing commands, always prompt for `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` using AskUserQuestion
- **Environment**: Default to `dev` if not specified
- **Response formatting**: Use `| jq .` to format JSON responses for readability
- **Headers capture**: Use `-D /tmp/headers.txt` to dump response headers to a file
- **Important headers to display**:
  - `X-Twilio-Request-Id` - Critical for debugging with BigQuery logs
  - `HTTP/1.1` or `HTTP/2` status line - Shows response status code
  - `Content-Type` - Confirms JSON response
- **Content-Type**: Always include `-H "Content-Type: application/json"` for POST/PATCH requests
- **Always print request details** before executing (method, URL, payload summary)

## Example Interactions

User: "Create a WhatsApp sender in dev"
→ Generate CREATE curl command with dev URL and sample payload
→ If user wants to execute: Ask for credentials, then run the command

User: "Get sender SN123 in stage"
→ Generate GET curl command with stage URL and sender SID

User: "List all senders in prod"
→ Generate GET ALL curl command with prod URL

User: "Update sender profile for SN456"
→ Generate PATCH curl command with update payload

## Sample Payloads

### WhatsApp Sender
```json
{
  "sender_id": "whatsapp:+18166435132",
  "configuration": {
    "waba_id": "1394386238892041"
  },
  "profile": {
    "name": "Twilio Test1",
    "description": "Senders API UAT",
    "logo_url": "https://www.logomaker.com/wp-content/uploads/2018/10/twitter.png",
    "emails": [{ "email": "twilio@twilio.com" }],
    "websites": [{ "website": "https://twilio.com" }]
  }
}
```

### RCS Sender
```json
{
  "sender_id": "rcs:+18166435132",
  "configuration": {
    "brand_id": "brand-123",
    "agent_id": "agent-456"
  },
  "profile": {
    "name": "RCS Business",
    "description": "RCS messaging service",
    "logo_url": "https://example.com/logo.png"
  }
}
```

## Credential Security

**IMPORTANT**:
- Never hardcode credentials in commands
- Always prompt for `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` using AskUserQuestion
- Be careful when sharing command output that might contain sensitive data
- Use single quotes with literal credentials: `-u 'ACCOUNT_SID:AUTH_TOKEN'`
- Replace `ACCOUNT_SID` and `AUTH_TOKEN` with actual values when executing
