"""DICOM series to NIfTI conversion and S3 upload for Merlin."""

from __future__ import annotations

import hashlib

import numpy as np


def dicom_series_to_nifti_bytes(datasets: list) -> bytes:
    """Stack DICOM datasets into a 3D NIfTI volume and return gzipped .nii.gz bytes.

    Args:
        datasets: List of pydicom.Dataset objects (one per slice), already sorted.

    Returns:
        Gzipped NIfTI bytes ready for S3 upload.
    """
    import tempfile
    from pathlib import Path

    import nibabel as nib

    slices = [ds.pixel_array for ds in datasets]
    volume = np.stack(slices, axis=-1)  # (rows, cols, num_slices)

    affine = _build_affine(datasets)
    img = nib.Nifti1Image(volume.astype(np.float32), affine)

    with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        nib.save(img, str(tmp_path))
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)


def _build_affine(datasets: list) -> np.ndarray:
    """Build a 4x4 affine matrix from DICOM spatial tags.

    Falls back to identity if tags are missing — Merlin resamples to a fixed
    target shape regardless.
    """
    if not datasets:
        return np.eye(4)

    ds0 = datasets[0]

    try:
        ipp = [float(x) for x in ds0.ImagePositionPatient]
        iop = [float(x) for x in ds0.ImageOrientationPatient]
        ps = [float(x) for x in ds0.PixelSpacing]
        st = float(getattr(ds0, "SliceThickness", 1.0))
    except (AttributeError, TypeError, ValueError):
        return np.eye(4)

    row_cos = np.array(iop[:3])
    col_cos = np.array(iop[3:])
    slice_cos = np.cross(row_cos, col_cos)

    affine = np.eye(4)
    affine[:3, 0] = row_cos * ps[1]
    affine[:3, 1] = col_cos * ps[0]
    affine[:3, 2] = slice_cos * st
    affine[:3, 3] = ipp

    return affine


def series_fingerprint(datasets: list) -> str:
    """Compute a deterministic fingerprint for a DICOM series.

    Uses **sorted SOPInstanceUIDs** from every slice so the hash is
    identical regardless of file-load order or kernel restart. Each
    DICOM file has a globally unique SOPInstanceUID that never changes.
    """
    if not datasets:
        return hashlib.sha256(b"empty").hexdigest()[:16]

    sop_uids = sorted(str(getattr(ds, "SOPInstanceUID", "")) for ds in datasets)
    raw = "|".join(sop_uids)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def volume_exists_in_s3(s3_client, bucket: str, key: str) -> bool:
    """Check whether an S3 object exists (HEAD request)."""
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def upload_volume_to_s3(
    s3_client, nifti_bytes: bytes, bucket: str, prefix: str, fingerprint: str | None = None,
) -> str:
    """Upload NIfTI bytes to S3 and return the s3:// URI.

    If *fingerprint* is provided, uses it as a deterministic key so the same
    series always lands at the same path (enabling cache hits).

    Args:
        s3_client: boto3 S3 client.
        nifti_bytes: Gzipped NIfTI file content.
        bucket: S3 bucket name.
        prefix: Key prefix (e.g. "volumes/").
        fingerprint: Optional deterministic key fragment.

    Returns:
        Full S3 URI, e.g. "s3://bucket/volumes/abc123.nii.gz".
    """
    name = fingerprint if fingerprint else hashlib.sha256(nifti_bytes).hexdigest()[:16]
    key = f"{prefix}{name}.nii.gz"
    s3_client.put_object(Bucket=bucket, Key=key, Body=nifti_bytes)
    return f"s3://{bucket}/{key}"
