"""Centralized application state for the MedGemma dashboard."""

from __future__ import annotations

import traitlets


class AppState(traitlets.HasTraits):
    """Single source of truth shared across all dashboard components."""

    current_ds = traitlets.Any(default_value=None)
    current_png_bytes = traitlets.Bytes(default_value=b"")
    current_file_name = traitlets.Unicode(default_value="")
    report_text = traitlets.Unicode(default_value="")
    report_file_name = traitlets.Unicode(default_value="")
    sm_client = traitlets.Any(default_value=None)

    # Series viewing state
    series_datasets = traitlets.List(default_value=[])
    series_png_cache = traitlets.List(default_value=[])
    series_index = traitlets.Int(default_value=0)
    series_dir_name = traitlets.Unicode(default_value="")
