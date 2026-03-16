"""Credential form and connection status bar."""

from __future__ import annotations

import ipywidgets as widgets

from utils.aws_client import try_init_client, try_init_from_env
from utils.config import ENDPOINT_NAME, REGION


def _success_html():
    return (
        "<div style='color:#2e7d32;padding:8px;border-left:4px solid #2e7d32;"
        f"background:#f1f8e9;'>Connected. Region: <b>{REGION}</b>,"
        f" Endpoint: <b>{ENDPOINT_NAME}</b></div>"
    )


def _error_status_html(msg):
    return (
        f"<div style='color:#d32f2f;padding:8px;border-left:4px solid #d32f2f;"
        f"background:#fff3f3;'>{msg}</div>"
    )


def build_app_bar(state):
    """Build the credential form and connection status widgets."""

    cred_status = widgets.HTML(value="")

    access_key_input = widgets.Text(
        description="Access Key ID:",
        placeholder="AKIA...",
        layout=widgets.Layout(width="400px"),
        style={"description_width": "120px"},
    )
    secret_key_input = widgets.Password(
        description="Secret Key:",
        placeholder="Enter your AWS secret access key",
        layout=widgets.Layout(width="400px"),
        style={"description_width": "120px"},
    )
    connect_btn = widgets.Button(
        description="Connect", icon="plug", button_style="warning",
        layout=widgets.Layout(width="140px", height="36px"),
    )
    cred_form = widgets.VBox(
        [
            widgets.HTML(
                "<div style='padding:4px 0 4px 0;font-size:13px;color:#555;'>"
                "AWS credentials not found in environment. Enter them below:</div>"
            ),
            access_key_input,
            secret_key_input,
            connect_btn,
        ],
        layout=widgets.Layout(padding="8px", border="1px solid #e0e0e0", margin="0 0 8px 0"),
    )

    # Try env vars first
    client, error = try_init_from_env()
    if client is not None:
        state.sm_client = client
        cred_status.value = _success_html()
        cred_form.layout.display = "none"
    elif error is not None:
        cred_status.value = _error_status_html(error)
    else:
        cred_form.layout.display = ""

    def _on_connect(_btn):
        client, error = try_init_client(
            access_key_input.value.strip(),
            secret_key_input.value.strip(),
        )
        if client is not None:
            state.sm_client = client
            cred_status.value = _success_html()
            cred_form.layout.display = "none"
        else:
            cred_status.value = _error_status_html(error)

    connect_btn.on_click(_on_connect)

    return widgets.VBox([cred_form, cred_status])
