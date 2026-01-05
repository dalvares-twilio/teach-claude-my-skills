---
name: twilio-phone-number-manager
description: Search, purchase, and manage Twilio phone numbers. Always uses Prod API (api.twilio.com). Defaults to US Local SMS-enabled numbers. Maintains a registry of purchased numbers.
---

# Twilio Phone Number Manager

This skill manages Twilio phone number operations including searching, purchasing, and tracking phone numbers.

## When to Use

- "purchase a phone number"
- "buy a Twilio number"
- "provision a new number"
- "list my phone numbers"
- "search available numbers"

## Key Constraints

- **Phone number purchases ALWAYS use Twilio Prod API** (`api.twilio.com`)
- **Default search:** US Local, SMS-enabled
- Numbers purchased here can be used in Senders API tests on any environment (dev/stage/prod)

## Credential Management

### Prod Credentials Storage
Store in `/tmp/twilio_prod_credentials.json`:
```json
{
  "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "auth_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "description": "Prod account for phone number purchases"
}
```

### Credential Workflow
1. Check if `/tmp/twilio_prod_credentials.json` exists
2. If exists: Display masked credentials
   ```
   Found saved Prod credentials: AC...xxxx
   Use these credentials? (Y/n/override)
   ```
3. If not exists or user wants override: Prompt for credentials, save to file

### Credential Commands
```bash
# Check for existing credentials
cat /tmp/twilio_prod_credentials.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Account: {d[\"account_sid\"][:6]}...{d[\"account_sid\"][-4:]}')" || echo "No saved credentials"

# Save credentials (use python to create JSON properly)
python3 << 'EOF'
import json
creds = {
    "account_sid": "ACCOUNT_SID_HERE",
    "auth_token": "AUTH_TOKEN_HERE",
    "description": "Prod account for phone number purchases"
}
with open('/tmp/twilio_prod_credentials.json', 'w') as f:
    json.dump(creds, f, indent=2)
print("Credentials saved")
EOF
```

## Phone Number Operations

### 1. Search Available Numbers

**Defaults (unless user specifies otherwise):**
- Country: **US only**
- Type: **Local**
- Required capability: **SMS enabled**

**API Call:**
```bash
# Read credentials
CREDS=$(cat /tmp/twilio_prod_credentials.json)
ACCOUNT_SID=$(echo $CREDS | python3 -c "import sys,json; print(json.load(sys.stdin)['account_sid'])")
AUTH_TOKEN=$(echo $CREDS | python3 -c "import sys,json; print(json.load(sys.stdin)['auth_token'])")

# Search for US Local SMS-enabled numbers
curl -s "https://api.twilio.com/2010-04-01/Accounts/$ACCOUNT_SID/AvailablePhoneNumbers/US/Local.json?SmsEnabled=true" \
  -u "$ACCOUNT_SID:$AUTH_TOKEN" | python3 -m json.tool
```

**Optional Filters (add to URL):**
- Area code: `&AreaCode=415`
- Contains pattern: `&Contains=777`
- MMS enabled: `&MmsEnabled=true`
- Voice enabled: `&VoiceEnabled=true`

**Display Format:**
```
Available Phone Numbers (US Local, SMS-enabled):

| #  | Phone Number     | Location      | Capabilities        |
|----|------------------|---------------|---------------------|
| 1  | (762) 226-8498   | Dalton, GA    | SMS, MMS, Voice, Fax|
| 2  | (920) 614-6192   | Rio, WI       | SMS, MMS, Voice, Fax|
| 3  | (925) 320-6534   | Moraga, CA    | SMS, MMS, Voice, Fax|

Enter number to purchase (e.g., +17622268498) or 'cancel':
```

### 2. Purchase Number

```bash
# Purchase a specific number
curl -s -X POST "https://api.twilio.com/2010-04-01/Accounts/$ACCOUNT_SID/IncomingPhoneNumbers.json" \
  -u "$ACCOUNT_SID:$AUTH_TOKEN" \
  -d "PhoneNumber=+1XXXXXXXXXX" | python3 -m json.tool
```

**Workflow:**
1. Verify number is SMS-capable (from search results)
2. Execute purchase API call
3. Extract SID and details from response
4. Add to phone number registry
5. Display confirmation

**Success Output:**
```
✓ Phone Number Purchased Successfully!

Phone Number: +17622268498
SID: PNd85bd337f0b42195924a4d39f811e5e5
Friendly Name: (762) 226-8498
Location: Dalton, GA
Capabilities: SMS, MMS, Voice, Fax

Added to registry. Ready for use in Senders API tests.
```

### 3. List Purchased Numbers

Read from registry and display:
```bash
cat /Users/dalvares/.claude/skills/twilio-phone-number-manager/phone-numbers.json | python3 -m json.tool
```

**Display Format:**
```
Purchased Phone Numbers:

| #  | Phone Number     | Location      | Purchased    | SID         |
|----|------------------|---------------|--------------|-------------|
| 1  | +17622268498     | Dalton, GA    | 2026-01-05   | PN...e5e5   |
| 2  | +19253206534     | Moraga, CA    | 2026-01-05   | PN...1234   |

Select a number to use, or 'new' to purchase a new one:
```

## Phone Number Registry

**Location:** `/Users/dalvares/.claude/skills/twilio-phone-number-manager/phone-numbers.json`

**Schema:**
```json
{
  "purchased_numbers": [
    {
      "phone_number": "+17622268498",
      "sid": "PNd85bd337f0b42195924a4d39f811e5e5",
      "friendly_name": "(762) 226-8498",
      "location": "Dalton, GA",
      "capabilities": ["SMS", "MMS", "Voice", "Fax"],
      "purchased_at": "2026-01-05T01:02:38Z"
    }
  ]
}
```

**Adding to Registry (Python):**
```python
import json
from datetime import datetime

# Load existing registry
registry_path = '/Users/dalvares/.claude/skills/twilio-phone-number-manager/phone-numbers.json'
try:
    with open(registry_path, 'r') as f:
        registry = json.load(f)
except FileNotFoundError:
    registry = {"purchased_numbers": []}

# Add new number (from purchase response)
new_number = {
    "phone_number": "+1XXXXXXXXXX",
    "sid": "PNXXXXXXXXX",
    "friendly_name": "(XXX) XXX-XXXX",
    "location": "City, ST",
    "capabilities": ["SMS", "MMS", "Voice", "Fax"],
    "purchased_at": datetime.utcnow().isoformat() + "Z"
}
registry["purchased_numbers"].append(new_number)

# Save registry
with open(registry_path, 'w') as f:
    json.dump(registry, f, indent=2)
```

## Integration with Senders E2E Testing

This skill is invoked by `senders-e2e-testing` when:
1. User requests a new phone number for testing
2. User wants to select from existing purchased numbers

**Return value to orchestrator:**
- Selected phone number (e.g., `+17622268498`)
- Ready for use in `sender_id` format: `whatsapp:+17622268498`

## Example Session

```
User: "I need to purchase a phone number"

Claude: "Checking for saved Prod credentials...
Found: AC...a613
Use these credentials? (Y/n/override)"

User: "Y"

Claude: "Searching for available US Local SMS-enabled numbers...

Available Phone Numbers:
| #  | Phone Number     | Location      | Capabilities        |
|----|------------------|---------------|---------------------|
| 1  | (762) 226-8498   | Dalton, GA    | SMS, MMS, Voice, Fax|
| 2  | (920) 614-6192   | Rio, WI       | SMS, MMS, Voice, Fax|
| 3  | (925) 320-6534   | Moraga, CA    | SMS, MMS, Voice, Fax|

Enter number to purchase (e.g., +17622268498):"

User: "+17622268498"

Claude: "Purchasing +17622268498...

✓ Phone Number Purchased Successfully!
Phone Number: +17622268498
SID: PNd85bd337f0b42195924a4d39f811e5e5
Capabilities: SMS, MMS, Voice, Fax

Added to registry."
```

## Related Skills

- `senders-e2e-testing` - Orchestrates this skill for E2E testing workflows
