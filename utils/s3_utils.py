"""S3 URI parsing helper."""

from __future__ import annotations


def parse_s3_uri(uri: str) -> tuple[str, str]:
    """Parse an S3 URI into (bucket, key).

    >>> parse_s3_uri("s3://my-bucket/path/to/object.json")
    ('my-bucket', 'path/to/object.json')
    """
    if not uri.startswith("s3://"):
        raise ValueError(f"Not a valid S3 URI: {uri}")
    without_prefix = uri[len("s3://"):]
    bucket, _, key = without_prefix.partition("/")
    if not bucket or not key:
        raise ValueError(f"Incomplete S3 URI: {uri}")
    return bucket, key
