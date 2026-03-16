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
    '<div style="display:flex;align-items:center;gap:8px;padding:8px 0;">'
    '<div style="width:18px;height:18px;border:2px solid #e0e0e0;'
    'border-top-color:#1976d2;border-radius:50%;animation:spin 0.8s linear infinite;"></div>'
    '<span style="font-size:13px;color:#6c757d;">Analyzing...</span></div>'
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
        "<div style='display:flex;flex-direction:column;gap:10px;'>"
        "<div style='background:#e3f2fd;padding:10px 14px;border-radius:10px 10px 10px 2px;"
        "font-size:13px;line-height:1.5;'>"
        "<div style='font-size:11px;font-weight:600;color:#1565c0;margin-bottom:4px;'>You</div>"
        f"{prompt}</div>"
        "<div style='background:#f5f5f5;padding:10px 14px;border-radius:10px 10px 2px 10px;"
        "font-size:13px;line-height:1.6;'>"
        "<div style='font-size:11px;font-weight:600;color:#495057;margin-bottom:4px;'>"
        "MedGemma</div>"
        f"{response_html}</div></div>"
    )


def _error_card(msg):
    return (
        f"<div style='color:#d32f2f;background:#fff3f3;padding:10px 12px;"
        f"border-left:3px solid #d32f2f;border-radius:4px;font-size:13px;'>{msg}</div>"
    )


def build_chat(state):
    """Build the MedGemma prompt and response panel."""

    prompt_area = widgets.Textarea(
        value="Describe this medical image. What findings are visible?",
        placeholder="Enter your question about the image...",
        rows=3,
        layout=widgets.Layout(width="100%"),
    )
    send_button = widgets.Button(
        description="Ask MedGemma",
        icon="paper-plane",
        button_style="primary",
        layout=widgets.Layout(width="100%", height="38px"),
    )
    spinner = widgets.HTML(value="")
    response_area = widgets.HTML(
        value=(
            "<div style='color:#6c757d;padding:24px;text-align:center;"
            "font-size:13px;'>Response will appear here after inference.</div>"
        ),
    )

    def _on_send(_btn):
        if not state.current_png_bytes:
            response_area.value = _error_card(
                "No image loaded. Select a DICOM file first."
            )
            return
        if state.sm_client is None:
            response_area.value = _error_card(
                "Not connected to AWS. Enter credentials above."
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
            timing = (
                f"<div style='font-size:11px;color:#adb5bd;margin-top:8px;'>"
                f"Response time: {elapsed:.1f}s</div>"
            )
            response_area.value = _chat_bubble(prompt, generated) + timing

        except botocore.exceptions.ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "ModelError":
                response_area.value = _error_card(
                    "Model error &mdash; endpoint may still be loading."
                )
            else:
                response_area.value = _error_card(f"AWS error ({code}): {e}")
        except botocore.exceptions.ReadTimeoutError:
            response_area.value = _error_card(
                "Request timed out. Endpoint may be cold-starting (5-10 min)."
            )
        except Exception as e:
            response_area.value = _error_card(f"Unexpected error: {e}")
        finally:
            send_button.disabled = False
            spinner.value = ""

    send_button.on_click(_on_send)

    return widgets.VBox(
        [
            widgets.HTML(
                "<div style='font-size:13px;font-weight:700;color:#495057;"
                "padding:0 0 8px;'>MedGemma Analysis</div>"
            ),
            prompt_area,
            send_button,
            spinner,
            response_area,
        ],
        layout=widgets.Layout(
            width="45%", padding="0 0 0 16px",
            border_left="1px solid #e9ecef",
        ),
    )
