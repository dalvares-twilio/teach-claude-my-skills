#!/bin/bash

# Read the JSON input from stdin
json_input=$(cat)

# Extract the command from the JSON
command=$(echo "$json_input" | jq -r '.tool_input.command')

# Log the command for debugging
echo "Validating command: $command" >> /tmp/claude-hook-log.txt

# Check for potentially dangerous commands
if [[ $command == *"rm -rf /"* || $command == *"rm -rf /*"* || $command == *"rm -rf ~"* || $command == *"rm -rf"* || $command == *"rm"* ]]; then
  echo '{"block": true, "reason": "Command using rm is not allowed as it could delete files"}'
  exit 2
fi

# Block attempts to modify git configuration
if [[ $command == *"git config"* && ($command == *"user.email"* || $command == *"user.name"*) ]]; then
  echo '{"block": true, "reason": "Modifying git configuration is not allowed"}'
  exit 2
fi

# Allow the command to proceed
exit 0