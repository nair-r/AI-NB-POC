"""KServe predictor HTTP client and PVC path translation."""

from __future__ import annotations

from pathlib import Path

import requests

from utils.config import (
    INFERENCE_URL,
    LOCAL_DATA_ROOT,
    POD_DATA_ROOT,
    REQUEST_TIMEOUT,
)


def translate_path(local_path: str | Path) -> str:
    """Map a kernel-visible path under LOCAL_DATA_ROOT to the pod's mount."""
    p = Path(local_path).resolve()
    local_root = Path(LOCAL_DATA_ROOT).resolve()
    try:
        rel = p.relative_to(local_root)
    except ValueError as e:
        raise ValueError(
            f"Path {p} is outside {local_root}; cannot translate to pod path."
        ) from e
    return str(Path(POD_DATA_ROOT) / rel)


def predict(payload: dict) -> dict:
    """POST a payload to the KServe predictor and return the parsed JSON response."""
    resp = requests.post(
        INFERENCE_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()
