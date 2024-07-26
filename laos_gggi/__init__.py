import logging
from laos_gggi.data import (
    load_emdat_data,
    load_wb_data,
    load_gpcc_data,
    load_co2_data,
    load_ocean_heat_data,
    load_hadcrut_data,
    load_all_data,
)


_log = logging.getLogger(__name__)

if not logging.root.handlers:
    _log.setLevel(logging.INFO)
    if len(_log.handlers) == 0:
        handler = logging.StreamHandler()
        _log.addHandler(handler)

__all__ = [
    "load_emdat_data",
    "load_wb_data",
    "load_gpcc_data",
    "load_co2_data",
    "load_ocean_heat_data",
    "load_hadcrut_data",
    "load_all_data",
]
