"""Endpoint and credential configuration for the Medical AI POC."""

# Hardcoded for this POC. A configuration UI is coming soon.
ENDPOINT_NAME = "medgemma-endpoint"
REGION = "us-east-1"
CONTENT_TYPE = "application/json"

# S3 bucket for volume uploads and async inference I/O
VOLUME_S3_BUCKET = "ai-poc-sagemaker-endpoint-706262411476"
VOLUME_S3_PREFIX = "volumes/"
ASYNC_INPUT_PREFIX = "async-input/"
ASYNC_INFERENCE = True  # Endpoint deployed with --async-inference

# AWS credentials are read from environment variables.
# Set these before launching Voilà:
#   export AWS_ACCESS_KEY_ID=...
#   export AWS_SECRET_ACCESS_KEY=...
#   export AWS_DEFAULT_REGION=us-east-1
