"""Inference endpoint and path-translation configuration for the Medical AI POC."""

import os

MODEL_NAME = os.environ.get("MODEL_NAME", "medgemma")

# In-cluster KServe predictor URL. Override with INFERENCE_URL env var.
INFERENCE_URL = os.environ.get(
    "INFERENCE_URL",
    f"http://{MODEL_NAME}-predictor.xnat.svc.cluster.local/v1/models/{MODEL_NAME}:predict",
)

# KServe scale-to-zero cold starts can take several minutes while the model
# weights mount and vLLM spins up.
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "900"))

# PVC path translation. The JupyterHub kernel and the inference pod mount the
# same archive under different prefixes; paths match from AI-POC/ downward.
LOCAL_DATA_ROOT = os.environ.get("LOCAL_DATA_ROOT", "/data/projects/AI-POC")
POD_DATA_ROOT = os.environ.get("POD_DATA_ROOT", "/data/xnat/archive/AI-POC")
