"""AWS SageMaker runtime client initialization."""

from __future__ import annotations

import os

import boto3

from utils.config import ENDPOINT_NAME, REGION


def _success_html():
    return (
        "<div style='color:#2e7d32;padding:8px;border-left:4px solid #2e7d32;"
        f"background:#f1f8e9;'>Connected. Region: <b>{REGION}</b>,"
        f" Endpoint: <b>{ENDPOINT_NAME}</b></div>"
    )


def _error_html(msg):
    return (
        f"<div style='color:#d32f2f;padding:8px;border-left:4px solid #d32f2f;"
        f"background:#fff3f3;'>{msg}</div>"
    )


def try_init_client(access_key_id, secret_access_key):
    """Try to create a SageMaker runtime client with the given credentials.

    Returns:
        Tuple of (client_or_None, status_html_string).
    """
    if not access_key_id or not secret_access_key:
        return None, _error_html("Both Access Key ID and Secret Access Key are required.")
    try:
        client = boto3.client(
            "sagemaker-runtime",
            region_name=REGION,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )
        return client, _success_html()
    except Exception as e:
        return None, _error_html(f"AWS client error: {e}")


def try_init_from_env():
    """Try to create a client from environment variables.

    Returns:
        Tuple of (client_or_None, status_html_or_None). Returns (None, None)
        if env vars are not set (so the dashboard knows to show input fields).
    """
    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    if not access_key or not secret_key:
        return None, None
    return try_init_client(access_key, secret_key)
