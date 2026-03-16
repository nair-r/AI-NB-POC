"""MedGemma prompt, inference, and response display."""

from __future__ import annotations

import base64
import json
import re
import time

import botocore
import ipywidgets as widgets

from utils.config import CONTENT_TYPE, ENDPOINT_NAME

_SPINNER_HTML = (
    '<div style="display:flex;align-items:center;gap:8px;">'
    '<div style="width:20px;height:20px;border:3px solid #ccc;border-top-color:#1976d2;'
    'border-radius:50%;animation:spin 0.8s linear infinite;"></div>'
    '<span>Sending to MedGemma...</span></div>'
    '<style>@keyframes spin{to{transform:rotate(360deg)}}</style>'
)


def _md_to_html(text):
    """Convert basic markdown (bold, italic, newlines) to HTML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = text.replace("\n", "<br>")
    return text


def _chat_bubble(prompt, response):
    response_html = _md_to_html(response)
    return (
        "<div style='max-width:100%;'>"
        "<div style='background:#e3f2fd;padding:12px 16px;border-radius:12px 12px 12px 0;"
        "margin-bottom:8px;font-size:13px;'>"
        f"<b>You:</b> {prompt}</div>"
        "<div style='background:#f5f5f5;padding:12px 16px;border-radius:12px 12px 0 12px;"
        f"font-size:13px;line-height:1.5;'><b>MedGemma:</b><br>{response_html}</div></div>"
    )


def _error_card(msg):
    return (
        f"<div style='color:#d32f2f;background:#fff3f3;padding:12px;"
        f"border-left:4px solid #d32f2f;border-radius:4px;'>{msg}</div>"
    )


def build_chat(state):
    """Build the MedGemma prompt and response panel."""

    prompt_area = widgets.Textarea(
        value="Describe this medical image. What findings are visible?",
        placeholder="Enter your question about the image...",
        rows=4,
        layout=widgets.Layout(width="100%"),
    )
    send_button = widgets.Button(
        description=" Ask MedGemma",
        icon="paper-plane",
        button_style="primary",
        layout=widgets.Layout(width="200px", height="40px"),
    )
    spinner = widgets.HTML(value="")
    response_area = widgets.HTML(
        value="<div style='color:#888;padding:16px;'>Response will appear here after inference.</div>",
    )
    multi_turn_note = widgets.HTML(
        value=(
            "<div style='font-size:11px;color:#999;margin-top:8px;'>"
            "Single-shot inference only. Multi-turn conversation coming soon.</div>"
        ),
    )

    def _on_send(_btn):
        if not state.current_png_bytes:
            response_area.value = _error_card("No image loaded. Select a DICOM file first.")
            return
        if state.sm_client is None:
            response_area.value = _error_card(
                "AWS credentials not configured. Enter them above and click Connect."
            )
            return

        prompt = prompt_area.value.strip()
        if not prompt:
            response_area.value = _error_card("Please enter a prompt.")
            return

        send_button.disabled = True
        spinner.value = _SPINNER_HTML

        t0 = time.time()
        try:
            payload = {
                "text": prompt,
                "image": base64.b64encode(state.current_png_bytes).decode("utf-8"),
            }
            resp = state.sm_client.invoke_endpoint(
                EndpointName=ENDPOINT_NAME,
                ContentType=CONTENT_TYPE,
                Body=json.dumps(payload),
            )
            elapsed = time.time() - t0
            result = json.loads(resp["Body"].read().decode("utf-8"))
            generated = result.get("generated_text", "(No text in response)")
            timing_html = (
                f"<div style='font-size:11px;color:#777;margin-top:4px;'>"
                f"Response time: {elapsed:.1f}s</div>"
            )
            response_area.value = _chat_bubble(prompt, generated) + timing_html

        except botocore.exceptions.ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ModelError":
                response_area.value = _error_card(
                    "Model error — the endpoint may still be loading or rejected the input."
                )
            else:
                response_area.value = _error_card(f"AWS error ({code}): {e}")
        except botocore.exceptions.ReadTimeoutError:
            response_area.value = _error_card(
                "Request timed out. The endpoint may be cold-starting "
                "(can take 5-10 min on first call)."
            )
        except Exception as e:
            response_area.value = _error_card(f"Unexpected error: {e}")
        finally:
            send_button.disabled = False
            spinner.value = ""

    send_button.on_click(_on_send)

    return widgets.VBox(
        [
            widgets.HTML("<h4 style='margin:0 0 4px 0;'>MedGemma</h4>"),
            multi_turn_note,
            prompt_area,
            widgets.HBox([send_button, spinner]),
            response_area,
        ],
        layout=widgets.Layout(width="50%", padding="8px"),
    )
