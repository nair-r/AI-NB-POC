"""Centralized application state for the MedGemma dashboard."""

from __future__ import annotations

import traitlets


class AppState(traitlets.HasTraits):
    """Single source of truth shared across all dashboard components."""

    current_dir = traitlets.Any(default_value=None)
    current_ds = traitlets.Any(default_value=None)
    current_png_bytes = traitlets.Bytes(default_value=b"")
    sm_client = traitlets.Any(default_value=None)
