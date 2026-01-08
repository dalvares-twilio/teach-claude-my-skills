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
- **CRITICAL: ALWAYS use PROD credentials** - regardless of which environment (dev/stage/prod) you're testing the Senders API on
- **Default search:** US Local, SMS-enabled
- Numbers purchased here can be used in Senders API tests on any environment (dev/stage/prod)

## Prod Credentials (MANDATORY)

**Credentials file:** `/tmp/twilio_prod_credentials.json`

**Known Prod Account for Phone Purchases:**
```
Account SID: AC[REDACTED - Ask user for prod account SID]
```

**IMPORTANT RULE:**
1. Before ANY phone number operation, check if `/tmp/twilio_prod_credentials.json` exists
2. If it exists, verify it contains the correct prod account (ask user for Account SID)
3. If missing or has wrong account, ASK the user for prod credentials before proceeding
4. NEVER use dev/stage credentials for phone purchases - this is a billing/provisioning operation that only works on prod

## Python Script (Recommended)

**ALWAYS use the Python script** instead of raw curl commands. It handles credentials, error handling, and registry management reliably.

**Script location:** `phone_manager.py` (same directory as this skill)

### Commands

```bash
# Set credentials (once per session, or if /tmp credentials expired)
python3 $SKILL_DIR/phone_manager.py set-credentials ACCOUNT_SID AUTH_TOKEN

# Search for available numbers (default: US Local, SMS-enabled)
python3 $SKILL_DIR/phone_manager.py search
python3 $SKILL_DIR/phone_manager.py search --area-code=415
python3 $SKILL_DIR/phone_manager.py search --limit=10

# Purchase a specific number
python3 $SKILL_DIR/phone_manager.py purchase +17656001985

# List all purchased numbers from registry
python3 $SKILL_DIR/phone_manager.py list
```

**Where `$SKILL_DIR`** = directory containing this skill (e.g., `~/.claude/skills/twilio-phone-number-manager`)

### Workflow

1. **Check credentials:** Script reads from `/tmp/twilio_prod_credentials.json`
2. **If missing:** Run `set-credentials` command first
3. **Search:** Find available numbers
4. **Purchase:** Buy selected number (auto-added to registry)
5. **Verify:** Use `list` to confirm purchase

### Output Examples

**Search:**
```
Available Phone Numbers (US Local, SMS-enabled):

| #  | Phone Number     | Location           | Capabilities         |
|----|------------------|--------------------|----------------------|
| 1  | +17656001985     | Amboy, IN          | SMS, MMS, Voice, Fax |
| 2  | +17653905169     | Kingman, IN        | SMS, MMS, Voice, Fax |

First available: +17656001985
```

**Purchase:**
```
==================================================
Phone Number Purchased Successfully!
==================================================
Phone Number:   +17656001985
SID:            PNd85bd337f0b42195924a4d39f811e5e5
Friendly Name:  (765) 600-1985
Capabilities:   SMS, MMS, Voice, Fax
==================================================

Added to registry: /path/to/phone-numbers.json
```

## Files

| File | Location | Purpose |
|------|----------|---------|
| `phone_manager.py` | Skill directory | Main script (portable) |
| `phone-numbers.json` | Skill directory | Registry of purchased numbers |
| `twilio_prod_credentials.json` | `/tmp/` | API credentials (ephemeral) |

## Phone Number Registry

**Location:** Same directory as `phone_manager.py` → `phone-numbers.json`

**Schema:**
```json
{
  "purchased_numbers": [
    {
      "phone_number": "+17622268498",
      "sid": "PNd85bd337f0b42195924a4d39f811e5e5",
      "friendly_name": "(762) 226-8498",
      "capabilities": ["SMS", "MMS", "Voice", "Fax"],
      "purchased_at": "2026-01-05T01:02:38Z"
    }
  ]
}
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
