import re

from dataclasses import dataclass
from datetime import date
from pathlib import Path

SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class DataSource:
    """
    One upstream file, declared beside the loader that fetches it.

    ``sha256`` detects drift between what upstream served when ``retrieved`` was recorded and what it
    serves now. It is not provenance: nobody has verified the recorded digest against the publisher.

    Parameters
    ----------
    url : str
        Address to download from.
    filename : str
        Name to store the download under, inside the cache directory. A bare name, never a path.
    licence : str
        Terms the data is published under. EM-DAT is licensed and HydroRIVERS requires attribution,
        so this is load-bearing rather than decorative.
    citation : str
        How to credit the publisher.
    retrieved : str
        ISO date the ``sha256`` was recorded.
    sha256 : str, optional
        Lower-case hex digest of the downloaded bytes. Default None, which skips verification.
    """

    url: str
    filename: str
    licence: str
    citation: str
    retrieved: str
    sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"{self.filename}: url must be http(s), got {self.url!r}")

        # A filename carrying a directory would let a source write outside the cache.
        if Path(self.filename).name != self.filename or not self.filename:
            raise ValueError(f"url {self.url}: filename must be a bare name, got {self.filename!r}")

        if self.sha256 is not None and not SHA256_PATTERN.fullmatch(self.sha256):
            raise ValueError(f"{self.filename}: sha256 must be 64 lower-case hex characters")

        date.fromisoformat(self.retrieved)

    def path(self, cache_dir: Path) -> Path:
        """Return where this source is stored inside ``cache_dir``."""
        return cache_dir / self.filename
