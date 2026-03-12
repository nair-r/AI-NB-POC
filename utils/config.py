"""Endpoint and credential configuration for the MedGemma POC."""

# Hardcoded for this POC. A configuration UI is coming soon.
ENDPOINT_NAME = "medgemma-endpoint"
REGION = "us-east-1"
CONTENT_TYPE = "application/json"

# AWS credentials are read from environment variables.
# Set these before launching Voilà:
#   export AWS_ACCESS_KEY_ID=...
#   export AWS_SECRET_ACCESS_KEY=...
#   export AWS_DEFAULT_REGION=us-east-1
