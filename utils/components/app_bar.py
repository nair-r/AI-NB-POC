"""App header bar and credential form."""

from __future__ import annotations

import ipywidgets as widgets

from utils.aws_client import try_init_client, try_init_from_env
from utils.config import ENDPOINT_NAME, REGION


def build_app_bar(state):
    """Build header bar and credential section.

    Returns:
        Tuple of (header_widget, credential_section_widget).
    """

    header = widgets.HTML(value=(
        "<div style='background:linear-gradient(135deg,#1565c0,#0d47a1);"
        "color:white;padding:14px 24px;'>"
        "<div style='font-size:18px;font-weight:700;letter-spacing:-0.3px;'>"
        "&#x1F3E5; Medical AI Inference Dashboard</div>"
        "<div style='font-size:11px;opacity:0.8;margin-top:2px;'>"
        "Medical image analysis powered by MedGemma &amp; Merlin on SageMaker</div></div>"
    ))

    status_bar = widgets.HTML(value="")

    access_key_input = widgets.Text(
        placeholder="AKIA...",
        layout=widgets.Layout(width="100%"),
    )
    secret_key_input = widgets.Password(
        placeholder="Enter secret access key",
        layout=widgets.Layout(width="100%"),
    )
    connect_btn = widgets.Button(
        description="Connect", icon="plug", button_style="primary",
        layout=widgets.Layout(width="140px", height="36px"),
    )

    cred_section = widgets.VBox(
        [
            widgets.HTML(
                "<div style='font-size:13px;color:#495057;font-weight:600;"
                "padding:0 0 8px;'>AWS Credentials</div>"
            ),
            widgets.HBox([
                widgets.VBox([
                    widgets.HTML(
                        "<div style='font-size:11px;color:#6c757d;"
                        "margin-bottom:2px;'>Access Key ID</div>"
                    ),
                    access_key_input,
                ], layout=widgets.Layout(flex="1")),
                widgets.VBox([
                    widgets.HTML(
                        "<div style='font-size:11px;color:#6c757d;"
                        "margin-bottom:2px;'>Secret Access Key</div>"
                    ),
                    secret_key_input,
                ], layout=widgets.Layout(flex="1")),
                widgets.VBox([
                    widgets.HTML(
                        "<div style='font-size:11px;color:transparent;"
                        "margin-bottom:2px;'>.</div>"
                    ),
                    connect_btn,
                ]),
            ]),
            status_bar,
        ],
        layout=widgets.Layout(padding="12px 24px", border_bottom="1px solid #dee2e6"),
    )
    cred_section.add_class("medgemma-cred")

    # Try env vars first
    sm_client, s3_client, error = try_init_from_env()
    if sm_client is not None:
        state.sm_client = sm_client
        state.s3_client = s3_client
        status_bar.value = (
            "<div style='color:#2e7d32;font-size:12px;padding:6px 0;'>"
            f"&#10003; Connected &mdash; Region: <b>{REGION}</b>, "
            f"Endpoint: <b>{ENDPOINT_NAME}</b></div>"
        )
        cred_section.layout.display = "none"
    elif error is not None:
        status_bar.value = (
            f"<div style='color:#d32f2f;font-size:12px;padding:6px 0;'>"
            f"&#10007; {error}</div>"
        )

    def _on_connect(_btn):
        sm_client, s3_client, error = try_init_client(
            access_key_input.value.strip(),
            secret_key_input.value.strip(),
        )
        if sm_client is not None:
            state.sm_client = sm_client
            state.s3_client = s3_client
            status_bar.value = (
                "<div style='color:#2e7d32;font-size:12px;padding:6px 0;'>"
                f"&#10003; Connected &mdash; Region: <b>{REGION}</b>, "
                f"Endpoint: <b>{ENDPOINT_NAME}</b></div>"
            )
            cred_section.layout.display = "none"
        else:
            status_bar.value = (
                f"<div style='color:#d32f2f;font-size:12px;padding:6px 0;'>"
                f"&#10007; {error}</div>"
            )

    connect_btn.on_click(_on_connect)

    return header, cred_section
