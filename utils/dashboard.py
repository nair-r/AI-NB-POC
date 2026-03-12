"""Dashboard widget assembly and event wiring for the MedGemma demo."""

from __future__ import annotations

import base64
import json
import re
import time
import warnings
from pathlib import Path

import botocore
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output

from utils.aws_client import try_init_client, try_init_from_env
from utils.config import CONTENT_TYPE, ENDPOINT_NAME
from utils.dicom_utils import (
    dicom_to_pil,
    dicom_to_png_bytes,
    extract_metadata,
    is_dicom_candidate,
    read_dicom,
)

warnings.filterwarnings("ignore", category=UserWarning)

# ── HTML helpers ─────────────────────────────────────────────────────

_PLACEHOLDER_HTML = (
    "<div style='display:flex;align-items:center;justify-content:center;"
    "width:100%;min-height:400px;background:#e0e0e0;border-radius:4px;"
    "color:#888;font-size:16px;'>Select an image</div>"
)

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


def _metadata_table(rows):
    trs = "".join(
        f"<tr><td style='padding:2px 8px;font-weight:bold;white-space:nowrap;'>{k}</td>"
        f"<td style='padding:2px 8px;'>{v}</td></tr>"
        for k, v in rows
    )
    return (
        "<table style='font-size:12px;border-collapse:collapse;"
        f"margin-top:8px;width:100%;'>{trs}</table>"
    )


# ── Dashboard builder ────────────────────────────────────────────────


def build_and_display_app():
    """Build the full dashboard widget tree, wire events, and display it."""

    # Shared mutable state
    state = {
        "current_dir": None,
        "current_ds": None,
        "current_png_bytes": None,
        "sm_client": None,
    }

    # ── AWS credential widgets ───────────────────────────────────────
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
    client, env_html = try_init_from_env()
    if client is not None:
        state["sm_client"] = client
        cred_status.value = env_html
        cred_form.layout.display = "none"
    else:
        cred_form.layout.display = ""

    def _on_connect(_btn):
        client, html = try_init_client(
            access_key_input.value.strip(),
            secret_key_input.value.strip(),
        )
        if client is not None:
            state["sm_client"] = client
            cred_status.value = html
            cred_form.layout.display = "none"
        else:
            cred_status.value = html

    connect_btn.on_click(_on_connect)

    # ── Image panel (left) ───────────────────────────────────────────
    image_placeholder = widgets.HTML(value=_PLACEHOLDER_HTML)
    image_widget = widgets.Image(
        format="png",
        layout=widgets.Layout(
            max_width="100%", max_height="500px", display="none",
            object_fit="contain",
        ),
    )
    image_label = widgets.HTML(value="")

    # ── MedGemma panel (right) ───────────────────────────────────────
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

    # ── File browser widgets ─────────────────────────────────────────
    root_text = widgets.Text(
        value="/data", description="Root path:", layout=widgets.Layout(width="300px"),
    )
    browse_btn = widgets.Button(description="Browse", icon="folder-open", button_style="info")
    nav_up_btn = widgets.Button(
        description="Up", icon="arrow-up", layout=widgets.Layout(width="60px"),
    )
    open_btn = widgets.Button(
        description="Open", icon="folder-open", button_style="success",
        layout=widgets.Layout(width="80px"),
    )
    breadcrumb = widgets.HTML(value="<span style='color:#888;'>No directory selected</span>")
    file_list = widgets.Select(options=[], rows=12, layout=widgets.Layout(width="100%"))
    browser_status = widgets.HTML(value="")

    # ── Metadata panel ───────────────────────────────────────────────
    metadata_html = widgets.HTML(
        value="<div style='color:#888;padding:8px;font-size:13px;'>No image information to display.</div>",
    )

    # ── File browser logic ───────────────────────────────────────────

    def _list_directory(directory):
        try:
            entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            browser_status.value = _error_card("Permission denied.")
            return

        options = []
        for entry in entries:
            if entry.is_dir():
                options.append(f"\U0001F4C1 {entry.name}")
            elif is_dicom_candidate(entry):
                options.append(f"\U0001F4C4 {entry.name}")

        file_list.options = options if options else ["(empty)"]
        file_list.value = None
        breadcrumb.value = (
            f"<span style='font-size:12px;color:#555;'><b>Path:</b> {directory}</span>"
        )

    def _on_browse(_btn):
        p = Path(root_text.value.strip())
        if not p.exists() or not p.is_dir():
            browser_status.value = _error_card(f"Directory not found: {p}")
            return
        browser_status.value = ""
        state["current_dir"] = p
        _list_directory(p)

    def _on_nav_up(_btn):
        cur = state["current_dir"]
        if cur is None:
            return
        parent = cur.parent
        if parent != cur:
            state["current_dir"] = parent
            _list_directory(parent)

    def _display_dicom(file_path):
        ds = read_dicom(file_path)
        if ds is None:
            browser_status.value = _error_card("Could not read DICOM file.")
            return

        try:
            _ = ds.pixel_array
        except Exception:
            browser_status.value = _error_card(
                "This DICOM has no pixel data, or requires a transfer syntax handler "
                "(install pylibjpeg or python-gdcm for compressed DICOMs)."
            )
            return

        try:
            pil_img = dicom_to_pil(ds)
        except Exception as e:
            browser_status.value = _error_card(f"Error rendering DICOM: {e}")
            return

        state["current_ds"] = ds
        state["current_png_bytes"] = dicom_to_png_bytes(ds)
        browser_status.value = ""

        # Show image in left panel
        image_widget.value = state["current_png_bytes"]
        image_widget.layout.display = ""
        image_placeholder.layout.display = "none"
        image_label.value = (
            f"<div style='font-size:12px;color:#555;padding:4px 0;'>"
            f"<b>{file_path.name}</b></div>"
        )

        # Update metadata panel
        meta_rows = extract_metadata(ds)
        metadata_html.value = _metadata_table(meta_rows) if meta_rows else ""

    def _resolve_selected():
        """Resolve the currently highlighted item in file_list to a Path."""
        val = file_list.value
        if not val or val == "(empty)" or state["current_dir"] is None:
            return None
        name = val.split(" ", 1)[1] if " " in val else val
        return state["current_dir"] / name

    def _open_selected():
        """Open the selected item: enter directory or load DICOM."""
        target = _resolve_selected()
        if target is None:
            return
        if target.is_dir():
            state["current_dir"] = target
            _list_directory(target)
        else:
            _display_dicom(target)

    def _on_open(_btn):
        _open_selected()

    browse_btn.on_click(_on_browse)
    nav_up_btn.on_click(_on_nav_up)
    open_btn.on_click(_on_open)

    # ── Inference logic ──────────────────────────────────────────────

    def _on_send(_btn):
        if state["current_png_bytes"] is None:
            response_area.value = _error_card("No image loaded. Select a DICOM file first.")
            return
        if state["sm_client"] is None:
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
                "image": base64.b64encode(state["current_png_bytes"]).decode("utf-8"),
            }
            resp = state["sm_client"].invoke_endpoint(
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

    # ── Layout assembly ──────────────────────────────────────────────
    #
    #  ┌──────────────────────────────────────────────┐
    #  │ Credentials                                  │
    #  ├──────────────────────┬───────────────────────┤
    #  │ Image Panel (left)   │ MedGemma Panel (right)│
    #  ├──────────────────────┴───────────────────────┤
    #  │ File Browser (full width)                    │
    #  ├──────────────────────────────────────────────┤
    #  │ Image Information (full width)               │
    #  └──────────────────────────────────────────────┘

    image_panel = widgets.VBox(
        [
            widgets.HTML("<h4 style='margin:0 0 4px 0;'>Image</h4>"),
            image_label,
            image_placeholder,
            image_widget,
        ],
        layout=widgets.Layout(
            width="50%", padding="8px", border_right="1px solid #e0e0e0",
        ),
    )

    medgemma_panel = widgets.VBox(
        [
            widgets.HTML("<h4 style='margin:0 0 4px 0;'>MedGemma</h4>"),
            multi_turn_note,
            prompt_area,
            widgets.HBox([send_button, spinner]),
            response_area,
        ],
        layout=widgets.Layout(width="50%", padding="8px"),
    )

    file_browser_panel = widgets.VBox(
        [
            widgets.HTML("<h4 style='margin:0 0 4px 0;'>File Browser</h4>"),
            widgets.HBox([root_text, browse_btn, nav_up_btn, open_btn]),
            breadcrumb,
            widgets.HTML(
                "<div style='font-size:11px;color:#999;margin-bottom:2px;'>"
                "Select an item, then click <b>Open</b> to enter a folder or load a DICOM.</div>"
            ),
            file_list,
            browser_status,
        ],
        layout=widgets.Layout(
            padding="8px", border_top="1px solid #e0e0e0", width="100%",
        ),
    )

    info_panel = widgets.VBox(
        [
            widgets.HTML("<h4 style='margin:0 0 4px 0;'>Image Information</h4>"),
            metadata_html,
        ],
        layout=widgets.Layout(
            padding="8px", border_top="1px solid #e0e0e0", width="100%",
        ),
    )

    app = widgets.VBox([
        cred_form,
        cred_status,
        widgets.HBox(
            [image_panel, medgemma_panel],
            layout=widgets.Layout(min_height="420px"),
        ),
        file_browser_panel,
        info_panel,
    ])

    display(app)
