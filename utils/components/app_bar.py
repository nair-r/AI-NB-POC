"""App header bar."""

from __future__ import annotations

import ipywidgets as widgets

from utils.config import INFERENCE_URL, MODEL_NAME


def build_app_bar():
    """Build the top header.

    Returns the header widget.
    """
    return widgets.HTML(value=(
        "<div style='background:linear-gradient(135deg,#1565c0,#0d47a1);"
        "color:white;padding:14px 24px;'>"
        "<div style='font-size:18px;font-weight:700;letter-spacing:-0.3px;'>"
        "&#x1F3E5; Medical AI Inference Dashboard</div>"
        "<div style='font-size:11px;opacity:0.8;margin-top:2px;'>"
        f"KServe endpoint: <b>{MODEL_NAME}</b> &mdash; "
        f"<code style='opacity:0.9;'>{INFERENCE_URL}</code></div></div>"
    ))
