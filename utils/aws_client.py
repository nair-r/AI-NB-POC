"""AWS SageMaker runtime and S3 client initialization."""

from __future__ import annotations

import os

import boto3

from utils.config import REGION


def try_init_client(access_key_id, secret_access_key):
    """Try to create SageMaker runtime and S3 clients with the given credentials.

    Returns:
        Tuple of (sm_client, s3_client, None) on success
        or (None, None, error_message) on failure.
    """
    if not access_key_id or not secret_access_key:
        return None, None, "Both Access Key ID and Secret Access Key are required."
    try:
        kwargs = dict(
            region_name=REGION,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
        sm_client = boto3.client("sagemaker-runtime", **kwargs)
        s3_client = boto3.client("s3", **kwargs)
        return sm_client, s3_client, None
    except Exception as e:
        return None, None, f"AWS client error: {e}"


def try_init_from_env():
    """Try to create clients from environment variables.

    Returns:
        Tuple of (sm_client, s3_client, None) on success,
        (None, None, error_message) on failure,
        or (None, None, None) if env vars are not set.
    """
    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    if not access_key or not secret_key:
        return None, None, None
    return try_init_client(access_key, secret_key)
