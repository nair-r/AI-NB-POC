"""Image display and metadata panel."""

from __future__ import annotations

import ipywidgets as widgets

_PLACEHOLDER_HTML = (
    "<div style='display:flex;align-items:center;justify-content:center;"
    "width:100%;min-height:400px;background:#e0e0e0;border-radius:4px;"
    "color:#888;font-size:16px;'>Select an image</div>"
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


def build_viewer(state):
    """Build image display and metadata widgets.

    Returns a dict with keys:
        image_panel       - VBox for the left image area
        info_panel        - VBox for the full-width metadata area
        image_widget      - Image widget (for cross-component updates)
        image_placeholder - HTML placeholder (hidden when image loaded)
        image_label       - HTML label showing filename
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

    metadata_html = widgets.HTML(
        value="<div style='color:#888;padding:8px;font-size:13px;'>No image information to display.</div>",
    )

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

    info_panel = widgets.VBox(
        [
            widgets.HTML("<h4 style='margin:0 0 4px 0;'>Image Information</h4>"),
            metadata_html,
        ],
        layout=widgets.Layout(
            padding="8px", border_top="1px solid #e0e0e0", width="100%",
        ),
    )

    return {
        "image_panel": image_panel,
        "info_panel": info_panel,
        "image_widget": image_widget,
        "image_placeholder": image_placeholder,
        "image_label": image_label,
        "metadata_html": metadata_html,
        "metadata_table": _metadata_table,
    }
