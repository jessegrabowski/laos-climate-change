import logging

from climate_risk.data_functions import (
    annual_precipitation,
    build_country_year_panel,
    build_time_series,
    load_co2_data,
    load_emdat_events,
    load_gpcc_data,
    load_hadcrut_data,
    load_ocean_heat_data,
    load_rivers_data,
    load_shapefile,
    load_wb_data,
    process_ipcc_scenarios,
)

_log = logging.getLogger(__name__)

if not logging.root.handlers:
    _log.setLevel(logging.INFO)
    if len(_log.handlers) == 0:
        handler = logging.StreamHandler()
        _log.addHandler(handler)

__all__ = [
    "annual_precipitation",
    "build_country_year_panel",
    "build_time_series",
    "load_co2_data",
    "load_emdat_events",
    "load_gpcc_data",
    "load_hadcrut_data",
    "load_ocean_heat_data",
    "load_rivers_data",
    "load_shapefile",
    "load_wb_data",
    "process_ipcc_scenarios",
]
