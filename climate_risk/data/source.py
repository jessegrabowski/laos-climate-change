from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DataSource:
    """
    One upstream file, declared beside the loader that fetches it.

    Parameters
    ----------
    url : str
        Address to download from.
    filename : str
        Name to store the download under, inside the cache directory. A bare name, never a path.
    licence : str
        Terms the data is published under. EM-DAT is licensed and HydroRIVERS requires attribution.
    citation : str
        How to credit the publisher.
    retrieved : str
        ISO date this declaration was last checked against the publisher.
    """

    url: str
    filename: str
    licence: str
    citation: str
    retrieved: str

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"{self.filename}: url must be http(s), got {self.url!r}")

        # A filename carrying a directory would let a source write outside the cache.
        if not self.filename or Path(self.filename).name != self.filename:
            raise ValueError(f"url {self.url}: filename must be a bare name, got {self.filename!r}")

        try:
            date.fromisoformat(self.retrieved)
        except ValueError as err:
            raise ValueError(f"{self.filename}: retrieved must be an ISO date, got {self.retrieved!r}") from err

    def path(self, cache_dir: Path) -> Path:
        """Return where this source is stored inside ``cache_dir``."""
        return cache_dir / self.filename
