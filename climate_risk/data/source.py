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
class ManualSource:
    """
    One upstream file the user has to place in the cache by hand.

    Carries no URL: these are published under terms that forbid automated download, so there is
    nothing for :func:`climate_risk.data.fetch.fetch` to consume and no way to register one for the
    reachability check.

    Parameters
    ----------
    filename : str
        Name the file is stored under, inside its cache directory. A bare name, never a path.
    homepage : str
        Where a person goes to obtain the file.
    licence : str
        Terms the data is published under, including any restriction on redistribution.
    citation : str
        How to credit the publisher.
    retrieved : str
        ISO date this declaration was last checked against the publisher.

    Raises
    ------
    ValueError
        If ``filename`` carries a path, ``homepage`` is not http(s), or ``retrieved`` is not an ISO
        date.
    """

    filename: str
    homepage: str
    licence: str
    citation: str
    retrieved: str

    def __post_init__(self) -> None:
        if not self.filename or Path(self.filename).name != self.filename:
            raise ValueError(f"{self.homepage}: filename must be a bare name, got {self.filename!r}")

        if not self.homepage.startswith(("http://", "https://")):
            raise ValueError(f"{self.filename}: homepage must be http(s), got {self.homepage!r}")

        try:
            date.fromisoformat(self.retrieved)
        except ValueError as err:
            raise ValueError(f"{self.filename}: retrieved must be an ISO date, got {self.retrieved!r}") from err

    def path(self, directory: Path) -> Path:
        """Return where this source is stored inside ``directory``."""
        return directory / self.filename

    def require(self, directory: Path) -> Path:
        """
        Return the path to the file, raising if nobody has put it there.

        Raises
        ------
        NotImplementedError
            If the file is absent. It cannot be downloaded on the user's behalf.
        """
        path = self.path(directory)
        if not path.exists():
            raise NotImplementedError(
                f"No {self.filename} was found at `{path}`.\n"
                f"Licence: {self.licence}\n"
                f"Obtain it from {self.homepage} and place it at `{path}`."
            )

        return path


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
