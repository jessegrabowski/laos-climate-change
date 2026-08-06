import hashlib
import logging
import os

from pathlib import Path

import requests

from tqdm.auto import tqdm

from climate_risk.data.source import DataSource

_log = logging.getLogger(__name__)

# Data hosts reject urllib's default agent: the World Bank boundaries archive answers 403 to
# `Python-urllib/3.x` and 200 to a browser, from the same URL.
USER_AGENT = "climate-risk (+https://github.com/jessegrabowski/laos-climate-change)"

CHUNK_BYTES = 1 << 20
TIMEOUT_SECONDS = 60


class ChecksumMismatchError(Exception):
    """Raised when a download's digest does not match the one its DataSource records."""


def sha256_of(path: Path) -> str:
    """Return the lower-case hex SHA-256 of a file, read in chunks so size does not matter."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_BYTES):
            digest.update(chunk)

    return digest.hexdigest()


def fetch(source: DataSource, cache_dir: Path, *, force: bool = False) -> Path:
    """
    Download ``source`` into ``cache_dir`` unless it is already there, and return its path.

    The download goes to a sibling ``.part`` file and is moved into place only once complete, so an
    interrupted transfer can never be mistaken for a cache hit.

    Parameters
    ----------
    source : DataSource
        What to fetch, and the digest to verify it against.
    cache_dir : Path
        Directory to store the file in. Created if absent.
    force : bool, optional
        Re-download even when the file is already present. Default False.

    Returns
    -------
    Path
        The downloaded file.

    Raises
    ------
    ChecksumMismatchError
        If ``source.sha256`` is set and the downloaded bytes do not match it. The partial download
        is left in place, named ``.part``, for inspection.
    """
    destination = source.path(cache_dir)

    if destination.exists() and not force:
        return destination

    cache_dir.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")

    _log.info(f"Downloading {source.filename} from {source.url}")
    with requests.get(source.url, stream=True, timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}) as response:
        response.raise_for_status()
        total = int(response.headers.get("Content-Length", 0))

        with (
            partial.open("wb") as handle,
            tqdm(total=total or None, unit="B", unit_scale=True, desc=source.filename) as progress,
        ):
            for chunk in response.iter_content(chunk_size=CHUNK_BYTES):
                handle.write(chunk)
                progress.update(len(chunk))

    if source.sha256 is not None:
        digest = sha256_of(partial)
        if digest != source.sha256:
            raise ChecksumMismatchError(
                f"{source.filename}: expected sha256 {source.sha256}, got {digest}. "
                f"Upstream may have changed since {source.retrieved}. Partial download left at {partial}."
            )

    os.replace(partial, destination)

    return destination
