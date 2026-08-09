import logging
import os

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import pandas as pd
import polars as pl

_log = logging.getLogger(__name__)

PARAMETER_SEPARATOR = "__"
VALUE_SEPARATOR = "="

# A key becomes a filename, so a value carrying a path separator would write outside the cache, and
# one carrying a key separator would make two different parameter sets collide on a single entry.
FORBIDDEN_IN_KEY = ("/", "\\", PARAMETER_SEPARATOR, VALUE_SEPARATOR)


@dataclass(frozen=True, slots=True)
class CacheFormat[T]:
    """
    A matched reader and writer. Declaring them together is what stops the two drifting apart.

    Parameters
    ----------
    suffix : str
        File extension the artefact is stored under.
    read : callable
        Reads the artefact back from a path.
    write : callable
        Writes the artefact to a path.
    atomic : bool
        Whether ``write`` can be sent to a temporary path and moved into place. False for formats
        carrying sidecar files, which a single move would leave behind.
    """

    suffix: str
    read: Callable[[Path], T]
    write: Callable[[T, Path], None]
    atomic: bool


def pandas_parquet() -> CacheFormat[pd.DataFrame]:
    """A parquet round-trip. The file carries dtypes and the index, so nothing is restored by hand."""
    return CacheFormat(
        suffix=".parquet",
        read=pd.read_parquet,
        write=lambda frame, path: frame.to_parquet(path),
        atomic=True,
    )


def polars_parquet() -> CacheFormat[pl.DataFrame]:
    """A parquet round-trip for a tidy frame. The file carries dtypes, so nothing is restored by hand."""
    return CacheFormat(
        suffix=".parquet",
        read=pl.read_parquet,
        write=lambda frame, path: frame.write_parquet(path),
        atomic=True,
    )


def geo_parquet() -> CacheFormat[gpd.GeoDataFrame]:
    """A GeoParquet round-trip. Column names, dtypes and CRS all survive, and it is a single file."""
    return CacheFormat(
        suffix=".parquet",
        read=gpd.read_parquet,
        write=lambda frame, path: frame.to_parquet(path),
        atomic=True,
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
        A filename stem, such as ``points__grid_size=400__region=sea``.
    """
    parts = [_key_part(name, "name")]
    for key, value in sorted((params or {}).items()):
        parts.append(f"{_key_part(key, 'parameter')}{VALUE_SEPARATOR}{_key_part(value, f'value of {key}')}")

    return PARAMETER_SEPARATOR.join(parts)


def _key_part(value: object, described_as: str) -> str:
    if not isinstance(value, str | int):
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
    T
        The artefact, read from the cache or freshly built.
    """
    path = (cache_dir / cache_key(name, params)).with_suffix(fmt.suffix)

    if path.exists() and not force:
        _log.info(f"Loading cached {name} from {path}")
        return fmt.read(path)

    cache_dir.mkdir(parents=True, exist_ok=True)

    _log.info(f"Building {name}")
    artefact = builder()

    if fmt.atomic:
        partial = path.with_suffix(path.suffix + ".part")
        fmt.write(artefact, partial)
        os.replace(partial, path)
    else:
        fmt.write(artefact, path)

    return artefact
