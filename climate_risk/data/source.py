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


@dataclass(frozen=True, slots=True)
class ShapefileArchive:
    """
    A zipped shapefile, together with the layer inside it to read.

    Parameters
    ----------
    source : DataSource
        The archive to fetch.
    member : str
        Path to the layer within the archive, case included. A case-insensitive filesystem hides a
        mismatch here that fails on Linux.

    Raises
    ------
    ValueError
        If ``member`` is empty, or escapes the directory the archive unpacks into.
    """

    source: DataSource
    member: str

    def __post_init__(self) -> None:
        if not self.member:
            raise ValueError(f"{self.source.filename}: member must name a layer inside the archive")

        if Path(self.member).is_absolute() or ".." in Path(self.member).parts:
            raise ValueError(f"{self.source.filename}: member must stay inside the archive, got {self.member!r}")

    def extracted_path(self, directory: Path) -> Path:
        """Return where this archive's layer unpacks to under ``directory``."""
        return directory / self.member
