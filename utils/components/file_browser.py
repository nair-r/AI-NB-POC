"""File navigation widgets and directory listing."""

from __future__ import annotations

from pathlib import Path

import ipywidgets as widgets

from utils.dicom_utils import (
    dicom_to_pil,
    dicom_to_png_bytes,
    extract_metadata,
    is_dicom_candidate,
    read_dicom,
)


def _error_card(msg):
    return (
        f"<div style='color:#d32f2f;background:#fff3f3;padding:12px;"
        f"border-left:4px solid #d32f2f;border-radius:4px;'>{msg}</div>"
    )


def build_file_browser(state, viewer):
    """Build file browser widgets and wire navigation events.

    Args:
        state: AppState instance.
        viewer: dict returned by build_viewer (contains widgets to update).
    """

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

    # Unpack viewer widgets needed for cross-component updates
    image_widget = viewer["image_widget"]
    image_placeholder = viewer["image_placeholder"]
    image_label = viewer["image_label"]
    metadata_html = viewer["metadata_html"]
    metadata_table = viewer["metadata_table"]

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
        state.current_dir = p
        _list_directory(p)

    def _on_nav_up(_btn):
        cur = state.current_dir
        if cur is None:
            return
        parent = cur.parent
        if parent != cur:
            state.current_dir = parent
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
            dicom_to_pil(ds)
        except Exception as e:
            browser_status.value = _error_card(f"Error rendering DICOM: {e}")
            return

        state.current_ds = ds
        state.current_png_bytes = dicom_to_png_bytes(ds)
        browser_status.value = ""

        # Update image panel
        image_widget.value = state.current_png_bytes
        image_widget.layout.display = ""
        image_placeholder.layout.display = "none"
        image_label.value = (
            f"<div style='font-size:12px;color:#555;padding:4px 0;'>"
            f"<b>{file_path.name}</b></div>"
        )

        # Update metadata panel
        meta_rows = extract_metadata(ds)
        metadata_html.value = metadata_table(meta_rows) if meta_rows else ""

    def _resolve_selected():
        val = file_list.value
        if not val or val == "(empty)" or state.current_dir is None:
            return None
        name = val.split(" ", 1)[1] if " " in val else val
        return state.current_dir / name

    def _open_selected():
        target = _resolve_selected()
        if target is None:
            return
        if target.is_dir():
            state.current_dir = target
            _list_directory(target)
        else:
            _display_dicom(target)

    def _on_open(_btn):
        _open_selected()

    browse_btn.on_click(_on_browse)
    nav_up_btn.on_click(_on_nav_up)
    open_btn.on_click(_on_open)

    return widgets.VBox(
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
