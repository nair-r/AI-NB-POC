"""Sidebar file browser with click-to-open navigation."""

from __future__ import annotations

import html
from pathlib import Path

import ipywidgets as widgets

from utils.dicom_utils import (
    dicom_to_pil,
    dicom_to_png_bytes,
    extract_metadata,
    is_dicom_candidate,
    read_dicom,
)

_TEXT_EXTENSIONS = {
    ".txt", ".csv", ".json", ".xml", ".html", ".log",
    ".md", ".yaml", ".yml", ".cfg", ".ini", ".conf",
}


def _is_text_file(p):
    """Check if a path is a readable text file."""
    return p.suffix.lower() in _TEXT_EXTENSIONS


def _error_card(msg):
    return (
        f"<div style='color:#d32f2f;background:#fff3f3;padding:10px 12px;"
        f"border-left:3px solid #d32f2f;border-radius:4px;font-size:12px;"
        f"margin-top:4px;'>{msg}</div>"
    )


def build_file_browser(state, viewer):
    """Build sidebar file browser with click-to-open behavior.

    Args:
        state: AppState instance.
        viewer: dict returned by build_viewer (contains widgets to update).
    """

    root_text = widgets.Text(
        value="/data",
        placeholder="/path/to/data",
        layout=widgets.Layout(width="100%"),
    )
    browse_btn = widgets.Button(
        description="Go", icon="folder-open", button_style="info",
        layout=widgets.Layout(width="60px", height="32px"),
    )
    nav_up_btn = widgets.Button(
        description="", icon="arrow-up",
        layout=widgets.Layout(width="36px", height="32px"),
    )
    breadcrumb = widgets.HTML(
        value=(
            "<div style='font-size:11px;color:#6c757d;padding:4px 0;'>"
            "No directory selected</div>"
        ),
    )
    file_list = widgets.Select(
        options=[], rows=20,
        layout=widgets.Layout(width="100%"),
    )
    browser_status = widgets.HTML(value="")

    # Viewer widgets for cross-component updates
    image_widget = viewer["image_widget"]
    image_placeholder = viewer["image_placeholder"]
    image_label = viewer["image_label"]
    text_viewer = viewer["text_viewer"]
    metadata_html = viewer["metadata_html"]
    metadata_table = viewer["metadata_table"]
    info_panel = viewer["info_panel"]

    # Guard flag to prevent re-entrant selection events during list refresh
    _refreshing = [False]

    def _list_directory(directory):
        _refreshing[0] = True
        try:
            entries = sorted(
                directory.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except PermissionError:
            browser_status.value = _error_card("Permission denied.")
            _refreshing[0] = False
            return

        options = []
        # Parent directory entry
        if directory.parent != directory:
            options.append("\u2B06 ..")
        for entry in entries:
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                options.append(f"\U0001F4C1 {entry.name}")
            elif is_dicom_candidate(entry):
                options.append(f"\U0001F52C {entry.name}")
            elif _is_text_file(entry):
                options.append(f"\U0001F4C4 {entry.name}")

        file_list.options = options if options else ["(empty directory)"]
        file_list.value = None
        _refreshing[0] = False

        # Breadcrumb
        dir_str = str(directory)
        if len(dir_str) > 35:
            dir_str = "\u2026" + dir_str[-32:]
        breadcrumb.value = (
            f"<div style='font-size:11px;color:#6c757d;padding:4px 0;"
            f"border-bottom:1px solid #e9ecef;margin-bottom:4px;'>"
            f"&#128194; <b>{dir_str}</b></div>"
        )

    def _on_browse(_btn=None):
        p = Path(root_text.value.strip())
        if not p.exists() or not p.is_dir():
            browser_status.value = _error_card(f"Not found: {p}")
            return
        browser_status.value = ""
        state.current_dir = p
        _list_directory(p)

    def _on_nav_up(_btn=None):
        if state.current_dir is None:
            return
        parent = state.current_dir.parent
        if parent != state.current_dir:
            state.current_dir = parent
            root_text.value = str(parent)
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
                "No pixel data or missing transfer syntax handler."
            )
            return

        try:
            dicom_to_pil(ds)
        except Exception as e:
            browser_status.value = _error_card(f"Render error: {e}")
            return

        state.current_ds = ds
        state.current_png_bytes = dicom_to_png_bytes(ds)
        state.current_file_name = file_path.name
        browser_status.value = ""

        # Show image, hide text
        image_widget.value = state.current_png_bytes
        image_widget.layout.display = ""
        image_placeholder.layout.display = "none"
        text_viewer.layout.display = "none"
        image_label.value = (
            f"<div style='font-size:13px;color:#495057;padding:0 0 8px;'>"
            f"&#x1F52C; <b>{file_path.name}</b></div>"
        )

        # Show metadata
        meta_rows = extract_metadata(ds)
        if meta_rows:
            metadata_html.value = metadata_table(meta_rows)
            info_panel.layout.display = ""
        else:
            info_panel.layout.display = "none"

    def _display_text(file_path):
        try:
            content = file_path.read_text(errors="replace")[:50_000]
        except Exception as e:
            browser_status.value = _error_card(f"Could not read: {e}")
            return

        safe = html.escape(content)
        state.current_text = content
        state.current_file_name = file_path.name
        state.current_ds = None
        state.current_png_bytes = b""
        browser_status.value = ""

        # Show text, hide image
        text_viewer.value = (
            f"<pre style='font-size:12px;line-height:1.6;margin:0;padding:12px;"
            f"background:#f8f9fa;border:1px solid #e9ecef;border-radius:6px;"
            f"overflow:auto;max-height:450px;white-space:pre-wrap;"
            f"word-wrap:break-word;"
            f"font-family:SF Mono,Monaco,Consolas,monospace;'>{safe}</pre>"
        )
        text_viewer.layout.display = ""
        image_widget.layout.display = "none"
        image_placeholder.layout.display = "none"
        image_label.value = (
            f"<div style='font-size:13px;color:#495057;padding:0 0 8px;'>"
            f"&#x1F4C4; <b>{file_path.name}</b></div>"
        )

        # Hide DICOM metadata
        info_panel.layout.display = "none"

    def _on_select(change):
        if _refreshing[0]:
            return
        val = change["new"]
        if not val or val == "(empty directory)":
            return

        # Parse item name (skip emoji prefix)
        name = val.split(" ", 1)[1] if " " in val else val

        # Parent directory
        if name == "..":
            _on_nav_up()
            return

        if state.current_dir is None:
            return
        target = state.current_dir / name

        if target.is_dir():
            state.current_dir = target
            root_text.value = str(target)
            _list_directory(target)
        elif is_dicom_candidate(target):
            _display_dicom(target)
        elif _is_text_file(target):
            _display_text(target)

    browse_btn.on_click(_on_browse)
    nav_up_btn.on_click(_on_nav_up)
    file_list.observe(_on_select, names="value")

    # Auto-browse default directory on startup
    _on_browse()

    sidebar = widgets.VBox(
        [
            widgets.HTML(
                "<div style='font-size:13px;font-weight:700;color:#495057;"
                "padding:0 0 8px;'>File Browser</div>"
            ),
            widgets.HBox(
                [root_text, nav_up_btn, browse_btn],
                layout=widgets.Layout(width="100%"),
            ),
            breadcrumb,
            file_list,
            browser_status,
        ],
        layout=widgets.Layout(
            width="280px", min_width="280px",
            padding="12px",
        ),
    )
    sidebar.add_class("medgemma-sidebar")

    return sidebar
