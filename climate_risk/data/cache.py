import logging

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

_log = logging.getLogger(__name__)

# A key becomes a filename, so a value carrying a separator would write outside the cache, and one
# carrying the pair separators would make two different parameter sets collide on one entry.
FORBIDDEN_IN_KEY = ("/", "\\", "__", "-")


@dataclass(frozen=True, slots=True)
class CacheFormat[T]:
    """A matched reader and writer. Declaring them together is what stops the two drifting apart."""

    suffix: str
    read: Callable[[Path], T]
    write: Callable[[T, Path], None]


def pandas_csv(**read_kwargs: Any) -> CacheFormat[pd.DataFrame]:
    """A CSV round-trip, where ``read_kwargs`` restore whatever the index was when it was written."""
    return CacheFormat(
        suffix=".csv",
        read=lambda path: pd.read_csv(path, **read_kwargs),
        write=lambda frame, path: frame.to_csv(path),
    )


def geo_shapefile() -> CacheFormat[gpd.GeoDataFrame]:
    return CacheFormat(
        suffix=".shp",
        read=gpd.read_file,
        write=lambda frame, path: frame.to_file(path),
    )


def cache_key(name: str, params: Mapping[str, object] | None = None) -> str:
    """
    Build the cache filename stem for ``name`` under ``params``.

    Parameters are sorted, so the same set always yields the same key however the caller ordered it.

    Parameters
    ----------
    name : str
        Logical name of the cached artefact.
    params : mapping of str to object, optional
        Values distinguishing this entry from others under the same name. Each must be a string,
        integer or boolean. Default None, meaning the name alone identifies the entry.

    Returns
    -------
    str
        A filename stem, such as ``points__grid_size-400__region-laos``.

    Raises
    ------
    ValueError
        If a name or value would not survive being put in a filename.
    """
    parts = [_key_part(name, "name")]
    for key, value in sorted((params or {}).items()):
        parts.append(f"{_key_part(key, 'parameter')}-{_key_part(value, f'value of {key}')}")

    return "__".join(parts)


def _key_part(value: object, described_as: str) -> str:
    if not isinstance(value, str | int | bool):
        raise ValueError(f"{described_as} must be a string, integer or boolean, got {value!r}")

    text = str(value)
    if not text:
        raise ValueError(f"{described_as} must not be empty")

    forbidden = [character for character in FORBIDDEN_IN_KEY if character in text]
    if forbidden:
        raise ValueError(f"{described_as} must not contain {forbidden}, got {text!r}")

    return text


def cached[T](
    cache_dir: Path,
    name: str,
    builder: Callable[[], T],
    fmt: CacheFormat[T],
    *,
    params: Mapping[str, object] | None = None,
    force: bool = False,
) -> T:
    """
    Return the cached artefact for ``name``, building and storing it if it is not already there.

    One implementation of check-then-build-then-write, so a call site cannot spell the key one way
    when it writes and another when it reads.

    Parameters
    ----------
    cache_dir : Path
        Directory to store the artefact in. Created if absent.
    name : str
        Logical name of the artefact.
    builder : callable
        Produces the artefact. Called only on a miss.
    fmt : CacheFormat
        How to read and write it.
    params : mapping of str to object, optional
        Values distinguishing this entry from others under the same name. Default None.
    force : bool, optional
        Rebuild even when the artefact is already cached. Default False.

    Returns
    -------
    The artefact, either read from the cache or freshly built.
    """
    path = (cache_dir / cache_key(name, params)).with_suffix(fmt.suffix)

    if path.exists() and not force:
        _log.info(f"Loading cached {name} from {path}")
        return fmt.read(path)

    _log.info(f"Building {name}")
    artefact = builder()

    cache_dir.mkdir(parents=True, exist_ok=True)
    fmt.write(artefact, path)

    return artefact
