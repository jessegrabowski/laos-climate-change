import os
import pathlib

from copy import deepcopy

import pymc as pm
import xarray as xr


def drop_transformed(idata: xr.DataTree, model: pm.Model | None = None) -> xr.DataTree:
    model = pm.modelcontext(model)

    value_var_names = [x.name for x in model.value_vars if x.name.endswith("__")]
    value_var_dims = [x for x in idata.posterior.indexes.keys() if "__dim" in x]

    idata.posterior = idata.posterior.drop_vars(value_var_names).drop_dims(value_var_dims)

    return idata


def sample_or_load(
    fp: str,
    *,
    model: pm.Model | None = None,
    force_resample: bool = False,
    sample_kwargs: dict | None = None,
    compile_kwargs: dict | None = None,
    save_results: bool = True,
) -> xr.DataTree:
    """Sample the model or load the model from disk.

    Parameters
    ----------
    fp: str
        The file path to save/load the inference data.
    model: pm.Model, optional
        The PyMC model to sample. Defaults to None, in which case the currently active model context is used.
    force_resample: bool, optional
        Whether to resample the model, even if data is found at the filepath. Defaults to False.
    sample_kwargs: dict, optional
        Additional keyword arguments to pass to the sampling function.
    compile_kwargs: dict, options
        Pytensor.function kwargs, passed to `sample_posterior_predictive` and `compute_log_likelihood`.
    save_results: bool, optional
        Whether to save the results to disk. Defaults to True.

    Returns
    -------
    idata: xr.DataTree
        The sampled inference data.

    This function performs posterior and posterior predictive sampling of a PyMC model. It either loads the model from disk or samples it using the provided model and sample_kwargs. If the file already exists and resampling is not requested, it loads the data from disk. Otherwise, it samples the model, performs posterior predictive sampling, and saves the resulting inference data to disk.
    """
    _fp = pathlib.Path(fp)

    sample_kwargs = {} if sample_kwargs is None else sample_kwargs
    compile_kwargs = {} if compile_kwargs is None else compile_kwargs

    # Create directory structure if necessary
    os.makedirs(_fp.parent, exist_ok=True)

    # Declared up front: PyMC is untyped, so the sampling branch below infers Any without it.
    idata: xr.DataTree

    if _fp.exists() and not force_resample:
        idata = xr.open_datatree(_fp)
        idata.load()  # Force load to avoid mismatch if the memory is overwritten before idata is used
        return idata

    with pm.modelcontext(model):
        idata = pm.sample(**sample_kwargs)
        if sample_kwargs.get("nuts_sampler", "pymc") == "nutpie":
            idata = drop_transformed(idata)

        idata = pm.sample_posterior_predictive(
            idata, extend_inferencedata=True, compile_kwargs=deepcopy(compile_kwargs)
        )
        idata = pm.compute_log_likelihood(idata, extend_inferencedata=True, compile_kwargs=deepcopy(compile_kwargs))

        if save_results:
            if _fp.exists():
                os.remove(_fp)

            idata.to_netcdf(_fp)

    return idata
