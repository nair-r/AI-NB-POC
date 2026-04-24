"""Inference endpoint and path-translation configuration for the Medical AI POC."""

import os


def _parse_models(raw: str) -> dict[str, str]:
    """Parse MODELS env var as comma-separated 'Label=name' pairs (or bare names)."""
    out: dict[str, str] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if "=" in entry:
            label, name = entry.split("=", 1)
            out[label.strip()] = name.strip()
        else:
            out[entry] = entry
    return out


# Dropdown options: display label -> KServe InferenceService name.
MODELS = _parse_models(os.environ.get("MODELS", "MedGemma=medgemma"))

# In-cluster URL template. {model} is substituted with the selected model name.
INFERENCE_URL_TEMPLATE = os.environ.get(
    "INFERENCE_URL_TEMPLATE",
    "http://{model}-predictor.xnat.svc.cluster.local/v1/models/{model}:predict",
)

# KServe scale-to-zero cold starts can take several minutes while the model
# weights mount and vLLM spins up.
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "900"))

# PVC path translation. The JupyterHub kernel and the inference pod mount the
# same archive under different prefixes, and the first segment under AI-POC/
# differs between the two views (notebook = "experiments", XNAT archive =
# "arc001"). SEGMENT_MAP rewrites that first segment; anything not in the map
# passes through unchanged.
LOCAL_DATA_ROOT = os.environ.get("LOCAL_DATA_ROOT", "/data/projects/AI-POC")
POD_DATA_ROOT = os.environ.get("POD_DATA_ROOT", "/data/xnat/archive/AI-POC")
SEGMENT_MAP = {"experiments": "arc001"}
