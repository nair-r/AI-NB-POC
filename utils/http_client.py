"""KServe predictor HTTP client and PVC path translation."""

from __future__ import annotations

from pathlib import Path

import requests

from utils.config import (
    INFERENCE_URL_TEMPLATE,
    LOCAL_DATA_ROOT,
    POD_DATA_ROOT,
    REQUEST_TIMEOUT,
    SEGMENT_MAP,
)


def translate_path(local_path: str | Path) -> str:
    """Map a kernel-visible path under LOCAL_DATA_ROOT to the pod's mount.

    Rewrites the first path segment under LOCAL_DATA_ROOT using SEGMENT_MAP
    (e.g. 'experiments' -> 'arc001'); segments not in the map pass through.
    """
    p = Path(local_path).resolve()
    local_root = Path(LOCAL_DATA_ROOT).resolve()
    try:
        rel = p.relative_to(local_root)
    except ValueError as e:
        raise ValueError(
            f"Path {p} is outside {local_root}; cannot translate to pod path."
        ) from e
    parts = list(rel.parts)
    if parts and parts[0] in SEGMENT_MAP:
        parts[0] = SEGMENT_MAP[parts[0]]
    return str(Path(POD_DATA_ROOT).joinpath(*parts)) if parts else POD_DATA_ROOT


def predict(payload: dict, model_name: str) -> dict:
    """POST a payload to the KServe predictor for the given model."""
    url = INFERENCE_URL_TEMPLATE.format(model=model_name)
    resp = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()
