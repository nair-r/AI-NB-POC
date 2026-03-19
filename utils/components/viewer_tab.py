"""Image display, report display, and metadata panel."""

from __future__ import annotations

import ipywidgets as widgets

from utils.dicom_utils import extract_metadata

_PLACEHOLDER_HTML = (
    "<div style='display:flex;align-items:center;justify-content:center;"
    "width:100%;min-height:350px;background:#f8f9fa;border-radius:8px;"
    "border:2px dashed #dee2e6;color:#6c757d;font-size:14px;"
    "flex-direction:column;gap:8px;'>"
    "<span style='font-size:36px;opacity:0.5;'>&#128203;</span>"
    "<span>Select a file from the browser</span></div>"
)


def _metadata_table(rows):
    trs = "".join(
        f"<tr><td style='padding:4px 12px;font-weight:600;white-space:nowrap;"
        f"color:#495057;font-size:12px;border-bottom:1px solid #f0f0f0;'>{k}</td>"
        f"<td style='padding:4px 12px;font-size:12px;color:#6c757d;"
        f"border-bottom:1px solid #f0f0f0;'>{v}</td></tr>"
        for k, v in rows
    )
    return (
        f"<table style='font-size:12px;border-collapse:collapse;width:100%;'>"
        f"{trs}</table>"
    )


def build_viewer(state):
    """Build image display, report display, and metadata widgets.

    Returns a dict with keys:
        viewer_panel      - VBox for the main viewer area
        info_panel        - VBox for DICOM metadata (hidden until image loaded)
        image_widget      - Image widget (for cross-component updates)
        image_placeholder - HTML placeholder (hidden when content loaded)
        image_label       - HTML label showing filename
        report_display    - HTML widget for attached report content
        metadata_html     - HTML widget for metadata table
        metadata_table    - formatter function for metadata rows
    """

    image_placeholder = widgets.HTML(value=_PLACEHOLDER_HTML)
    image_widget = widgets.Image(
        format="png",
        layout=widgets.Layout(
            max_width="100%", max_height="500px", display="none",
            object_fit="contain",
        ),
    )
    image_label = widgets.HTML(value="")
    report_display = widgets.HTML(value="")
    metadata_html = widgets.HTML(value="")

    series_info_label = widgets.HTML(
        value="",
        layout=widgets.Layout(display="none"),
    )
    slice_slider = widgets.IntSlider(
        min=0, max=0, value=0,
        description="Slice:",
        layout=widgets.Layout(width="100%", display="none"),
    )

    _slider_guard = [False]

    def _on_slider_change(change):
        if _slider_guard[0]:
            return
        idx = change["new"]
        if not state.series_datasets or idx >= len(state.series_datasets):
            return

        state.series_index = idx
        ds, png = state.series_datasets[idx], state.series_png_cache[idx]
        state.current_ds = ds
        state.current_png_bytes = png
        state.current_file_name = f"{state.series_dir_name} [{idx + 1}/{len(state.series_datasets)}]"

        image_widget.value = png
        series_info_label.value = (
            f"<div style='font-size:12px;color:#6c757d;padding:4px 0;'>"
            f"Slice {idx + 1} / {len(state.series_datasets)}</div>"
        )

        meta_rows = extract_metadata(ds)
        if meta_rows:
            metadata_html.value = _metadata_table(meta_rows)

    slice_slider.observe(_on_slider_change, names="value")

    viewer_panel = widgets.VBox(
        [
            image_label,
            image_placeholder,
            image_widget,
            series_info_label,
            slice_slider,
        ],
        layout=widgets.Layout(
            flex="1.2", padding="0 16px 0 0",
            min_height="400px",
        ),
    )

    info_panel = widgets.VBox(
        [
            widgets.HTML(
                "<div style='font-size:13px;font-weight:700;color:#495057;"
                "padding:8px 0 4px;border-top:1px solid #e9ecef;margin-top:12px;'>"
                "DICOM Metadata</div>"
            ),
            metadata_html,
        ],
        layout=widgets.Layout(padding="0", width="100%", display="none"),
    )

    return {
        "viewer_panel": viewer_panel,
        "info_panel": info_panel,
        "image_widget": image_widget,
        "image_placeholder": image_placeholder,
        "image_label": image_label,
        "report_display": report_display,
        "metadata_html": metadata_html,
        "metadata_table": _metadata_table,
        "slice_slider": slice_slider,
        "series_info_label": series_info_label,
    }
